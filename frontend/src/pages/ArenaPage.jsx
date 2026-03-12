import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { arenaAPI, teamsAPI } from '../services/endpoints';
import { toast } from 'sonner';
import './ArenaPage.css';

export default function ArenaPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [teams, setTeams] = useState([]);
  const [history, setHistory] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [activeTab, setActiveTab] = useState('combat'); // combat, history, leaderboard
  
  const [selectedTeamId, setSelectedTeamId] = useState('');
  
  // Battle state
  const [combatState, setCombatState] = useState('idle'); // idle, searching, vs, result
  const [battleResult, setBattleResult] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statusRes, teamsRes, historyRes, lbRes] = await Promise.all([
        arenaAPI.getStatus(),
        teamsAPI.getMy(),
        arenaAPI.history(10),
        arenaAPI.leaderboard(50)
      ]);
      setStatus(statusRes.data);
      setTeams(teamsRes.data);
      if (teamsRes.data.length > 0) {
        setSelectedTeamId(teamsRes.data[0].id.toString());
      }
      setHistory(historyRes.data);
      setLeaderboard(lbRes.data);
    } catch (err) {
      toast.error('Error al cargar datos de la Arena');
    }
    setLoading(false);
  };

  const startCombat = async () => {
    if (!selectedTeamId) {
      toast.error('Selecciona un equipo primero');
      return;
    }
    if (status?.arena_tickets <= 0) {
      toast.error('No te quedan tickets hoy. Vuelve mañana o compra más.');
      return;
    }
    
    setCombatState('searching');
    
    // Simulate finding match (1.5 seconds)
    setTimeout(async () => {
      try {
        const res = await arenaAPI.simulate(parseInt(selectedTeamId));
        setBattleResult(res.data);
        setCombatState('vs'); // Transition to VS screen
        
        // Refresh status to get new tickets & elo
        const statusRes = await arenaAPI.getStatus();
        setStatus(statusRes.data);
        
        // Refresh history & LB
        Promise.all([
          arenaAPI.history(10),
          arenaAPI.leaderboard(50)
        ]).then(([histRes, lbRes]) => {
          setHistory(histRes.data);
          setLeaderboard(lbRes.data);
        });

        // Hold VS screen for 2.5 seconds before showing result
        setTimeout(() => {
            setCombatState('result');

            // Fire epic toast based on result
            if (res.data.result === 'victory') {
                toast.success(
                  <div style={{ textAlign: 'center' }}>
                    <h3 style={{ margin: '0 0 8px 0', fontSize: '1.2rem' }}>¡VICTORIA ÉPICA!</h3>
                    <p style={{ margin: 0, color: '#fbbf24', fontWeight: 'bold' }}>+{res.data.global_rating_change} ELO Global</p>
                    {res.data.coins_rewarded > 0 && <p style={{ margin: 0, color: '#10b981', fontWeight: 'bold' }}>+{res.data.coins_rewarded.toLocaleString('es-ES')} Monedas (Liga)</p>}
                  </div>,
                  { duration: 5000, style: { background: '#1e293b', border: '1px solid #fbbf24', color: 'white' } }
                );
            } else if (res.data.result === 'defeat') {
                toast.error(`Derrota... ${res.data.global_rating_change} ELO`, {
                  style: { background: '#1e293b', border: '1px solid #ef4444', color: 'white' }
                });
            } else {
                toast(`Empate reñido. Nadie pierde.`, {
                  style: { background: '#1e293b', border: '1px solid #94a3b8', color: 'white' }
                });
            }

        }, 2500);
        
      } catch (err) {
        toast.error(err.response?.data?.detail || 'Error en el combate');
        setCombatState('idle');
      }
    }, 1500);
  };

  const closeResult = async () => {
    setCombatState('idle');
    setBattleResult(null);
    await loadData();
  };

  const selectedTeamDetails = teams.find(t => t.id.toString() === selectedTeamId);

  if (loading) {
    return <div className="arena-container" style={{ textAlign: 'center', paddingTop: '100px', fontSize: '1.5rem', color: '#fbbf24', animation: 'pulseOpacity 1s infinite alternate' }}>Cargando Arena Global...</div>;
  }

  return (
    <div className="arena-container">
      <header className="arena-header">
        <h1 className="arena-title">⚔️ LA ARENA</h1>
        {status && (
          <div className="arena-stats-card">
            <div className="stat-group">
              <span className="stat-label">Rango Global</span>
              <span className="stat-value elo">{status.global_elo} ELO</span>
            </div>
            <div style={{ width: '2px', height: '40px', background: 'rgba(255,255,255,0.1)' }}></div>
            <div className="stat-group">
              <span className="stat-label">Tickets Diarios</span>
              <span className="stat-value tickets">🎟️ {status.arena_tickets} / 5</span>
            </div>
          </div>
        )}
      </header>

      <div className="arena-tabs">
        <button className={`arena-tab-btn ${activeTab === 'combat' ? 'active' : ''}`} onClick={() => setActiveTab('combat')}>⚔️ Combate</button>
        <button className={`arena-tab-btn ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>📜 Historial</button>
        <button className={`arena-tab-btn ${activeTab === 'leaderboard' ? 'active' : ''}`} onClick={() => setActiveTab('leaderboard')}>🏆 Top Global</button>
      </div>

      {activeTab === 'combat' && (
      <div>
        <h2 style={{ fontSize: '1.8rem', marginBottom: '8px' }}>Paso 1: Selecciona a tu Campeón</h2>
        <p style={{ color: '#94a3b8', fontSize: '1.1rem', marginBottom: '32px' }}>
          Juega con la plantilla de cualquiera de tus Ligas Privadas. Si ganas, esa liga recibirá un botín millonario en monedas.
        </p>

        {teams.length === 0 ? (
          <div style={{ padding: '32px', background: 'rgba(239,68,68,0.1)', border: '1px solid #ef4444', color: '#ef4444', borderRadius: '16px', textAlign: 'center', fontSize: '1.2rem' }}>
            No tienes ningún equipo todavía. Únete a una Liga Fantasy Privada para empezar a combatir en el Modo Arena.
          </div>
        ) : (
          <>
            <div className="teams-grid">
              {teams.map(t => (
                <div 
                  key={t.id} 
                  className={`team-card ${selectedTeamId === t.id.toString() ? 'selected' : ''}`}
                  onClick={() => setSelectedTeamId(t.id.toString())}
                >
                  <span className="team-card-league">🏆 {t.league_name || 'Desconocida'}</span>
                  <h3 className="team-card-name">{t.name}</h3>
                  <div className="team-card-ovr">
                    <span>Valoración (OVR)</span>
                    <span>{t.overall_rating.toFixed(0)}</span>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="combat-area">
              <button 
                className="combat-btn"
                onClick={startCombat}
                disabled={combatState !== 'idle' || status?.arena_tickets <= 0 || !selectedTeamId}
              >
                {status?.arena_tickets > 0 ? 'ENTRAR AL COMBATE (1 TICKET)' : 'SIN TICKETS (VUELVE MAÑANA)'}
              </button>
            </div>
          </>
        )}
      </div>
      )}

      {/* Battle Flow Overlays */}
      {combatState === 'searching' && (
        <div className="battle-overlay">
          <div className="radar-container">
             <div className="radar-spinner"></div>
          </div>
          <h2 className="searching-text">LOCALIZANDO RIVAL...</h2>
          <p style={{ color: '#94a3b8', fontSize: '1.5rem', marginTop: '16px' }}>
            Tu equipo <strong style={{ color: '#f8fafc' }}>{selectedTeamDetails?.name}</strong> (OVR {selectedTeamDetails?.overall_rating.toFixed(0)}) está preparándose para la colisión.
          </p>
        </div>
      )}

      {combatState === 'vs' && battleResult && (
        <div className="battle-overlay">
          <div className="vs-screen">
             <div className="vs-team">
               <h2>{battleResult.team1_name}</h2>
               <div className="ovr-badge">OVR {battleResult.team1_ovr.toFixed(0)}</div>
             </div>
             
             <div className="vs-lightning">VS</div>

             <div className="vs-team">
               <h2>{battleResult.team2_name}</h2>
               <div className="ovr-badge">OVR {battleResult.team2_ovr.toFixed(0)}</div>
             </div>
          </div>
        </div>
      )}

      {combatState === 'result' && battleResult && (
        <div className="battle-overlay">
          <div className={`battle-result-modal ${battleResult.result}`}>
            <div className="result-glow"></div>
            <div className="result-content">
                <h2 className="result-title">
                  {battleResult.result === 'victory' && '¡VICTORIA!'}
                  {battleResult.result === 'defeat' && 'DERROTA...'}
                  {battleResult.result === 'draw' && 'EMPATE'}
                </h2>
                
                <div style={{ color: '#94a3b8', fontSize: '1.5rem', textTransform: 'uppercase', letterSpacing: '2px' }}>
                  Resultado Final
                </div>

                <div className="score-display">
                  <div className="score-num">{battleResult.team1_score}</div>
                  <div className="score-divider">-</div>
                  <div className="score-num">{battleResult.team2_score}</div>
                </div>
                
                <div style={{ color: '#f8fafc', fontSize: '1.2rem', marginBottom: '24px' }}>
                  contra <span style={{ color: '#fbbf24', fontWeight: 'bold' }}>{battleResult.team2_name}</span> (OVR {battleResult.team2_ovr.toFixed(0)})
                </div>

                <div className="rewards-showcase">
                  <div className={`reward-pillar elo ${battleResult.global_rating_change >= 0 ? 'positive' : 'negative'}`}>
                    <span className="reward-label">ELO Global</span>
                    <span className="reward-value">{battleResult.global_rating_change > 0 ? '+' : ''}{battleResult.global_rating_change}</span>
                  </div>
                  
                  {battleResult.coins_rewarded > 0 && (
                    <div className="reward-pillar coins">
                      <span className="reward-label">Recompensa (A Tu Liga)</span>
                      <span className="reward-value">+{battleResult.coins_rewarded.toLocaleString('es-ES')} 🪙</span>
                    </div>
                  )}
                </div>

                <button className="close-result-btn" onClick={closeResult}>VOLVER A LA ARENA</button>
            </div>
          </div>
        </div>
      )}

      {/* Battle History */}
      {activeTab === 'history' && (
        <div className="arena-list-container">
          <h2 style={{ fontSize: '2rem', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            📜 Registro de Batallas
          </h2>
          
          {history.length > 0 ? (
            history.map(b => (
              <div key={b.id} className={`history-row ${b.result}`}>
                <div>
                  <div style={{ fontSize: '1.2rem', fontWeight: '800', marginBottom: '4px', textTransform: 'uppercase' }}>
                    {b.result === 'victory' ? 'VICTORIA' : b.result === 'defeat' ? 'DERROTA' : 'EMPATE'} 
                    <span style={{ color: '#94a3b8', fontWeight: 'normal', textTransform: 'none' }}> contra {b.opponent_name}</span>
                  </div>
                  <div style={{ color: '#64748b', fontSize: '0.9rem' }}>{new Date(b.simulated_at).toLocaleString('es-ES')}</div>
                </div>
                <div style={{ fontSize: '2rem', fontWeight: '900', color: '#f8fafc', background: 'rgba(0,0,0,0.3)', padding: '8px 20px', borderRadius: '12px' }}>
                  {b.my_score} - {b.opponent_score}
                </div>
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', color: '#94a3b8', padding: '40px', fontSize: '1.2rem' }}>
              No has librado batallas aún. Entra al combate para dejar tu huella.
            </div>
          )}
        </div>
      )}

      {/* Leaderboard */}
      {activeTab === 'leaderboard' && (
        <div className="arena-list-container">
          <h2 style={{ fontSize: '2rem', marginBottom: '24px', color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '12px' }}>
            🏆 Top 50 Global
          </h2>

          {leaderboard.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {leaderboard.map(lb => (
                <div key={lb.team_id} className="history-row" style={{ borderLeftColor: '#fbbf24', background: 'rgba(30, 41, 59, 0.8)' }}>
                  <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
                    <span style={{ fontSize: '2rem', fontWeight: '900', color: '#fbbf24', minWidth: '60px', textShadow: '0 0 10px rgba(251,191,36,0.3)' }}>#{lb.rank}</span>
                    <div>
                      <span style={{ fontWeight: '800', fontSize: '1.3rem', display: 'block', marginBottom: '4px' }}>{lb.team_name}</span>
                      <span style={{ background: '#334155', padding: '2px 8px', borderRadius: '4px', color: '#f8fafc', fontSize: '0.85rem' }}>@{lb.username}</span>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: '900', color: '#fbbf24', fontSize: '1.8rem', textShadow: '0 0 15px rgba(251,191,36,0.3)' }}>
                      {lb.arena_rating} <span style={{ fontSize: '1rem', color: '#94a3b8' }}>ELO</span>
                    </div>
                    <div style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '4px' }}>
                      <span style={{ color: '#10b981', fontWeight: 'bold' }}>{lb.arena_wins}V</span> - {lb.arena_draws}E - <span style={{ color: '#ef4444', fontWeight: 'bold' }}>{lb.arena_losses}D</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: '#94a3b8', padding: '40px', fontSize: '1.2rem' }}>
              El ranking global se está calculando.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
