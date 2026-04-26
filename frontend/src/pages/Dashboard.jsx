import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { teamsAPI } from '../services/endpoints';
import AppLayout from '../components/AppLayout';
import './Dashboard.css';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [teams, setTeams] = useState([]);
  const [selectedDashboardTeamId, setSelectedDashboardTeamId] = useState(null);
  const [loadingTeam, setLoadingTeam] = useState(true);

  useEffect(() => {
    const loadTeams = async () => {
      try {
        const res = await teamsAPI.getMy();
        const loadedTeams = Array.isArray(res.data) ? res.data : [res.data];
        setTeams(loadedTeams);
        if (loadedTeams.length > 0) setSelectedDashboardTeamId(loadedTeams[0].id);
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

  const logoutButton = (
    <button className="dash-logout-btn" onClick={handleLogout} title="Cerrar sesión">
      Cerrar Sesión
    </button>
  );

  return (
    <AppLayout title="Inicio" rightContent={logoutButton}>
      <div className="dashboard-content">
        {/* Welcome Hero Banner */}
        <section className="dash-hero-banner">
          <div className="dash-hero-avatar">
            {user?.username?.charAt(0)?.toUpperCase() || 'M'}
            <span className="dash-hero-level">{user?.level || 1}</span>
          </div>
          <div className="dash-hero-info">
            <span className="dash-hero-badge">Scottish Premiership</span>
            <h2>Bienvenido, {user?.username || 'Manager'}</h2>
            <div className="dash-xp-bar">
              <div 
                className="dash-xp-fill" 
                style={{ width: `${Math.min((user?.experience || 0) % 100, 100)}%` }}
              ></div>
            </div>
            <p>Gestiona tu plantilla, ficha estrellas y compite.</p>
          </div>
          <div className="dash-hero-league-logo">
            <img src="/spfl-logo.png" alt="SPFL" />
          </div>
        </section>

        {/* My Leagues / Teams Summary */}
        <section className="dash-section">
          <div className="dash-section-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 className="dash-section-title">Tu Club</h2>
              {teams.length > 1 && (
                <select 
                  className="dash-team-selector"
                  value={selectedDashboardTeamId || ''}
                  onChange={e => setSelectedDashboardTeamId(Number(e.target.value))}
                >
                  {teams.map(t => (
                    <option key={t.id} value={t.id}>{t.name} ({t.league_name})</option>
                  ))}
                </select>
              )}
            </div>
            <button className="dash-section-link" onClick={() => navigate('/leagues')}>
              Mis Ligas ›
            </button>
          </div>
          {teams.length === 0 ? (
            <div className="dash-squad-card empty">
              <div className="dash-squad-placeholder">
                <span className="empty-icon">🏆</span>
                <p>Aún no tienes equipo</p>
                <button
                  className="btn-primary"
                  onClick={() => navigate('/leagues')}
                >
                  Unirse a una Liga →
                </button>
              </div>
            </div>
          ) : (
            teams
              .filter(team => team.id === selectedDashboardTeamId || !selectedDashboardTeamId)
              .slice(0, 1)
              .map(team => (
              <div className="dash-squad-card premium" key={team.id} onClick={() => navigate(`/team?league_id=${team.league_id}`)}>
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
            <button className="dash-action-card" onClick={() => navigate('/market')}>
              <div className="dash-action-icon">💸</div>
              <div className="dash-action-info">
                <h3>Mercado</h3>
              </div>
            </button>

            <button className="dash-action-card" onClick={() => navigate('/arena')}>
              <div className="dash-action-icon">⚔️</div>
              <div className="dash-action-info">
                <h3>PvP Arena</h3>
              </div>
            </button>

            <button className="dash-action-card" onClick={() => navigate('/leagues')}>
              <div className="dash-action-icon">🏆</div>
              <div className="dash-action-info">
                <h3>Ligas</h3>
              </div>
            </button>

            <button className="dash-action-card" onClick={() => navigate('/profile')}>
              <div className="dash-action-icon">👤</div>
              <div className="dash-action-info">
                <h3>Perfil</h3>
              </div>
            </button>

            {user?.role === 'admin' && (
              <button className="dash-action-card" onClick={() => navigate('/admin')}>
                <div className="dash-action-icon">🛡️</div>
                <div className="dash-action-info">
                  <h3>Admin</h3>
                </div>
              </button>
            )}
          </div>
        </section>
      </div>
    </AppLayout>
  );
}
