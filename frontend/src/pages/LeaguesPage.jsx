import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { leaguesAPI } from '../services/endpoints';
import './LeaguesPage.css';

export default function LeaguesPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [leagues, setLeagues] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('my'); // my, create, join, invitations
  const [message, setMessage] = useState('');

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
    } catch {}
    setLoading(false);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    setMessage('');
    try {
      await leaguesAPI.create({
        name: newName,
        description: newDesc,
        max_members: newMax,
        is_public: false
      });
      setMessage('✅ ¡Liga creada!');
      setNewName('');
      setNewDesc('');
      setActiveTab('my');
      await loadData();
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
      await leaguesAPI.joinByCode(joinCode);
      setMessage('✅ ¡Te has unido a la liga!');
      setJoinCode('');
      setActiveTab('my');
      await loadData();
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Código inválido'}`);
    }
    setJoining(false);
  };

  const handleAccept = async (id) => {
    try {
      await leaguesAPI.acceptInvitation(id);
      setMessage('✅ Invitación aceptada');
      await loadData();
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Error'}`);
    }
  };

  const handleReject = async (id) => {
    try {
      await leaguesAPI.rejectInvitation(id);
      await loadData();
    } catch {}
  };

  const handleInvite = async (leagueId) => {
    if (!inviteUsername.trim()) return;
    setInviting(true);
    try {
      await leaguesAPI.invite(leagueId, { username: inviteUsername });
      setMessage(`✅ Invitación enviada a @${inviteUsername}`);
      setInviteUsername('');
      setInviteLeagueId(null);
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Error'}`);
    }
    setInviting(false);
  };

  const handleLeave = async (leagueId) => {
    try {
      await leaguesAPI.leave(leagueId);
      setMessage('Has salido de la liga');
      await loadData();
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.detail || 'Error'}`);
    }
  };

  return (
    <div className="leagues-page">
      {/* Header */}
      <header className="lg-header">
        <button className="lg-back-btn" onClick={() => navigate('/dashboard')}>←</button>
        <h1 className="lg-title">🏆 Ligas</h1>
        <div className="lg-coins">🪙 {user?.coins?.toLocaleString()}</div>
      </header>

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
              <button className="lg-cta-btn" onClick={() => setActiveTab('create')}>
                🏆 Crear una Liga
              </button>
              <button className="lg-cta-btn secondary" onClick={() => setActiveTab('join')}>
                🔗 Unirse con Código
              </button>
            </div>
          ) : (
            <div className="lg-list">
              {leagues.map(league => (
                <div key={league.id} className="lg-card">
                  <div className="lg-card-main">
                    <h3 className="lg-card-name">{league.name}</h3>
                    <span className="lg-card-owner">por @{league.owner_username}</span>
                    <div className="lg-card-stats">
                      <span>👥 {league.member_count}/{league.max_members}</span>
                    </div>
                  </div>
                  <div className="lg-card-actions">
                    <button
                      className="lg-card-btn view"
                      onClick={() => navigate(`/leagues/${league.id}`)}
                    >
                      Ver
                    </button>
                    <button
                      className="lg-card-btn invite"
                      onClick={() => setInviteLeagueId(inviteLeagueId === league.id ? null : league.id)}
                    >
                      Invitar
                    </button>
                  </div>

                  {/* Inline invite form */}
                  {inviteLeagueId === league.id && (
                    <div className="lg-invite-inline">
                      <input
                        type="text"
                        value={inviteUsername}
                        onChange={(e) => setInviteUsername(e.target.value)}
                        placeholder="Username del amigo"
                        className="lg-input"
                      />
                      <button
                        className="lg-invite-send"
                        onClick={() => handleInvite(league.id)}
                        disabled={inviting}
                      >
                        {inviting ? '...' : 'Enviar'}
                      </button>
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
            <button type="submit" className="lg-submit-btn" disabled={creating}>
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
            <button type="submit" className="lg-submit-btn" disabled={joining}>
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
                    <button className="lg-invite-btn accept" onClick={() => handleAccept(inv.id)}>
                      ✓ Aceptar
                    </button>
                    <button className="lg-invite-btn reject" onClick={() => handleReject(inv.id)}>
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Bottom Nav */}
      <div className="lg-bottom-bar">
        <button className="lg-bottom-btn" onClick={() => navigate('/dashboard')}>🏠 Home</button>
        <button className="lg-bottom-btn" onClick={() => navigate('/team')}>⚽ Equipo</button>
        <button className="lg-bottom-btn active">🏆 Ligas</button>
      </div>
    </div>
  );
}
