import { useState, useEffect } from 'react';
import { playersAPI } from '../services/endpoints';
import './PlayerDetailModal.css';

export default function PlayerDetailModal({ playerId, playerObj, onClose, isReadOnly, onClausulazo, onBlindar }) {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!playerId) return;
        const fetchHistory = async () => {
            setLoading(true);
            try {
                const res = await playersAPI.getHistory(playerId);
                setHistory(res.data);
            } catch { setError('Error al cargar historial'); }
            finally { setLoading(false); }
        };
        fetchHistory();
    }, [playerId]);

    if (!playerId) return null;

    const name = playerObj?.name || playerObj?.player_name || '???';
    const ovr = playerObj?.current_overall || playerObj?.overall_rating || 0;
    const pos = playerObj?.position || '??';
    const rarity = playerObj?.base_rarity || 'bronze';
    const img = playerObj?.image_url;
    const value = playerObj?.current_market_value || playerObj?.current_price || 0;
    const team = playerObj?.current_team || 'Equipo Desconocido';

    // Use real stats from backend, fallback to seeded OVR-based estimate
    const getStat = (base, variation, seedOffset) => {
        const seed = parseInt(playerId) || 123;
        let x = Math.sin(seed + seedOffset) * 10000;
        const randomFraction = x - Math.floor(x);
        return Math.min(99, Math.max(1, base + Math.floor(randomFraction * variation)));
    };

    let stats = [];

    if (pos === 'GK') {
        stats = [
            { label: 'DIV', value: playerObj?.diving || getStat(ovr - 2, 8, 1) },
            { label: 'HAN', value: playerObj?.handling || getStat(ovr - 5, 8, 2) },
            { label: 'KIC', value: playerObj?.kicking || getStat(ovr - 8, 15, 3) },
            { label: 'REF', value: playerObj?.reflexes || getStat(ovr, 8, 4) },
            { label: 'SPD', value: playerObj?.speed || getStat(35, 15, 5) },
            { label: 'POS', value: playerObj?.positioning || getStat(ovr - 3, 8, 6) }
        ];
    } else {
        stats = [
            { label: 'PAC', value: playerObj?.pace || getStat(ovr - 5, 10, 1) },
            { label: 'SHO', value: playerObj?.shooting || getStat(ovr - 8, 10, 2) },
            { label: 'PAS', value: playerObj?.passing || getStat(ovr - 6, 10, 3) },
            { label: 'DRI', value: playerObj?.dribbling || getStat(ovr - 5, 10, 4) },
            { label: 'DEF', value: playerObj?.defending || (pos === 'DEF' ? getStat(ovr - 3, 8, 5) : getStat(25, 20, 5)) },
            { label: 'PHY', value: playerObj?.physical || getStat(ovr - 7, 10, 6) },
        ];
    }

    const formatValue = (v) => {
        if (v >= 1000000000) return (v / 1000000000).toFixed(1) + 'B';
        if (v >= 1000000) return (v / 1000000).toFixed(1) + 'M';
        if (v >= 1000) return (v / 1000).toFixed(0) + 'K';
        return v?.toLocaleString() || '0';
    };

    // Premium gradients for card backgrounds
    const rarityGradient = {
        bronze: 'linear-gradient(135deg, #d48b6c 0%, #9a5b3a 45%, #5c3018 100%)',
        silver: 'linear-gradient(135deg, #ffffff 0%, #cbd5e1 45%, #64748b 100%)',
        gold: 'linear-gradient(135deg, #fef08a 0%, #eab308 45%, #854d0e 100%)',
        legend: 'linear-gradient(135deg, #f3e8ff 0%, #c084fc 45%, #4c1d95 100%)',
    };

    const accentColor = {
        bronze: '#fed7aa',
        silver: '#f8fafc',
        gold: '#fef9c3',
        legend: '#e9d5ff',
    };

    const accent = accentColor[rarity] || '#cd7f32';

    return (
        <div className="pdm-overlay" onClick={onClose}>
            <div className="pdm-modal" onClick={e => e.stopPropagation()}>

                {/* Close button */}
                <button className="pdm-close" onClick={onClose}>✕</button>

                {/* Card section */}
                <div className="pdm-card-section">
                    <div className="pdm-card" style={{ background: rarityGradient[rarity] || rarityGradient.bronze }}>
                        {/* Shimmer overlay */}
                        <div className="pdm-card-shimmer" />

                        {/* OVR + Position */}
                        <div className="pdm-card-meta">
                            <span className="pdm-card-ovr">{ovr}</span>
                            <span className="pdm-card-pos" style={{ color: accent }}>{pos}</span>
                        </div>

                        {/* Player image */}
                        <div className="pdm-card-img-wrap">
                            <img
                                src={img || '/images/placeholder.png'}
                                alt={name}
                                className="pdm-card-img"
                                onError={(e) => { e.target.src = '/images/placeholder.png'; }}
                            />
                        </div>

                        {/* Name at bottom */}
                        <div className="pdm-card-name">{name}</div>
                    </div>
                </div>

                {/* Info bar */}
                <div className="pdm-info-bar">
                    <div className="pdm-info-item">
                        <span className="pdm-info-label">Equipo</span>
                        <span className="pdm-info-value">🛡️ {team}</span>
                    </div>
                    <div className="pdm-info-divider" />
                    <div className="pdm-info-item">
                        <span className="pdm-info-label">Valor</span>
                        <span className="pdm-info-value" style={{ color: '#fbbf24' }}>💰 {formatValue(value)}</span>
                    </div>
                </div>

                {/* Stats */}
                <div className="pdm-stats">
                    <h3 className="pdm-stats-title">Atributos</h3>
                    <div className="pdm-stats-grid">
                        {stats.map(s => (
                            <div key={s.label} className="pdm-stat-row">
                                <span className="pdm-stat-label">{s.label}</span>
                                <div className="pdm-stat-bar-bg">
                                    <div
                                        className="pdm-stat-bar-fill"
                                        style={{
                                            width: `${s.value}%`,
                                            background: s.value >= 85 ? '#059669' // dark green
                                                : s.value >= 70 ? '#10b981' // green
                                                    : s.value >= 50 ? '#fbbf24' // yellow
                                                        : '#ef4444' // red
                                        }}
                                    />
                                </div>
                                <span className="pdm-stat-value" style={{ color: s.value >= 70 ? '#fff' : '#94a3b8' }}>{s.value}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* History */}
                <div className="pdm-history">
                    <h3 className="pdm-stats-title">Historial de Partidos</h3>
                    {loading ? (
                        <div className="pdm-empty">Cargando estadísticas...</div>
                    ) : error ? (
                        <div className="pdm-empty" style={{ color: '#fca5a5' }}>{error}</div>
                    ) : history.length === 0 ? (
                        <div className="pdm-empty">Sin datos de partidos esta temporada</div>
                    ) : (
                        <div className="pdm-table-wrap">
                            <table className="pdm-table">
                                <thead>
                                    <tr>
                                        <th>JOR</th>
                                        <th>Partido</th>
                                        <th>Resultado</th>
                                        <th>Minutos</th>
                                        <th>G/A</th>
                                        <th>Pts</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {history.map((h, idx) => {
                                        const isHome = team === h.home_team;
                                        const resultText = h.status === 'FINISHED'
                                            ? `${h.home_score}-${h.away_score}`
                                            : 'vs';
                                        return (
                                            <tr key={idx}>
                                                <td>{h.gameweek_number > 0 ? h.gameweek_number : '-'}</td>
                                                <td className="pdm-match-name">
                                                    <span className={isHome ? 'pdm-match-home' : 'pdm-match-away'}>{h.home_team}</span>
                                                    <span className="pdm-match-vs">vs</span>
                                                    <span className={!isHome ? 'pdm-match-home' : 'pdm-match-away'}>{h.away_team}</span>
                                                </td>
                                                <td style={{ fontWeight: 700 }}>{resultText}</td>
                                                <td>{h.minutes_played}'</td>
                                                <td>{h.goals}/{h.assists}</td>
                                                <td className="pdm-fp">{h.fantasy_points}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* Actions Row */}
                {(onClausulazo || onBlindar) && playerObj?.id && (
                    <div className="pdm-actions-bar" style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                        {isReadOnly && onClausulazo && (
                            <button
                                onClick={() => onClausulazo(playerObj)}
                                style={{ flex: 1, padding: '12px', borderRadius: '8px', background: 'linear-gradient(135deg, #f59e0b, #d97706)', color: 'white', fontWeight: 'bold', border: 'none', cursor: 'pointer' }}
                            >
                                💎 Pagar Cláusula ({formatValue(value)})
                            </button>
                        )}
                        {!isReadOnly && onBlindar && (
                            <button
                                onClick={() => onBlindar(playerObj)}
                                style={{ flex: 1, padding: '12px', borderRadius: '8px', background: 'linear-gradient(135deg, #3b82f6, #2563eb)', color: 'white', fontWeight: 'bold', border: 'none', cursor: 'pointer' }}
                            >
                                🛡️ Blindar Jugador
                            </button>
                        )}
                    </div>
                )}

            </div>
        </div>
    );
}
