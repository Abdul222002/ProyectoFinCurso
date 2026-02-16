import { useNavigate, useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { playersAPI } from '../services/endpoints';
import './CardDetailPage.css';

export default function CardDetailPage() {
  const navigate = useNavigate();
  const { playerId } = useParams();
  const [player, setPlayer] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadPlayer(); }, [playerId]);

  const loadPlayer = async () => {
    setLoading(true);
    try {
      const res = await playersAPI.getDetail(playerId);
      setPlayer(res.data);
    } catch {
      setPlayer(null);
    }
    setLoading(false);
  };

  const formatPrice = (price) => {
    if (price >= 1000000) return (price / 1000000).toFixed(1) + 'M';
    if (price >= 1000) return (price / 1000).toFixed(0) + 'K';
    return price?.toLocaleString();
  };

  const getRarityLabel = (rarity) => {
    switch (rarity) {
      case 'gold': return '🥇 Gold';
      case 'silver': return '🥈 Silver';
      case 'legend': return '⭐ Legend';
      default: return '🥉 Bronze';
    }
  };

  if (loading) {
    return (
      <div className="card-detail-page">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
          <div>Cargando...</div>
        </div>
      </div>
    );
  }

  if (!player) {
    return (
      <div className="card-detail-page">
        <header className="cd-header">
          <button className="cd-back-btn" onClick={() => navigate(-1)}>← Volver</button>
        </header>
        <div style={{ textAlign: 'center', marginTop: '3rem' }}>
          <p>Jugador no encontrado</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card-detail-page">
      {/* Header */}
      <header className="cd-header">
        <button className="cd-back-btn" onClick={() => navigate(-1)}>←</button>
        <h1 className="cd-player-name">{player.name}</h1>
        <span className="cd-rarity-badge">{getRarityLabel(player.base_rarity)}</span>
      </header>

      {/* Hero Card */}
      <section className="cd-hero">
        <div className="cd-card-display">
          <div className="cd-ovr">{player.overall_rating}</div>
          <div className="cd-position">{player.position}</div>
          <div className="cd-team-name">{player.current_team || 'Free Agent'}</div>
        </div>
      </section>

      {/* Price Info */}
      <section className="cd-price-section">
        <div className="cd-price-main">
          <span className="cd-price-label">Valor de Mercado</span>
          <span className="cd-price-value">🪙 {formatPrice(player.current_price)}</span>
        </div>
        <div className="cd-price-change">
          <span className={player.price_change_pct >= 0 ? 'cd-up' : 'cd-down'}>
            {player.price_change_pct >= 0 ? '▲' : '▼'} {Math.abs(player.price_change_pct).toFixed(1)}%
          </span>
          <span className="cd-target">Target: 🪙 {formatPrice(player.target_price)}</span>
        </div>
      </section>

      {/* Info Cards */}
      <section className="cd-info-grid">
        <div className="cd-info-card">
          <span className="cd-info-label">Tipo</span>
          <span className="cd-info-value">{player.is_legend ? '⭐ Leyenda' : '👤 Actual'}</span>
        </div>
        <div className="cd-info-card">
          <span className="cd-info-label">Rareza</span>
          <span className="cd-info-value">{getRarityLabel(player.base_rarity)}</span>
        </div>
        <div className="cd-info-card">
          <span className="cd-info-label">Posición</span>
          <span className="cd-info-value">{player.position}</span>
        </div>
        <div className="cd-info-card">
          <span className="cd-info-label">Equipo</span>
          <span className="cd-info-value">{player.current_team || 'N/A'}</span>
        </div>
      </section>

      {/* Actions */}
      <div className="cd-actions">
        <button className="cd-action-btn buy" onClick={() => navigate('/market')}>
          📈 Ver en Mercado
        </button>
        <button className="cd-action-btn analysis" onClick={() => navigate(`/analysis/${playerId}`)}>
          📊 Análisis de Precio
        </button>
      </div>
    </div>
  );
}
