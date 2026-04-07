import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { adminAPI } from '../services/endpoints';
import { toast } from 'sonner';
import './AdminDashboard.css';

const parseCoinInput = (val) => {
    if (!val) return 0;
    let str = val.toString().trim().toUpperCase().replace(/,/g, '');
    let mult = 1;
    if (str.endsWith('K')) { mult = 1e3; str = str.slice(0, -1); }
    else if (str.endsWith('M')) { mult = 1e6; str = str.slice(0, -1); }
    else if (str.endsWith('B')) { mult = 1e9; str = str.slice(0, -1); }
    
    if (str.includes(',')) str = str.replace(/,/g, ''); // just in case
    const num = parseFloat(str);
    return isNaN(num) ? 0 : Math.floor(num * mult);
};

function QuickCoinEdit({ initialCoins, onSave }) {
    const [val, setVal] = useState(initialCoins.toString());
    const parsed = parseCoinInput(val);
    
    const handleAdd = (amount) => {
        const newVal = parsed + amount;
        if (newVal < 0) return;
        setVal(newVal.toString());
    };
    
    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
            <div style={{ display: 'flex', gap: 8 }}>
                <input
                    type="text"
                    value={val}
                    onChange={(e) => setVal(e.target.value)}
                    style={{ width: 140, padding: '8px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.05)', color: '#fff', fontSize: 15, textAlign: 'right', outline: 'none' }}
                    placeholder="Ej. 1.5M, 500K"
                />
                <button className="adm-save-btn" style={{ padding: '8px 14px' }} onClick={() => onSave(parsed)}>💾 Guardar</button>
            </div>
            
            <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end', width: '100%' }}>
                <span style={{ fontSize: 12, color: '#84cc16', marginRight: 'auto', alignSelf: 'center', fontWeight: 'bold' }}>
                    = {parsed.toLocaleString()} €
                </span>
                <button type="button" onClick={() => handleAdd(-1000000)} style={quickBtnStyle}>-1M</button>
                <button type="button" onClick={() => handleAdd(1000000)} style={quickBtnStyle}>+1M</button>
                <button type="button" onClick={() => handleAdd(10000000)} style={quickBtnStyle}>+10M</button>
            </div>
        </div>
    );
}

const quickBtnStyle = {
    background: 'rgba(255,255,255,0.1)',
    border: 'none',
    color: '#fff',
    padding: '4px 8px',
    borderRadius: 4,
    fontSize: 11,
    cursor: 'pointer',
    fontWeight: 600
};

export default function AdminDashboard() {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('stats');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    // Data
    const [stats, setStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [leagues, setLeagues] = useState([]);
    const [players, setPlayers] = useState([]);
    const [playersTotal, setPlayersTotal] = useState(0);
    const [availableTeams, setAvailableTeams] = useState([]);
    const [teams, setTeams] = useState([]);

    // Search / Filters
    const [userSearch, setUserSearch] = useState('');
    const [leagueSearch, setLeagueSearch] = useState('');
    const [playerSearch, setPlayerSearch] = useState('');
    const [teamSearch, setTeamSearch] = useState('');

    // Player Filters
    const [filterPos, setFilterPos] = useState('');
    const [filterRarity, setFilterRarity] = useState('');
    const [filterTeam, setFilterTeam] = useState('');
    const [filterLegend, setFilterLegend] = useState('');

    // Player edit modal
    const [editingPlayer, setEditingPlayer] = useState(null);
    const [editForm, setEditForm] = useState({});

    // Coin editor modal
    const [coinUser, setCoinUser] = useState(null);
    const [coinData, setCoinData] = useState(null);
    const [coinLoading, setCoinLoading] = useState(false);

    useEffect(() => {
        if (user && user.role !== 'admin') navigate('/dashboard');
    }, [user, navigate]);

    useEffect(() => {
        if (activeTab === 'stats') loadStats();
        if (activeTab === 'users') loadUsers();
        if (activeTab === 'leagues') loadLeagues();
        if (activeTab === 'players') loadPlayers();
        if (activeTab === 'teams') loadTeams();
    }, [activeTab]);

    const loadStats = async () => {
        setLoading(true);
        try { const r = await adminAPI.getStats(); setStats(r.data); } catch { setStats(null); }
        setLoading(false);
    };
    const loadUsers = async (s) => {
        setLoading(true);
        try { const r = await adminAPI.getUsers(s || userSearch || undefined); setUsers(r.data); } catch { setUsers([]); }
        setLoading(false);
    };
    const loadLeagues = async (s) => {
        setLoading(true);
        try { const r = await adminAPI.getLeagues(s || leagueSearch || undefined); setLeagues(r.data); } catch { setLeagues([]); }
        setLoading(false);
    };
    const loadTeams = async (s) => {
        setLoading(true);
        try { const r = await adminAPI.getTeams(s || teamSearch || undefined); setTeams(r.data); } catch { setTeams([]); }
        setLoading(false);
    };

    const loadPlayers = async (searchOverride) => {
        setLoading(true);
        try {
            const params = { limit: 600, offset: 0 };
            const s = searchOverride !== undefined ? searchOverride : playerSearch;
            if (s) params.search = s;
            if (filterPos) params.position = filterPos;
            if (filterRarity) params.rarity = filterRarity;
            if (filterTeam) params.team = filterTeam;
            if (filterLegend === 'true') params.is_legend = true;
            if (filterLegend === 'false') params.is_legend = false;

            const r = await adminAPI.getPlayers(params);
            setPlayers(r.data.players || []);
            setPlayersTotal(r.data.total || 0);
            if (r.data.available_teams) setAvailableTeams(r.data.available_teams);
        } catch { setPlayers([]); }
        setLoading(false);
    };

    // Re-load when filters change
    useEffect(() => {
        if (activeTab === 'players') loadPlayers();
    }, [filterPos, filterRarity, filterTeam, filterLegend]);

    const handleDeleteUser = async (id, name) => {
        toast.error(`¿Eliminar @${name}?`, {
            cancel: { label: 'Cancelar' },
            action: {
                label: 'Eliminar',
                onClick: async () => {
                    try { const r = await adminAPI.deleteUser(id); setMessage(`✅ ${r.data.message}`); loadUsers(); }
                    catch (e) { setMessage(`❌ ${e.response?.data?.detail || 'Error'}`); }
                    setTimeout(() => setMessage(''), 4000);
                }
            }
        });
    };
    const handleDeleteLeague = async (id, name) => {
        toast.error(`¿Eliminar liga "${name}"?`, {
            cancel: { label: 'Cancelar' },
            action: {
                label: 'Eliminar',
                onClick: async () => {
                    try { const r = await adminAPI.deleteLeague(id); setMessage(`✅ ${r.data.message}`); loadLeagues(); }
                    catch (e) { setMessage(`❌ ${e.response?.data?.detail || 'Error'}`); }
                    setTimeout(() => setMessage(''), 4000);
                }
            }
        });
    };

    const openEditPlayer = (p) => {
        setEditingPlayer(p);
        setEditForm({
            name: p.name || '', age: p.age || 0, nationality: p.nationality || '',
            position: p.position || 'FWD', overall_rating: p.overall_rating || 50,
            potential: p.potential || 50, pace: p.pace || 50, shooting: p.shooting || 50,
            passing: p.passing || 50, dribbling: p.dribbling || 50,
            defending: p.defending || 50, physical: p.physical || 50,
            base_rarity: p.base_rarity || 'bronze', image_url: p.image_url || '',
            current_price: p.current_price || 0, current_team: p.team_name || '',
            is_legend: p.is_legend || false,
        });
    };

    const handleSavePlayer = async () => {
        if (!editingPlayer) return;
        try {
            const r = await adminAPI.updatePlayer(editingPlayer.id, editForm);
            setMessage(`✅ ${r.data.message}`);
            setEditingPlayer(null);
            loadPlayers();
        } catch (e) { setMessage(`❌ ${e.response?.data?.detail || 'Error'}`); }
        setTimeout(() => setMessage(''), 4000);
    };

    // ── Coin management ──
    const openCoinEditor = async (u) => {
        setCoinUser(u);
        setCoinLoading(true);
        try {
            const r = await adminAPI.getUserLeagueCoins(u.id);
            setCoinData(r.data);
        } catch { setCoinData(null); }
        setCoinLoading(false);
    };

    const handleSaveCoins = async (leagueId, newCoins) => {
        if (!coinUser) return;
        try {
            await adminAPI.updateUserLeagueCoins(coinUser.id, { league_id: leagueId, coins: newCoins });
            setMessage(`✅ Monedas actualizadas para @${coinUser.username}`);
            // Refresh
            const r = await adminAPI.getUserLeagueCoins(coinUser.id);
            setCoinData(r.data);
            loadUsers();
        } catch (e) { setMessage(`❌ ${e.response?.data?.detail || 'Error'}`); }
        setTimeout(() => setMessage(''), 4000);
    };

    const fmt = (p) => {
        if (p >= 1e9) return (p / 1e9).toFixed(1) + 'B';
        if (p >= 1e6) return (p / 1e6).toFixed(1) + 'M';
        if (p >= 1e3) return (p / 1e3).toFixed(0) + 'K';
        return p?.toLocaleString() || '0';
    };

    const tabs = [
        { key: 'stats', label: '📊 Resumen' }, { key: 'users', label: '👥 Usuarios' },
        { key: 'leagues', label: '🏆 Ligas' }, { key: 'players', label: '⚽ Jugadores' },
        { key: 'teams', label: '👕 Equipos' },
    ];

    const statLabels = {
        overall_rating: 'OVR', potential: 'POT', pace: 'PAC',
        shooting: 'SHO', passing: 'PAS', dribbling: 'DRI',
        defending: 'DEF', physical: 'PHY',
    };

    const getStatColor = (val) => {
        if (val >= 85) return '#22c55e';
        if (val >= 70) return '#84cc16';
        if (val >= 55) return '#fbbf24';
        if (val >= 40) return '#f97316';
        return '#ef4444';
    };

    return (
        <div className="adm">
            <header className="adm-header">
                <button className="adm-back" onClick={() => navigate('/dashboard')}>←</button>
                <div className="adm-header-center">
                    <span className="adm-header-badge">ADMIN</span>
                    <h1>Panel de Administración</h1>
                </div>
                <div style={{ width: 40 }} />
            </header>

            {message && <div className={`adm-message ${message.startsWith('✅') ? 'success' : 'error'}`}>{message}</div>}

            <div className="adm-tabs">
                {tabs.map(t => (
                    <button key={t.key} className={`adm-tab ${activeTab === t.key ? 'active' : ''}`} onClick={() => setActiveTab(t.key)}>{t.label}</button>
                ))}
            </div>

            <div className="adm-content">
                {loading && <div className="adm-loading"><div className="adm-spinner" />Cargando...</div>}

                {/* STATS */}
                {activeTab === 'stats' && stats && !loading && (
                    <div className="adm-stats-grid">
                        {[
                            { icon: '👥', val: stats.total_users, lbl: 'Usuarios' },
                            { icon: '🏆', val: stats.total_leagues, lbl: 'Ligas' },
                            { icon: '⚽', val: stats.total_players, lbl: 'Jugadores' },
                            { icon: '👕', val: stats.total_teams, lbl: 'Equipos' }
                        ].map((s, i) => (
                            <div key={i} className="adm-stat-card">
                                <span className="adm-stat-icon">{s.icon}</span>
                                <div className="adm-stat-value">{s.val}</div>
                                <div className="adm-stat-label">{s.lbl}</div>
                            </div>
                        ))}
                    </div>
                )}

                {/* USERS */}
                {activeTab === 'users' && !loading && (
                    <div className="adm-table-section">
                        <div className="adm-search-bar">
                            <input type="text" placeholder="Buscar por username o email..." value={userSearch}
                                onChange={e => setUserSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && loadUsers(userSearch)}
                                className="adm-search-input" />
                            <button className="adm-search-btn" onClick={() => loadUsers(userSearch)}>Buscar</button>
                        </div>
                        <div className="adm-table-wrap">
                            <table className="adm-table">
                                <thead><tr><th>ID</th><th>Username</th><th>Email</th><th>Rol</th><th>Ligas</th><th>Creado</th><th></th></tr></thead>
                                <tbody>
                                    {users.map(u => (
                                        <tr key={u.id} className={u.role === 'admin' ? 'admin-row' : ''}>
                                            <td>{u.id}</td>
                                            <td className="adm-user-cell"><strong>@{u.username}</strong></td>
                                            <td>{u.email}</td>
                                            <td><span className={`adm-role-badge role-${u.role}`}>{u.role}</span></td>
                                            <td>{u.league_count > 0 ? <span className="adm-league-count">{u.league_count}</span> : '0'}</td>
                                            <td className="adm-date">{u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}</td>
                                            <td style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                                                <button className="adm-edit-btn" title="Editar monedas" onClick={() => openCoinEditor(u)}>🪙</button>
                                                {u.role !== 'admin' ? <button className="adm-delete-btn" onClick={() => handleDeleteUser(u.id, u.username)}>🗑️</button> : <span className="adm-protected">🛡️</span>}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {users.length === 0 && <div className="adm-empty">No se encontraron usuarios</div>}
                        </div>
                    </div>
                )}

                {/* LEAGUES */}
                {activeTab === 'leagues' && !loading && (
                    <div className="adm-table-section">
                        <div className="adm-search-bar">
                            <input type="text" placeholder="Buscar liga..." value={leagueSearch}
                                onChange={e => setLeagueSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && loadLeagues(leagueSearch)}
                                className="adm-search-input" />
                            <button className="adm-search-btn" onClick={() => loadLeagues(leagueSearch)}>Buscar</button>
                        </div>
                        <div className="adm-table-wrap">
                            <table className="adm-table">
                                <thead><tr><th>ID</th><th>Nombre</th><th>Propietario</th><th>Miembros</th><th>Código</th><th>Creada</th><th></th></tr></thead>
                                <tbody>
                                    {leagues.map(lg => (
                                        <tr key={lg.id}>
                                            <td>{lg.id}</td><td><strong>{lg.name}</strong></td><td>@{lg.owner_username}</td>
                                            <td>{lg.member_count}/{lg.max_members}</td><td className="adm-code">{lg.invite_code}</td>
                                            <td className="adm-date">{lg.created_at ? new Date(lg.created_at).toLocaleDateString() : '-'}</td>
                                            <td><button className="adm-delete-btn" onClick={() => handleDeleteLeague(lg.id, lg.name)}>🗑️</button></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {leagues.length === 0 && <div className="adm-empty">No se encontraron ligas</div>}
                        </div>
                    </div>
                )}

                {/* PLAYERS */}
                {activeTab === 'players' && !loading && (
                    <div className="adm-table-section">
                        {/* Search + Filters */}
                        <div className="adm-search-bar">
                            <input type="text" placeholder="Buscar jugador..." value={playerSearch}
                                onChange={e => setPlayerSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && loadPlayers(playerSearch)}
                                className="adm-search-input" />
                            <button className="adm-search-btn" onClick={() => loadPlayers(playerSearch)}>Buscar</button>
                            <span className="adm-count-badge">{playersTotal} jugadores</span>
                        </div>
                        <div className="adm-filters-bar">
                            <select value={filterPos} onChange={e => setFilterPos(e.target.value)} className="adm-filter-select">
                                <option value="">Todas posiciones</option>
                                <option value="GK">🧤 Portero (GK)</option>
                                <option value="DEF">🛡️ Defensa (DEF)</option>
                                <option value="MID">🎯 Medio (MID)</option>
                                <option value="FWD">⚡ Delantero (FWD)</option>
                            </select>
                            <select value={filterRarity} onChange={e => setFilterRarity(e.target.value)} className="adm-filter-select">
                                <option value="">Todas rarezas</option>
                                <option value="bronze">🟤 Bronce</option>
                                <option value="silver">⚪ Plata</option>
                                <option value="gold">🟡 Oro</option>
                                <option value="legend">🟣 Leyenda</option>
                            </select>
                            <select value={filterTeam} onChange={e => setFilterTeam(e.target.value)} className="adm-filter-select">
                                <option value="">Todos equipos</option>
                                {availableTeams.map(t => <option key={t} value={t}>{t}</option>)}
                            </select>
                            <select value={filterLegend} onChange={e => setFilterLegend(e.target.value)} className="adm-filter-select">
                                <option value="">Todos</option>
                                <option value="true">⭐ Solo leyendas</option>
                                <option value="false">Solo actuales</option>
                            </select>
                            {(filterPos || filterRarity || filterTeam || filterLegend) && (
                                <button className="adm-clear-filters" onClick={() => { setFilterPos(''); setFilterRarity(''); setFilterTeam(''); setFilterLegend(''); }}>
                                    ✕ Limpiar
                                </button>
                            )}
                        </div>

                        <div className="adm-table-wrap">
                            <table className="adm-table">
                                <thead>
                                    <tr><th></th><th>Nombre</th><th>Pos</th><th>OVR</th><th>Rareza</th><th>Equipo</th><th>Precio</th><th>Cartas</th><th></th></tr>
                                </thead>
                                <tbody>
                                    {players.map(p => (
                                        <tr key={p.id}>
                                            <td><img src={p.image_url || '/images/placeholder.png'} alt="" className="adm-player-thumb" onError={e => { e.target.src = '/images/placeholder.png'; }} /></td>
                                            <td><strong>{p.name}</strong>{p.is_legend && <span className="adm-legend-star"> ⭐</span>}</td>
                                            <td><span className={`adm-pos-badge pos-${p.position}`}>{p.position}</span></td>
                                            <td><span className="adm-ovr">{p.overall_rating}</span></td>
                                            <td><span className={`adm-rarity-badge rarity-${p.base_rarity}`}>{p.base_rarity}</span></td>
                                            <td>{p.team_name || '-'}</td>
                                            <td>{fmt(p.current_price)}</td>
                                            <td>{p.cards_in_circulation}</td>
                                            <td><button className="adm-edit-btn" onClick={() => openEditPlayer(p)}>✏️</button></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {players.length === 0 && <div className="adm-empty">No se encontraron jugadores con estos filtros</div>}
                        </div>
                    </div>
                )}

                {/* TEAMS */}
                {activeTab === 'teams' && !loading && (
                    <div className="adm-table-section">
                        <div className="adm-search-bar">
                            <input type="text" placeholder="Buscar equipo..." value={teamSearch}
                                onChange={e => setTeamSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && loadTeams(teamSearch)}
                                className="adm-search-input" />
                            <button className="adm-search-btn" onClick={() => loadTeams(teamSearch)}>Buscar</button>
                        </div>
                        <div className="adm-table-wrap">
                            <table className="adm-table">
                                <thead><tr><th>ID</th><th>Nombre</th><th>Dueño</th><th>Liga</th><th>OVR</th><th>Formación</th><th>Jugadores</th><th>Arena</th><th>ELO</th></tr></thead>
                                <tbody>
                                    {teams.map(t => (
                                        <tr key={t.id}>
                                            <td>{t.id}</td><td><strong>{t.name}</strong></td><td className="adm-user-cell">@{t.owner_username}</td>
                                            <td>{t.league_name}</td><td><span className="adm-ovr">{t.overall_rating}</span></td>
                                            <td className="adm-code">{t.formation}</td><td>{t.player_count}</td>
                                            <td>{t.arena_record}</td><td><strong>{t.arena_rating}</strong></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {teams.length === 0 && <div className="adm-empty">No se encontraron equipos</div>}
                        </div>
                    </div>
                )}
            </div>

            {/* ====== PLAYER EDIT MODAL ====== */}
            {editingPlayer && (
                <div className="adm-modal-overlay" onClick={() => setEditingPlayer(null)}>
                    <div className="adm-modal adm-modal-lg" onClick={e => e.stopPropagation()}>
                        <div className="adm-modal-header">
                            <div className="adm-modal-title-row">
                                <h2>Editar Jugador</h2>
                                <span className={`adm-rarity-badge rarity-${editForm.base_rarity}`}>{editForm.base_rarity}</span>
                            </div>
                            <button className="adm-modal-close" onClick={() => setEditingPlayer(null)}>✕</button>
                        </div>

                        <div className="adm-modal-body">
                            {/* Top section: Image + core info */}
                            <div className="adm-edit-top">
                                <div className="adm-edit-img-section">
                                    <div className="adm-edit-img-wrap">
                                        <img
                                            src={editForm.image_url || '/images/placeholder.png'}
                                            alt={editForm.name}
                                            onError={e => { e.target.src = '/images/placeholder.png'; }}
                                        />
                                        <div className="adm-edit-ovr-badge" style={{ color: getStatColor(editForm.overall_rating) }}>
                                            {editForm.overall_rating}
                                        </div>
                                    </div>
                                    <div className="adm-edit-player-name">{editForm.name}</div>
                                    <div className="adm-edit-player-meta">
                                        {editForm.position} · {editForm.current_team || 'Sin equipo'}
                                        {editForm.is_legend && <span> · ⭐ Leyenda</span>}
                                    </div>
                                </div>

                                {/* Hexagonal stat radar visual */}
                                <div className="adm-edit-stats-visual">
                                    {Object.entries(statLabels).filter(([k]) => k !== 'overall_rating' && k !== 'potential').map(([key, label]) => (
                                        <div key={key} className="adm-stat-bar-row">
                                            <span className="adm-stat-bar-label">{label}</span>
                                            <div className="adm-stat-bar-track">
                                                <div className="adm-stat-bar-fill" style={{ width: `${editForm[key]}%`, background: getStatColor(editForm[key]) }} />
                                            </div>
                                            <span className="adm-stat-bar-value" style={{ color: getStatColor(editForm[key]) }}>{editForm[key]}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Info Fields */}
                            <div className="adm-edit-section">
                                <h3>📋 Información</h3>
                                <div className="adm-edit-grid">
                                    <label><span>Nombre</span><input type="text" value={editForm.name} onChange={e => setEditForm({ ...editForm, name: e.target.value })} /></label>
                                    <label><span>Edad</span><input type="number" value={editForm.age} onChange={e => setEditForm({ ...editForm, age: parseInt(e.target.value) || 0 })} /></label>
                                    <label><span>Nacionalidad</span><input type="text" value={editForm.nationality} onChange={e => setEditForm({ ...editForm, nationality: e.target.value })} /></label>
                                    <label><span>Equipo</span><input type="text" value={editForm.current_team} onChange={e => setEditForm({ ...editForm, current_team: e.target.value })} /></label>
                                    <label><span>Posición</span>
                                        <select value={editForm.position} onChange={e => setEditForm({ ...editForm, position: e.target.value })}>
                                            <option value="GK">GK</option><option value="DEF">DEF</option><option value="MID">MID</option><option value="FWD">FWD</option>
                                        </select>
                                    </label>
                                    <label><span>Rareza</span>
                                        <select value={editForm.base_rarity} onChange={e => setEditForm({ ...editForm, base_rarity: e.target.value })}>
                                            <option value="bronze">Bronce</option><option value="silver">Plata</option><option value="gold">Oro</option><option value="legend">Leyenda</option>
                                        </select>
                                    </label>
                                    <label><span>Leyenda</span>
                                        <select value={editForm.is_legend ? 'true' : 'false'} onChange={e => setEditForm({ ...editForm, is_legend: e.target.value === 'true' })}>
                                            <option value="false">No</option><option value="true">Sí</option>
                                        </select>
                                    </label>
                                    <label><span>Precio (€)</span><input type="number" value={editForm.current_price} onChange={e => setEditForm({ ...editForm, current_price: parseFloat(e.target.value) || 0 })} /></label>
                                    <label className="full-width"><span>URL de Imagen</span><input type="text" value={editForm.image_url} onChange={e => setEditForm({ ...editForm, image_url: e.target.value })} /></label>
                                </div>
                            </div>

                            {/* Stats sliders */}
                            <div className="adm-edit-section">
                                <h3>📊 Estadísticas</h3>
                                <div className="adm-edit-grid stats-grid">
                                    {Object.entries(statLabels).map(([key, label]) => (
                                        <label key={key}>
                                            <span>{label}</span>
                                            <div className="adm-stat-input-wrap">
                                                <input type="range" min="1" max="99" value={editForm[key] || 50}
                                                    onChange={e => setEditForm({ ...editForm, [key]: parseInt(e.target.value) })}
                                                    style={{ accentColor: getStatColor(editForm[key] || 50) }} />
                                                <span className="adm-stat-display" style={{ color: getStatColor(editForm[key] || 50) }}>{editForm[key]}</span>
                                            </div>
                                        </label>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="adm-modal-footer">
                            <button className="adm-cancel-btn" onClick={() => setEditingPlayer(null)}>Cancelar</button>
                            <button className="adm-save-btn" onClick={handleSavePlayer}>💾 Guardar Cambios</button>
                        </div>
                    </div>
                </div>
            )}

            {/* ====== COIN EDITOR MODAL ====== */}
            {coinUser && (
                <div className="adm-modal-overlay" onClick={() => { setCoinUser(null); setCoinData(null); }}>
                    <div className="adm-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 520 }}>
                        <div className="adm-modal-header">
                            <h2>🪙 Monedas de @{coinUser.username}</h2>
                            <button className="adm-modal-close" onClick={() => { setCoinUser(null); setCoinData(null); }}>✕</button>
                        </div>
                        <div className="adm-modal-body">
                            {coinLoading && <div className="adm-loading"><div className="adm-spinner" />Cargando...</div>}
                            {coinData && !coinLoading && (
                                <>
                                    {/* Per-league coins */}
                                    <div className="adm-edit-section">
                                        <h3>🏆 Monedas por Liga</h3>
                                        {coinData.leagues.length === 0 && <p style={{ color: 'rgba(255,255,255,0.5)', padding: '12px 0' }}>Este usuario no pertenece a ninguna liga.</p>}
                                        {coinData.leagues.map(lg => (
                                            <div key={lg.league_id} style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 10, padding: '10px 12px', borderRadius: 10, background: 'rgba(255,255,255,0.04)' }}>
                                                <div style={{ flex: 1 }}>
                                                    <div style={{ fontWeight: 600, color: '#fff' }}>{lg.league_name}</div>
                                                    <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)' }}>Puntos: {lg.league_points}</div>
                                                </div>
                                                <QuickCoinEdit 
                                                    initialCoins={lg.coins} 
                                                    onSave={(newCoins) => handleSaveCoins(lg.league_id, newCoins)} 
                                                />
                                            </div>
                                        ))}
                                    </div>
                                </>
                            )}
                        </div>
                        <div className="adm-modal-footer">
                            <button className="adm-cancel-btn" onClick={() => { setCoinUser(null); setCoinData(null); }}>Cerrar</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
