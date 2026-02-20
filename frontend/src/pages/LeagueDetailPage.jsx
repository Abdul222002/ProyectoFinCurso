import { useNavigate, useParams } from 'react-router-dom';
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { leaguesAPI, auctionAPI, packsAPI } from '../services/endpoints';
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

  useEffect(() => {
    if (activeTab === 'market') loadAuction();
    // Auto-refresh every 10s to see new bids
    const interval = setInterval(() => {
        if (activeTab === 'market') loadAuction();
    }, 10000);
    return () => clearInterval(interval);
  }, [activeTab, loadAuction]);

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

  const handleOpenPack = async () => {
    if (opening) return;
    if (user?.coins < 150000000) {
      setMessage('❌ Necesitas 150.000.000 monedas para abrir un sobre de iconos');
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
    if (!inviteUsername.trim()) return;
    setInviting(true);
    try {
      await leaguesAPI.invite(leagueId, { username: inviteUsername });
      setMessage(`✅ Invitación enviada a @${inviteUsername}`);
      setInviteUsername('');
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Error'}`);
    }
    setInviting(false);
  };

  const handleLeave = async () => {
    if (!window.confirm('¿Seguro que quieres salir de esta liga?')) return;
    try {
      await leaguesAPI.leave(leagueId);
      navigate('/leagues');
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Error'}`);
    }
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
        <div className="ld-coins">🪙 {formatPrice(user?.coins)}</div>
      </header>

      {/* Message */}
      {message && (
        <div className={`ld-message ${message.startsWith('✅') ? 'success' : 'error'}`}>
          {message}
          <button className="ld-msg-close" onClick={() => setMessage('')}>✕</button>
        </div>
      )}

      {/* Tabs */}
      <div className="ld-tabs">
        <button className={`ld-tab ${activeTab === 'standings' ? 'active' : ''}`} onClick={() => setActiveTab('standings')}>
          🏅 Clasificación
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
            {league.members?.sort((a, b) => b.league_points - a.league_points).map((member, idx) => (
              <div key={member.id} className={`ld-member-row ${member.user_id === user?.id ? 'me' : ''}`}>
                <span className="ld-rank">{idx + 1}</span>
                <div className="ld-member-info">
                  <span className="ld-member-name">
                    @{member.username}
                    {member.is_admin && ' 👑'}
                  </span>
                  <span className="ld-member-pts">{member.league_points} pts</span>
                </div>
              </div>
            ))}
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
              <div className="ld-auction-grid">
                {auction.slots.map(slot => {
                    const minBid = slot.current_bid > 0 ? slot.current_bid + 1 : slot.base_price;
                    const isWinning = slot.highest_bidder_id === user?.id;
                    
                    return (
                        <div key={slot.id} className={`ld-auction-card ${isWinning ? 'winning' : ''}`}>
                            <div className="ld-auction-card-top">
                                <div className="ld-player-ovr" style={{ borderColor: getRarityColor(slot.base_rarity) }}>
                                    {slot.overall_rating}
                                </div>
                                <div className="ld-auction-info">
                                    <div className="ld-player-name">{slot.player_name}</div>
                                    <div className="ld-player-pos">{slot.position}</div>
                                </div>
                            </div>
                            
                            <div className="ld-auction-stats">
                                <div className="ld-stat-row">
                                    <span>Precio Base</span>
                                    <span>{formatPrice(slot.base_price)}</span>
                                </div>
                                <div className="ld-stat-row bid">
                                    <span>Puja Actual</span>
                                    <span className="ld-current-bid">{formatPrice(slot.current_bid)}</span>
                                </div>
                                <div className="ld-stat-row bidder">
                                    <span>Ganador</span>
                                    <span>{slot.highest_bidder_username ? `@${slot.highest_bidder_username}` : 'Nadie'}</span>
                                </div>
                            </div>

                            <div className="ld-bid-controls">
                                <input 
                                    type="number" 
                                    placeholder={`Mín: ${formatPrice(minBid)}`}
                                    value={bidAmounts[slot.id] || ''}
                                    onChange={(e) => setBidAmounts({...bidAmounts, [slot.id]: e.target.value})}
                                    className="ld-bid-input"
                                />
                                <button 
                                    className="ld-bid-btn"
                                    onClick={() => handleBid(slot.id, slot.current_bid, slot.base_price)}
                                    disabled={bidding === slot.id}
                                >
                                    {bidding === slot.id ? '...' : 'Pujar'}
                                </button>
                            </div>
                        </div>
                    );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ==== PACKS TAB ==== */}
      {activeTab === 'packs' && (
        <div className="ld-content">
          <div className="ld-packs-section">
            {/* Pack Card */}
            <div className="ld-pack-card">
              <div className="ld-pack-glow"></div>
              <div className="ld-pack-icon">🎴</div>
              <h2 className="ld-pack-title">Sobre de Iconos</h2>
              <p className="ld-pack-desc">
                Contiene <strong>3 cartas legendarias</strong> aleatorias.
                Los iconos solo se pueden obtener a través de sobres.
              </p>
              <div className="ld-pack-price">🪙 150.000.000</div>
              <button
                className={`ld-pack-btn ${opening ? 'opening' : ''}`}
                onClick={handleOpenPack}
                disabled={opening}
              >
                {opening ? (
                  <span className="ld-pack-spinner">⚽</span>
                ) : (
                  '🎴 Abrir Sobre'
                )}
              </button>
            </div>

            {/* Pack Result */}
            {packResult && packResult.cards && (
              <div className="ld-pack-result">
                <h3 className="ld-result-title">¡Sobre abierto!</h3>
                <div className="ld-result-cards">
                  {packResult.cards.map((card, idx) => (
                    <div key={idx} className="ld-result-card legend">
                      <div className="ld-card-ovr">{card.overall_rating}</div>
                      <div className="ld-card-name">{card.player_name}</div>
                      <div className="ld-card-pos">{card.position}</div>
                      <div className="ld-card-badge">⭐ ICON</div>
                    </div>
                  ))}
                </div>
                <div className="ld-result-coins">
                  Monedas restantes: 🪙 {formatPrice(packResult.remaining_coins)}
                </div>
              </div>
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
        </div>
      )}

      {/* ==== INFO TAB ==== */}
      {activeTab === 'info' && (
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
      )}

      {/* Bottom Nav */}
      <div className="ld-bottom-bar">
        <button className="ld-bottom-btn" onClick={() => navigate('/dashboard')}>🏠 Home</button>
        <button className="ld-bottom-btn" onClick={() => navigate(`/team?league=${leagueId}`)}>⚽ Equipo</button>
        <button className="ld-bottom-btn active">🏆 Liga</button>
      </div>
    </div>
  );
}
