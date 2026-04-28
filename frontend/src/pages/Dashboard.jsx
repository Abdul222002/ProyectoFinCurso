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

  const handleLogout = () => { logout(); navigate('/login'); };

  const logoutButton = (
    <button className="dash-logout-btn" onClick={handleLogout}>Cerrar Sesión</button>
  );

  const selectedTeam = teams.find(t => t.id === selectedDashboardTeamId) || teams[0];

  const ACTIONS = [
    {
      id: 'market', icon: '💸', label: 'Mercado', desc: 'Subastas y sobres',
      cls: 'market', onClick: () => navigate('/market')
    },
    {
      id: 'arena', icon: '⚔️', label: 'FootArena', desc: 'Combates PvP',
      cls: 'arena', onClick: () => navigate('/arena')
    },
    {
      id: 'leagues', icon: '🏆', label: 'Ligas', desc: 'Clasificaciones',
      cls: 'leagues', onClick: () => navigate('/leagues')
    },
    {
      id: 'profile', icon: '👤', label: 'Perfil', desc: 'Historial y logros',
      cls: 'profile', onClick: () => navigate('/profile')
    },
    ...(user?.role === 'admin' ? [{
      id: 'admin', icon: '🛡️', label: 'Admin', desc: 'Panel de control',
      cls: 'admin', onClick: () => navigate('/admin')
    }] : [])
  ];

  return (
    <AppLayout title="Inicio" rightContent={logoutButton}>
      <div className="dashboard-content">

        {/* ── HERO BANNER ── */}
        <section className="dash-hero-banner">
          <div className="dash-hero-avatar">
            {user?.username?.charAt(0)?.toUpperCase() || 'M'}
            <span className="dash-hero-level">{user?.level || 1}</span>
          </div>

          <div className="dash-hero-info">
            <span className="dash-hero-badge">
              {selectedTeam?.league_name || 'Fantasy Manager'}
            </span>
            <h2>Bienvenido, {user?.username || 'Manager'}</h2>
            <div className="dash-xp-bar">
              <div
                className="dash-xp-fill"
                style={{ width: `${Math.min((user?.experience || 0) % 100, 100)}%` }}
              />
            </div>
            <p>Gestiona tu plantilla, ficha estrellas y compite.</p>
          </div>

          {/* League logo — big & prominent */}
          <div className="dash-hero-league-logo">
            <img
              src="/spfl-logo.png"
              alt="SPFL"
              onError={e => { e.target.src = '/logo-premium.png'; }}
            />
          </div>
        </section>

        {/* ── MY TEAM CARD ── */}
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

          {loadingTeam ? (
            <div className="dash-squad-card empty">
              <div className="dash-squad-placeholder"><p>Cargando...</p></div>
            </div>
          ) : !selectedTeam ? (
            <div className="dash-squad-card empty">
              <div className="dash-squad-placeholder">
                <span className="empty-icon">🏆</span>
                <p>Aún no tienes equipo</p>
                <button className="btn-primary" onClick={() => navigate('/leagues')}>
                  Unirse a una Liga →
                </button>
              </div>
            </div>
          ) : (
            <div className="dash-squad-card premium" onClick={() => navigate(`/team?league_id=${selectedTeam.league_id}`)}>
              <div className="dash-squad-content">
                {/* OVR circle */}
                <div className="dash-squad-overall">
                  <svg viewBox="0 0 36 36" className="circular-chart">
                    <path className="circle-bg"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path className="circle"
                      strokeDasharray={`${selectedTeam.overall_rating || 0}, 100`}
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <text x="18" y="20.35" className="percentage">
                      {selectedTeam.overall_rating?.toFixed(0) || '--'}
                    </text>
                  </svg>
                  <span className="dash-squad-ovr-label">OVR</span>
                </div>

                {/* Team shield */}
                {selectedTeam.shield_url && (
                  <div className="dash-squad-shield">
                    <img
                      src={selectedTeam.shield_url}
                      alt=""
                      onError={e => { e.target.parentElement.style.display = 'none'; }}
                    />
                  </div>
                )}

                {/* Team info */}
                <div className="dash-squad-info">
                  <h3 className="dash-squad-name">{selectedTeam.name}</h3>
                  <p className="dash-squad-league">⚽ {selectedTeam.league_name || 'Liga Activa'}</p>
                  <div className="dash-squad-minis">
                    <div className="dash-squad-mini">
                      <strong>{selectedTeam.players?.filter(p => p.is_in_lineup).length || 0}</strong> Titulares
                    </div>
                    <div className="dash-squad-mini">
                      <strong>{selectedTeam.active_formation || '4-4-2'}</strong> Formación
                    </div>
                    <div className="dash-squad-mini">
                      <strong>{selectedTeam.players?.length || 0}</strong> Jugadores
                    </div>
                  </div>
                </div>

                <div className="dash-squad-arrow">›</div>
              </div>
            </div>
          )}
        </section>

        {/* ── QUICK ACTIONS ── */}
        <section className="dash-section">
          <h2 className="dash-section-title">Accesos Rápidos</h2>
          <div className="dash-actions-grid">
            {ACTIONS.map(a => (
              <button key={a.id} className={`dash-action-card ${a.cls}`} onClick={a.onClick}>
                <div className="dash-action-icon-wrap">{a.icon}</div>
                <div className="dash-action-info">
                  <h3>{a.label}</h3>
                  <p>{a.desc}</p>
                </div>
              </button>
            ))}
          </div>
        </section>

      </div>
    </AppLayout>
  );
}
