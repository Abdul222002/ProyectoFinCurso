import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { teamsAPI, leaguesAPI } from '../services/endpoints';
import './Dashboard.css';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [teams, setTeams] = useState([]);
  const [loadingTeam, setLoadingTeam] = useState(true);

  useEffect(() => {
    const loadTeams = async () => {
      try {
        const res = await teamsAPI.getMy();
        setTeams(Array.isArray(res.data) ? res.data : [res.data]);
      } catch {
        setTeams([]);
      } finally {
        setLoadingTeam(false);
      }
    };
    loadTeams();
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const formatCoins = (coins) => {
    if (coins >= 1000) return (coins / 1000).toFixed(1) + 'k';
    return coins;
  };

  // Best team for summary display
  const bestTeam = teams.length > 0
    ? teams.reduce((best, t) => t.overall_rating > best.overall_rating ? t : best, teams[0])
    : null;

  return (
    <div className="dashboard">
      {/* Top Header */}
      <header className="dash-header">
        <div className="dash-header-left">
          <div className="dash-avatar">
            <div className="dash-avatar-img">
              {user?.username?.charAt(0)?.toUpperCase() || 'M'}
            </div>
            <div className="dash-level-badge">{user?.level || 1}</div>
          </div>
          <div className="dash-user-info">
            <h1 className="dash-username">{user?.username || 'Manager'}</h1>
            <div className="dash-xp-bar">
              <div
                className="dash-xp-fill"
                style={{ width: `${Math.min((user?.experience || 0) % 100, 100)}%` }}
              ></div>
            </div>
          </div>
        </div>
        <div className="dash-header-right">
          <button className="dash-logout-btn" onClick={handleLogout} title="Cerrar sesión">
            ↩️
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="dash-main">
        {/* Welcome Hero Banner */}
        <section className="dash-hero-banner">
          <div className="dash-hero-content">
            <span className="dash-hero-badge">NUEVA TEMPORADA</span>
            <h2>Bienvenido de nuevo, {user?.username || 'Manager'}</h2>
            <p>Gestiona tu plantilla, ficha estrellas y compite en la Arena.</p>
          </div>
          <div className="dash-hero-image">
            <span style={{ fontSize: '4rem' }}>⚽</span>
          </div>
        </section>

        {/* My Leagues / Teams Summary */}
        <section className="dash-section">
          <div className="dash-section-header">
            <h2 className="dash-section-title">Tu Club ({teams.length})</h2>
            <button className="dash-section-link" onClick={() => navigate('/leagues')}>
              Mis Ligas ›
            </button>
          </div>
          {teams.length === 0 ? (
            <div className="dash-squad-card empty">
              <div className="dash-squad-placeholder">
                <span style={{ fontSize: '2.5rem' }}>🏆</span>
                <p>Aún no tienes equipo</p>
                <button
                  className="dash-primary-btn"
                  onClick={() => navigate('/leagues')}
                >
                  Unirse a una Liga →
                </button>
              </div>
            </div>
          ) : (
            teams.slice(0, 1).map(team => (
              <div className="dash-squad-card premium" key={team.id} onClick={() => navigate(`/team?league_id=${team.league_id}`)}>
                <div className="dash-squad-texture"></div>
                <div className="dash-squad-content">
                  <div className="dash-squad-overall">
                    <svg viewBox="0 0 36 36" className="circular-chart">
                      <path className="circle-bg"
                        d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                      <path className="circle"
                        strokeDasharray={`${team.overall_rating || 0}, 100`}
                        d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                      <text x="18" y="20.35" className="percentage">{team.overall_rating?.toFixed(0) || '--'}</text>
                    </svg>
                    <span className="dash-squad-ovr-label">GRL</span>
                  </div>
                  <div className="dash-squad-info">
                    <h3 className="dash-squad-name">{team.name}</h3>
                    <p className="dash-squad-league">⚔️ {team.league_name || 'Liga Activa'}</p>
                    <div className="dash-squad-minis">
                      <div className="dash-squad-mini">
                        <strong>{team.players?.filter(p => p.is_in_lineup).length || 0}</strong> Titulares
                      </div>
                      <div className="dash-squad-mini">
                        <strong>{team.active_formation || '4-4-2'}</strong> Formación
                      </div>
                    </div>
                  </div>
                  <div className="dash-squad-arrow">›</div>
                </div>
              </div>
            ))
          )}
        </section>

        {/* Quick Actions Grid */}
        <section className="dash-section">
          <h2 className="dash-section-title">Accesos Rápidos</h2>
          <div className="dash-actions-grid">
            <button className="dash-action-card action-team" onClick={() => navigate('/team')}>
              <div className="dash-action-icon">👕</div>
              <div className="dash-action-info">
                <h3>Mi Equipo</h3>
                <p>Gestionar</p>
              </div>
            </button>

            <button className="dash-action-card action-market" onClick={() => navigate('/market')}>
              <div className="dash-action-icon">💸</div>
              <div className="dash-action-info">
                <h3>Mercado</h3>
                <p>Transferencias</p>
              </div>
            </button>

            <button className="dash-action-card action-arena" onClick={() => navigate('/arena')}>
              <div className="dash-action-icon">⚔️</div>
              <div className="dash-action-info">
                <h3>PvP Arena</h3>
                <p>Compite</p>
              </div>
            </button>

            <button className="dash-action-card action-leagues" onClick={() => navigate('/leagues')}>
              <div className="dash-action-icon">🏆</div>
              <div className="dash-action-info">
                <h3>Ligas</h3>
                <p>Ver clasificación</p>
              </div>
            </button>

            <button className="dash-action-card action-profile" onClick={() => navigate('/profile')}>
              <div className="dash-action-icon">👤</div>
              <div className="dash-action-info">
                <h3>Mi Perfil</h3>
                <p>Mensajes</p>
              </div>
            </button>

            {user?.role === 'admin' && (
              <button className="dash-action-card action-admin" onClick={() => navigate('/admin')}>
                <div className="dash-action-icon">🛡️</div>
                <div className="dash-action-info">
                  <h3>Admin</h3>
                  <p>Panel Admin</p>
                </div>
              </button>
            )}
          </div>
        </section>

        {/* Trending Section (Mocked logic for fullness) */}
        <section className="dash-section">
          <div className="dash-section-header">
            <h2 className="dash-section-title">Jugadores Top de la Semana</h2>
            <span className="dash-badge">Premium</span>
          </div>
          <div className="dash-trending-scroll">
            {/* Mock cards to fill the space */}
            <div className="dash-trending-card">
              <div className="trend-img-wrap gold-bg">
                <img src="/images/placeholder.png" alt="Player" className="trend-img" />
                <span className="trend-ovr">81</span>
              </div>
              <div className="trend-info">
                <h4>J. Tavernier</h4>
                <p>Rangers</p>
              </div>
              <div className="trend-price">💰 12.5M</div>
            </div>
            <div className="dash-trending-card">
              <div className="trend-img-wrap legend-bg">
                <img src="/images/placeholder.png" alt="Player" className="trend-img" />
                <span className="trend-ovr">93</span>
              </div>
              <div className="trend-info">
                <h4>K. Dalglish</h4>
                <p>Icon</p>
              </div>
              <div className="trend-price">💰 85.0M</div>
            </div>
            <div className="dash-trending-card">
              <div className="trend-img-wrap gold-bg">
                <img src="/images/placeholder.png" alt="Player" className="trend-img" />
                <span className="trend-ovr">78</span>
              </div>
              <div className="trend-info">
                <h4>B. Miovski</h4>
                <p>Aberdeen</p>
              </div>
              <div className="trend-price">💰 8.0M</div>
            </div>
          </div>
        </section>

      </main>

      {/* Bottom Navigation */}
      <nav className="dash-nav">
        <ul className="dash-nav-list">
          <li>
            <button className="dash-nav-item dash-nav-item--active">
              <span className="dash-nav-icon">🏠</span>
            </button>
          </li>
          <li>
            <button className="dash-nav-item" onClick={() => navigate('/team')}>
              <span className="dash-nav-icon">👥</span>
            </button>
          </li>
          <li>
            <button className="dash-nav-item dash-nav-item--center" onClick={() => navigate('/arena')}>
              <span className="dash-nav-icon">⚔️</span>
            </button>
          </li>
          <li>
            <button className="dash-nav-item" onClick={() => navigate('/market')}>
              <span className="dash-nav-icon">🛍️</span>
            </button>
          </li>
          <li>
            <button className="dash-nav-item" onClick={() => navigate('/leagues')}>
              <span className="dash-nav-icon">🏆</span>
            </button>
          </li>
        </ul>
      </nav>
    </div>
  );
}
