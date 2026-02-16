import { useNavigate, useParams } from 'react-router-dom';
import { useState, useEffect, useCallback } from 'react';
import { playersAPI } from '../services/endpoints';
import './PriceAnalysisPage.css';

export default function PriceAnalysisPage() {
  const navigate = useNavigate();
  const { playerId } = useParams();
  const [player, setPlayer] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadPlayer = useCallback(async () => {
    setLoading(true);
    try {
      const res = await playersAPI.getDetail(playerId);
      setPlayer(res.data);
    } catch {
      setPlayer(null);
    }
    setLoading(false);
  }, [playerId]);

  useEffect(() => { loadPlayer(); }, [loadPlayer]);

  const formatPrice = (price) => {
    if (!price) return '0';
    if (price >= 1000000) return (price / 1000000).toFixed(2) + 'M';
    if (price >= 1000) return (price / 1000).toFixed(0) + 'K';
    return price.toLocaleString();
  };

  if (loading) {
    return (
      <div className="price-page">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
          Cargando...
        </div>
      </div>
    );
  }

  if (!player) {
    return (
      <div className="price-page">
        <header className="pa-header">
          <button className="pa-back-btn" onClick={() => navigate(-1)}>← Volver</button>
        </header>
        <div style={{ textAlign: 'center', marginTop: '3rem' }}>Jugador no encontrado</div>
      </div>
    );
  }

  const gap = player.target_price - player.current_price;
  const gapPct = player.price_change_pct;
  const isBuySignal = gapPct > 5;
  const isSellSignal = gapPct < -5;

  return (
    <div className="price-page">
      {/* Header */}
      <header className="pa-header">
        <button className="pa-back-btn" onClick={() => navigate(-1)}>←</button>
        <div className="pa-header-info">
          <h1>{player.name}</h1>
          <span>{player.position} · {player.current_team || 'Free Agent'}</span>
        </div>
      </header>

      {/* Price Hero */}
      <section className="pa-price-hero">
        <div className="pa-current-price">
          <span className="pa-label">Precio Actual</span>
          <span className="pa-value">🪙 {formatPrice(player.current_price)}</span>
        </div>
        <div className="pa-price-arrow">
          <span className={gapPct >= 0 ? 'pa-arrow-up' : 'pa-arrow-down'}>
            {gapPct >= 0 ? '▲' : '▼'} {Math.abs(gapPct).toFixed(1)}%
          </span>
        </div>
        <div className="pa-target-price">
          <span className="pa-label">Precio Objetivo</span>
          <span className="pa-value">🪙 {formatPrice(player.target_price)}</span>
        </div>
      </section>

      {/* Signal */}
      <section className="pa-signal-section">
        <div className={`pa-signal ${isBuySignal ? 'buy' : isSellSignal ? 'sell' : 'hold'}`}>
          <span className="pa-signal-icon">
            {isBuySignal ? '🟢' : isSellSignal ? '🔴' : '🟡'}
          </span>
          <div className="pa-signal-info">
            <span className="pa-signal-label">
              {isBuySignal ? 'Señal de COMPRA' : isSellSignal ? 'Señal de VENTA' : 'MANTENER'}
            </span>
            <span className="pa-signal-desc">
              {isBuySignal
                ? `El precio actual está por debajo del objetivo. Gap: +${gapPct.toFixed(1)}%`
                : isSellSignal
                  ? `El precio actual supera el objetivo. Gap: ${gapPct.toFixed(1)}%`
                  : 'El precio está cerca de su valor justo'
              }
            </span>
          </div>
        </div>
      </section>

      {/* Stats Grid */}
      <section className="pa-stats-grid">
        <div className="pa-stat-card">
          <span className="pa-stat-label">OVR</span>
          <span className="pa-stat-value">{player.overall_rating}</span>
        </div>
        <div className="pa-stat-card">
          <span className="pa-stat-label">Rareza</span>
          <span className="pa-stat-value">{player.base_rarity}</span>
        </div>
        <div className="pa-stat-card">
          <span className="pa-stat-label">Gap Absoluto</span>
          <span className="pa-stat-value">🪙 {formatPrice(Math.abs(gap))}</span>
        </div>
        <div className="pa-stat-card">
          <span className="pa-stat-label">Tipo</span>
          <span className="pa-stat-value">{player.is_legend ? 'Leyenda' : 'Actual'}</span>
        </div>
      </section>

      {/* Market Explanation */}
      <section className="pa-explanation">
        <h3>🧠 Cómo funciona el mercado</h3>
        <p>
          El <strong>precio actual</strong> se mueve diariamente hacia el <strong>precio objetivo</strong>.
          El precio objetivo se recalcula cada fin de semana según el rendimiento real del jugador en la Scottish Premiership.
          Si el gap es grande y positivo, es un buen momento para comprar. Si es negativo, considera vender.
        </p>
      </section>

      {/* Actions */}
      <div className="pa-actions">
        <button className="pa-action-btn" onClick={() => navigate(`/player/${playerId}`)}>
          👤 Ver Carta
        </button>
        <button className="pa-action-btn primary" onClick={() => navigate('/market')}>
          📈 Ir al Mercado
        </button>
      </div>
    </div>
  );
}
