import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { leaguesAPI } from '../services/endpoints';
import { toast } from 'sonner';
import './ProfilePage.css';

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [leagues, setLeagues] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [activeTab, setActiveTab] = useState('info');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [leaguesRes, invRes] = await Promise.all([
          leaguesAPI.myLeagues(),
          leaguesAPI.pendingInvitations()
        ]);
        setLeagues(Array.isArray(leaguesRes.data) ? leaguesRes.data : []);
        setInvitations(Array.isArray(invRes.data) ? invRes.data : []);
      } catch {
        setLeagues([]);
        setInvitations([]);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const handleAccept = async (id) => {
    try {
      await leaguesAPI.acceptInvitation(id);
      toast.success('✅ ¡Te has unido a la liga!');
      setInvitations(prev => prev.filter(inv => inv.id !== id));
      // Refresh leagues
      const res = await leaguesAPI.myLeagues();
      setLeagues(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al aceptar invitación');
    }
  };

  const handleReject = async (id) => {
    try {
      await leaguesAPI.rejectInvitation(id);
      toast.info('Invitación rechazada');
      setInvitations(prev => prev.filter(inv => inv.id !== id));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al rechazar invitación');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  if (loading) {
    return (
      <div className="profile-page">
        <div className="profile-loading">⚽ Cargando perfil...</div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      {/* Background glow */}
      <div className="profile-bg-glow"></div>

      {/* Header */}
      <header className="profile-header">
        <button className="profile-back-btn" onClick={() => navigate('/dashboard')}>
          <span>‹</span> Volver
        </button>
        <h1 className="profile-page-title">Mi Perfil</h1>
        <button className="profile-logout-btn" onClick={handleLogout}>
          Cerrar sesión
        </button>
      </header>

      {/* User Card */}
      <section className="profile-user-card">
        <div className="profile-avatar">
          <span className="profile-avatar-letter">
            {user?.username?.charAt(0)?.toUpperCase() || '?'}
          </span>
        </div>
        <div className="profile-user-info">
          <h2 className="profile-username">{user?.username || 'Manager'}</h2>
          <p className="profile-email">{user?.email || ''}</p>
          <div className="profile-meta">
            <span className="profile-meta-item">
              🏆 {leagues.length} {leagues.length === 1 ? 'liga' : 'ligas'}
            </span>
            <span className="profile-meta-item">
              ⭐ Nivel {user?.level || 1}
            </span>
            <span className="profile-meta-item">
              📅 Desde {formatDate(user?.created_at)}
            </span>
          </div>
        </div>
      </section>

      {/* Tabs */}
      <nav className="profile-tabs">
        <button
          className={`profile-tab ${activeTab === 'info' ? 'active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          🏟️ Mis Ligas
        </button>
        <button
          className={`profile-tab ${activeTab === 'inbox' ? 'active' : ''}`}
          onClick={() => setActiveTab('inbox')}
        >
          📩 Mensajes {invitations.length > 0 && <span className="profile-tab-badge">{invitations.length}</span>}
        </button>
      </nav>

      {/* Tab Content */}
      <main className="profile-content">
        {/* My Leagues Tab */}
        {activeTab === 'info' && (
          <div className="profile-leagues-list">
            {leagues.length === 0 ? (
              <div className="profile-empty">
                <span className="profile-empty-icon">🏆</span>
                <p>No estás en ninguna liga</p>
                <button className="profile-action-btn" onClick={() => navigate('/leagues')}>
                  Unirse a una Liga →
                </button>
              </div>
            ) : (
              leagues.map(league => (
                <div
                  key={league.id}
                  className="profile-league-card"
                  onClick={() => navigate(`/leagues/${league.id}`)}
                >
                  <div className="profile-league-icon">⚽</div>
                  <div className="profile-league-info">
                    <h3 className="profile-league-name">{league.name}</h3>
                    <p className="profile-league-detail">
                      {league.member_count || '?'} miembros · Creada {formatDate(league.created_at)}
                    </p>
                  </div>
                  <span className="profile-league-arrow">›</span>
                </div>
              ))
            )}
          </div>
        )}

        {/* Inbox Tab */}
        {activeTab === 'inbox' && (
          <div className="profile-inbox">
            {invitations.length === 0 ? (
              <div className="profile-empty">
                <span className="profile-empty-icon">📭</span>
                <p>No tienes invitaciones pendientes</p>
                <span className="profile-empty-sub">Cuando alguien te invite a una liga, aparecerá aquí.</span>
              </div>
            ) : (
              invitations.map(inv => (
                <div key={inv.id} className="profile-invitation-card">
                  <div className="profile-invitation-header">
                    <span className="profile-invitation-icon">📩</span>
                    <div className="profile-invitation-info">
                      <h3 className="profile-invitation-title">
                        Invitación a <strong>{inv.league_name}</strong>
                      </h3>
                      <p className="profile-invitation-from">
                        De: {inv.invited_by_name || 'Admin'} · {formatDate(inv.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="profile-invitation-actions">
                    <button
                      className="profile-inv-btn accept"
                      onClick={() => handleAccept(inv.id)}
                    >
                      ✅ Aceptar
                    </button>
                    <button
                      className="profile-inv-btn reject"
                      onClick={() => handleReject(inv.id)}
                    >
                      ❌ Rechazar
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </main>
    </div>
  );
}
