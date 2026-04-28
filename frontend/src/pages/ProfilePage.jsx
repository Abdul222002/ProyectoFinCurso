import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { leaguesAPI } from '../services/endpoints';
import { toast } from 'sonner';
import AppLayout from '../components/AppLayout';
import WelcomeTeamModal from '../components/WelcomeTeamModal';
import './ProfilePage.css';

export default function ProfilePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [leagues, setLeagues] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [welcomeData, setWelcomeData] = useState(null);
  const [activeTab, setActiveTab] = useState('info');
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [saving, setSaving] = useState(false);

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
      const res = await leaguesAPI.acceptInvitation(id);
      setInvitations(prev => prev.filter(inv => inv.id !== id));
      const leaguesRes = await leaguesAPI.myLeagues();
      setLeagues(Array.isArray(leaguesRes.data) ? leaguesRes.data : []);
      if (res.data?.assigned_players?.length > 0) {
        setWelcomeData({
          leagueName: res.data.name,
          leagueId: res.data.id,
          players: res.data.assigned_players,
        });
      } else {
        toast.success('✅ ¡Te has unido a la liga!');
      }
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

  const handleSaveProfile = async () => {
    if (!newUsername.trim() || newUsername === user?.username) {
      setEditMode(false);
      return;
    }
    
    setSaving(true);
    try {
      const { authAPI } = await import('../services/endpoints');
      await authAPI.updateProfile({ username: newUsername });
      toast.success('Perfil actualizado correctamente');
      setTimeout(() => window.location.reload(), 1000);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al actualizar perfil');
      setSaving(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  if (loading) {
    return (
      <AppLayout title="Mi Perfil" backTo="/dashboard">
        <div className="profile-loading">Cargando perfil...</div>
      </AppLayout>
    );
  }

  return (
    <>
    <AppLayout title="Mi Perfil" backTo="/dashboard">
      <div className="profile-container">
        
        {/* User Card */}
        <section className="profile-user-card">
          <div className="profile-avatar">
            <span className="profile-avatar-letter">
              {user?.username?.charAt(0)?.toUpperCase() || '?'}
            </span>
          </div>
          <div className="profile-user-info">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {editMode ? (
                <input 
                  type="text" 
                  value={newUsername} 
                  onChange={e => setNewUsername(e.target.value)}
                  className="profile-edit-input"
                  autoFocus
                  disabled={saving}
                />
              ) : (
                <h2 className="profile-username">{user?.username || 'Manager'}</h2>
              )}
              
              {editMode ? (
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button 
                    className="btn-primary profile-save-btn" 
                    onClick={handleSaveProfile}
                    disabled={saving}
                  >
                    {saving ? '...' : 'Guardar'}
                  </button>
                  <button 
                    className="profile-cancel-btn"
                    onClick={() => setEditMode(false)}
                    disabled={saving}
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <button 
                  className="profile-edit-toggle"
                  onClick={() => {
                    setNewUsername(user?.username || '');
                    setEditMode(true);
                  }}
                  title="Editar Nombre"
                >
                  ✏️
                </button>
              )}
            </div>
            <p className="profile-email">{user?.email || ''}</p>
            <div className="profile-meta">
              <span className="profile-meta-badge">
                🏆 {leagues.length} {leagues.length === 1 ? 'liga' : 'ligas'}
              </span>
              <span className="profile-meta-badge">
                ⭐ Nivel {user?.level || 1}
              </span>
              <span className="profile-meta-badge">
                📅 Desde {formatDate(user?.created_at)}
              </span>
            </div>
          </div>
        </section>

        {/* Tabs */}
        <div className="lg-tabs" style={{ margin: '0 20px 10px', borderRadius: '14px', overflow: 'hidden' }}>
          <button
            className={`lg-tab ${activeTab === 'info' ? 'active' : ''}`}
            onClick={() => setActiveTab('info')}
          >
            🏟️ Mis Ligas
          </button>
          <button
            className={`lg-tab ${activeTab === 'inbox' ? 'active' : ''}`}
            onClick={() => setActiveTab('inbox')}
          >
            📩 Mensajes {invitations.length > 0 && <span className="profile-tab-badge">{invitations.length}</span>}
          </button>
        </div>

        {/* Tab Content */}
        <main className="profile-main-content">
          {activeTab === 'info' && (
            <div className="profile-leagues-list">
              {leagues.length === 0 ? (
                <div className="lg-empty">
                  <span className="profile-empty-icon">🏆</span>
                  <p>No estás en ninguna liga</p>
                  <button className="btn-primary" onClick={() => navigate('/leagues')}>
                    Unirse a una Liga →
                  </button>
                </div>
              ) : (
                leagues.map(league => (
                  <div
                    key={league.id}
                    className="lg-card profile-league-card"
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

          {activeTab === 'inbox' && (
            <div className="profile-inbox">
              {invitations.length === 0 ? (
                <div className="lg-empty">
                  <span className="profile-empty-icon">📭</span>
                  <p>No tienes invitaciones pendientes</p>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)'}}>
                    Cuando alguien te invite a una liga, aparecerá aquí.
                  </span>
                </div>
              ) : (
                invitations.map(inv => (
                  <div key={inv.id} className="profile-invitation-card lg-card">
                    <div className="profile-invitation-content">
                      <span className="profile-invitation-icon">📩</span>
                      <div className="profile-invitation-info">
                        <h3 className="profile-invitation-title">
                          Invitación a <strong>{inv.league_name}</strong>
                        </h3>
                        <p className="profile-invitation-from">
                          De: {inv.invited_by_username || 'Admin'} · {formatDate(inv.created_at)}
                        </p>
                      </div>
                      <div className="profile-invitation-actions">
                        <button
                          className="btn-primary"
                          onClick={() => handleAccept(inv.id)}
                        >
                          Aceptar
                        </button>
                        <button
                          className="lg-btn-danger"
                          onClick={() => handleReject(inv.id)}
                        >
                          Rechazar
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </main>
      </div>
    </AppLayout>

    {welcomeData && (
      <WelcomeTeamModal
        leagueName={welcomeData.leagueName}
        leagueId={welcomeData.leagueId}
        players={welcomeData.players}
        onClose={() => setWelcomeData(null)}
      />
    )}
    </>
  );
}
