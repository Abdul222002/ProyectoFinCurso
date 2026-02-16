import { useNavigate, useParams } from 'react-router-dom';
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { leaguesAPI, marketAPI, packsAPI } from '../services/endpoints';
import './LeagueDetailPage.css';

export default function LeagueDetailPage() {
  const navigate = useNavigate();
  const { leagueId } = useParams();
  const { user, refreshUser } = useAuth();

  const [league, setLeague] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('standings');
  const [message, setMessage] = useState('');

  // Market state
  const [players, setPlayers] = useState([]);
  const [marketLoading, setMarketLoading] = useState(false);
  const [buying, setBuying] = useState(null);
  const [marketFilter, setMarketFilter] = useState({ position: '', sort_by: 'overall_rating', order: 'desc', search: '' });

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

  // Load market players
  const loadMarket = useCallback(async () => {
    setMarketLoading(true);
    try {
      const params = { limit: 200 };
      if (marketFilter.position) params.position = marketFilter.position;
      if (marketFilter.search) params.search = marketFilter.search;
      params.sort_by = marketFilter.sort_by;
      params.order = marketFilter.order;
      const res = await marketAPI.list(params);
      setPlayers(res.data);
    } catch {
      setPlayers([]);
    }
    setMarketLoading(false);
  }, [marketFilter]);

  useEffect(() => {
    if (activeTab === 'market') loadMarket();
  }, [activeTab, loadMarket]);

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

  const handleBuy = async (playerId, playerName, price) => {
    if (buying) return;
    if (user?.coins < price) {
      setMessage(`❌ No tienes suficientes monedas para ${playerName}`);
      setTimeout(() => setMessage(''), 3000);
      return;
    }
    setBuying(playerId);
    try {
      const res = await marketAPI.buy(playerId);
      setMessage(`✅ ${res.data.message} — Te quedan 🪙 ${res.data.remaining_coins.toLocaleString()}`);
      if (refreshUser) refreshUser();
      setTimeout(() => setMessage(''), 4000);
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Error al comprar'}`);
      setTimeout(() => setMessage(''), 3000);
    }
    setBuying(null);
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

      {/* ==== MARKET TAB ==== */}
      {activeTab === 'market' && (
        <div className="ld-content">
          {/* Search & Filters */}
          <div className="ld-market-filters">
            <input
              type="text"
              value={marketFilter.search}
              onChange={(e) => setMarketFilter({ ...marketFilter, search: e.target.value })}
              placeholder="🔍 Buscar jugador..."
              className="ld-search-input"
            />
            <select
              value={marketFilter.position}
              onChange={(e) => setMarketFilter({ ...marketFilter, position: e.target.value })}
              className="ld-filter-select"
            >
              <option value="">Todas</option>
              <option value="GK">Porteros</option>
              <option value="DEF">Defensas</option>
              <option value="MID">Medios</option>
              <option value="FWD">Delanteros</option>
            </select>
            <button
              className="ld-filter-btn"
              onClick={() => setMarketFilter({ ...marketFilter, order: marketFilter.order === 'desc' ? 'asc' : 'desc' })}
            >
              {marketFilter.order === 'desc' ? '↓' : '↑'}
            </button>
          </div>

          {/* Player List */}
          <div className="ld-market-list">
            {marketLoading ? (
              <div className="ld-loading-small">Cargando jugadores...</div>
            ) : players.length === 0 ? (
              <div className="ld-empty">No hay jugadores disponibles</div>
            ) : (
              <>
                <div className="ld-market-count">{players.length} jugadores disponibles</div>
                {players.map(player => (
                  <div key={player.id} className="ld-player-row">
                    <div className="ld-player-info">
                      <div className="ld-player-ovr" style={{ borderColor: getRarityColor(player.base_rarity) }}>
                        {player.overall_rating}
                      </div>
                      <div className="ld-player-details">
                        <span className="ld-player-name">{player.name}</span>
                        <span className="ld-player-meta">
                          {player.position} · {player.current_team || 'Free Agent'}
                        </span>
                      </div>
                    </div>
                    <div className="ld-player-price-section">
                      <span className="ld-price">🪙 {formatPrice(player.current_price)}</span>
                      <button
                        className="ld-buy-btn"
                        onClick={() => handleBuy(player.id, player.name, player.current_price)}
                        disabled={buying === player.id}
                      >
                        {buying === player.id ? '...' : 'Comprar'}
                      </button>
                    </div>
                  </div>
                ))}
              </>
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
