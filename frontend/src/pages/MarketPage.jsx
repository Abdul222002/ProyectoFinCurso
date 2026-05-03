import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { leaguesAPI, auctionAPI } from '../services/endpoints';
import { resolvePlayerImageUrl } from '../utils/mediaUrl';
import AppLayout from '../components/AppLayout';
import './MarketPage.css';

export default function MarketPage() {
  const navigate = useNavigate();
  const [leagues, setLeagues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [trends, setTrends] = useState([]);
  const [trendsLoading, setTrendsLoading] = useState(true);

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

    const loadTrends = async () => {
      try {
        const res = await auctionAPI.getGlobalTrends();
        setTrends(res.data || []);
      } catch {
        setTrends([]);
      } finally {
        setTrendsLoading(false);
      }
    };

    load();
    loadTrends();
  }, []);

  const formatPrice = (price) => {
    if (price >= 1000000) return (price / 1000000).toFixed(1) + 'M';
    if (price >= 1000) return (price / 1000).toFixed(0) + 'K';
    return price?.toLocaleString() || '0';
  };

  const getRarityClass = (rarity) => {
    switch (rarity?.toLowerCase()) {
      case 'gold': return 'gold';
      case 'legend': return 'diamond';
      case 'silver': return 'silver';
      default: return 'bronze';
    }
  };

  return (
    <AppLayout title="🛍️ Mercado" backTo="/dashboard">
      <div className="mkt-container">

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
                <strong>10+</strong><span>Subastas/día</span>
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

        {/* Comprar Sobres Section */}
        <div className="mkt-packs-section">
          <div className="mkt-packs-card" onClick={() => {
            if (leagues.length === 1) {
              navigate(`/leagues/${leagues[0].id}?tab=packs`);
            } else {
              document.getElementById('mkt-leagues-section')?.scrollIntoView({ behavior: 'smooth' });
            }
          }}>
            <div className="mkt-packs-icon">🎁</div>
            <div className="mkt-packs-info">
              <h3>Comprar Sobres</h3>
              <p>Refuerza tu plantilla abriendo sobres de jugadores garantizados. Selecciona una liga para comprar.</p>
            </div>
            <div className="mkt-packs-arrow">›</div>
          </div>
        </div>

        {/* Trending highlights (Mock) */}
        <div className="mkt-highlights">
          <div className="mkt-section-header">
            <h3 className="mkt-section-title">En Tendencia Global</h3>
            <span className="mkt-badge-hot">🔥 Hot</span>
          </div>
          <div className="mkt-highlight-scroll">
            {trendsLoading ? (
              <div className="mkt-loading-small">Cargando tendencias...</div>
            ) : trends.length === 0 ? (
              <div className="mkt-no-trends">No hay tendencias hoy</div>
            ) : (
              trends.map(player => (
                <div key={player.id} className={`mkt-h-card ${player.base_rarity === 'legend' ? 'premium' : ''}`}>
                  <div className={`mkt-h-img ${getRarityClass(player.base_rarity)}`}>
                    <img 
                      src={resolvePlayerImageUrl(player.image_url, player.name)} 
                      alt={player.name}
                      className="mkt-h-player-img"
                      onError={(e) => { e.target.onerror=null; e.target.src=`https://ui-avatars.com/api/?name=${encodeURIComponent(player.name)}&background=152e20&color=25f478&bold=true`; }}
                    />
                    <span className="mkt-h-ovr">{player.overall_rating}</span>
                  </div>
                  <div className="mkt-h-info">
                    <span className="mkt-h-name">{player.name}</span>
                    <span className="mkt-h-price">{formatPrice(player.current_price)} 🪙</span>
                    {player.acquisitions_count > 0 && (
                      <span className="mkt-h-count">🔥 {player.acquisitions_count} fichajes</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Leagues */}
        <div className="mkt-section" id="mkt-leagues-section">
          <h3 className="mkt-section-title">Mercado de Ligas (Entrar)</h3>

          {loading ? (
            <div className="mkt-loading">
              <div className="mkt-loading-spinner" />
              <span>Cargando mercados...</span>
            </div>
          ) : leagues.length === 0 ? (
            <div className="lg-empty">
              <span className="mkt-empty-icon">🏆</span>
              <p>No estás en ninguna liga todavía</p>
              <button className="btn-primary" onClick={() => navigate('/leagues')}>
                Unirme a una liga →
              </button>
            </div>
          ) : (
            <div className="mkt-league-list">
              {leagues.map(league => (
                <button
                  key={league.id}
                  className="mkt-league-card"
                  onClick={() => navigate(`/leagues/${league.id}?tab=market`)}
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
                  <div className="mkt-league-arrow">›</div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
