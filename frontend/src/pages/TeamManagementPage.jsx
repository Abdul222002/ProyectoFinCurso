import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { teamsAPI, leaguesAPI, auctionAPI } from '../services/endpoints';
import TeamCustomizerModal from '../components/TeamCustomizerModal';
import PlayerDetailModal from '../components/PlayerDetailModal';
import FormationPitch, { getFormationSlots } from '../components/FormationPitch';
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
  const [showCustomizer, setShowCustomizer] = useState(false);
  const [gameweek, setGameweek] = useState(null);
  const [gwLineup, setGwLineup] = useState(null);
  const [selectedPlayerForDetail, setSelectedPlayerForDetail] = useState(null);

  // ── Player picker state ──
  const [pickerPos, setPickerPos] = useState(null);

  // ── Sell modal state ──
  const [sellCard, setSellCard] = useState(null);
  const [sellPrice, setSellPrice] = useState('');
  const [selling, setSelling] = useState(false);

  // ── Listed cards tracking ──
  const [listedCardIds, setListedCardIds] = useState(new Set());

  const FORMATIONS = ['4-4-2', '4-3-3', '3-5-2', '4-2-3-1', '3-4-3', '5-3-2', '5-4-1'];

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      if (leagueIdParam) {
        const res = await teamsAPI.getMy(leagueIdParam);
        setSelectedTeam(res.data);
        setTeams([res.data]);
      } else {
        const res = await teamsAPI.getMy();
        const allTeams = Array.isArray(res.data) ? res.data : [res.data];
        setTeams(allTeams);
        if (allTeams.length > 0) setSelectedTeam(allTeams[0]);
      }
    } catch {
      setTeams([]);
      setSelectedTeam(null);
    }
    try {
      const gwRes = await teamsAPI.getActiveGameweek();
      setGameweek(gwRes.data);
    } catch {
      setGameweek(null);
    }
    setLoading(false);
  }, [leagueIdParam]);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    if (selectedTeam && gameweek) {
      (async () => {
        try {
          const res = await teamsAPI.getGameweekLineup(selectedTeam.league_id, gameweek.id);
          setGwLineup(res.data);
        } catch { setGwLineup(null); }
      })();
    }
  }, [selectedTeam, gameweek]);

  // Load listed cards
  useEffect(() => {
    if (!selectedTeam) return;
    const loadListings = async () => {
      try {
        const res = await auctionAPI.getListings(selectedTeam.league_id);
        const myListings = (Array.isArray(res.data) ? res.data : []).filter(l => l.is_mine);
        setListedCardIds(new Set(myListings.map(l => l.card_id)));
      } catch { setListedCardIds(new Set()); }
    };
    loadListings();
  }, [selectedTeam]);

  // ── Add player to lineup ──
  const handleAddToLineup = async (cardId) => {
    if (!selectedTeam || !selectedTeam.players) return;
    const currentLineup = selectedTeam.players.filter(p => p.is_in_lineup);
    if (currentLineup.length >= 11) {
      setError('Ya tienes 11 titulares. Quita uno primero.');
      setTimeout(() => setError(''), 3000);
      return;
    }
    const currentIds = currentLineup.map(p => p.id);
    try {
      const res = await teamsAPI.setLineup(selectedTeam.league_id, [...currentIds, cardId]);
      setSelectedTeam(res.data);
      setTeams(prev => prev.map(t => t.id === res.data.id ? res.data : t));
      setError('');
      setPickerPos(null);
      if (gameweek && new Date() < new Date(gameweek.start_date)) setGwLineup(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al actualizar alineación');
      setTimeout(() => setError(''), 3000);
    }
  };

  // ── Remove player from lineup (crash-safe) ──
  const handleRemoveFromLineup = async (cardId) => {
    if (!selectedTeam || !selectedTeam.players) return;
    const newIds = selectedTeam.players
      .filter(p => p.is_in_lineup && p.id !== cardId)
      .map(p => p.id);
    try {
      const res = await teamsAPI.setLineup(selectedTeam.league_id, newIds);
      if (res && res.data) {
        setSelectedTeam(res.data);
        setTeams(prev => prev.map(t => t.id === res.data.id ? res.data : t));
      }
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al quitar jugador');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleFormationChange = async (formation) => {
    if (!selectedTeam) return;
    try {
      await teamsAPI.update(selectedTeam.league_id, { formation });
      const res = await teamsAPI.setLineup(selectedTeam.league_id, []);
      setSelectedTeam(res.data);
      setTeams(prev => prev.map(t => t.id === res.data.id ? res.data : t));
      setSuccess(`Formación cambiada a ${formation}. Monta tu nuevo 11.`);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cambiar formación');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleCancelListing = async (cardId) => {
    if (!selectedTeam) return;
    try {
      const res = await auctionAPI.getListings(selectedTeam.league_id);
      const listing = (Array.isArray(res.data) ? res.data : []).find(l => l.is_mine && l.card_id === cardId);
      if (!listing) { setError('Listado no encontrado'); return; }
      await auctionAPI.cancelListing(selectedTeam.league_id, listing.id);
      setSuccess('✅ Jugador retirado del mercado');
      setListedCardIds(prev => { const n = new Set(prev); n.delete(cardId); return n; });
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error');
      setTimeout(() => setError(''), 3000);
    }
  };

  // ── Loading state ──
  if (loading) {
    return <div className="team-page"><div className="team-loading">⚽ Cargando equipos...</div></div>;
  }

  // ── No teams ──
  if (teams.length === 0) {
    return (
      <div className="team-page">
        <header className="team-header">
          <button className="team-back-btn" onClick={() => navigate(leagueIdParam ? `/leagues/${leagueIdParam}` : '/dashboard')}>← Volver</button>
          <h1 className="team-title">Mi Equipo</h1>
        </header>
        <div className="team-empty">
          <span className="team-empty-icon">🏆</span>
          <h2>No tienes equipos aún</h2>
          <p>Únete a una liga para crear tu equipo automáticamente con 15 jugadores aleatorios.</p>
          <button className="team-create-btn" onClick={() => navigate('/leagues')}>Ir a Ligas →</button>
        </div>
      </div>
    );
  }

  const lineup = selectedTeam?.players?.filter(p => p.is_in_lineup) || [];
  const bench = selectedTeam?.players?.filter(p => !p.is_in_lineup) || [];
  const pickerPlayers = pickerPos ? bench.filter(p => p.position === pickerPos) : [];
  const POS_LABELS = { GK: 'Portero', DEF: 'Defensa', MID: 'Centrocampista', FWD: 'Delantero' };

  return (
    <div className="team-page">
      {/* ── Modals ── */}
      {showCustomizer && selectedTeam && (
        <TeamCustomizerModal
          team={selectedTeam}
          leagueId={selectedTeam.league_id}
          onClose={() => setShowCustomizer(false)}
          onSaved={() => { loadData(); setSuccess('✅ Equipo actualizado'); setTimeout(() => setSuccess(''), 3000); }}
        />
      )}
      {selectedPlayerForDetail && (
        <PlayerDetailModal
          playerId={selectedPlayerForDetail.player_id}
          playerObj={selectedPlayerForDetail}
          onClose={() => setSelectedPlayerForDetail(null)}
        />
      )}

      {/* ── Player Picker Modal ── */}
      {pickerPos && (
        <div className="picker-overlay" onClick={() => setPickerPos(null)}>
          <div className="picker-modal" onClick={e => e.stopPropagation()}>
            <div className="picker-header">
              <h3>Elegir {POS_LABELS[pickerPos]}</h3>
              <button className="picker-close" onClick={() => setPickerPos(null)}>✕</button>
            </div>
            {pickerPlayers.length === 0 ? (
              <div className="picker-empty">
                No tienes {POS_LABELS[pickerPos].toLowerCase()}s disponibles en el banquillo
              </div>
            ) : (
              <div className="picker-list">
                {pickerPlayers.map(card => (
                  <div
                    key={card.id}
                    className="picker-card"
                    data-rarity={card.base_rarity || 'bronze'}
                    onClick={() => handleAddToLineup(card.id)}
                  >
                    <div className="picker-card-img">
                      <img
                        src={card.image_url || '/images/placeholder.png'}
                        alt={card.player_name}
                        onError={(e) => { e.target.src = '/images/placeholder.png'; }}
                      />
                    </div>
                    <div className="picker-card-info">
                      <span className="picker-card-name">{card.player_name}</span>
                      <span className="picker-card-pos">{card.position}</span>
                    </div>
                    <div className="picker-card-ovr">{card.current_overall}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Header ── */}
      <header className="team-header">
        <button className="team-back-btn" onClick={() => navigate(leagueIdParam ? `/leagues/${leagueIdParam}` : '/dashboard')}>← Volver</button>
        <div className="team-header-center">
          {selectedTeam?.shield_url && <img src={selectedTeam.shield_url} alt="Escudo" className="team-shield-mini" />}
          <h1 className="team-title">{selectedTeam?.name || 'Mi Equipo'}</h1>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <div className="team-ovr">OVR {selectedTeam?.overall_rating?.toFixed(1) || '--'}</div>
          <button className="team-customize-btn" onClick={() => setShowCustomizer(true)} title="Personalizar equipo">✏️</button>
        </div>
      </header>

      {/* ── League selector ── */}
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

      {/* ── Gameweek Info ── */}
      {gameweek && (
        <div className="team-gw-info-card">
          <div className="team-gw-details">
            <span className="team-gw-badge">JORNADA {gameweek.number}</span>
            <span className="team-gw-date">
              Límite: {new Date(gameweek.start_date).toLocaleString('es-ES', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          <div className="team-gw-status">
            {gameweek.is_finished ? (
              <span className="team-status-saved">✅ Jornada finalizada</span>
            ) : new Date() > new Date(gameweek.start_date) ? (
              <span className="team-status-locked">🔒 Jornada en curso — alineación bloqueada</span>
            ) : gwLineup ? (
              <span className="team-status-saved">✅ Equipo guardado para esta jornada</span>
            ) : (
              <span className="team-status-pending">⚠️ Organiza tu 11 antes del límite</span>
            )}
          </div>
        </div>
      )}

      {/* ── Formation Selector ── */}
      <div className="team-formation">
        <label>Formación:</label>
        <div className="team-formation-options">
          {FORMATIONS.map(f => (
            <button
              key={f}
              className={`team-formation-btn ${selectedTeam?.active_formation === f ? 'active' : ''}`}
              onClick={() => handleFormationChange(f)}
            >{f}</button>
          ))}
        </div>
      </div>

      {/* ── PITCH ── */}
      <section className="team-section">
        <h2 className="team-section-title">⚽ Titulares ({lineup.length}/11)</h2>
        <FormationPitch
          lineup={lineup}
          formation={selectedTeam?.active_formation || '4-3-3'}
          onPlayerClick={(player) => setSelectedPlayerForDetail({ ...player, name: player.player_name })}
          onRemovePlayer={handleRemoveFromLineup}
          onSlotClick={(pos) => setPickerPos(pos)}
        />
      </section>

      {/* ══ SELL MODAL ══ */}
      {sellCard && (
        <div className="picker-overlay" onClick={() => setSellCard(null)}>
          <div className="picker-modal" onClick={e => e.stopPropagation()}>
            <div className="picker-header">
              <h3>🏷️ Poner en venta</h3>
              <button className="picker-close" onClick={() => setSellCard(null)}>✕</button>
            </div>
            <div style={{ padding: '16px 20px' }}>
              <div className="picker-card" data-rarity={sellCard.base_rarity || 'bronze'} style={{ cursor: 'default' }}>
                <div className="picker-card-img">
                  {sellCard.image_url ? <img src={sellCard.image_url} alt={sellCard.player_name} /> : <div className="picker-card-fallback">⚽</div>}
                </div>
                <div className="picker-card-info">
                  <span className="picker-card-name">{sellCard.player_name}</span>
                  <span className="picker-card-pos">{sellCard.position} · OVR {sellCard.current_overall}</span>
                </div>
                <div className="picker-card-ovr">{sellCard.current_overall}</div>
              </div>
              <div style={{ marginTop: 16 }}>
                <label style={{ color: '#94a3b8', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Precio de venta (mínimo: {Math.round(sellCard.current_market_value || 0).toLocaleString()})</label>
                <input
                  type="number"
                  value={sellPrice}
                  onChange={e => setSellPrice(e.target.value)}
                  placeholder={`${Math.round(sellCard.current_market_value || 0).toLocaleString()}`}
                  min={Math.round(sellCard.current_market_value || 0)}
                  style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.05)', color: '#fff', fontSize: '1rem', marginTop: 8 }}
                />
              </div>
              <button
                disabled={selling || !sellPrice || Number(sellPrice) < Math.round(sellCard.current_market_value || 0)}
                onClick={async () => {
                  setSelling(true);
                  try {
                    await auctionAPI.listCard(selectedTeam.league_id, sellCard.id, Number(sellPrice));
                    setSuccess(`✅ ${sellCard.player_name} puesto en venta por ${Number(sellPrice).toLocaleString()}`);
                    setSellCard(null); setSellPrice('');
                    setListedCardIds(prev => new Set([...prev, sellCard.id]));
                    setTimeout(() => setSuccess(''), 4000);
                  } catch (err) {
                    setError(err.response?.data?.detail || 'Error al poner en venta');
                    setTimeout(() => setError(''), 4000);
                  }
                  setSelling(false);
                }}
                style={{ width: '100%', marginTop: 16, padding: '14px', borderRadius: '12px', border: 'none', background: selling ? '#475569' : 'linear-gradient(135deg, #22c55e, #16a34a)', color: '#fff', fontWeight: 800, fontSize: '1rem', cursor: selling ? 'wait' : 'pointer' }}
              >
                {selling ? 'Poniendo en venta...' : '🏷️ Poner en venta'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Bench ── */}
      <section className="team-section">
        <h2 className="team-section-title">🪑 Suplentes ({bench.length})</h2>
        <div className="team-players-grid">
          {bench.map(card => {
            const isListed = listedCardIds.has(card.id);
            return (
              <div
                key={card.id}
                className={`team-player-card ${isListed ? 'on-sale' : ''}`}
                data-rarity={card.base_rarity || 'bronze'}
                onClick={() => setSelectedPlayerForDetail({ ...card, name: card.player_name })}
                style={{ cursor: 'pointer' }}
              >
                {isListed && <div className="team-player-sale-badge">📢 EN VENTA</div>}
                <div className="team-player-ovr-badge">{card.current_overall}</div>
                <div className="team-player-pos-badge">{card.position}</div>
                <div className="team-player-image-container">
                  <img
                    src={card.image_url || '/images/placeholder.png'}
                    alt={card.player_name}
                    className="team-player-img"
                    onError={(e) => { e.target.src = '/images/placeholder.png'; }}
                  />
                </div>
                <div className="team-player-info">
                  <span className="team-player-name">{card.player_name}</span>
                </div>
                {isListed ? (
                  <button
                    className="team-player-action team-player-action--cancel"
                    onClick={(e) => { e.stopPropagation(); handleCancelListing(card.id); }}
                  >❌ Retirar</button>
                ) : card.is_tradeable ? (
                  <button
                    className="team-player-action team-player-action--sell"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSellCard(card);
                      setSellPrice(Math.round(card.current_market_value || 0).toString());
                    }}
                  >🏷️ Vender</button>
                ) : null}
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Bottom nav ── */}
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
