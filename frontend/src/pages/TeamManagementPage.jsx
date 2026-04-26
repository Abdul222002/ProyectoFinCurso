import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { teamsAPI, auctionAPI } from '../services/endpoints';
import TeamCustomizerModal from '../components/TeamCustomizerModal';
import PlayerDetailModal from '../components/PlayerDetailModal';
import FormationPitch, { getFormationSlots } from '../components/FormationPitch';
import AppLayout from '../components/AppLayout';
import { resolvePlayerImageUrl } from '../utils/mediaUrl';
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

  // Picker state
  const [pickerPos, setPickerPos] = useState(null);

  // Sell modal state
  const [sellCard, setSellCard] = useState(null);
  const [sellPrice, setSellPrice] = useState('');
  const [selling, setSelling] = useState(false);

  // Listed cards tracking & Release state
  const [listedCardIds, setListedCardIds] = useState(new Set());
  const [releaseCard, setReleaseCard] = useState(null);
  const [releasing, setReleasing] = useState(false);
  
  // Gameweek points state
  const [gwPoints, setGwPoints] = useState(null);

  // Breakdown modal state
  const [gwBreakdown, setGwBreakdown] = useState(null);
  const [loadingBreakdown, setLoadingBreakdown] = useState(false);

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

  const handleGwClick = async (gwNumber) => {
    if (!selectedTeam) return;
    setLoadingBreakdown(true);
    try {
      const res = await teamsAPI.getGameweekLineupBreakdown(selectedTeam.league_id, gwNumber, isReadOnly ? userIdParam : null);
      setGwBreakdown({ gameweek_number: gwNumber, ...res.data });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al cargar desglose');
    }
    setLoadingBreakdown(false);
  };

  const handleAddToLineup = async (cardId) => {
    if (!selectedTeam || !selectedTeam.players) return;
    const cardToAdd = selectedTeam.players.find(p => p.id === cardId);
    if (!cardToAdd) return;

    // Auto-corregir alineación actual: solo contar los que realmente caben
    const formation = selectedTeam.active_formation || '4-3-3';
    const slotsLimit = getFormationSlots(formation);
    const counts = { GK: 0, DEF: 0, MID: 0, FWD: 0 };
    const validLineup = [];
    
    // Filtrar los que están en la base de datos como titulares, pero respetando límites
    for (const p of selectedTeam.players.filter(p => p.is_in_lineup)) {
      const pos = p.position || p.player?.position;
      if (!pos) continue;
      const maxAllowed = pos === 'GK' ? 1 : (slotsLimit[pos] || 0);
      if (counts[pos] < maxAllowed) {
        counts[pos]++;
        validLineup.push(p);
      }
    }

    if (validLineup.length >= 11) {
      setError('Ya tienes 11 titulares. Quita uno primero.');
      setTimeout(() => setError(''), 3000);
      return;
    }
    
    const pos = cardToAdd.position || cardToAdd.player?.position;
    const maxAllowed = pos === 'GK' ? 1 : (slotsLimit[pos] || 0);

    if (counts[pos] >= maxAllowed) {
      setError(`Tu formación ya tiene el máximo de jugadores en la posición ${pos}.`);
      setTimeout(() => setError(''), 3000);
      return;
    }
    
    const currentIds = validLineup.map(p => p.id);
    try {
      await teamsAPI.setLineup(selectedTeam.league_id, [...currentIds, cardId]);
      await loadData();
      setError('');
      setPickerPos(null);
      if (gameweek && new Date() < new Date(gameweek.start_date)) setGwLineup(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al actualizar alineación');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleRemoveFromLineup = async (cardId) => {
    if (!selectedTeam || !selectedTeam.players) return;
    
    // Auto-corregir al quitar: enviar solo los válidos excluyendo el que queremos quitar
    const formation = selectedTeam.active_formation || '4-3-3';
    const slotsLimit = getFormationSlots(formation);
    const counts = { GK: 0, DEF: 0, MID: 0, FWD: 0 };
    const newIds = [];
    
    for (const p of selectedTeam.players.filter(p => p.is_in_lineup)) {
      if (p.id === cardId) continue; // Excluir el que quitamos
      
      const pos = p.position || p.player?.position;
      if (!pos) continue;
      const maxAllowed = pos === 'GK' ? 1 : (slotsLimit[pos] || 0);
      if (counts[pos] < maxAllowed) {
        counts[pos]++;
        newIds.push(p.id);
      }
    }
    try {
      await teamsAPI.setLineup(selectedTeam.league_id, newIds);
      await loadData();
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al quitar jugador');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleFormationChange = async (formation) => {
    if (!selectedTeam) return;
    try {
      const slotsStr = getFormationSlots(formation);
      const currentLineup = selectedTeam.players.filter(p => p.is_in_lineup);
      const counts = { GK: 0, DEF: 0, MID: 0, FWD: 0 };
      const newIds = [];

      for (const p of currentLineup) {
        if (!p.player || !p.player.position) {
          if (p.position) {
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
      const formation = selectedTeam.active_formation || '4-3-3';
      const slotsLimit = getFormationSlots(formation);
      const counts = { GK: 0, DEF: 0, MID: 0, FWD: 0 };
      const validIds = [];
      
      for (const p of selectedTeam.players.filter(p => p.is_in_lineup)) {
        const pos = p.position || p.player?.position;
        if (!pos) continue;
        const maxAllowed = pos === 'GK' ? 1 : (slotsLimit[pos] || 0);
        if (counts[pos] < maxAllowed) {
          counts[pos]++;
          validIds.push(p.id);
        }
      }
      
      await teamsAPI.update(selectedTeam.league_id, { formation });
      await teamsAPI.setLineup(selectedTeam.league_id, validIds);
      setSuccess('✅ Alineación guardada para la próxima jornada.');
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

  const executeClausulazo = async (playerObj) => {
    try {
      const leagueId = leagueIdParam || selectedTeam?.league_id;
      if (!leagueId) { toast.error('No se pudo determinar la liga'); return; }
      await auctionAPI.payClause(leagueId, playerObj.id);
      toast.success(`✅ Has fichado a ${playerObj.player_name}`);
      setSelectedPlayerForDetail(null);
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al pagar cláusula');
    }
  };

  const handleClausulazo = (playerObj) => {
    toast.error(`¿Pagar la cláusula de ${playerObj.player_name}? Se descontarán ${formatPrice(playerObj.current_market_value)}.`, {
      cancel: { label: 'Cancelar' },
      action: { label: 'Comprar', onClick: () => executeClausulazo(playerObj) }
    });
  };

  const executeBlindar = async (playerObj, amount) => {
    try {
      const leagueId = leagueIdParam || selectedTeam?.league_id;
      await auctionAPI.protectPlayer(leagueId, playerObj.id, amount);
      toast.success(`✅ Cláusula aumentada en ${formatPrice(amount)}`);
      setSelectedPlayerForDetail(null);
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al blindar jugador');
    }
  };

  const handleBlindar = (playerObj) => {
    const amountStr = window.prompt(`¿Cuántas monedas quieres quemar para subir la cláusula de ${playerObj.player_name}?`);
    if (!amountStr) return;
    const amount = parseInt(amountStr, 10);
    if (isNaN(amount) || amount <= 0) { toast.error('Cantidad inválida'); return; }

    toast.warning(`¿Seguro que quieres quemar ${formatPrice(amount)} para blindar a ${playerObj.player_name}?`, {
      cancel: { label: 'Cancelar' },
      action: { label: 'Blindar', onClick: () => executeBlindar(playerObj, amount) }
    });
  };

  if (loading) {
    return (
      <AppLayout title="Cargando...">
        <div className="tm-loading">Cargando equipos...</div>
      </AppLayout>
    );
  }

  if (teams.length === 0) {
    return (
      <AppLayout title="Mi Equipo" backTo={leagueIdParam ? `/leagues/${leagueIdParam}` : '/dashboard'}>
        <div className="lg-empty">
          <span style={{ fontSize: '3rem', display: 'block', marginBottom: '16px' }}>🏆</span>
          <h2>No tienes equipos aún</h2>
          <p>Únete a una liga para crear tu equipo automáticamente.</p>
          <button className="btn-primary" style={{ marginTop: '16px' }} onClick={() => navigate('/leagues')}>Ir a Ligas →</button>
        </div>
      </AppLayout>
    );
  }

  const lineup = selectedTeam?.players?.filter(p => p.is_in_lineup) || [];
  const bench = selectedTeam?.players?.filter(p => !p.is_in_lineup) || [];
  const pickerPlayers = pickerPos ? bench.filter(p => p.position === pickerPos) : [];
  const POS_LABELS = { GK: 'Portero', DEF: 'Defensa', MID: 'Centrocampista', FWD: 'Delantero' };

  const headerRight = (
    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
      <div className="tm-value-badge">
        <span className="tm-value-icon">💰</span>
        <span>{formatPrice(selectedTeam?.team_value || 0)}</span>
      </div>
      <div className="tm-ovr-badge">OVR {selectedTeam?.overall_rating?.toFixed(1) || '--'}</div>
    </div>
  );

  return (
    <AppLayout 
      title={(
        <div className="tm-header-title">
          {selectedTeam?.shield_url && (
            <img src={selectedTeam.shield_url} alt="" className="tm-header-logo" />
          )}
          <span>{selectedTeam?.name || 'Mi Equipo'}</span>
        </div>
      )} 
      backTo={leagueIdParam ? `/leagues/${leagueIdParam}` : '/dashboard'}
      rightContent={headerRight}
    >
      <div className="tm-page-content">

        {/* 1. Rival Banner */}
        {isReadOnly && (
          <div className="tm-rival-banner">
            <span>Estás viendo el equipo de <strong>{selectedTeam?.name || 'otro usuario'}</strong></span>
          </div>
        )}

        {/* 2. Customize Bar */}
        <div className="tm-actions-bar">
          {teams.length > 1 && (
            <div className="tm-league-selector">
              {teams.map(t => (
                <button
                  key={t.id}
                  className={`tm-league-btn ${selectedTeam?.id === t.id ? 'active' : ''}`}
                  onClick={() => navigate(`/team?league_id=${t.league_id}`)}
                >
                  {t.league_name || 'Liga'}
                </button>
              ))}
            </div>
          )}
          {!isReadOnly && (
            <button className="btn-secondary" onClick={() => setShowCustomizer(true)}>
              ✏️ Personalizar
            </button>
          )}
        </div>

        {/* 3. Messages */}
        {error && <div className="tm-message error">❌ {error}</div>}
        {success && <div className="tm-message success">✅ {success}</div>}

        {/* 4. Gameweek Info */}
        {gameweek && (
          <div className="tm-gw-card tm-card">
            <div className="tm-gw-header">
              <span className="tm-gw-badge">JORNADA {gameweek.number}</span>
              <span className="tm-gw-date">Límite: {new Date(gameweek.start_date).toLocaleString('es-ES', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>
            </div>
            <div className="tm-gw-status">
              {gameweek.is_finished ? (
                <span className="tm-status-saved">✅ Jornada finalizada</span>
              ) : new Date() > new Date(gameweek.start_date) ? (
                <span className="tm-status-locked">🔒 Alineación bloqueada</span>
              ) : gwLineup ? (
                <span className="tm-status-saved">✅ Equipo guardado para esta jornada</span>
              ) : (
                <span className="tm-status-pending">⚠️ Organiza tu 11 antes del límite</span>
              )}
            </div>
          </div>
        )}

        {/* 5. Formation & Pitch */}
        <div className="tm-section tm-card">
          <div className="tm-formation-bar">
            <div>
              <label>Formación:</label>
              <select 
                className="tm-formation-select" 
                value={selectedTeam?.active_formation || '4-3-3'}
                onChange={(e) => handleFormationChange(e.target.value)}
                disabled={isReadOnly}
              >
                {FORMATIONS.map(f => <option key={f} value={f}>{f}</option>)}
              </select>
            </div>
            {!isReadOnly && (
              <button className="btn-primary" onClick={handleSaveLineup}>
                💾 Guardar
              </button>
            )}
          </div>

          <h2 className="tm-section-title">⚽ Titulares ({lineup.length}/{(() => { const s = getFormationSlots(selectedTeam?.active_formation || '4-3-3'); return 1 + (s.DEF||0) + (s.MID||0) + (s.FWD||0); })()})</h2>
          
          <div className="tm-pitch-wrapper">
            <div className="tm-pitch-container">
              <FormationPitch
                lineup={lineup}
                formation={selectedTeam?.active_formation || '4-3-3'}
                onPlayerClick={(player) => setSelectedPlayerForDetail({ ...player, name: player.player_name })}
                onRemovePlayer={isReadOnly ? undefined : handleRemoveFromLineup}
                onSlotClick={isReadOnly ? undefined : (pos) => setPickerPos(pos)}
              />
            </div>
          </div>
        </div>

        {/* 6. GW Points section */}
        <div className="tm-section tm-card">
          <h2 className="tm-section-title">📊 Puntos por Jornada</h2>
          {gwPoints && gwPoints.gameweek_points && gwPoints.gameweek_points.length > 0 ? (
            <div className="tm-gw-points">
              <div className="tm-gw-total">
                <div className="tm-gw-total-label">Total Temporada</div>
                <div className="tm-gw-total-val">{gwPoints.total_points.toFixed(1)}</div>
              </div>
              <div className="tm-gw-points-list">
                {gwPoints.gameweek_points.map(gw => (
                  <div key={gw.gameweek_number} className="tm-gw-point-row" onClick={() => handleGwClick(gw.gameweek_number)} style={{ cursor: 'pointer', transition: 'transform 0.2s' }} onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.05)'} onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}>
                    <span>J{gw.gameweek_number}</span>
                    <strong style={{ color: gw.points_earned > 0 ? 'var(--success)' : 'inherit' }}>
                      {gw.points_earned.toFixed(1)} pts
                    </strong>
                  </div>
                ))}
              </div>
            </div>
          ) : (
             <div className="tm-empty" style={{ padding: '20px' }}>No hay datos de puntos aún</div>
          )}
        </div>

        {/* 7. Bench (Horizontal Scroll) */}
        <div className="tm-section">
          <h2 className="tm-section-title">🪑 Banquillo ({bench.length})</h2>
          
          <div className="tm-bench-list">
            {bench.length === 0 ? (
              <div className="lg-empty" style={{ padding: '20px', width: '100%' }}>Banquillo vacío</div>
            ) : (
              bench.map(card => {
                const isListed = listedCardIds.has(card.id);
                return (
                  <div key={card.id} className="tm-bench-card" onClick={() => setSelectedPlayerForDetail({ ...card, name: card.player_name })}>
                    <div className="tm-bench-img-wrap">
                      <img src={resolvePlayerImageUrl(card.image_url)} alt={card.player_name} loading="lazy" decoding="async" />
                      <div className="tm-bench-pos">{card.position}</div>
                    </div>
                    
                    <div className="tm-bench-info">
                      <div className="tm-bench-name">{card.player_name}</div>
                      <div className="tm-bench-ovr">OVR {card.current_overall}</div>
                      {isListed && <div className="tm-bench-sale-text">En Venta</div>}
                    </div>

                    {!isReadOnly && (
                      <div className="tm-bench-actions" onClick={e => e.stopPropagation()}>
                        {isListed ? (
                          <button className="tm-btn tm-btn-cancel" onClick={() => handleCancelListing(card.id)}>
                            Retirar
                          </button>
                        ) : card.is_tradeable ? (
                          <>
                            <button className="tm-btn tm-btn-sell" onClick={() => { setSellCard(card); setSellPrice(Math.round(card.current_market_value || 0).toString()); }}>
                              Vender
                            </button>
                            <button className="tm-btn tm-btn-release" onClick={() => setReleaseCard(card)}>
                              Despedir
                            </button>
                          </>
                        ) : null}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Modals placed outside main flow */}
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
            onSell={!isReadOnly ? async (playerObj) => {
              // If in lineup, remove first
              if (playerObj.is_in_lineup) {
                await handleRemoveFromLineup(playerObj.id);
              }
              setSellCard(playerObj);
              setSellPrice(Math.round(playerObj.current_market_value || 0).toString());
            } : undefined}
            onRelease={!isReadOnly ? async (playerObj) => {
              if (playerObj.is_in_lineup) {
                await handleRemoveFromLineup(playerObj.id);
              }
              setReleaseCard(playerObj);
            } : undefined}
            onClose={() => setSelectedPlayerForDetail(null)}
          />
        )}

        {/* Player Picker Modal */}
        {pickerPos && (
          <div className="tm-picker-overlay" onClick={() => setPickerPos(null)}>
            <div className="tm-picker-modal" onClick={e => e.stopPropagation()}>
              <div className="tm-picker-header">
                <h3>Elegir {POS_LABELS[pickerPos]}</h3>
                <button className="tm-picker-close" onClick={() => setPickerPos(null)}>✕</button>
              </div>
              {pickerPlayers.length === 0 ? (
                <div className="tm-picker-empty">No tienes {POS_LABELS[pickerPos].toLowerCase()}s disponibles en el banquillo.</div>
              ) : (
                <div className="tm-picker-list">
                  {pickerPlayers.map(card => (
                    <div key={card.id} className="tm-picker-card" onClick={() => handleAddToLineup(card.id)}>
                      <div className="tm-picker-card-img-wrap">
                        <img 
                          src={resolvePlayerImageUrl(card.image_url, card.player_name)} 
                          alt={card.player_name} 
                          loading="lazy" 
                          decoding="async" 
                          onError={(e) => { 
                            e.target.onerror = null; 
                            e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(card.player_name||'UFL')}&background=152e20&color=25f478&bold=true`; 
                          }} 
                        />
                      </div>
                      <div className="tm-picker-card-info">
                        <span className="tm-picker-card-name" style={{ color: 'var(--text-primary)', fontWeight: 800 }}>{card.player_name}</span>
                        <span className="tm-picker-card-pos" style={{ color: 'var(--text-secondary)' }}>OVR {card.current_overall}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Sell / Release Modals */}
        {sellCard && (
          <div className="tm-picker-overlay" onClick={() => setSellCard(null)}>
            <div className="tm-picker-modal" onClick={e => e.stopPropagation()}>
              <div className="tm-picker-header">
                <h3>🏷️ Vender Jugador</h3>
                <button className="tm-picker-close" onClick={() => setSellCard(null)}>✕</button>
              </div>
              <div style={{ padding: '16px' }}>
                <p>Vender a <strong>{sellCard.player_name}</strong>. Precio mínimo: {Math.round(sellCard.current_market_value || 0).toLocaleString()}</p>
                <input
                  type="number"
                  className="ld-input"
                  value={sellPrice}
                  onChange={e => setSellPrice(e.target.value)}
                  placeholder="Precio"
                  min={Math.round(sellCard.current_market_value || 0)}
                  style={{ width: '100%', marginTop: '16px', marginBottom: '16px' }}
                />
                <button
                  className="btn-primary"
                  style={{ width: '100%', padding: '12px' }}
                  disabled={selling || !sellPrice || Number(sellPrice) < Math.round(sellCard.current_market_value || 0)}
                  onClick={async () => {
                    setSelling(true);
                    try {
                      await auctionAPI.listCard(selectedTeam.league_id, sellCard.id, Number(sellPrice));
                      setSuccess(`✅ Puesto en venta por ${Number(sellPrice).toLocaleString()}`);
                      setSellCard(null); setSellPrice('');
                      setListedCardIds(prev => new Set([...prev, sellCard.id]));
                    } catch (err) { setError('Error al vender'); }
                    setSelling(false);
                  }}
                >
                  {selling ? 'Procesando...' : 'Confirmar Venta'}
                </button>
              </div>
            </div>
          </div>
        )}

        {releaseCard && (
          <div className="tm-picker-overlay" onClick={() => setReleaseCard(null)}>
            <div className="tm-picker-modal" onClick={e => e.stopPropagation()}>
              <div className="tm-picker-header">
                <h3>🔓 Despedir Jugador</h3>
                <button className="tm-picker-close" onClick={() => setReleaseCard(null)}>✕</button>
              </div>
              <div style={{ padding: '16px' }}>
                <p>¿Despedir a <strong>{releaseCard.player_name}</strong>?</p>
                <p style={{ color: 'var(--danger)', marginTop: '8px', fontSize: '0.9rem' }}>
                  Recibirás el 50% de valor ({Math.round((releaseCard.current_market_value || 0) / 2).toLocaleString()}). Acción irreversible.
                </p>
                <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
                  <button className="btn-secondary" style={{ flex: 1 }} onClick={() => setReleaseCard(null)}>Cancelar</button>
                  <button className="lg-btn-danger" style={{ flex: 1 }} disabled={releasing} onClick={async () => {
                    setReleasing(true);
                    try {
                      await teamsAPI.releasePlayer(selectedTeam.league_id, releaseCard.id);
                      setSuccess('✅ Jugador liberado'); await loadData(); setReleaseCard(null);
                    } catch (err) { setError('Error al liberar'); }
                    setReleasing(false);
                  }}>
                    {releasing ? '...' : 'Confirmar'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Breakdown Modal */}
        {gwBreakdown && (
          <div className="tm-picker-overlay" onClick={() => setGwBreakdown(null)}>
            <div className="tm-picker-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '600px', width: '95%' }}>
              <div className="tm-picker-header">
                <h3>Resumen Jornada {gwBreakdown.gameweek_number}</h3>
                <button className="tm-picker-close" onClick={() => setGwBreakdown(null)}>✕</button>
              </div>
              <div style={{ padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', background: 'var(--surface-light)', padding: '12px', borderRadius: '8px' }}>
                  <span>Formación: <strong>{gwBreakdown.formation}</strong></span>
                  <span>Total Puntos: <strong style={{ color: 'var(--success)' }}>{gwBreakdown.total_points.toFixed(1)}</strong></span>
                </div>
                
                {gwBreakdown.lineup_players.length === 0 ? (
                  <div className="tm-empty">No hay datos de jugadores para esta alineación.</div>
                ) : (
                  <div className="tm-picker-list" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
                    {gwBreakdown.lineup_players.map(card => (
                      <div key={card.id} className="tm-picker-card" style={{ cursor: 'default', display: 'flex', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <div className="tm-picker-card-img-wrap" style={{ width: '50px', height: '60px' }}>
                            <img 
                              src={resolvePlayerImageUrl(card.image_url, card.player_name)} 
                              alt={card.player_name} 
                              loading="lazy" 
                              decoding="async" 
                              onError={(e) => { 
                                e.target.onerror = null; 
                                e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(card.player_name||'UFL')}&background=1b2a47&color=f1c40f&bold=true`; 
                              }} 
                            />
                          </div>
                          <div className="tm-picker-card-info">
                            <span className="tm-picker-card-name" style={{ color: 'var(--text-primary)', fontWeight: 800 }}>{card.player_name}</span>
                            <span className="tm-picker-card-pos" style={{ color: 'var(--text-secondary)' }}>{card.position} {card.is_legend ? '🌟' : ''}</span>
                          </div>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', fontWeight: 'bold', fontSize: '1.2rem', color: card.points_earned > 0 ? 'var(--success)' : 'var(--text-primary)' }}>
                          {card.points_earned.toFixed(1)} pts
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

      </div>
    </AppLayout>
  );
}
