import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { teamsAPI, leaguesAPI, auctionAPI, marketAPI } from '../services/endpoints';
import TeamCustomizerModal from '../components/TeamCustomizerModal';
import PlayerDetailModal from '../components/PlayerDetailModal';
import FormationPitch, { getFormationSlots } from '../components/FormationPitch';
import { toast } from 'sonner';
import './TeamManagementPage.css';

export default function TeamManagementPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const leagueIdParam = searchParams.get('league_id');
  const userIdParam = searchParams.get('user_id');
  const isReadOnly = !!userIdParam && userIdParam !== String(user?.id);

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

  // ── Listed cards tracking & Release state ──
  const [listedCardIds, setListedCardIds] = useState(new Set());
  const [releaseCard, setReleaseCard] = useState(null);
  const [releasing, setReleasing] = useState(false);
  
  // Gameweek points state
  const [gwPoints, setGwPoints] = useState(null);

  const FORMATIONS = ['4-4-2', '4-3-3', '3-5-2', '4-2-3-1', '3-4-3', '5-3-2', '5-4-1'];

  const formatPrice = (price) => {
    if (price >= 1000000) return `€${(price / 1000000).toFixed(1)}M`;
    return `€${price.toLocaleString('es-ES')}`;
  };

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      if (leagueIdParam && userIdParam) {
        const res = await teamsAPI.getUserTeam(leagueIdParam, userIdParam);
        setSelectedTeam(res.data);
        setTeams([res.data]);
      } else if (leagueIdParam) {
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
  }, [leagueIdParam, userIdParam]);

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

  // Load gameweek points
  useEffect(() => {
    if (!selectedTeam) return;
    const loadPoints = async () => {
      try {
        let res;
        if (isReadOnly && userIdParam) {
          res = await teamsAPI.getUserGameweekPoints(selectedTeam.league_id, userIdParam);
        } else {
          res = await teamsAPI.getGameweekPoints(selectedTeam.league_id);
        }
        setGwPoints(res.data);
      } catch { setGwPoints(null); }
    };
    loadPoints();
  }, [selectedTeam, isReadOnly, userIdParam]);

  // ── Add player to lineup ──
  const handleAddToLineup = async (cardId) => {
    if (!selectedTeam || !selectedTeam.players) return;

    // Find the chosen card from the bench to know its position
    const cardToAdd = selectedTeam.players.find(p => p.id === cardId);
    if (!cardToAdd) return;

    const currentLineup = selectedTeam.players.filter(p => p.is_in_lineup);
    if (currentLineup.length >= 11) {
      setError('Ya tienes 11 titulares. Quita uno primero.');
      setTimeout(() => setError(''), 3000);
      return;
    }

    // Bugfix: ensure we don't exceed the chosen formation slots for this position
    const slotsLimit = getFormationSlots(selectedTeam.active_formation || '4-3-3');
    const pos = cardToAdd.position;
    const samePosInLineup = currentLineup.filter(p => p.position === pos).length;

    const maxAllowed = pos === 'GK' ? 1 : (slotsLimit[pos] || 0);

    if (samePosInLineup >= maxAllowed) {
      setError(`Tu formación ya tiene el máximo de jugadores en la posición ${pos}.`);
      setTimeout(() => setError(''), 3000);
      return;
    }

    const currentIds = currentLineup.map(p => p.id);
    try {
      await teamsAPI.setLineup(selectedTeam.league_id, [...currentIds, cardId]);
      await loadData(); // REFRESCA AL 100% LA BD
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
      await teamsAPI.setLineup(selectedTeam.league_id, newIds);
      await loadData(); // REFRESCA AL 100% LA BD
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al quitar jugador');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleFormationChange = async (formation) => {
    if (!selectedTeam) return;
    try {
      // 1. Calculate how many players of each position fit in the new formation
      const slotsStr = getFormationSlots(formation);
      // getFormationSlots returns { DEF: 4, MID: 3, FWD: 3 }

      const currentLineup = selectedTeam.players.filter(p => p.is_in_lineup);
      const counts = { GK: 0, DEF: 0, MID: 0, FWD: 0 };
      const newIds = [];

      for (const p of currentLineup) {
        if (!p.player || !p.player.position) {
          if (p.position) { // Try card level if player level missing
            p.player = { position: p.position };
          } else {
            continue;
          }
        }

        const pos = p.player.position;
        if (pos === 'GK' && counts.GK < 1) {
          counts.GK++;
          newIds.push(p.id);
        } else if (pos === 'DEF' && counts.DEF < slotsStr.DEF) {
          counts.DEF++;
          newIds.push(p.id);
        } else if (pos === 'MID' && counts.MID < slotsStr.MID) {
          counts.MID++;
          newIds.push(p.id);
        } else if (pos === 'FWD' && counts.FWD < slotsStr.FWD) {
          counts.FWD++;
          newIds.push(p.id);
        }
      }

      await teamsAPI.update(selectedTeam.league_id, { formation });
      await teamsAPI.setLineup(selectedTeam.league_id, newIds);
      await loadData();
      setSuccess(`Formación cambiada a ${formation}. Alineación ajustada.`);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cambiar formación');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleSaveLineup = async () => {
    if (!selectedTeam) return;
    try {
      const currentLineup = selectedTeam.players.filter(p => p.is_in_lineup);
      const currentIds = currentLineup.map(p => p.id);
      // Garantizar que la formación activa actual se guarde forzosamente
      await teamsAPI.update(selectedTeam.league_id, { formation: selectedTeam.active_formation });
      await teamsAPI.setLineup(selectedTeam.league_id, currentIds);
      setSuccess('✅ Alineación y formación guardadas para la próxima jornada.');
      setTimeout(() => setSuccess(''), 4000);
      if (gameweek && new Date() < new Date(gameweek.start_date)) setGwLineup(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al guardar la alineación');
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

  const handleClausulazo = async (playerObj) => {
    toast.error(`¿Pagar la cláusula de ${playerObj.player_name}? Se descontarán ${formatPrice(playerObj.current_market_value)} y pasará a tu equipo.`, {
      cancel: { label: 'Cancelar' },
      action: {
        label: 'Comprar',
        onClick: async () => {
          try {
            await auctionAPI.payClause(leagueIdParam, playerObj.id);
            toast.success(`✅ Has fichado a ${playerObj.player_name}`);
            setSelectedPlayerForDetail(null);
            loadData();
          } catch (err) {
            toast.error(err.response?.data?.detail || 'Error al pagar cláusula');
          }
        }
      }
    });
  };

  const handleBlindar = async (playerObj) => {
    const amountStr = window.prompt(`¿Cuántas monedas quieres quemar para subir la cláusula de ${playerObj.player_name}?`);
    if (!amountStr) return;
    const amount = parseInt(amountStr, 10);
    if (isNaN(amount) || amount <= 0) {
      toast.error('Cantidad inválida');
      return;
    }

    toast.warning(`¿Seguro que quieres quemar ${formatPrice(amount)} para blindar a ${playerObj.player_name}?`, {
      cancel: { label: 'Cancelar' },
      action: {
        label: 'Blindar',
        onClick: async () => {
          try {
            await auctionAPI.protectPlayer(selectedTeam.league_id, playerObj.id, amount);
            toast.success(`✅ Cláusula aumentada en ${formatPrice(amount)}`);
            setSelectedPlayerForDetail(null);
            loadData();
          } catch (err) {
            toast.error(err.response?.data?.detail || 'Error al blindar jugador');
          }
        }
      }
    });
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
      {/* ── Rival Banner ── */}
      {isReadOnly && (
        <div className="rival-banner">
          <div className="rival-banner-content">
            <span className="rival-banner-icon">👁️</span>
            <span className="rival-banner-text">
              Estás viendo el equipo de <strong>{selectedTeam?.name || 'otro usuario'}</strong>
            </span>
          </div>
          <button className="rival-banner-back" onClick={() => navigate(leagueIdParam ? `/leagues/${leagueIdParam}` : '/dashboard')}>
            ← Volver a la liga
          </button>
        </div>
      )}
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
          isReadOnly={isReadOnly}
          onClausulazo={handleClausulazo}
          onBlindar={handleBlindar}
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
        <button className="team-back-btn" onClick={() => navigate(leagueIdParam ? `/leagues/${leagueIdParam}` : '/dashboard')}>
          <span style={{ fontSize: '1.2rem' }}>‹</span> Volver
        </button>
        <div className="team-header-center">
          {selectedTeam?.shield_url && <img src={selectedTeam.shield_url} alt="Escudo" className="team-shield-mini" />}
          <h1 className="team-title">{selectedTeam?.name || 'Mi Equipo'}</h1>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <div className="team-value-badge">
            <span className="team-value-icon">💰</span>
            <span className="team-value-amount">{formatPrice(selectedTeam?.team_value || 0)}</span>
          </div>
          <div className="team-ovr">OVR {selectedTeam?.overall_rating?.toFixed(1) || '--'}</div>
          {!isReadOnly && (
            <button className="team-customize-btn" onClick={() => setShowCustomizer(true)} title="Personalizar equipo">✏️</button>
          )}
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
        <div>
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
        {!isReadOnly && (
          <button className="tm-save-lineup-btn" onClick={handleSaveLineup}>
            💾 Guardar Alineación
          </button>
        )}
      </div>

      {/* ── PITCH ── */}
      <section className="team-section">
        <h2 className="team-section-title">⚽ Titulares ({lineup.length}/11)</h2>
        <FormationPitch
          lineup={lineup}
          formation={selectedTeam?.active_formation || '4-3-3'}
          onPlayerClick={(player) => setSelectedPlayerForDetail({ ...player, name: player.player_name })}
          onRemovePlayer={isReadOnly ? undefined : handleRemoveFromLineup}
          onSlotClick={isReadOnly ? undefined : (pos) => setPickerPos(pos)}
        />
      </section>

      {/* ══ GAMEWEEK POINTS ══ */}
      <section className="team-section">
        <h2 className="team-section-title">📊 Puntos por Jornada</h2>
        {gwPoints && gwPoints.gameweek_points && gwPoints.gameweek_points.length > 0 ? (
          <div className="gw-points-container">
            <div className="gw-points-total-card">
              <div className="gw-points-total-label">Puntos Totales</div>
              <div className="gw-points-total-value">{gwPoints.total_points.toFixed(1)}</div>
              <div className="gw-points-total-sub">{gwPoints.gameweek_points.length} jornadas jugadas</div>
            </div>
            <div className="gw-points-grid">
              {gwPoints.gameweek_points.map(gw => {
                const maxPts = Math.max(...gwPoints.gameweek_points.map(g => g.points_earned), 1);
                const pct = Math.min(100, (gw.points_earned / maxPts) * 100);
                return (
                  <div key={gw.gameweek_number} className="gw-points-row">
                    <span className="gw-points-label">J{gw.gameweek_number}</span>
                    <div className="gw-points-bar-bg">
                      <div
                        className="gw-points-bar-fill"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className={`gw-points-value ${gw.points_earned > 0 ? 'positive' : ''}`}>
                      {gw.points_earned.toFixed(1)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="gw-points-empty">No hay datos de puntos por jornada aún</div>
        )}
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

      {/* ══ RELEASE MODAL ══ */}
      {releaseCard && (
        <div className="picker-overlay" onClick={() => setReleaseCard(null)} style={{ zIndex: 110 }}>
          <div className="picker-modal" onClick={e => e.stopPropagation()}>
            <div className="picker-header">
              <h3>🔓 Confirmar Liberación</h3>
              <button className="picker-close" onClick={() => setReleaseCard(null)}>✕</button>
            </div>
            <div style={{ padding: '24px 20px', textAlign: 'center' }}>
              <div className="picker-card" data-rarity={releaseCard.base_rarity || 'bronze'} style={{ cursor: 'default', margin: '0 auto 16px', maxWidth: '300px' }}>
                <div className="picker-card-img">
                  {releaseCard.image_url ? <img src={releaseCard.image_url} alt={releaseCard.player_name} /> : <div className="picker-card-fallback">⚽</div>}
                </div>
                <div className="picker-card-info" style={{ textAlign: 'left' }}>
                  <span className="picker-card-name">{releaseCard.player_name}</span>
                  <span className="picker-card-pos">{releaseCard.position} · OVR {releaseCard.current_overall}</span>
                </div>
              </div>
              <p style={{ color: '#fff', fontSize: '1.05rem', marginBottom: '8px' }}>
                ¿Estás seguro de que quieres liberar a <strong>{releaseCard.player_name}</strong>?
              </p>
              <p style={{ color: '#fbbf24', fontSize: '1.2rem', fontWeight: '800', marginBottom: '8px' }}>
                Recibirás {Math.round((releaseCard.current_market_value || 0) / 2).toLocaleString()} monedas
              </p>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '24px' }}>
                Esto es el 50% de su valor de mercado actual. Esta acción <span style={{ color: '#ef4444' }}>no se puede deshacer</span>.
              </p>

              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={() => setReleaseCard(null)}
                  style={{ flex: 1, padding: '14px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.05)', color: '#fff', fontWeight: 600, fontSize: '1rem', cursor: 'pointer' }}
                >
                  Cancelar
                </button>
                <button
                  disabled={releasing}
                  onClick={async () => {
                    setReleasing(true);
                    const releaseValue = Math.round((releaseCard.current_market_value || 0) / 2);
                    try {
                      await teamsAPI.releasePlayer(selectedTeam.league_id, releaseCard.id);
                      setSuccess(`✅ ${releaseCard.player_name} liberado por ${releaseValue.toLocaleString()} monedas`);
                      await loadData();
                      setReleaseCard(null);
                      setTimeout(() => setSuccess(''), 4000);
                    } catch (err) {
                      setError(err.response?.data?.detail || 'Error al liberar jugador');
                      setTimeout(() => setError(''), 4000);
                    }
                    setReleasing(false);
                  }}
                  style={{ flex: 1, padding: '14px', borderRadius: '12px', border: 'none', background: releasing ? '#b45309' : 'linear-gradient(135deg, #f59e0b, #d97706)', color: '#fff', fontWeight: 800, fontSize: '1rem', cursor: releasing ? 'wait' : 'pointer' }}
                >
                  {releasing ? 'Liberando...' : '🔓 Liberar'}
                </button>
              </div>
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
                {isListed && !isReadOnly ? (
                  <button
                    className="team-player-action team-player-action--cancel"
                    onClick={(e) => { e.stopPropagation(); handleCancelListing(card.id); }}
                  >❌ Retirar</button>
                ) : card.is_tradeable && !isReadOnly ? (
                  <div className="team-player-actions-row" onClick={(e) => e.stopPropagation()}>
                    <button
                      className="team-player-action team-player-action--sell"
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        setSellCard(card);
                        setSellPrice(Math.round(card.current_market_value || 0).toString());
                      }}
                    >🏷️ Vender</button>
                    <button
                      className="team-player-action team-player-action--release"
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        setReleaseCard(card);
                      }}
                    >🔓 Liberar</button>
                  </div>
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
