import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { marketAPI } from '../services/endpoints';
import './MarketPage.css';

export default function MarketPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(null);
  const [message, setMessage] = useState('');
  const [filter, setFilter] = useState({ position: '', sort_by: 'overall_rating', order: 'desc' });

  useEffect(() => { loadPlayers(); }, [filter]);

  const loadPlayers = async () => {
    setLoading(true);
    try {
      const params = { limit: 50 };
      if (filter.position) params.position = filter.position;
      params.sort_by = filter.sort_by;
      params.order = filter.order;
      const res = await marketAPI.list(params);
      setPlayers(res.data);
    } catch {
      setPlayers([]);
    }
    setLoading(false);
  };

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
      // Refresh user coins via auth (reload page data)
      setTimeout(() => setMessage(''), 4000);
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Error al comprar'}`);
      setTimeout(() => setMessage(''), 3000);
    }
    setBuying(null);
  };

  const formatPrice = (price) => {
    if (price >= 1000000) return (price / 1000000).toFixed(1) + 'M';
    if (price >= 1000) return (price / 1000).toFixed(0) + 'K';
    return price.toLocaleString();
  };

  const getRarityColor = (rarity) => {
    switch (rarity) {
      case 'gold': return '#fbbf24';
      case 'silver': return '#94a3b8';
      case 'legend': return '#a78bfa';
      default: return '#cd7f32';
    }
  };

  return (
    <div className="market-page">
      {/* Header */}
      <header className="market-header">
        <button className="market-back-btn" onClick={() => navigate('/dashboard')}>←</button>
        <h1 className="market-title">Mercado de Fichajes</h1>
        <div className="market-coins">🪙 {user?.coins?.toLocaleString()}</div>
      </header>

      {/* Message Banner */}
      {message && (
        <div className={`market-message ${message.startsWith('✅') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}

      {/* Filters */}
      <div className="market-filters">
        <select
          value={filter.position}
          onChange={(e) => setFilter({ ...filter, position: e.target.value })}
          className="market-filter-select"
        >
          <option value="">Todas</option>
          <option value="GK">Porteros</option>
          <option value="DEF">Defensas</option>
          <option value="MID">Medios</option>
          <option value="FWD">Delanteros</option>
        </select>
        <select
          value={filter.sort_by}
          onChange={(e) => setFilter({ ...filter, sort_by: e.target.value })}
          className="market-filter-select"
        >
          <option value="overall_rating">OVR</option>
          <option value="current_price">Precio</option>
          <option value="name">Nombre</option>
        </select>
        <button
          className="market-filter-btn"
          onClick={() => setFilter({ ...filter, order: filter.order === 'desc' ? 'asc' : 'desc' })}
        >
          {filter.order === 'desc' ? '↓' : '↑'}
        </button>
      </div>

      {/* Player List */}
      <div className="market-list">
        {loading ? (
          <div className="market-loading">Cargando jugadores...</div>
        ) : players.length === 0 ? (
          <div className="market-empty">No hay jugadores disponibles</div>
        ) : (
          players.map(player => (
            <div key={player.id} className="market-player-row">
              <div className="market-player-info">
                <div
                  className="market-player-ovr"
                  style={{ borderColor: getRarityColor(player.base_rarity) }}
                >
                  {player.overall_rating}
                </div>
                <div className="market-player-details">
                  <span className="market-player-name">{player.name}</span>
                  <span className="market-player-meta">
                    {player.position} · {player.current_team || 'Free Agent'}
                    {player.is_legend && ' ⭐'}
                  </span>
                </div>
              </div>
              <div className="market-player-price-section">
                <div className="market-price-info">
                  <span className="market-price">🪙 {formatPrice(player.current_price)}</span>
                  <span className={`market-price-change ${player.price_change_pct >= 0 ? 'up' : 'down'}`}>
                    {player.price_change_pct >= 0 ? '▲' : '▼'} {Math.abs(player.price_change_pct).toFixed(1)}%
                  </span>
                </div>
                <button
                  className="market-buy-btn"
                  onClick={() => handleBuy(player.id, player.name, player.current_price)}
                  disabled={buying === player.id}
                >
                  {buying === player.id ? '...' : 'Comprar'}
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Bottom Nav */}
      <div className="market-bottom-bar">
        <button className="market-bottom-btn" onClick={() => navigate('/team')}>⚽ Equipo</button>
        <button className="market-bottom-btn active">📈 Mercado</button>
        <button className="market-bottom-btn" onClick={() => navigate('/arena')}>⚔️ Arena</button>
      </div>
    </div>
  );
}
