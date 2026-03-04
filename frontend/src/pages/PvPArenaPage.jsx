import { useNavigate } from 'react-router-dom';
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { arenaAPI } from '../services/endpoints';
import './PvPArenaPage.css';

export default function PvPArenaPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [history, setHistory] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [lastResult, setLastResult] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('arena'); // arena, history, leaderboard

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await arenaAPI.leaderboard();
      setLeaderboard(res.data);

      const historyRes = await arenaAPI.history();
      setHistory(historyRes.data);
    } catch {
      // fail silently
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSimulate = async () => {
    if (simulating) return;
    setSimulating(true);
    setLastResult(null);
    try {
      const res = await arenaAPI.simulate();
      setLastResult(res.data);
      // Refresh data
      const [histRes, lbRes] = await Promise.all([
        arenaAPI.history(10),
        arenaAPI.leaderboard(20)
      ]);
      setHistory(histRes.data);
      setLeaderboard(lbRes.data);
    } catch (err) {
      setLastResult({ error: err.response?.data?.detail || 'Error al simular. ¿Tienes equipo creado?' });
    }
    setSimulating(false);
  };

  const getResultColor = (result) => {
    switch (result) {
      case 'victory': return '#4ade80';
      case 'defeat': return '#f87171';
      default: return '#facc15';
    }
  };

  const getResultText = (result) => {
    switch (result) {
      case 'victory': return 'VICTORIA';
      case 'defeat': return 'DERROTA';
      default: return 'EMPATE';
    }
  };

  return (
    <div className="pvp-page">
      {/* Header */}
      <header className="pvp-header">
        <button className="pvp-back-btn" onClick={() => navigate('/dashboard')}>←</button>
        <h1 className="pvp-title">⚔️ Arena PvP</h1>
      </header>

      {/* Tab Nav */}
      <div className="pvp-tabs">
        <button className={`pvp-tab ${activeTab === 'arena' ? 'active' : ''}`} onClick={() => setActiveTab('arena')}>
          ⚔️ Arena
        </button>
        <button className={`pvp-tab ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>
          📜 Historial
        </button>
        <button className={`pvp-tab ${activeTab === 'leaderboard' ? 'active' : ''}`} onClick={() => setActiveTab('leaderboard')}>
          🏆 Ranking
        </button>
      </div>

      {/* Arena Tab */}
      {activeTab === 'arena' && (
        <div className="pvp-arena-content">
          {/* Simulate Button */}
          <div className="pvp-simulate-section">
            <button
              className={`pvp-simulate-btn ${simulating ? 'simulating' : ''}`}
              onClick={handleSimulate}
              disabled={simulating}
            >
              {simulating ? (
                <span className="pvp-spinner">⚽</span>
              ) : (
                <>
                  <span className="pvp-btn-icon">⚔️</span>
                  <span>Buscar Rival</span>
                </>
              )}
            </button>
            <p className="pvp-simulate-hint">Se emparejará contra un rival de rating similar</p>
          </div>

          {/* Last Result */}
          {lastResult && !lastResult.error && (
            <div className="pvp-result-card" style={{ borderColor: getResultColor(lastResult.result) }}>
              <div className="pvp-result-header" style={{ color: getResultColor(lastResult.result) }}>
                {getResultText(lastResult.result)}
              </div>
              <div className="pvp-result-match">
                <div className="pvp-result-team">
                  <span className="pvp-result-name">{lastResult.team1_name}</span>
                  <span className="pvp-result-ovr">OVR {lastResult.team1_ovr.toFixed(1)}</span>
                </div>
                <div className="pvp-result-score">
                  <span>{lastResult.team1_score}</span>
                  <span className="pvp-vs">-</span>
                  <span>{lastResult.team2_score}</span>
                </div>
                <div className="pvp-result-team">
                  <span className="pvp-result-name">{lastResult.team2_name}</span>
                  <span className="pvp-result-ovr">OVR {lastResult.team2_ovr.toFixed(1)}</span>
                </div>
              </div>
              <div className="pvp-result-rating">
                Rating: <span style={{ color: lastResult.rating_change >= 0 ? '#4ade80' : '#f87171' }}>
                  {lastResult.rating_change >= 0 ? '+' : ''}{lastResult.rating_change}
                </span>
              </div>
            </div>
          )}

          {lastResult?.error && (
            <div className="pvp-error">{lastResult.error}</div>
          )}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="pvp-history-content">
          {history.length === 0 ? (
            <div className="pvp-empty">Aún no has jugado ningún partido</div>
          ) : (
            history.map(b => (
              <div key={b.id} className="pvp-history-row">
                <span className="pvp-history-result" style={{ color: getResultColor(b.result) }}>
                  {getResultText(b.result)}
                </span>
                <span className="pvp-history-info">
                  vs {b.opponent_name} · {b.my_score}-{b.opponent_score}
                </span>
                <span className="pvp-history-time">
                  {new Date(b.simulated_at).toLocaleDateString()}
                </span>
              </div>
            ))
          )}
        </div>
      )}

      {/* Leaderboard Tab */}
      {activeTab === 'leaderboard' && (
        <div className="pvp-leaderboard-content">
          {leaderboard.length === 0 ? (
            <div className="pvp-empty">No hay datos de ranking aún</div>
          ) : (
            leaderboard.map(entry => (
              <div key={entry.team_id} className="pvp-lb-row">
                <span className="pvp-lb-rank">#{entry.rank}</span>
                <div className="pvp-lb-info">
                  <span className="pvp-lb-name">{entry.team_name}</span>
                  <span className="pvp-lb-user">@{entry.username}</span>
                </div>
                <div className="pvp-lb-stats">
                  <span className="pvp-lb-rating">⭐ {entry.arena_rating}</span>
                  <span className="pvp-lb-record">
                    {entry.arena_wins}W {entry.arena_draws}D {entry.arena_losses}L
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Bottom Bar */}
      <div className="pvp-bottom-bar">
        <button className="pvp-bottom-btn" onClick={() => navigate('/team')}>⚽ Equipo</button>
        <button className="pvp-bottom-btn" onClick={() => navigate('/market')}>📈 Mercado</button>
        <button className="pvp-bottom-btn active">⚔️ Arena</button>
      </div>
    </div>
  );
}
