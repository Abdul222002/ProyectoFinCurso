import { useNavigate, useParams } from 'react-router-dom';
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { leaguesAPI, auctionAPI, packsAPI, authAPI } from '../services/endpoints';
import PackOpeningModal from '../components/PackOpeningModal';
import PlayerDetailModal from '../components/PlayerDetailModal';
import { toast } from 'sonner';
import AppLayout from '../components/AppLayout';
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

  // Invite state
  const [inviteUsername, setInviteUsername] = useState('');
  const [inviting, setInviting] = useState(false);
  
  // Pack history and opening state
  const [packHistory, setPackHistory] = useState([]);
  const [packResult, setPackResult] = useState(null);
  const [opening, setOpening] = useState(false);
  const [expandedPacks, setExpandedPacks] = useState(new Set());

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const showMessage = (msg) => {
    setMessage(msg);
    setTimeout(() => setMessage(''), 4000);
  };

  const myMembership = league?.members?.find(m => m.user_id === user?.id);
  const myCoins = myMembership?.coins || 0;
  const myLockedCoins = myMembership?.locked_coins || 0;
  const freeCoins = myCoins - myLockedCoins;
  const displayAvailable = freeCoins;

  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    const delayFn = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await authAPI.searchUsers(searchQuery);
        setSearchResults(res.data || []);
      } catch (err) {
        setSearchResults([]);
      }
      setSearching(false);
    }, 300);
    return () => clearTimeout(delayFn);
  }, [searchQuery]);

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
      if (activeTab === 'market' && document.visibilityState === 'visible') { 
        pollAuction(); pollListings(); 
      }
    }, 10000);
    return () => clearInterval(interval);
  }, [activeTab, loadAuction, loadListings, loadOffers, pollAuction, pollListings]);

  useEffect(() => {
    if (!auction?.ends_at) return;
    const interval = setInterval(() => {
      const now = new Date().getTime();
      const end = new Date(auction.ends_at).getTime();
      const distance = end - now;

      if (distance < 0) {
        setTimeLeft('SUBASTA FINALIZADA');
        if (auction.is_active) loadAuction();
      } else {
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        setTimeLeft(`${hours}h ${minutes}m ${seconds}s`);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [auction, loadAuction]);

  const loadPackHistory = useCallback(async () => {
    try {
      const res = await packsAPI.history(leagueId);
      setPackHistory(Array.isArray(res.data) ? res.data : []);
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

    const minBid = currentBid > 0 ? currentBid + 1 : basePrice;
    if (amount < minBid) {
      showMessage(`❌ La puja debe ser al menos ${formatPrice(minBid)}`);
      return;
    }

    setBidding(slotId);
    try {
      const res = await auctionAPI.placeBid(leagueId, slotId, amount);
      showMessage(`✅ ${res.data.message}`);
      await Promise.all([loadAuction(), loadLeague()]);
      setBidAmounts(prev => ({ ...prev, [slotId]: '' }));
    } catch (err) {
      showMessage(`❌ ${err.response?.data?.detail || 'Error al pujar'}`);
    }
    setBidding(null);
  };

  const executeWithdraw = async (slotId) => {
    setBidding(slotId);
    try {
      const res = await auctionAPI.withdrawBid(leagueId, slotId);
      showMessage(`✅ ${res.data.message}`);
      await new Promise(resolve => setTimeout(resolve, 300));
      await Promise.all([loadAuction(), loadLeague()]);
    } catch (err) {
      showMessage(`❌ ${err.response?.data?.detail || 'Error al retirar puja'}`);
    }
    setBidding(null);
  };

  const handleWithdrawBid = (slotId) => {
    toast.warning('¿Seguro que quieres retirar tu puja?', {
      cancel: { label: 'Cancelar' },
      action: { label: 'Sí, retirar', onClick: () => executeWithdraw(slotId) }
    });
  };

  const handleOpenPack = async () => {
    if (opening) return;
    if (myCoins < 150000000) {
      showMessage(`❌ No tienes suficientes monedas. Necesitas 150.000.000, tienes ${myCoins.toLocaleString('es-ES')}`);
      return;
    }
    setOpening(true);
    setPackResult(null);
    try {
      const res = await packsAPI.openIcon(leagueId);
      setPackResult(res.data);
      showMessage(`✅ ${res.data.message}`);
      if (refreshUser) refreshUser();
      loadPackHistory();
    } catch (err) {
      showMessage(`❌ ${err.response?.data?.detail || 'Error al abrir sobre'}`);
    }
    setOpening(false);
  };

  const handleInvite = async (targetUser = null) => {
    let input = (targetUser || inviteUsername).trim();
    if (!input) return;
    setInviting(true);
    
    const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input);
    input = input.startsWith('@') ? input.slice(1) : input;
    const payload = isEmail ? { email: input } : { username: input };
    
    try {
      await leaguesAPI.invite(leagueId, payload);
      showMessage(`✅ Invitación enviada a ${input}`);
      setInviteUsername('');
      setSearchQuery('');
      setSearchResults([]);
    } catch (err) {
      showMessage(`❌ ${err.response?.data?.detail || 'Error al invitar'}`);
    } finally {
      setInviting(false);
    }
  };

  const executeLeave = async () => {
    try {
      await leaguesAPI.leave(leagueId);
      navigate('/leagues');
    } catch (err) {
      showMessage(`❌ ${err.response?.data?.detail || 'Error al salir'}`);
    }
  };

  const handleLeave = () => {
    toast.error('¿Seguro que quieres salir de esta liga?', {
      cancel: { label: 'Cancelar' },
      action: { label: 'Sí, salir', onClick: () => executeLeave() }
    });
  };

  const executeKick = async (memberId, memberUsername) => {
    try {
      await leaguesAPI.kickMember(leagueId, memberId);
      showMessage(`✅ @${memberUsername} ha sido expulsado.`);
      await new Promise(resolve => setTimeout(resolve, 300));
      loadLeague();
    } catch (err) {
      showMessage(`❌ ${err.response?.data?.detail || 'Error al expulsar'}`);
    }
  };

  const handleKick = (memberId, memberUsername) => {
    toast.error(`¿Seguro que quieres expulsar a @${memberUsername} de la liga?`, {
      cancel: { label: 'Cancelar' },
      action: { label: 'Expulsar', onClick: () => executeKick(memberId, memberUsername) }
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
      case 'gold': return 'var(--gold)';
      case 'silver': return 'var(--text-muted)';
      case 'legend': return '#a78bfa';
      default: return '#cd7f32';
    }
  };

  const handleAcceptOffer = async (offerId) => {
    try {
      const res = await auctionAPI.acceptOffer(leagueId, offerId);
      showMessage(`✅ ${res.data.message}`);
      loadOffers(); 
      loadListings();
    } catch (err) { 
      showMessage(`❌ ${err.response?.data?.detail || 'Error'}`); 
    }
  };

  const handleBuyListing = async (listingId) => {
    try {
      const res = await auctionAPI.buyListing(leagueId, listingId);
      showMessage(`✅ ${res.data.message}`);
      loadListings();
    } catch (err) { 
      showMessage(`❌ ${err.response?.data?.detail || 'Error'}`); 
    }
  };

  const handleCancelListing = async (listingId) => {
    try {
      await auctionAPI.cancelListing(leagueId, listingId);
      showMessage('✅ Listado cancelado');
      loadListings();
    } catch (err) { 
      showMessage(`❌ ${err.response?.data?.detail || 'Error'}`); 
    }
  };

  const togglePackExpansion = (packId) => {
    const newExpanded = new Set(expandedPacks);
    if (newExpanded.has(packId)) newExpanded.delete(packId);
    else newExpanded.add(packId);
    setExpandedPacks(newExpanded);
  };

  if (loading) {
    return (
      <AppLayout title="Cargando Liga..." backTo="/leagues">
        <div className="ld-loading">Cargando datos...</div>
      </AppLayout>
    );
  }

  if (!league) {
    return (
      <AppLayout title="Liga no encontrada" backTo="/leagues">
        <div className="ld-loading">Esta liga no existe o no tienes acceso.</div>
      </AppLayout>
    );
  }

  const headerRight = (
    <div className="ld-coins-wrap">
      <div className="ld-coins">🪙 {formatPrice(displayAvailable)}</div>
      {myLockedCoins > 0 && (
        <div className="ld-coins-locked" title="Monedas bloqueadas en pujas activas">🔒 {formatPrice(myLockedCoins)} Retenidas</div>
      )}
    </div>
  );

  return (
    <AppLayout title={league.name} backTo="/leagues" rightContent={headerRight}>
      <div className="ld-page-content">

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

        {/* Subtitle / Minor Info below header conceptually */}
        <div className="ld-subtitle-bar">
          <span>👥 {league.member_count}/{league.max_members}</span>
          <span>·</span>
          <span>Código: <strong>{league.invite_code}</strong></span>
        </div>

        {/* Tabs */}
        <div className="lg-tabs">
          <button className={`lg-tab ${activeTab === 'standings' ? 'active' : ''}`} onClick={() => setActiveTab('standings')}>
            🏅 Clasificación
          </button>
          <button className="lg-tab" onClick={() => navigate(`/team?league_id=${leagueId}`)}>
            ⚽ Mi Equipo
          </button>
          <button className={`lg-tab ${activeTab === 'market' ? 'active' : ''}`} onClick={() => setActiveTab('market')}>
            📈 Mercado
          </button>
          <button className={`lg-tab ${activeTab === 'packs' ? 'active' : ''}`} onClick={() => setActiveTab('packs')}>
            🎴 Sobres
          </button>
          <button className={`lg-tab ${activeTab === 'info' ? 'active' : ''}`} onClick={() => setActiveTab('info')}>
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

                let borderClass = '';
                if (idx === 0) borderClass = 'ld-rank-gold';
                else if (idx === 1) borderClass = 'ld-rank-silver';
                else if (idx === 2) borderClass = 'ld-rank-bronze';

                return (
                  <div
                    key={member.id}
                    className={`ld-member-row ${isSelf ? 'me' : ''} ${borderClass}`}
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
                        className="ld-leave-btn ld-kick-btn"
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
                <div className="lg-empty">
                   <span className="mkt-empty-icon">⏳</span>
                   <p>No hay subasta activa</p>
                </div>
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
                        onClick={() => setSelectedPlayerForDetail({ ...slot, player_id: slot.player_id, name: slot.player_name, current_price: slot.base_price })}
                        style={{ cursor: 'pointer' }}
                      >
                        <div className="ld-market-row-accent neutral"></div>

                        <div className="ld-market-row-info-col">
                          <div className="ld-market-row-img-wrap" style={{ borderColor: getRarityColor(slot.base_rarity) }}>
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
                              <span style={{ color: hasBid ? 'var(--gold)' : 'var(--text-secondary)' }}>
                                {hasBid ? 'Puja activa' : 'Sin participación'}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="ld-market-row-price-col">
                          <div className={`ld-market-row-price ${slot.current_bid > 0 ? 'highlight' : ''}`}>
                            {formatPrice(slot.current_bid > 0 ? slot.current_bid : slot.base_price)}
                          </div>
                          <div className="ld-market-row-subprice">
                            {slot.current_bid > 0 ? `Base: ${formatPrice(slot.base_price)}` : 'Precio Base'}
                          </div>
                        </div>

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
                              className="btn-primary"
                              style={{ padding: '8px 12px', fontSize: '0.85rem' }}
                              onClick={() => handleBid(slot.id, slot.current_bid, slot.base_price)}
                              disabled={bidding === slot.id}
                            >
                              {bidding === slot.id ? '...' : (hasBid ? 'Actualizar' : 'Pujar')}
                            </button>
                            {hasBid && (
                              <button
                                className="lg-btn-danger"
                                style={{ padding: '8px 12px', fontSize: '0.85rem' }}
                                onClick={() => handleWithdrawBid(slot.id)}
                                disabled={bidding === slot.id}
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
                <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--gold)', marginBottom: 12 }}>🤖 Ofertas del Sistema</h2>
                <p className="ld-auction-desc">El sistema te ha hecho una oferta por tus jugadores en venta.</p>
                <div className="ld-market-list-view">
                  {offers.map(offer => (
                    <div key={offer.id} className="ld-market-row dark-row">
                      <div className="ld-market-row-accent warning"></div>

                      <div className="ld-market-row-info-col">
                        <div className="ld-market-row-img-wrap" style={{ borderColor: 'var(--gold)' }}>
                          <div className="ld-player-fallback" style={{ display: 'flex', width: '100%', height: '100%', alignItems: 'center', justifyContent: 'center' }}>🤖</div>
                        </div>
                        <div className="ld-market-row-details">
                          <div className="ld-market-row-name">{offer.player_name}</div>
                          <div className="ld-market-row-team">
                            <span style={{ color: 'var(--gold)' }}>Oferta del Sistema</span>
                          </div>
                        </div>
                      </div>

                      <div className="ld-market-row-price-col">
                        <div className="ld-market-row-price highlight">
                          {formatPrice(offer.offer_price)}
                        </div>
                        <div className="ld-market-row-subprice" style={{ color: 'var(--danger)' }}>
                          Tú pedías: {formatPrice(offer.asking_price)}
                        </div>
                      </div>

                      <div className="ld-market-row-action-col" onClick={e => e.stopPropagation()}>
                        <div className="ld-market-row-bid-wrap">
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginRight: '8px', textAlign: 'right', lineHeight: 1.2 }}>
                            Expira:<br />{new Date(offer.expires_at).toLocaleString('es-ES', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                          </div>
                          <button
                            className="btn-primary"
                            style={{ padding: '8px 12px', fontSize: '0.85rem' }}
                            onClick={() => handleAcceptOffer(offer.id)}
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
              <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: 12 }}>🏷️ Fichajes Recientes & En Venta</h2>
              <p className="ld-auction-desc">Jugadores puestos a la venta por usuarios de la liga.</p>

              {listingsLoading ? (
                <div className="ld-loading-small">Cargando listados...</div>
              ) : listings.length === 0 ? (
                <div className="lg-empty">
                   <p>No hay jugadores en venta</p>
                </div>
              ) : (
                <div className="ld-market-list-view">
                  {listings.map((listing, index) => (
                    <div
                      key={listing.id}
                      className={`ld-market-row ${index % 2 === 0 ? 'dark-row' : ''}`}
                      style={{ cursor: 'pointer' }}
                      onClick={() => setSelectedPlayerForDetail({
                        ...listing,
                        player_id: listing.player_id || listing.card?.player_id,
                        name: listing.player_name,
                        current_price: listing.asking_price,
                        current_market_value: listing.asking_price
                      })}
                    >
                      <div className={`ld-market-row-accent ${listing.is_mine ? 'warning' : 'neutral'}`}></div>

                      <div className="ld-market-row-info-col">
                        <div className="ld-market-row-img-wrap" style={{ borderColor: getRarityColor(listing.base_rarity) }}>
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

                      <div className="ld-market-row-price-col">
                        <div className="ld-market-row-price highlight">
                          {formatPrice(listing.asking_price)}
                        </div>
                        <div className="ld-market-row-subprice">
                          Precio Solicitado
                        </div>
                      </div>

                      <div className="ld-market-row-action-col" onClick={e => e.stopPropagation()}>
                        <div className="ld-market-row-bid-wrap">
                          {listing.is_mine ? (
                            <button
                              className="lg-btn-danger"
                              style={{ padding: '8px 12px', fontSize: '0.85rem' }}
                              onClick={() => handleCancelListing(listing.id)}
                            >
                              Retirar
                            </button>
                          ) : (
                            <button
                              className="btn-primary"
                              style={{ padding: '8px 12px', fontSize: '0.85rem' }}
                              onClick={() => handleBuyListing(listing.id)}
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
              <div className="ld-pack-container">
                <div className="ld-pack-card-premium">
                  <img
                    src="/images/pack-cover.png"
                    alt="Sobre Legendario"
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      borderRadius: '16px',
                      display: 'block'
                    }}
                    onError={(e) => { e.target.style.display='none'; }}
                  />
                </div>
              </div>

              <div className="ld-pack-info-area">
                <p className="ld-pack-info-desc">Contiene <strong>1 carta legendaria</strong> aleatoria</p>
                <div className="ld-pack-price-tag">🪙 150.000.000</div>
              </div>

              <button
                className={`ld-pack-open-btn ${opening ? 'opening' : ''}`}
                onClick={handleOpenPack}
                disabled={opening}
              >
                {opening ? '⚽ Abriendo...' : '⚡ ABRIR SOBRE'}
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
                <div className="ld-history-list">
                  {packHistory.map(p => {
                    const isExpanded = expandedPacks.has(p.id);
                    return (
                      <div key={p.id} className="ld-card" style={{ marginBottom: '8px', padding: '12px' }}>
                        <div 
                          className="ld-history-row"
                          onClick={() => togglePackExpansion(p.id)}
                          style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                        >
                          <div className="ld-history-main" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span style={{ fontSize: '1.5rem' }}>🎴</span>
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                              <strong style={{ color: 'var(--text-primary)' }}>Sobre de Iconos</strong>
                              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{new Date(p.opened_at).toLocaleDateString()} · {p.cards_obtained} {p.cards_obtained === 1 ? 'carta' : 'cartas'}</span>
                            </div>
                          </div>
                          <span style={{ color: 'var(--gold)' }}>{isExpanded ? '▲' : '▼'}</span>
                        </div>
                        
                        {isExpanded && p.cards && p.cards.length > 0 && (
                          <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border)' }}>
                            {p.cards.map((card, cidx) => (
                              <div key={cidx} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
                                <span style={{ color: getRarityColor(card.base_rarity), fontWeight: 800 }}>★ {card.player_name}</span>
                                <span style={{ color: 'var(--text-secondary)' }}>OVR {card.overall_rating}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ==== INFO TAB ==== */}
        {activeTab === 'info' && (
          <div className="ld-content">
            <div className="ld-info-section">
              <div className="ld-card">
                <h3 style={{ margin: '0 0 16px', color: 'var(--text-primary)', fontWeight: 800 }}>📋 Información de la Liga</h3>
                <div className="ld-info-row">
                  <span>Nombre</span>
                  <strong>{league.name}</strong>
                </div>
                {league.description && (
                  <div className="ld-info-row">
                    <span>Descripción</span>
                    <span style={{ textAlign: 'right', flex: 1 }}>{league.description}</span>
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
              <div className="ld-card" style={{ overflow: 'visible' }}>
                <h3 style={{ margin: '0 0 8px', color: 'var(--text-primary)', fontWeight: 800 }}>📩 Invitar amigo</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0 0 16px' }}>Busca un usuario por su nombre o email para invitarle a la liga.</p>
                <div style={{ position: 'relative' }}>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      type="text"
                      className="ld-input"
                      placeholder="Buscar nombre o correo..."
                      value={searchQuery}
                      onChange={e => {
                        setSearchQuery(e.target.value);
                        setInviteUsername(e.target.value);
                      }}
                      style={{ flex: 1 }}
                    />
                    <button className="btn-primary" onClick={() => handleInvite()} disabled={inviting}>
                      {inviting ? '...' : 'Enviar'}
                    </button>
                  </div>
                  {/* Search Results Dropdown */}
                  {(searchResults.length > 0 || searching) && searchQuery.length >= 2 && (
                    <div className="ld-search-dropdown" style={{
                      position: 'absolute', top: '100%', left: 0, right: 0, 
                      backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-strong)', 
                      borderRadius: '8px', zIndex: 50, marginTop: '4px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.5)', maxHeight: '200px', overflowY: 'auto'
                    }}>
                      {searching ? (
                        <div style={{ padding: '12px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Buscando...</div>
                      ) : searchResults.length > 0 ? (
                        searchResults.map(u => (
                          <div key={u.id} style={{
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            padding: '10px 12px', borderBottom: '1px solid var(--border)', cursor: 'pointer'
                          }}
                          onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--bg-hover)'}
                          onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                          onClick={() => {
                            setInviteUsername(u.username);
                            setSearchQuery(u.username);
                            setSearchResults([]);
                          }}
                          >
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{ fontWeight: 800, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{u.username}</div>
                              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{u.email}</div>
                            </div>
                            <button 
                              className="btn-primary"
                              style={{ padding: '6px 12px', marginLeft: '8px', fontSize: '0.85rem' }}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleInvite(u.username);
                              }}
                              disabled={inviting}
                            >
                              Invitar
                            </button>
                          </div>
                        ))
                      ) : (
                        <div style={{ padding: '12px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>No se encontraron usuarios</div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Leave */}
              <button className="lg-btn-danger" style={{ width: '100%', padding: '16px' }} onClick={handleLeave}>
                🚪 Salir de la liga
              </button>
            </div>
          </div>
        )}

      </div>
    </AppLayout>
  );
}
