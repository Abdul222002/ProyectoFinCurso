import { useNavigate, useParams } from 'react-router-dom';
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { leaguesAPI, auctionAPI, packsAPI } from '../services/endpoints';
import PackOpeningModal from '../components/PackOpeningModal';
import { toast } from 'sonner';
import './LeagueDetailPage.css';

export default function LeagueDetailPage() {
  const navigate = useNavigate();
  const { leagueId } = useParams();
  const { user, refreshUser } = useAuth();

  const [league, setLeague] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('standings');
  const [message, setMessage] = useState('');

  // Auction state
  const [auction, setAuction] = useState(null);
  const [auctionLoading, setAuctionLoading] = useState(false);
  const [timeLeft, setTimeLeft] = useState('');
  const [bidAmounts, setBidAmounts] = useState({});
  const [bidding, setBidding] = useState(null);
  const [selectedPlayerForDetail, setSelectedPlayerForDetail] = useState(null);

  // User listings state
  const [listings, setListings] = useState([]);
  const [listingsLoading, setListingsLoading] = useState(false);

  // System offers state
  const [offers, setOffers] = useState([]);

  // Packs state
  const [opening, setOpening] = useState(false);
  const [packResult, setPackResult] = useState(null);
  const [packHistory, setPackHistory] = useState([]);

  // Invite state
  const [inviteUsername, setInviteUsername] = useState('');
  const [inviting, setInviting] = useState(false);

  const loadLeague = useCallback(async () => {
    setLoading(true);
    try {
      const res = await leaguesAPI.getDetail(leagueId);
      setLeague(res.data);
    } catch {
      setLeague(null);
    }
    setLoading(false);
  }, [leagueId]);

  useEffect(() => { loadLeague(); }, [loadLeague]);

  // Load auction
  const loadAuction = useCallback(async () => {
    setAuctionLoading(true);
    try {
      const res = await auctionAPI.getAuction(leagueId);
      setAuction(res.data);
    } catch {
      setAuction(null);
    }
    setAuctionLoading(false);
  }, [leagueId]);

  // Silent versions for polling - no loading spinner flash
  const pollAuction = useCallback(async () => {
    try {
      const res = await auctionAPI.getAuction(leagueId);
      setAuction(res.data);
    } catch { /* silently fail */ }
  }, [leagueId]);

  const pollListings = useCallback(async () => {
    try {
      const res = await auctionAPI.getListings(leagueId);
      setListings(Array.isArray(res.data) ? res.data : []);
    } catch { /* silently fail */ }
  }, [leagueId]);

  const loadListings = useCallback(async () => {
    setListingsLoading(true);
    try {
      const res = await auctionAPI.getListings(leagueId);
      setListings(Array.isArray(res.data) ? res.data : []);
    } catch { setListings([]); }
    setListingsLoading(false);
  }, [leagueId]);

  const loadOffers = useCallback(async () => {
    try {
      const res = await auctionAPI.getOffers(leagueId);
      setOffers(Array.isArray(res.data) ? res.data : []);
    } catch { setOffers([]); }
  }, [leagueId]);

  useEffect(() => {
    if (activeTab === 'market') { loadAuction(); loadListings(); loadOffers(); }
    const interval = setInterval(() => {
      if (activeTab === 'market') { pollAuction(); pollListings(); }
    }, 10000);
    return () => clearInterval(interval);
  }, [activeTab, loadAuction, loadListings, loadOffers, pollAuction, pollListings]);

  // Countdown timer
  useEffect(() => {
    if (!auction?.ends_at) return;
    const interval = setInterval(() => {
      const now = new Date().getTime();
      const end = new Date(auction.ends_at).getTime(); // is ISO string
      const distance = end - now;

      if (distance < 0) {
        setTimeLeft('SUBASTA FINALIZADA');
        if (auction.is_active) loadAuction(); // Reload to see if new one started
      } else {
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        setTimeLeft(`${hours}h ${minutes}m ${seconds}s`);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [auction]);

  // Load pack history
  const loadPackHistory = useCallback(async () => {
    try {
      const res = await packsAPI.history(leagueId);
      setPackHistory(res.data);
    } catch {
      setPackHistory([]);
    }
  }, [leagueId]);

  useEffect(() => {
    if (activeTab === 'packs') loadPackHistory();
  }, [activeTab, loadPackHistory]);

  const handleBid = async (slotId, currentBid, basePrice) => {
    const amount = parseInt(bidAmounts[slotId]);
    if (!amount) return;

    // Validations (min bid)
    const minBid = currentBid > 0 ? currentBid + 1 : basePrice;
    if (amount < minBid) {
      setMessage(`❌ La puja debe ser al menos ${formatPrice(minBid)}`);
      return;
    }

    setBidding(slotId);
    try {
      const res = await auctionAPI.placeBid(leagueId, slotId, amount);
      setMessage(`✅ ${res.data.message}`);
      // Force reload to get updated status
      loadAuction();
      // Clear input
      setBidAmounts(prev => ({ ...prev, [slotId]: '' }));
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Error al pujar'}`);
    }
    setBidding(null);
  };

  const handleWithdrawBid = async (slotId) => {
    toast.warning('¿Seguro que quieres retirar tu puja?', {
      cancel: { label: 'Cancelar' },
      action: {
        label: 'Sí, retirar',
        onClick: async () => {
          setBidding(slotId);
          try {
            const res = await auctionAPI.withdrawBid(leagueId, slotId);
            setMessage(`✅ ${res.data.message}`);
            loadAuction();
          } catch (err) {
            setMessage(`❌ ${err.response?.data?.detail || 'Error al retirar puja'}`);
          }
          setBidding(null);
        }
      }
    });
  };

  const handleOpenPack = async () => {
    if (opening) return;

    // Find user's league membership to get specific league coins
    const myMembership = league?.members?.find(m => m.user_id === user?.id);
    const leagueCoins = myMembership ? myMembership.coins : 0;

    if (leagueCoins < 150000000) {
      setMessage('❌ Necesitas 150.000.000 monedas en esta liga para abrir un sobre de iconos');
      setTimeout(() => setMessage(''), 4000);
      return;
    }
    setOpening(true);
    setPackResult(null);
    try {
      const res = await packsAPI.openIcon(leagueId);
      setPackResult(res.data);
      setMessage(`✅ ${res.data.message}`);
      if (refreshUser) refreshUser();
      loadPackHistory();
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Error al abrir sobre'}`);
    }
    setOpening(false);
  };

  const handleInvite = async () => {
    const input = inviteUsername.trim();
    if (!input) return;
    
    setInviting(true);
    
    // Determine if input is an email or username
    const isEmail = input.includes('@') && input.includes('.');
    const payload = isEmail ? { email: input } : { username: input };
    
    try {
      await leaguesAPI.invite(leagueId, payload);
      setMessage(`✅ Invitación enviada a ${input}`);
      setInviteUsername('');
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Error al invitar'}`);
    }
    setInviting(false);
  };

  const handleLeave = async () => {
    toast.error('¿Seguro que quieres salir de esta liga?', {
      cancel: { label: 'Cancelar' },
      action: {
        label: 'Sí, salir',
        onClick: async () => {
          try {
            await leaguesAPI.leave(leagueId);
            navigate('/leagues');
          } catch (err) {
            setMessage(`❌ ${err.response?.data?.detail || 'Error'}`);
          }
        }
      }
    });
  };

  const handleKick = async (memberId, memberUsername) => {
    toast.error(`¿Seguro que quieres expulsar a @${memberUsername} de la liga?`, {
      cancel: { label: 'Cancelar' },
      action: {
        label: 'Expulsar',
        onClick: async () => {
          try {
            await leaguesAPI.kickMember(leagueId, memberId);
            setMessage(`✅ @${memberUsername} ha sido expulsado.`);
            loadLeague();
          } catch (err) {
            setMessage(`❌ ${err.response?.data?.detail || 'Error al expulsar jugador'}`);
          }
        }
      }
    });
  };

  const formatPrice = (price) => {
    if (price >= 1000000000) return (price / 1000000000).toFixed(1) + 'B';
    if (price >= 1000000) return (price / 1000000).toFixed(1) + 'M';
    if (price >= 1000) return (price / 1000).toFixed(0) + 'K';
    return price?.toLocaleString() || '0';
  };

  const getRarityColor = (rarity) => {
    switch (rarity) {
      case 'gold': return '#fbbf24';
      case 'silver': return '#94a3b8';
      case 'legend': return '#a78bfa';
      default: return '#cd7f32';
    }
  };

  if (loading) {
    return (
      <div className="ld-page">
        <div className="ld-loading">Cargando liga...</div>
      </div>
    );
  }

  if (!league) {
    return (
      <div className="ld-page">
        <header className="ld-header">
          <button className="ld-back-btn" onClick={() => navigate('/leagues')}>←</button>
          <h1>Liga no encontrada</h1>
        </header>
      </div>
    );
  }

  // Find user's league membership to get specific league coins
  const myMembership = league?.members?.find(m => m.user_id === user?.id);
  const leagueCoins = myMembership ? myMembership.coins : 0;

  // Calculate coins locked in active winning bids so user can see real available balance
  const lockedCoins = auction?.slots?.reduce((total, slot) => {
    if (slot.highest_bidder_id === user?.id && slot.current_bid > 0) {
      return total + slot.current_bid;
    }
    return total;
  }, 0) || 0;
  const availableCoins = leagueCoins - lockedCoins;

  return (
    <div className="ld-page">
      {/* Header */}
      <header className="ld-header">
        <button className="ld-back-btn" onClick={() => navigate('/leagues')}>←</button>
        <div className="ld-header-info">
          <h1 className="ld-title">🏆 {league.name}</h1>
          <span className="ld-subtitle">
            👥 {league.member_count}/{league.max_members} · Código: <strong>{league.invite_code}</strong>
          </span>
        </div>
        <div className="ld-coins-wrap">
          <div className="ld-coins">🪙 {formatPrice(availableCoins)}</div>
          {lockedCoins > 0 && (
            <div className="ld-coins-locked" title="Monedas bloqueadas en pujas activas">🔒 {formatPrice(lockedCoins)}</div>
          )}
        </div>
      </header>

      {/* Message */}
      {message && (
        <div className={`ld-message ${message.startsWith('✅') ? 'success' : 'error'}`}>
          {message}
          <button className="ld-msg-close" onClick={() => setMessage('')}>✕</button>
        </div>
      )}

      {/* Player Detail Modal */}
      {selectedPlayerForDetail && (
        <PlayerDetailModal
          playerId={selectedPlayerForDetail.player_id}
          playerObj={selectedPlayerForDetail}
          onClose={() => setSelectedPlayerForDetail(null)}
        />
      )}

      {/* Tabs */}
      <div className="ld-tabs">
        <button className={`ld-tab ${activeTab === 'standings' ? 'active' : ''}`} onClick={() => setActiveTab('standings')}>
          🏅 Clasificación
        </button>
        <button className="ld-tab" onClick={() => navigate(`/team?league_id=${leagueId}`)}>
          ⚽ Mi Equipo
        </button>
        <button className={`ld-tab ${activeTab === 'market' ? 'active' : ''}`} onClick={() => setActiveTab('market')}>
          📈 Mercado
        </button>
        <button className={`ld-tab ${activeTab === 'packs' ? 'active' : ''}`} onClick={() => setActiveTab('packs')}>
          🎴 Sobres
        </button>
        <button className={`ld-tab ${activeTab === 'info' ? 'active' : ''}`} onClick={() => setActiveTab('info')}>
          ℹ️ Info
        </button>
      </div>

      {/* ==== STANDINGS TAB ==== */}
      {activeTab === 'standings' && (
        <div className="ld-content">
          <div className="ld-standings">
            {league.members?.sort((a, b) => b.league_points - a.league_points).map((member, idx) => {
              const isAdmin = myMembership?.is_admin || league.owner_id === user?.id;
              const isOwner = league.owner_id === member.user_id;
              const isSelf = member.user_id === user?.id;

              return (
                <div
                  key={member.id}
                  className={`ld-member-row ${isSelf ? 'me' : ''}`}
                  onClick={() => navigate(`/team?league_id=${leagueId}&user_id=${member.user_id}`)}
                  style={{ cursor: 'pointer' }}
                  title={`Ver equipo de @${member.username}`}
                >
                  <span className="ld-rank">{idx + 1}</span>
                  <div className="ld-member-info">
                    <span className="ld-member-name">
                      @{member.username}
                      {member.is_admin && ' 👑'}
                    </span>
                    <span className="ld-member-pts">{member.league_points} pts</span>
                  </div>
                  {isAdmin && !isOwner && !isSelf && (
                    <button
                      className="ld-leave-btn"
                      style={{ padding: '4px 12px', fontSize: '0.8rem', marginLeft: '10px', marginTop: '0', width: 'auto' }}
                      onClick={(e) => { e.stopPropagation(); handleKick(member.user_id, member.username); }}
                      title="Expulsar jugador"
                    >
                      🥾 Expulsar
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ==== MARKET TAB (AUCTION) ==== */}
      {activeTab === 'market' && (
        <div className="ld-content">
          <div className="ld-auction-header">
            <h2>⏳ Subasta Diaria</h2>
            <div className="ld-timer">
              {timeLeft || 'Calculando...'}
            </div>
          </div>
          <p className="ld-auction-desc">
            Los mejores postores al finalizar el tiempo se llevan a los jugadores.
          </p>

          <div className="ld-market-list">
            {auctionLoading ? (
              <div className="ld-loading-small">Cargando subasta...</div>
            ) : !auction || auction.slots.length === 0 ? (
              <div className="ld-empty">No hay subasta activa</div>
            ) : (
              <div className="ld-market-list-view">
                <div className="ld-market-list-header">
                  <div>Jugador</div>
                  <div style={{ textAlign: 'right' }}>Puja / Base</div>
                  <div style={{ textAlign: 'right' }}>Acción</div>
                </div>
                {auction.slots.map(slot => {
                  const minBid = slot.current_bid > 0 ? slot.current_bid + 1 : slot.base_price;
                  const hasBid = slot.user_has_bid;

                  return (
                    <div
                      key={slot.id}
                      className="ld-market-row"
                      onClick={() => setSelectedPlayerForDetail({ ...slot, name: slot.player_name, current_price: slot.base_price })}
                      style={{ cursor: 'pointer' }}
                    >
                      <div className={`ld-market-row-accent ${hasBid ? 'winning' : 'neutral'}`}></div>

                      {/* Player Info Col */}
                      <div className="ld-market-row-info-col">
                        <div className="ld-market-row-img-wrap" style={{ borderBottomColor: getRarityColor(slot.base_rarity) }}>
                          <img
                            src={slot.image_url || '/images/placeholder.png'}
                            alt={slot.player_name}
                            className="ld-market-row-img"
                            onError={(e) => { e.target.src = '/images/placeholder.png'; }}
                          />
                          <div className="ld-market-row-pos">{slot.position}</div>
                        </div>
                        <div className="ld-market-row-details">
                          <div className="ld-market-row-name">{slot.player_name}</div>
                          <div className="ld-market-row-team">
                            <span style={{ color: getRarityColor(slot.base_rarity) }}>OVR {slot.overall_rating}</span>
                            <span>•</span>
                            <span>{hasBid ? 'Has pujado' : 'No has pujado'}</span>
                            <span>•</span>
                            <span style={{ color: '#fbbf24', fontWeight: 'bold', fontSize: '1.05rem', textShadow: '0 0 5px rgba(251, 191, 36, 0.3)' }}>{slot.bid_count} {slot.bid_count === 1 ? 'puja' : 'pujas'}</span>
                          </div>
                        </div>
                      </div>

                      {/* Price Col */}
                      <div className="ld-market-row-price-col">
                        <div className={`ld-market-row-price ${slot.current_bid > 0 ? 'highlight' : ''}`}>
                          {formatPrice(slot.current_bid > 0 ? slot.current_bid : slot.base_price)}
                        </div>
                        <div className="ld-market-row-subprice">
                          {slot.current_bid > 0 ? `Base: ${formatPrice(slot.base_price)}` : 'Precio Base'}
                        </div>
                      </div>

                      {/* Action Col */}
                      <div className="ld-market-row-action-col" onClick={(e) => e.stopPropagation()}>
                        <div className="ld-market-row-bid-wrap">
                          <input
                            type="number"
                            placeholder={hasBid ? 'Subir a...' : `Mín: ${formatPrice(minBid)}`}
                            value={bidAmounts[slot.id] || ''}
                            onChange={(e) => setBidAmounts({ ...bidAmounts, [slot.id]: e.target.value })}
                            className="ld-market-row-input"
                          />
                          <button
                            className="ld-market-row-btn primary"
                            onClick={() => handleBid(slot.id, slot.current_bid, slot.base_price)}
                            disabled={bidding === slot.id}
                            title={hasBid ? 'Pujar de nuevo si crees que alguien ha superado tu puja.' : ''}
                          >
                            {bidding === slot.id ? '...' : (hasBid ? 'Pujar' : 'Pujar')}
                          </button>
                          {hasBid && (
                            <button
                              className="ld-market-row-btn danger"
                              onClick={() => handleWithdrawBid(slot.id)}
                              disabled={bidding === slot.id}
                              style={{ marginLeft: '4px' }}
                            >
                              Retirar
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* ═══ SYSTEM OFFERS ═══ */}
          {offers.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <h2 style={{ fontSize: '1rem', fontWeight: 800, color: '#fbbf24', marginBottom: 12 }}>🤖 Ofertas del Sistema</h2>
              <p className="ld-auction-desc">El sistema te ha hecho una oferta por tus jugadores en venta.</p>
              <div className="ld-market-list-view">
                {offers.map(offer => (
                  <div key={offer.id} className="ld-market-row">
                    <div className="ld-market-row-accent warning"></div>

                    {/* Player Info Col */}
                    <div className="ld-market-row-info-col">
                      <div className="ld-market-row-img-wrap" style={{ borderBottomColor: '#fbbf24' }}>
                        <div className="ld-player-fallback" style={{ display: 'flex', width: '100%', height: '100%', alignItems: 'center', justifyContent: 'center' }}>🤖</div>
                      </div>
                      <div className="ld-market-row-details">
                        <div className="ld-market-row-name">{offer.player_name}</div>
                        <div className="ld-market-row-team">
                          <span style={{ color: '#fbbf24' }}>Oferta del Sistema</span>
                        </div>
                      </div>
                    </div>

                    {/* Price Col */}
                    <div className="ld-market-row-price-col">
                      <div className="ld-market-row-price highlight">
                        {formatPrice(offer.offer_price)}
                      </div>
                      <div className="ld-market-row-subprice" style={{ color: '#ef4444' }}>
                        Tú pedías: {formatPrice(offer.asking_price)}
                      </div>
                    </div>

                    {/* Action Col */}
                    <div className="ld-market-row-action-col" onClick={e => e.stopPropagation()}>
                      <div className="ld-market-row-bid-wrap">
                        <div style={{ fontSize: '0.7rem', color: '#64748b', marginRight: '8px', textAlign: 'right', lineHeight: 1.2 }}>
                          Expira:<br />{new Date(offer.expires_at).toLocaleString('es-ES', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                        </div>
                        <button
                          className="ld-market-row-btn primary"
                          onClick={async () => {
                            try {
                              const res = await auctionAPI.acceptOffer(leagueId, offer.id);
                              setMessage(`✅ ${res.data.message}`);
                              loadOffers(); loadListings();
                            } catch (err) { setMessage(`❌ ${err.response?.data?.detail || 'Error'}`); }
                          }}
                        >
                          Aceptar
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ═══ USER LISTINGS ═══ */}
          <div style={{ marginTop: 24 }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 800, color: '#e2e8f0', marginBottom: 12 }}>🏷️ Jugadores en Venta</h2>
            <p className="ld-auction-desc">Jugadores puestos a la venta por usuarios de la liga.</p>

            {listingsLoading ? (
              <div className="ld-loading-small">Cargando listados...</div>
            ) : listings.length === 0 ? (
              <div className="ld-empty">No hay jugadores en venta</div>
            ) : (
              <div className="ld-market-list-view">
                {listings.map(listing => (
                  <div
                    key={listing.id}
                    className="ld-market-row"
                    style={{ cursor: 'pointer' }}
                    onClick={() => setSelectedPlayerForDetail({
                      ...listing,
                      name: listing.player_name,
                      current_price: listing.asking_price,
                      current_market_value: listing.asking_price
                    })}
                  >
                    <div className={`ld-market-row-accent ${listing.is_mine ? 'warning' : 'neutral'}`}></div>

                    {/* Player Info Col */}
                    <div className="ld-market-row-info-col">
                      <div className="ld-market-row-img-wrap" style={{ borderBottomColor: getRarityColor(listing.base_rarity) }}>
                        <img
                          src={listing.image_url || '/images/placeholder.png'}
                          alt={listing.player_name}
                          className="ld-market-row-img"
                          onError={(e) => { e.target.src = '/images/placeholder.png'; }}
                        />
                        <div className="ld-market-row-pos">{listing.position}</div>
                      </div>
                      <div className="ld-market-row-details">
                        <div className="ld-market-row-name">{listing.player_name}</div>
                        <div className="ld-market-row-team">
                          <span style={{ color: getRarityColor(listing.base_rarity) }}>OVR {listing.overall_rating}</span>
                          <span>•</span>
                          <span>Venta de: @{listing.seller_username}</span>
                        </div>
                      </div>
                    </div>

                    {/* Price Col */}
                    <div className="ld-market-row-price-col">
                      <div className="ld-market-row-price highlight">
                        {formatPrice(listing.asking_price)}
                      </div>
                      <div className="ld-market-row-subprice">
                        Precio
                      </div>
                    </div>

                    {/* Action Col */}
                    <div className="ld-market-row-action-col" onClick={e => e.stopPropagation()}>
                      <div className="ld-market-row-bid-wrap">
                        {listing.is_mine ? (
                          <button
                            className="ld-market-row-btn danger"
                            onClick={async () => {
                              try {
                                await auctionAPI.cancelListing(leagueId, listing.id);
                                setMessage('✅ Listado cancelado');
                                loadListings();
                              } catch (err) { setMessage(`❌ ${err.response?.data?.detail || 'Error'}`); }
                            }}
                          >
                            Retirar
                          </button>
                        ) : (
                          <button
                            className="ld-market-row-btn primary"
                            onClick={async () => {
                              try {
                                const res = await auctionAPI.buyListing(leagueId, listing.id);
                                setMessage(`✅ ${res.data.message}`);
                                loadListings();
                              } catch (err) { setMessage(`❌ ${err.response?.data?.detail || 'Error'}`); }
                            }}
                          >
                            Comprar
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ==== PACKS TAB — Premium Design ==== */}
      {activeTab === 'packs' && (
        <div className="ld-content">
          <div className="ld-packs-premium">
            {/* Background effects */}
            <div className="ld-pack-rays">
              {[0, 45, 90, 135, 180, 225, 270, 315].map(deg => (
                <div key={deg} className="ld-pack-ray" style={{ transform: `rotate(${deg}deg)` }} />
              ))}
              <div className="ld-pack-center-glow" />
              <div className="ld-pack-center-glow-inner" />
            </div>

            {/* Floating particles */}
            <div className="ld-pack-particle" style={{ top: '20%', left: '15%', animationDelay: '0s' }} />
            <div className="ld-pack-particle" style={{ top: '30%', right: '20%', animationDelay: '1.5s' }} />
            <div className="ld-pack-particle" style={{ bottom: '25%', left: '25%', animationDelay: '0.8s' }} />
            <div className="ld-pack-particle" style={{ top: '50%', right: '10%', animationDelay: '2s' }} />

            {/* Top label */}
            <div className="ld-pack-top-label">
              <div className="ld-pack-live-dot" />
              <span>Legendary Scottish Pack</span>
            </div>

            {/* The Pack */}
            <div className="ld-pack-container">
              <div className="ld-pack-energy-flare" />
              <div className="ld-pack-card-wrapper">
                <div className="ld-pack-card-premium">
                  <div className="ld-pack-card-gradient" />
                  <div className="ld-pack-card-content">
                    <div className="ld-pack-card-circle">
                      <span>🏆</span>
                    </div>
                    <div className="ld-pack-card-badge-text">LEGENDARY</div>
                    <div className="ld-pack-card-sub">SCOTTISH PREMIERSHIP</div>
                  </div>
                  <div className="ld-pack-foil-shine" />
                </div>
              </div>
            </div>

            {/* Pack info */}
            <div className="ld-pack-info-area">
              <p className="ld-pack-info-desc">Contiene <strong>1 carta legendaria</strong> aleatoria</p>
              <div className="ld-pack-price-tag">🪙 150.000.000</div>
            </div>

            {/* Open button */}
            <button
              className={`ld-pack-open-btn ${opening ? 'opening' : ''}`}
              onClick={handleOpenPack}
              disabled={opening}
            >
              <span className="ld-pack-btn-text">
                {opening ? '⚽ Abriendo...' : '⚡ ABRIR SOBRE'}
              </span>
              <div className="ld-pack-btn-shine" />
            </button>
          </div>

          {/* Pack Result Modal */}
          {packResult && packResult.cards && (
            <PackOpeningModal
              cards={packResult.cards}
              remainingCoins={packResult.remaining_coins}
              onClose={() => {
                setPackResult(null);
                loadLeague();
              }}
            />
          )}

          {/* Pack History */}
          {packHistory.length > 0 && (
            <div className="ld-pack-history">
              <h3>Historial de sobres</h3>
              {packHistory.map(p => (
                <div key={p.id} className="ld-history-row">
                  <span>🎴 Sobre de Iconos</span>
                  <span>{p.cards_obtained} cartas</span>
                  <span>{new Date(p.opened_at).toLocaleDateString()}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ==== INFO TAB ==== */}
      {
        activeTab === 'info' && (
          <div className="ld-content">
            <div className="ld-info-section">
              <div className="ld-info-card">
                <h3>📋 Información de la Liga</h3>
                <div className="ld-info-row">
                  <span>Nombre</span>
                  <strong>{league.name}</strong>
                </div>
                {league.description && (
                  <div className="ld-info-row">
                    <span>Descripción</span>
                    <span>{league.description}</span>
                  </div>
                )}
                <div className="ld-info-row">
                  <span>Propietario</span>
                  <span>@{league.owner_username}</span>
                </div>
                <div className="ld-info-row">
                  <span>Miembros</span>
                  <span>{league.member_count} / {league.max_members}</span>
                </div>
                <div className="ld-info-row">
                  <span>Código de invitación</span>
                  <strong className="ld-invite-code">{league.invite_code}</strong>
                </div>
                <div className="ld-info-row">
                  <span>Creada</span>
                  <span>{new Date(league.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              {/* Invite */}
              <div className="ld-info-card">
                <h3>📩 Invitar amigo</h3>
                <div className="ld-invite-form">
                  <input
                    type="text"
                    value={inviteUsername}
                    onChange={(e) => setInviteUsername(e.target.value)}
                    placeholder="Username del amigo"
                    className="ld-input"
                  />
                  <button className="ld-invite-btn" onClick={handleInvite} disabled={inviting}>
                    {inviting ? '...' : 'Enviar'}
                  </button>
                </div>
              </div>

              {/* Leave */}
              <button className="ld-leave-btn" onClick={handleLeave}>
                🚪 Salir de la liga
              </button>
            </div>
          </div>
        )
      }

      {/* Bottom Nav */}
      <div className="ld-bottom-bar">
        <button className="ld-bottom-btn" onClick={() => navigate('/dashboard')}>🏠 Home</button>
        <button className="ld-bottom-btn" onClick={() => navigate(`/team?league=${leagueId}`)}>⚽ Equipo</button>
        <button className="ld-bottom-btn active">🏆 Liga</button>
      </div>
    </div >
  );
}
