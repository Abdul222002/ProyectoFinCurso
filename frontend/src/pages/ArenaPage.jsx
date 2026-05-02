import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { arenaAPI, teamsAPI } from '../services/endpoints';
import AppLayout from '../components/AppLayout';
import { toast } from 'sonner';
import './ArenaPage.css';

const delay = ms => new Promise(r => setTimeout(r, ms));

// ── SHIELD helper ─────────────────────────────────────────────────────────────
function Shield({ url, size = 40, style = {} }) {
  if (url) {
    return (
      <img
        src={url} alt=""
        style={{ width: size, height: size, objectFit: 'contain', ...style }}
        onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
      />
    );
  }
  return null;
}
function ShieldFallback({ size = 40, style = {} }) {
  return (
    <span style={{ fontSize: size * 0.6, display: 'flex', alignItems: 'center', justifyContent: 'center', width: size, height: size, ...style }}>
      🛡️
    </span>
  );
}
function TeamShield({ team, size = 40, style = {} }) {
  return (
    <span style={{ display: 'inline-flex', position: 'relative', ...style }}>
      {team?.shield_url
        ? <Shield url={team.shield_url} size={size} />
        : null}
      <ShieldFallback size={size} style={{ display: team?.shield_url ? 'none' : 'flex' }} />
    </span>
  );
}

// ── PARTICLES CANVAS ──────────────────────────────────────────────────────────
function Particles() {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let W = canvas.width = window.innerWidth;
    let H = canvas.height = window.innerHeight;
    const pts = Array.from({ length: 60 }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      r: Math.random() * 1.8 + 0.4,
      vx: (Math.random() - 0.5) * 0.25,
      vy: -Math.random() * 0.25 - 0.05,
      phase: Math.random() * Math.PI * 2,
    }));
    let raf;
    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      const t = performance.now() / 1000;
      pts.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.y < -4) { p.y = H + 4; p.x = Math.random() * W; }
        const a = (Math.sin(t + p.phase) + 1) / 2 * 0.45 + 0.05;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(201,168,76,${a})`; ctx.fill();
      });
      raf = requestAnimationFrame(draw);
    };
    draw();
    const resize = () => { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; };
    window.addEventListener("resize", resize);
    return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", resize); };
  }, []);
  return <canvas ref={ref} style={{ position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none", opacity: 0.5 }} />;
}

// ── 3D TILT CARD ──────────────────────────────────────────────────────────────
function TiltCard({ children, className, onClick }) {
  const ref = useRef(null);
  const onMove = useCallback(e => {
    if (!ref.current) return;
    const r = ref.current.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width - 0.5) * 14;
    const y = ((e.clientY - r.top) / r.height - 0.5) * -14;
    ref.current.style.transform = `perspective(700px) rotateX(${y}deg) rotateY(${x}deg) translateY(-4px) scale(1.03)`;
    ref.current.style.setProperty("--gx", `${((e.clientX - r.left) / r.width) * 100}%`);
    ref.current.style.setProperty("--gy", `${((e.clientY - r.top) / r.height) * 100}%`);
  }, []);
  const onLeave = useCallback(() => {
    if (!ref.current) return;
    ref.current.style.transform = "";
  }, []);
  return (
    <div ref={ref} className={className} onClick={onClick}
      onMouseMove={onMove} onMouseLeave={onLeave}
      style={{ transition: "transform 0.25s ease", transformStyle: "preserve-3d", willChange: "transform" }}>
      {children}
    </div>
  );
}

// ── ANIMATED NUMBER ───────────────────────────────────────────────────────────
function Counter({ value }) {
  const [n, setN] = useState(value || 0);
  const prev = useRef(value || 0);
  useEffect(() => {
    if (value === prev.current) return;
    const s = prev.current, e = value || 0, t0 = performance.now();
    const tick = t => {
      const p = Math.min(1, (t - t0) / 600);
      const ease = p < 0.5 ? 2 * p * p : -1 + (4 - 2 * p) * p;
      setN(Math.round(s + (e - s) * ease));
      if (p < 1) requestAnimationFrame(tick); else prev.current = e;
    };
    requestAnimationFrame(tick);
  }, [value]);
  return <>{n.toLocaleString('es-ES')}</>;
}

// ── BATTLE OVERLAY ────────────────────────────────────────────────────────────
function BattleOverlay({ phase, myTeam, oppTeam, result, onClose }) {
  const [tick, setTick] = useState(0);
  useEffect(() => { const id = setInterval(() => setTick(t => t + 1), 90); return () => clearInterval(id); }, []);
  const dots = ["", ".", "..", "..."][tick % 4];

  if (phase === "searching") return (
    <div className="ov">
      <div className="ov-scan" />
      <div className="ov-dot" />
      <p className="ov-stxt">BUSCANDO RIVAL{dots}</p>
      <p className="ov-ssub">Emparejando por ELO · Por favor espera</p>
    </div>
  );

  if (phase === "vs") return (
    <div className="ov">
      <div className="ov-scan" />
      <div className="ov-vs-wrap">
        <div className="ov-vs-side left">
          <div className="ov-vs-shield">
            <TeamShield team={myTeam} size={80} />
          </div>
          <div className="ov-vs-name">{myTeam.name}</div>
          <div className="ov-vs-league">{myTeam.league_name || 'Liga Privada'}</div>
          <div className="ov-vs-ovr" style={{ color: "var(--gold)" }}>OVR <strong>{myTeam.overall_rating?.toFixed(0) || myTeam.ovr}</strong></div>
        </div>
        <div className="ov-vs-mid">
          <div className="ov-bolt">⚔️</div>
          <div className="ov-vs-label">VS</div>
        </div>
        <div className="ov-vs-side right">
          <div className="ov-vs-shield">
            {oppTeam?.shield_url
              ? <img src={oppTeam.shield_url} alt="" style={{ width: 80, height: 80, objectFit: 'contain' }} />
              : <span style={{ fontSize: '4rem' }}>🛡️</span>
            }
          </div>
          <div className="ov-vs-name">{oppTeam?.name || oppTeam?.team2_name || 'Desconocido'}</div>
          <div className="ov-vs-league">{oppTeam?.league_name || 'Rival Competitivo'}</div>
          <div className="ov-vs-ovr" style={{ color: "var(--danger)" }}>OVR <strong>{oppTeam?.overall_rating?.toFixed(0) || oppTeam?.team2_ovr?.toFixed(0) || oppTeam?.ovr}</strong></div>
        </div>
      </div>
      <p className="ov-ssub" style={{ marginTop: 48, animation: "blinkAnim 0.7s ease-in-out infinite alternate" }}>⚽ Partido iniciando...</p>
    </div>
  );

  if (phase === "result" && result) {
    const res = result.result;
    const myGoals = result.team1_score;
    const oppGoals = result.team2_score;
    const eloDelta = result.global_rating_change;
    const coins = result.coins_rewarded;

    const cfg = {
      victory: { label: "¡VICTORIA!", sub: "Aplastaste al rival", rc: "var(--gold)", rg: "rgba(201, 168, 76, 0.2)" },
      defeat: { label: "DERROTA", sub: "El rival fue superior", rc: "var(--danger)", rg: "rgba(239, 68, 68, 0.15)" },
      draw: { label: "EMPATE", sub: "Un partido muy igualado", rc: "var(--text-secondary)", rg: "transparent" },
    }[res] || { label: "FINALIZADO", sub: "Partido completado", rc: "var(--text-secondary)", rg: "transparent" };

    return (
      <div className="ov">
        <div className="ov-scan" />
        <div className="ov-rcard" style={{ "--rc": cfg.rc, "--rg": cfg.rg }}>
          <div className="ov-rshim" />
          <div className="ov-rglow" />
          <div className="ov-rtitle" style={{ color: cfg.rc }}>{cfg.label}</div>
          <div className="ov-rsub">{cfg.sub}</div>
          <div className="ov-score">
            <div className="ov-snum my">{myGoals}</div>
            <div className="ov-sdash">—</div>
            <div className="ov-snum op">{oppGoals}</div>
          </div>
          <div className="ov-rmatch">{myTeam.name} <span>vs</span> {oppTeam?.name || oppTeam?.team2_name}</div>
          <div className="ov-rewards">
            {[
              { icon: "📊", val: `${eloDelta >= 0 ? "+" : ""}${eloDelta}`, lbl: "ELO", col: eloDelta >= 0 ? "var(--gold)" : "var(--danger)", d: "0.18s" },
              { icon: "🪙", val: `+${coins?.toLocaleString('es-ES') || 0}`, lbl: "Monedas", col: "var(--gold)", d: "0.34s" },
              { icon: res === "victory" ? "🏆" : res === "draw" ? "🤝" : "💀", val: res === "victory" ? "Top 1%" : "¡Sigue!", lbl: "Rango", col: "var(--text-primary)", d: "0.50s" },
            ].map((rw, i) => (
              <div key={i} className="ov-rw" style={{ "--d": rw.d }}>
                <div className="ov-rw-icon">{rw.icon}</div>
                <div className="ov-rw-val" style={{ color: rw.col }}>{rw.val}</div>
                <div className="ov-rw-lbl">{rw.lbl}</div>
              </div>
            ))}
          </div>
          <button className="ov-close" onClick={onClose}>CONTINUAR →</button>
        </div>
      </div>
    );
  }
  return null;
}

// ── MAIN COMPONENT ────────────────────────────────────────────────────────────
export default function ArenaPage() {
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("battle");
  const [phase, setPhase] = useState(null);
  const [matchResult, setMatchResult] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);

  const [teams, setTeams] = useState([]);
  const [history, setHistory] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [status, setStatus] = useState(null);

  const [myTeam, setMyTeam] = useState(null);
  const [oppTeam, setOppTeam] = useState(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statusRes, teamsRes, historyRes, lbRes] = await Promise.all([
        arenaAPI.getStatus(),
        teamsAPI.getMy(),
        arenaAPI.history(20),
        arenaAPI.leaderboard(50)
      ]);
      setStatus(statusRes.data);
      setTeams(teamsRes.data);
      if (teamsRes.data.length > 0 && !myTeam) {
        setMyTeam(teamsRes.data[0]);
      }
      setHistory(historyRes.data);
      setLeaderboard(lbRes.data);
    } catch (err) {
      toast.error('Error al cargar datos de la Arena');
    }
    setLoading(false);
  };

  async function handleFight() {
    if (!myTeam || status?.arena_tickets <= 0 || isSimulating) return;
    setIsSimulating(true);
    setStatus(s => ({ ...s, arena_tickets: s.arena_tickets - 1 }));
    setOppTeam(null);
    setPhase("searching");
    const minWait = delay(2300);
    let simRes;
    try {
      const res = await arenaAPI.simulate(myTeam.id);
      simRes = res.data;
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error en el combate');
      setPhase(null);
      setStatus(s => ({ ...s, arena_tickets: s.arena_tickets + 1 }));
      setIsSimulating(false);
      return;
    }
    await minWait;
    setOppTeam(simRes);
    setPhase("vs");
    await delay(2500);
    setMatchResult(simRes);
    setPhase("result");
    try {
      const [freshStatus, freshHistory, freshLb] = await Promise.all([
        arenaAPI.getStatus(),
        arenaAPI.history(20),
        arenaAPI.leaderboard(50)
      ]);
      setStatus(freshStatus.data);
      setHistory(freshHistory.data);
      setLeaderboard(freshLb.data);
    } catch {
      // Si falla el refresco de datos, el resultado ya se mostró — no bloquear el botón
    } finally {
      // Garantizar que el botón quede desbloqueado aunque falle el refresco post-partido
      // El modal resultado aún está abierto; handleClose() pondrá isSimulating=false también
      // pero si el usuario no llega a ver el modal, este finally lo libera igualmente.
      // Nota: NO llamamos setIsSimulating aquí porque el modal aún está abierto.
      // El reset real sigue siendo en handleClose(). Este bloque solo protege contra crashes.
    }
    // isSimulating se resetea en handleClose, cuando el usuario cierra el resultado
  }

  function handleClose() {
    setPhase(null);
    setMatchResult(null);
    setOppTeam(null);
    setIsSimulating(false); // Desbloquear botón solo cuando el usuario cierra el resultado
    setTab("history");
  }

  if (loading) {
    return (
      <AppLayout title="Arena">
        <div style={{ textAlign: 'center', padding: '80px', color: 'var(--text-secondary)', fontWeight: 600 }}>
          CARGANDO ARENA...
        </div>
      </AppLayout>
    );
  }

  const historyWins = history.filter(h => h.result === "victory").length;
  const historyLosses = history.filter(h => h.result === "defeat").length;
  const historyDraws = history.filter(h => h.result === "draw").length;

  return (
    <AppLayout title="FootArena" rightContent={<div style={{ fontSize: '1.2rem' }}>⚔️</div>}>
      <Particles />

      {phase && (
        <BattleOverlay
          phase={phase}
          myTeam={myTeam}
          oppTeam={oppTeam}
          result={matchResult}
          onClose={handleClose}
        />
      )}

      <div className="ar">
        <div className="ar-content">

          {/* ── HERO ── */}
          <div className="ar-hero">
            <img
              src="/ufl-logo.png"
              alt="Logo"
              className="ar-logo"
              onError={e => { e.target.style.display = 'none'; }}
            />
            <div className="ar-badge">⚔️ TEMPORADA 25–26 ⚔️</div>
            <h1 className="ar-title">
              FOOT<span className="ar-hl">ARENA</span>
            </h1>
            <p className="ar-sub">Elige · Combate · Domina</p>

            {/* Stats row */}
            <div className="ar-stats">
              <div className="ar-stat">
                <span className="asv sg">⚔️ <Counter value={status?.global_elo || 0} /></span>
                <span className="asl">ELO</span>
              </div>
              <div className="ar-stat">
                <span className="asv sb">🎟 <Counter value={status?.arena_tickets || 0} /></span>
                <span className="asl">Tickets</span>
              </div>
              <div className="ar-stat">
                <span className="asv sg"><Counter value={historyWins} /></span>
                <span className="asl">Victorias</span>
              </div>
              <div className="ar-stat">
                <span className="asv sc"><Counter value={historyDraws} /></span>
                <span className="asl">Empates</span>
              </div>
              <div className="ar-stat">
                <span className="asv sr"><Counter value={historyLosses} /></span>
                <span className="asl">Derrotas</span>
              </div>
            </div>
          </div>

          {/* ── TABS ── */}
          <div className="ar-tabs-wrap">
            {[["battle", "⚔️ Combate"], ["history", "📋 Historial"], ["rankings", "🏅 Rankings"]].map(([id, lbl]) => (
              <button key={id} className={`ar-tab-btn ${tab === id ? "active" : ""}`} onClick={() => setTab(id)}>{lbl}</button>
            ))}
          </div>

          {/* ── BATTLE ── */}
          {tab === "battle" && (
            <div className="ar-main">
              <p className="ar-sub2">Selecciona el equipo que representarás en el combate</p>

              {teams.length === 0 ? (
                <div className="ar-empty">
                  <span style={{ fontSize: '3rem' }}>🛡️</span>
                  <p>No tienes equipos. Únete a una liga primero.</p>
                </div>
              ) : (
                <div className="ar-teams">
                  {teams.map(t => (
                    <TiltCard
                      key={t.id}
                      className={`ar-tc ${myTeam?.id === t.id ? "sel" : ""}`}
                      onClick={() => setMyTeam(myTeam?.id === t.id ? null : t)}
                    >
                      {myTeam?.id === t.id && <div className="tc-chk">✓</div>}
                      <div className="tc-shield-area">
                        <TeamShield team={t} size={44} />
                      </div>
                      <div className="tc-name">{t.name}</div>
                      <div className="tc-league">{t.league_name || 'Liga Privada'}</div>
                      <div className="tc-num">OVR {t.overall_rating?.toFixed(0)}</div>
                    </TiltCard>
                  ))}
                </div>
              )}

              {/* VS Preview */}
              {myTeam && (
                <div className="ar-prev">
                  {/* My team */}
                  <div className="pr-t">
                    <div className="pr-shield">
                      <TeamShield team={myTeam} size={64} />
                    </div>
                    <div className="pr-name">{myTeam.name}</div>
                    <div className="pr-league">{myTeam.league_name || 'Privada'}</div>
                    <div className="pr-ovr">OVR {myTeam.overall_rating?.toFixed(0)}</div>
                  </div>

                  {/* VS divider */}
                  <div className="pr-vs-col">
                    <div className="pr-vs">VS</div>
                  </div>

                  {/* Mystery rival */}
                  <div className="pr-t">
                    <div className="mystery">
                      <div className="mq">❓</div>
                      <span className="mtxt">Rival aleatorio</span>
                      <span className="msub">Buscando oponente</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Fight button */}
              <div className="ar-cw">
                <button
                  className="ar-cbtn"
                  disabled={!myTeam || (status?.arena_tickets || 0) <= 0 || isSimulating}
                  onClick={handleFight}
                >
                  {isSimulating
                    ? "⏳ COMBATIENDO..."
                    : (status?.arena_tickets || 0) <= 0
                      ? "SIN TICKETS"
                      : !myTeam
                        ? "ELIGE UN EQUIPO"
                        : "⚔️ COMBATIR"}
                </button>
                <div className="ar-chint">
                  {(status?.arena_tickets || 0) > 0 && !isSimulating
                    ? `${status?.arena_tickets} tickets disponibles · Consume 1 ticket`
                    : isSimulating
                      ? 'Partido en curso...'
                      : 'Vuelve mañana para recuperar tickets'}
                </div>
              </div>
            </div>
          )}

          {/* ── HISTORY ── */}
          {tab === "history" && (
            <div className="ar-main">
              <p className="ar-sub2">{history.length} partidos recientes</p>
              {history.length === 0
                ? <div className="ar-empty"><p>Aún no has jugado ningún partido</p></div>
                : <div className="ar-hlist">
                  {history.map((h, i) => {
                    const eloVal = h.global_rating_change ?? 0;
                    const diff = h.result === 'draw' ? '= ELO' : `${eloVal >= 0 ? '+' : ''}${eloVal}`;
                    return (
                      <div key={h.id} className={`ar-hr ${h.result}`} style={{ animationDelay: `${i * 0.06}s` }}>
                        <div className={`hbadge ${h.result}`}>
                          {h.result === "victory" ? "VIT" : h.result === "defeat" ? "DER" : "EMP"}
                        </div>
                        <div className="hmatch">
                          <div className="hscore">{h.my_score} — {h.opponent_score}</div>
                          <div className="hmatch-txt">vs {h.opponent_name}</div>
                        </div>
                        <div className="hmeta">
                          <div className={`helo ${h.result === "victory" ? "pos" : h.result === "defeat" ? "neg" : ""}`}>{diff}</div>
                          <div className="hdate">{new Date(h.simulated_at).toLocaleDateString()}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              }
            </div>
          )}

          {/* ── RANKINGS ── */}
          {tab === "rankings" && (
            <div className="ar-main">
              <p className="ar-sub2">Top 50 jugadores globales</p>
              <div className="ar-rlist">
                <div className="ar-rhead">
                  <div />
                  <div>Jugador</div>
                  <div style={{ textAlign: "center" }}>ELO</div>
                  <div style={{ textAlign: "center" }}>V</div>
                  <div style={{ textAlign: "center" }}>E</div>
                  <div style={{ textAlign: "center" }}>D</div>
                </div>
                {leaderboard.map((r, i) => {
                  const isMe = teams.some(t => t.id === r.team_id);
                  return (
                    <div key={r.team_id} className={`ar-rrow${isMe ? " me" : ""}`} style={{ animationDelay: `${i * 0.05}s` }}>
                      <div className={`rkn${r.rank === 1 ? " g1" : r.rank === 2 ? " g2" : r.rank === 3 ? " g3" : ""}`}>
                        {r.rank === 1 ? "🥇" : r.rank === 2 ? "🥈" : r.rank === 3 ? "🥉" : `#${r.rank}`}
                      </div>
                      <div className="rknm">
                        {r.team_name} {isMe && <span style={{ color: 'var(--gold)' }}>(Tú)</span>}
                      </div>
                      <div className="rkelo">{r.arena_rating}</div>
                      <div className="rkst" style={{ color: "var(--gold)" }}>{r.arena_wins}</div>
                      <div className="rkst" style={{ color: "var(--text-secondary)" }}>{r.arena_draws}</div>
                      <div className="rkst" style={{ color: "var(--danger)" }}>{r.arena_losses}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

        </div>
      </div>
    </AppLayout>
  );
}
