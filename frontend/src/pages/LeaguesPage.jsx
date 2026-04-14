import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { leaguesAPI, authAPI } from '../services/endpoints';
import { toast } from 'sonner';
import AppLayout from '../components/AppLayout';
import WelcomeTeamModal from '../components/WelcomeTeamModal';
import './LeaguesPage.css';

export default function LeaguesPage() {
  const { user } = useAuth();
  const [leagues, setLeagues] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('my'); // my, create, join, invitations
  const [message, setMessage] = useState('');
  const [welcomeData, setWelcomeData] = useState(null); // { leagueName, players }  →  shows modal

  // Create form
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newMax, setNewMax] = useState(10);
  const [creating, setCreating] = useState(false);

  // Join form
  const [joinCode, setJoinCode] = useState('');
  const [joining, setJoining] = useState(false);

  // Invite form
  const [inviteLeagueId, setInviteLeagueId] = useState(null);
  const [inviteUsername, setInviteUsername] = useState('');
  const [inviting, setInviting] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  // Debounced user search
  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    const delayFn = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await authAPI.searchUsers(searchQuery);
        setSearchResults(res.data || []);
      } catch (err) {
        setSearchResults([]);
      }
      setSearching(false);
    }, 300);
    return () => clearTimeout(delayFn);
  }, [searchQuery]);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [leaguesRes, invRes] = await Promise.all([
        leaguesAPI.myLeagues(),
        leaguesAPI.pendingInvitations()
      ]);
      setLeagues(leaguesRes.data);
      setInvitations(invRes.data);
    } catch { }
    setLoading(false);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    setMessage('');
    try {
      const res = await leaguesAPI.create({
        name: newName,
        description: newDesc,
        max_members: newMax,
        is_public: false
      });
      setNewName('');
      setNewDesc('');
      setActiveTab('my');
      await loadData();
      // Mostrar animación de bienvenida
      if (res.data?.assigned_players?.length > 0) {
        setWelcomeData({ leagueName: res.data.name, players: res.data.assigned_players });
      }
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Error al crear liga'}`);
    }
    setCreating(false);
  };

  const handleJoin = async (e) => {
    e.preventDefault();
    setJoining(true);
    setMessage('');
    try {
      const res = await leaguesAPI.joinByCode(joinCode);
      setJoinCode('');
      setActiveTab('my');
      await loadData();
      // Mostrar animación de bienvenida
      if (res.data?.assigned_players?.length > 0) {
        setWelcomeData({ leagueName: res.data.name, players: res.data.assigned_players });
      }
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Código inválido'}`);
    }
    setJoining(false);
  };

  const handleAccept = async (id) => {
    try {
      const res = await leaguesAPI.acceptInvitation(id);
      await loadData();
      // Mostrar animación de bienvenida
      if (res.data?.assigned_players?.length > 0) {
        setWelcomeData({ leagueName: res.data.name, players: res.data.assigned_players });
      }
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Error'}`);
    }
  };

  const handleReject = async (id) => {
    try {
      await leaguesAPI.rejectInvitation(id);
      await loadData();
    } catch { }
  };

  const handleInvite = async (leagueId, targetUser = null) => {
    let input = (targetUser || inviteUsername || searchQuery).trim();
    if (!input) return;
    setInviting(true);
    
    // Determine if input is an email or username
    const isEmail = input.includes('@') && input.includes('.');
    input = input.startsWith('@') ? input.slice(1) : input;
    const payload = isEmail ? { email: input } : { username: input };
    
    try {
      await leaguesAPI.invite(leagueId, payload);
      setMessage(`✅ Invitación enviada a ${input}`);
      setInviteUsername('');
      setSearchQuery('');
      setSearchResults([]);
      setInviteLeagueId(null);
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Error'}`);
    }
    setInviting(false);
  };

  const handleLeave = async (league) => {
    toast.error(`¿Seguro que quieres abandonar ${league.name}?`, {
      cancel: { label: 'Cancelar' },
      action: {
        label: 'Abandonar',
        onClick: async () => {
          try {
            await leaguesAPI.leave(league.id);
            setMessage(`✅ Has abandonado ${league.name}`);
            await loadData();
          } catch (err) {
            setMessage(`❌ ${err.response?.data?.detail || 'Error al abandonar la liga'}`);
          }
        }
      }
    });
  };

  return (
    <>
    <AppLayout title="🏆 Ligas" backTo="/dashboard">
      <div className="leagues-container">
        {/* Message */}
        {message && (
          <div className={`lg-message ${message.startsWith('✅') ? 'success' : 'error'}`}>
            {message}
            <button className="lg-msg-close" onClick={() => setMessage('')}>✕</button>
          </div>
        )}

        {/* Tabs */}
        <div className="lg-tabs">
          <button className={`lg-tab ${activeTab === 'my' ? 'active' : ''}`} onClick={() => setActiveTab('my')}>
            Mis Ligas
          </button>
          <button className={`lg-tab ${activeTab === 'create' ? 'active' : ''}`} onClick={() => setActiveTab('create')}>
            + Crear
          </button>
          <button className={`lg-tab ${activeTab === 'join' ? 'active' : ''}`} onClick={() => setActiveTab('join')}>
            Unirse
          </button>
          <button className={`lg-tab ${activeTab === 'invitations' ? 'active' : ''}`} onClick={() => setActiveTab('invitations')}>
            📩 {invitations.length > 0 ? `(${invitations.length})` : ''}
          </button>
        </div>

        {/* My Leagues */}
        {activeTab === 'my' && (
          <div className="lg-content">
            {loading ? (
              <div className="lg-loading">Cargando...</div>
            ) : leagues.length === 0 ? (
              <div className="lg-empty">
                <p>No estás en ninguna liga aún</p>
                <button className="btn-primary" onClick={() => setActiveTab('create')}>
                  🏆 Crear una Liga
                </button>
                <div style={{ padding: '8px' }}></div>
                <button className="btn-secondary" onClick={() => setActiveTab('join')}>
                  🔗 Unirse con Código
                </button>
              </div>
            ) : (
              <div className="lg-list">
                {leagues.map(league => (
                  <div key={league.id} className="lg-card">
                    <div className="lg-card-main">
                      <div className="lg-card-info">
                        <h3 className="lg-card-name">{league.name}</h3>
                        <div className="lg-card-meta">
                          <span className="lg-card-owner">por @{league.owner_username}</span>
                          <span className="lg-card-stats"> · {league.member_count}/{league.max_members} 👥</span>
                        </div>
                      </div>
                      <div className="lg-card-actions">
                        <button
                          className="btn-primary"
                          onClick={() => window.location.assign(`/leagues/${league.id}`)}
                        >
                          Ver
                        </button>
                        <button
                          className="btn-secondary"
                          onClick={() => setInviteLeagueId(inviteLeagueId === league.id ? null : league.id)}
                        >
                          Invitar
                        </button>
                        {league.owner_username !== user?.username && (
                          <button
                            className="lg-btn-danger"
                            onClick={() => handleLeave(league)}
                            title="Abandonar liga"
                          >
                            Salir
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Inline invite form */}
                    {inviteLeagueId === league.id && (
                      <div className="lg-invite-inline">
                        <input
                          type="text"
                          value={searchQuery || inviteUsername}
                          onChange={(e) => {
                            setSearchQuery(e.target.value);
                            setInviteUsername(e.target.value);
                          }}
                          placeholder="Nombre de usuario o correo..."
                          className="lg-input"
                        />
                        <button
                          className="lg-invite-send"
                          onClick={() => handleInvite(league.id)}
                          disabled={inviting}
                        >
                          {inviting || searching ? '...' : 'Enviar'}
                        </button>

                        {/* Search Results Dropdown */}
                        {searchResults.length > 0 && searchQuery.length >= 2 && (
                          <div className="ld-search-results">
                            {searchResults.map(u => (
                              <div
                                key={u.id}
                                className="ld-search-item"
                                onClick={() => {
                                  setInviteUsername(u.username);
                                  setSearchQuery('');
                                  setSearchResults([]);
                                  handleInvite(league.id, u.username);
                                }}
                              >
                                <div style={{ fontWeight: 'bold' }}>@{u.username}</div>
                                {u.email && <div style={{ fontSize: '0.8em', color: 'var(--text-secondary)' }}>{u.email}</div>}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Create League */}
        {activeTab === 'create' && (
          <div className="lg-content">
            <form onSubmit={handleCreate} className="lg-form">
              <h2 className="lg-form-title">Crear nueva liga</h2>
              <label className="lg-label">
                Nombre de la liga
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Ej: Liga de Amigos"
                  className="lg-input"
                  required
                  minLength={3}
                />
              </label>
              <label className="lg-label">
                Descripción (opcional)
                <textarea
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Describe tu liga..."
                  className="lg-textarea"
                  rows={3}
                />
              </label>
              <label className="lg-label">
                Máximo de miembros
                <select
                  value={newMax}
                  onChange={(e) => setNewMax(Number(e.target.value))}
                  className="lg-select"
                >
                  {[4, 6, 8, 10, 12, 16, 20].map(n => (
                    <option key={n} value={n}>{n} jugadores</option>
                  ))}
                </select>
              </label>
              <button type="submit" className="btn-primary" disabled={creating} style={{width: '100%', marginTop: '1rem'}}>
                {creating ? 'Creando...' : '🏆 Crear Liga'}
              </button>
            </form>
          </div>
        )}

        {/* Join by Code */}
        {activeTab === 'join' && (
          <div className="lg-content">
            <form onSubmit={handleJoin} className="lg-form">
              <h2 className="lg-form-title">Unirse a una liga</h2>
              <p className="lg-form-desc">
                Introduce el código de invitación que te ha dado un amigo
              </p>
              <label className="lg-label">
                Código de invitación
                <input
                  type="text"
                  value={joinCode}
                  onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                  placeholder="Ej: A1B2C3D4"
                  className="lg-input lg-input-code"
                  required
                  maxLength={8}
                />
              </label>
              <button type="submit" className="btn-primary" disabled={joining} style={{width: '100%', marginTop: '1rem'}}>
                {joining ? 'Uniéndose...' : '🔗 Unirse'}
              </button>
            </form>
          </div>
        )}

        {/* Pending Invitations */}
        {activeTab === 'invitations' && (
          <div className="lg-content">
            {invitations.length === 0 ? (
              <div className="lg-empty">
                <p>No tienes invitaciones pendientes</p>
              </div>
            ) : (
              <div className="lg-list">
                {invitations.map(inv => (
                  <div key={inv.id} className="lg-invite-card">
                    <div className="lg-invite-info">
                      <h3>{inv.league_name}</h3>
                      <span>Invitado por @{inv.invited_by_username}</span>
                    </div>
                    <div className="lg-invite-actions">
                      <button className="btn-primary" onClick={() => handleAccept(inv.id)}>
                        Aceptar
                      </button>
                      <button className="lg-btn-danger" onClick={() => handleReject(inv.id)}>
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>

    {/* ── Animación de bienvenida al unirse/crear liga ── */}
    {welcomeData && (
      <WelcomeTeamModal
        leagueName={welcomeData.leagueName}
        players={welcomeData.players}
        onClose={() => setWelcomeData(null)}
      />
    )}
    </>
  );
}
