import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { teamsAPI, leaguesAPI } from '../services/endpoints';
import './TeamManagementPage.css';

export default function TeamManagementPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const leagueIdParam = searchParams.get('league_id');

  const [teams, setTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const FORMATIONS = ['4-4-2', '4-3-3', '3-5-2', '4-2-3-1', '3-4-3', '5-3-2'];

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      if (leagueIdParam) {
        // Load specific league team
        const res = await teamsAPI.getMy(leagueIdParam);
        setSelectedTeam(res.data);
        setTeams([res.data]);
      } else {
        // Load all teams
        const res = await teamsAPI.getMy();
        const allTeams = Array.isArray(res.data) ? res.data : [res.data];
        setTeams(allTeams);
        if (allTeams.length > 0) {
          setSelectedTeam(allTeams[0]);
        }
      }
    } catch {
      setTeams([]);
      setSelectedTeam(null);
    }
    setLoading(false);
  }, [leagueIdParam]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleToggleLineup = async (cardId, isCurrentlyInLineup) => {
    if (!selectedTeam) return;

    const currentLineup = selectedTeam.players.filter(p => p.is_in_lineup).map(p => p.id);
    let newLineup;

    if (isCurrentlyInLineup) {
      newLineup = currentLineup.filter(id => id !== cardId);
    } else {
      if (currentLineup.length >= 11) {
        setError('Ya tienes 11 titulares. Quita uno primero.');
        return;
      }
      newLineup = [...currentLineup, cardId];
    }

    try {
      const res = await teamsAPI.setLineup(selectedTeam.league_id, newLineup);
      setSelectedTeam(res.data);
      setTeams(prev => prev.map(t => t.id === res.data.id ? res.data : t));
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al actualizar alineación');
    }
  };

  const handleFormationChange = async (formation) => {
    if (!selectedTeam) return;
    try {
      const res = await teamsAPI.update(selectedTeam.league_id, { formation });
      setSelectedTeam(res.data);
      setTeams(prev => prev.map(t => t.id === res.data.id ? res.data : t));
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cambiar formación');
    }
  };

  if (loading) {
    return (
      <div className="team-page">
        <div className="team-loading">⚽ Cargando equipos...</div>
      </div>
    );
  }

  // No teams — redirect to leagues
  if (teams.length === 0) {
    return (
      <div className="team-page">
        <header className="team-header">
          <button className="team-back-btn" onClick={() => navigate('/dashboard')}>← Volver</button>
          <h1 className="team-title">Mi Equipo</h1>
        </header>
        <div className="team-empty">
          <span className="team-empty-icon">🏆</span>
          <h2>No tienes equipos aún</h2>
          <p>Únete a una liga para crear tu equipo automáticamente con 15 jugadores aleatorios.</p>
          <button className="team-create-btn" onClick={() => navigate('/leagues')}>
            Ir a Ligas →
          </button>
        </div>
      </div>
    );
  }

  const lineup = selectedTeam?.players?.filter(p => p.is_in_lineup) || [];
  const bench = selectedTeam?.players?.filter(p => !p.is_in_lineup) || [];

  return (
    <div className="team-page">
      <header className="team-header">
        <button className="team-back-btn" onClick={() => navigate('/dashboard')}>← Volver</button>
        <h1 className="team-title">{selectedTeam?.name || 'Mi Equipo'}</h1>
        <div className="team-ovr">OVR {selectedTeam?.overall_rating?.toFixed(1) || '--'}</div>
      </header>

      {/* League selector (if multiple teams) */}
      {teams.length > 1 && (
        <div className="team-league-selector">
          {teams.map(t => (
            <button
              key={t.id}
              className={`team-league-btn ${selectedTeam?.id === t.id ? 'active' : ''}`}
              onClick={() => setSelectedTeam(t)}
            >
              {t.league_name || 'Liga'} — {t.name}
            </button>
          ))}
        </div>
      )}

      {error && <div className="team-error">❌ {error}</div>}
      {success && <div className="team-success">✅ {success}</div>}

      {/* Formation */}
      <div className="team-formation">
        <label>Formación:</label>
        <div className="team-formation-options">
          {FORMATIONS.map(f => (
            <button
              key={f}
              className={`team-formation-btn ${selectedTeam?.active_formation === f ? 'active' : ''}`}
              onClick={() => handleFormationChange(f)}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Lineup */}
      <section className="team-section">
        <h2 className="team-section-title">⚽ Titulares ({lineup.length}/11)</h2>
        <div className="team-players-grid">
          {lineup.map(card => (
            <div key={card.id} className="team-player-card team-player--lineup">
              <div className="team-player-ovr">{card.current_overall}</div>
              <div className="team-player-info">
                <span className="team-player-name">{card.player_name}</span>
                <span className="team-player-pos">{card.position}</span>
              </div>
              <button
                className="team-player-action team-player-action--remove"
                onClick={() => handleToggleLineup(card.id, true)}
              >
                ↓ Banco
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Bench */}
      <section className="team-section">
        <h2 className="team-section-title">🪑 Suplentes ({bench.length})</h2>
        <div className="team-players-grid">
          {bench.map(card => (
            <div key={card.id} className="team-player-card team-player--bench">
              <div className="team-player-ovr">{card.current_overall}</div>
              <div className="team-player-info">
                <span className="team-player-name">{card.player_name}</span>
                <span className="team-player-pos">{card.position}</span>
              </div>
              <button
                className="team-player-action team-player-action--add"
                onClick={() => handleToggleLineup(card.id, false)}
              >
                ↑ Titular
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Bottom nav */}
      <nav className="team-nav">
        <button onClick={() => navigate('/dashboard')}>🏠</button>
        <button className="active">👥</button>
        <button onClick={() => navigate('/arena')}>⚽</button>
        <button onClick={() => navigate('/market')}>🛍️</button>
        <button onClick={() => navigate('/leagues')}>🏆</button>
      </nav>
    </div>
  );
}
