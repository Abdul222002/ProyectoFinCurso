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
          <div className="dash-currency">
            <span className="dash-currency-icon">🪙</span>
            <span className="dash-currency-value">{formatCoins(user?.coins || 10000)}</span>
          </div>
          <button className="dash-logout-btn" onClick={handleLogout} title="Cerrar sesión">
            ⬅️
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="dash-main">
        {/* My Leagues / Teams Summary */}
        <section className="dash-section">
          <div className="dash-section-header">
            <h2 className="dash-section-title">Mis Ligas ({teams.length})</h2>
            <button className="dash-section-link" onClick={() => navigate('/leagues')}>
              Ver todas <span>›</span>
            </button>
          </div>
          {teams.length === 0 ? (
            <div className="dash-squad-card">
              <div className="dash-squad-bg"></div>
              <div className="dash-squad-content">
                <div className="dash-squad-visual">
                  <div className="dash-squad-placeholder">
                    <span>🏆</span>
                    <p>Únete a una liga para empezar</p>
                    <button
                      className="dash-section-link"
                      onClick={() => navigate('/leagues')}
                      style={{ marginTop: '8px', fontSize: '14px' }}
                    >
                      Crear o Unirse →
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            teams.map(team => (
              <div className="dash-squad-card" key={team.id} style={{ marginBottom: '12px', cursor: 'pointer' }}
                   onClick={() => navigate(`/team?league_id=${team.league_id}`)}>
                <div className="dash-squad-bg"></div>
                <div className="dash-squad-content">
                  <div className="dash-squad-stats">
                    <div className="dash-stat-main">
                      <span className="dash-stat-value">
                        {team.overall_rating?.toFixed(1) || '--'}
                      </span>
                      <span className="dash-stat-label">OVR</span>
                    </div>
                    <div className="dash-stat-row">
                      <div className="dash-stat-mini">
                        <span className="dash-stat-mini-value">
                          {team.players?.filter(p => p.is_in_lineup).length || 0}
                        </span>
                        <span className="dash-stat-mini-label">Titulares</span>
                      </div>
                      <div className="dash-stat-mini">
                        <span className="dash-stat-mini-value">
                          {team.active_formation || '4-4-2'}
                        </span>
                        <span className="dash-stat-mini-label">Formación</span>
                      </div>
                    </div>
                  </div>
                  <div className="dash-squad-visual">
                    <div className="dash-squad-placeholder">
                      <span>🏟️</span>
                      <p>{team.name}</p>
                      <small style={{ color: '#94a3b8', fontSize: '11px' }}>{team.league_name || 'Liga'}</small>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </section>

        {/* Quick Actions Grid */}
        <section className="dash-section">
          <h2 className="dash-section-title">Acciones Rápidas</h2>
          <div className="dash-actions-grid">
            <button className="dash-action-card dash-action--team" onClick={() => navigate('/leagues')}>
              <div className="dash-action-icon">🏆</div>
              <div className="dash-action-info">
                <h3>Ligas</h3>
                <p>Crea o únete</p>
              </div>
            </button>

            <button className="dash-action-card dash-action--market" onClick={() => navigate('/market')}>
              <div className="dash-action-icon">📈</div>
              <div className="dash-action-info">
                <h3>Mercado</h3>
                <p>Compra y vende</p>
              </div>
            </button>

            <button className="dash-action-card dash-action--arena" onClick={() => navigate('/arena')}>
              <div className="dash-action-icon">⚔️</div>
              <div className="dash-action-info">
                <h3>Arena PvP</h3>
                <p>Reta a otros</p>
              </div>
            </button>

            <button className="dash-action-card dash-action--packs" onClick={() => navigate('/team')}>
              <div className="dash-action-icon">⚽</div>
              <div className="dash-action-info">
                <h3>Equipos</h3>
                <p>Gestiona tu plantilla</p>
              </div>
            </button>
          </div>
        </section>

        {/* Gameweek Info */}
        <section className="dash-section">
          <div className="dash-section-header">
            <h2 className="dash-section-title">Jornada Actual</h2>
            <span className="dash-badge">Scottish Premiership</span>
          </div>
          <div className="dash-gameweek-card">
            <div className="dash-gameweek-info">
              <span className="dash-gameweek-label">Puntos Fantasy</span>
              <span className="dash-gameweek-points">{user?.total_points || 0}</span>
            </div>
            <div className="dash-gameweek-divider"></div>
            <div className="dash-gameweek-info">
              <span className="dash-gameweek-label">Equipos</span>
              <span className="dash-gameweek-rank">{teams.length}</span>
            </div>
          </div>
        </section>

        {/* Arena Stats (best team) */}
        {bestTeam && (
          <section className="dash-section">
            <h2 className="dash-section-title">Mejor Equipo — {bestTeam.name}</h2>
            <div className="dash-gameweek-card">
              <div className="dash-gameweek-info">
                <span className="dash-gameweek-label">Victorias</span>
                <span className="dash-gameweek-points" style={{ color: '#4ade80' }}>{bestTeam.arena_wins}</span>
              </div>
              <div className="dash-gameweek-divider"></div>
              <div className="dash-gameweek-info">
                <span className="dash-gameweek-label">Empates</span>
                <span className="dash-gameweek-points" style={{ color: '#facc15' }}>{bestTeam.arena_draws}</span>
              </div>
              <div className="dash-gameweek-divider"></div>
              <div className="dash-gameweek-info">
                <span className="dash-gameweek-label">Derrotas</span>
                <span className="dash-gameweek-points" style={{ color: '#f87171' }}>{bestTeam.arena_losses}</span>
              </div>
            </div>
          </section>
        )}
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
              <span className="dash-nav-icon">⚽</span>
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
