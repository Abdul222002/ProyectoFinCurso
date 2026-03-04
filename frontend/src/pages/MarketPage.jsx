import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { leaguesAPI } from '../services/endpoints';
import './MarketPage.css';

export default function MarketPage() {
  const navigate = useNavigate();
  const [leagues, setLeagues] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await leaguesAPI.myLeagues();
        setLeagues(Array.isArray(res.data) ? res.data : []);
      } catch {
        setLeagues([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="mkt">
      {/* Background glow */}
      <div className="mkt-bg-glow" />

      {/* Header */}
      <header className="mkt-header">
        <button className="mkt-back" onClick={() => navigate('/dashboard')}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6" /></svg>
        </button>
        <div className="mkt-header-center">
          <span className="mkt-header-icon">📈</span>
          <h1>Mercado</h1>
        </div>
        <div style={{ width: 40 }} />
      </header>

      {/* Hero promo section */}
      <div className="mkt-promo-hero">
        <div className="mkt-promo-content">
          <span className="mkt-live-badge"><span className="mkt-pulsing-dot" /> MERCADO ABIERTO</span>
          <h2>Ofertas Exclusivas</h2>
          <p>Encuentra el próximo <strong>Jugador Franquicia</strong> para tu equipo. Subastas diarias con miles de cartas en juego.</p>
          <div className="mkt-promo-stats">
            <div className="mkt-stat-item">
              <strong>24h</strong><span>Ciclo Diario</span>
            </div>
            <div className="mkt-stat-item">
              <strong>12+</strong><span>Cartas/día</span>
            </div>
          </div>
        </div>
        <div className="mkt-promo-visual">
          <div className="mkt-promo-card c1">
            <div className="mkt-card-ovr">92</div>
          </div>
          <div className="mkt-promo-card c2">
            <div className="mkt-card-ovr">88</div>
          </div>
        </div>
      </div>

      {/* Trending highlights (Mock) */}
      <div className="mkt-highlights">
        <div className="mkt-section-header">
          <h3 className="mkt-section-title">Top Fichajes Globales</h3>
          <span className="mkt-badge-hot">🔥 Hot</span>
        </div>
        <div className="mkt-highlight-scroll">
          {/* Mock Card 1 */}
          <div className="mkt-h-card gold">
            <div className="mkt-h-img">
              <img src="/images/placeholder.png" alt="Player" />
              <span className="mkt-h-ovr">82</span>
            </div>
            <div className="mkt-h-info">
              <span className="mkt-h-name">K. Furuhashi</span>
              <span className="mkt-h-price">💰 15.5M</span>
            </div>
          </div>
          {/* Mock Card 2 */}
          <div className="mkt-h-card premium">
            <div className="mkt-h-img">
              <img src="/images/placeholder.png" alt="Player" />
              <span className="mkt-h-ovr">92</span>
            </div>
            <div className="mkt-h-info">
              <span className="mkt-h-name">H. Larsson</span>
              <span className="mkt-h-price">💰 65.0M</span>
            </div>
          </div>
          {/* Mock Card 3 */}
          <div className="mkt-h-card silver">
            <div className="mkt-h-img">
              <img src="/images/placeholder.png" alt="Player" />
              <span className="mkt-h-ovr">76</span>
            </div>
            <div className="mkt-h-info">
              <span className="mkt-h-name">L. Shankland</span>
              <span className="mkt-h-price">💰 6.0M</span>
            </div>
          </div>
        </div>
      </div>

      {/* Leagues */}
      <div className="mkt-section">
        <h3 className="mkt-section-title">Selecciona tu liga</h3>

        {loading ? (
          <div className="mkt-loading">
            <div className="mkt-loading-spinner" />
            <span>Cargando ligas...</span>
          </div>
        ) : leagues.length === 0 ? (
          <div className="mkt-empty">
            <span className="mkt-empty-icon">🏆</span>
            <p>No estás en ninguna liga todavía</p>
            <button className="mkt-empty-btn" onClick={() => navigate('/leagues')}>
              Unirme a una liga →
            </button>
          </div>
        ) : (
          <div className="mkt-league-list">
            {leagues.map(league => (
              <button
                key={league.id}
                className="mkt-league-card"
                onClick={() => navigate(`/leagues/${league.id}`)}
              >
                <div className="mkt-league-icon-wrap">
                  <span className="mkt-league-icon">🏆</span>
                </div>
                <div className="mkt-league-info">
                  <span className="mkt-league-name">{league.name}</span>
                  <span className="mkt-league-sub">
                    {league.member_count || '?'} miembros · Subastas activas
                  </span>
                </div>
                <svg className="mkt-league-arrow" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6" /></svg>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Bottom Nav */}
      <nav className="mkt-nav">
        <button onClick={() => navigate('/dashboard')}>🏠</button>
        <button onClick={() => navigate('/team')}>👥</button>
        <button className="active">🛍️</button>
        <button onClick={() => navigate('/arena')}>⚔️</button>
        <button onClick={() => navigate('/leagues')}>🏆</button>
      </nav>
    </div>
  );
}
