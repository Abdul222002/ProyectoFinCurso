import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { arenaAPI, teamsAPI } from '../services/endpoints';
import { toast } from 'sonner';
import './ArenaPage.css';

const delay = ms => new Promise(r => setTimeout(r, ms));

// ── PARTICLES CANVAS ──────────────────────────────────────────────────────────
function Particles() {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let W = canvas.width = window.innerWidth;
    let H = canvas.height = window.innerHeight;
    const pts = Array.from({length:80}, () => ({
      x: Math.random()*W, y: Math.random()*H,
      r: Math.random()*1.4+0.3,
      vx: (Math.random()-0.5)*0.25,
      vy: -Math.random()*0.35-0.08,
      phase: Math.random()*Math.PI*2,
    }));
    let raf;
    const draw = () => {
      ctx.clearRect(0,0,W,H);
      const t = performance.now()/1000;
      pts.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.y < -4) { p.y = H+4; p.x = Math.random()*W; }
        const a = (Math.sin(t+p.phase)+1)/2*0.45+0.05;
        ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
        ctx.fillStyle = `rgba(180,255,200,${a})`; ctx.fill();
      });
      raf = requestAnimationFrame(draw);
    };
    draw();
    const resize = () => { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; };
    window.addEventListener("resize", resize);
    return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", resize); };
  }, []);
  return <canvas ref={ref} style={{position:"fixed",inset:0,zIndex:0,pointerEvents:"none",opacity:0.55}}/>;
}

// ── 3D TILT CARD ──────────────────────────────────────────────────────────────
function TiltCard({ children, className, onClick }) {
  const ref = useRef(null);
  const onMove = useCallback(e => {
    if (!ref.current) return;
    const r = ref.current.getBoundingClientRect();
    const x = ((e.clientX-r.left)/r.width -0.5)*20;
    const y = ((e.clientY-r.top) /r.height-0.5)*-20;
    ref.current.style.transform = `perspective(700px) rotateX(${y}deg) rotateY(${x}deg) translateY(-6px) scale(1.04)`;
    ref.current.style.setProperty("--gx", `${((e.clientX-r.left)/r.width)*100}%`);
    ref.current.style.setProperty("--gy", `${((e.clientY-r.top)/r.height)*100}%`);
  }, []);
  const onLeave = useCallback(() => {
    if (!ref.current) return;
    ref.current.style.transform = "";
  }, []);
  return (
    <div ref={ref} className={className} onClick={onClick}
      onMouseMove={onMove} onMouseLeave={onLeave}
      style={{transition:"transform 0.18s ease", transformStyle:"preserve-3d", willChange:"transform"}}>
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
      const p = Math.min(1,(t-t0)/600);
      const ease = p<0.5?2*p*p:-1+(4-2*p)*p;
      setN(Math.round(s+(e-s)*ease));
      if (p<1) requestAnimationFrame(tick); else prev.current = e;
    };
    requestAnimationFrame(tick);
  }, [value]);
  return <>{n.toLocaleString('es-ES')}</>;
}

// ── BATTLE OVERLAY ────────────────────────────────────────────────────────────
function BattleOverlay({ phase, myTeam, oppTeam, result, onClose }) {
  const [tick, setTick] = useState(0);
  useEffect(() => { const id = setInterval(()=>setTick(t=>t+1),90); return ()=>clearInterval(id); }, []);
  const dots = ["", ".", "..", "..."][tick % 4];

  if (phase === "searching") return (
    <div className="ov">
      <div className="ov-scan"/>
      {Array.from({length:18},(_,i)=>(
        <div key={i} className="ov-spark" style={{
          left:`${5+Math.random()*90}%`,
          animationDelay:`${i*0.18}s`,
          animationDuration:`${1.4+Math.random()*1.2}s`
        }}/>
      ))}
      <div className="ov-r r1"/><div className="ov-r r2"/><div className="ov-r r3"/><div className="ov-r r4"/>
      <div className="ov-sweep"/>
      <div className="ov-dot"/>
      <p className="ov-stxt">BUSCANDO RIVAL{dots}</p>
      <p className="ov-ssub">Emparejando por ELO · Por favor espera</p>
    </div>
  );

  if (phase === "vs") return (
    <div className="ov">
      <div className="ov-scan"/>
      <div className="ov-vs-wrap">
        <div className="ov-vs-side left">
          <div className="ov-vs-glow gl"/>
          <div className="ov-vs-emoji">🛡️</div>
          <div className="ov-vs-name">{myTeam.name}</div>
          <div className="ov-vs-league">{myTeam.league_name || 'Liga Privada'}</div>
          <div className="ov-vs-ovr" style={{color:"var(--acc)"}}>OVR <strong>{myTeam.overall_rating?.toFixed(0) || myTeam.ovr}</strong></div>
        </div>
        <div className="ov-vs-mid">
          <div className="ov-bolt">⚡</div>
          <div className="ov-vs-label">VS</div>
          <div className="ov-bolt b2">⚡</div>
        </div>
        <div className="ov-vs-side right">
          <div className="ov-vs-glow gr"/>
          <div className="ov-vs-emoji">⚔️</div>
          <div className="ov-vs-name">{oppTeam?.name || oppTeam?.team2_name || 'Desconocido'}</div>
          <div className="ov-vs-league">{oppTeam?.league_name || 'Rival Competitivo'}</div>
          <div className="ov-vs-ovr" style={{color:"var(--red)"}}>OVR <strong>{oppTeam?.overall_rating?.toFixed(0) || oppTeam?.team2_ovr?.toFixed(0) || oppTeam?.ovr}</strong></div>
        </div>
      </div>
      <p className="ov-ssub" style={{marginTop:48, animation:"blinkAnim 0.7s ease-in-out infinite alternate"}}>⚽ Partido iniciando...</p>
    </div>
  );

  if (phase === "result" && result) {
    const res = result.result; 
    const myGoals = result.team1_score;
    const oppGoals = result.team2_score;
    const eloDelta = result.global_rating_change;
    const coins = result.coins_rewarded;
    
    const cfg = {
      victory:{label:"¡VICTORIA!",  sub:"Aplastaste al rival",      rc:"#FFD700",rg:"rgba(255,215,0,0.2)"},
      defeat: {label:"DERROTA",     sub:"El rival fue superior",    rc:"#FF3B3B",rg:"rgba(255,59,59,0.15)"},
      draw:   {label:"EMPATE",      sub:"Un partido muy igualado",  rc:"#94a3b8",rg:"transparent"},
    }[res] || {label:"FINALIZADO", sub:"Partido completado", rc:"#94a3b8", rg:"transparent"};
    
    return (
      <div className="ov">
        <div className="ov-scan"/>
        <div className="ov-rcard" style={{"--rc":cfg.rc,"--rg":cfg.rg}}>
          <div className="ov-rshim"/>
          <div className="ov-rglow"/>
          <div className="ov-rtitle" style={{color:cfg.rc}}>{cfg.label}</div>
          <div className="ov-rsub">{cfg.sub}</div>
          <div className="ov-score">
            <div className="ov-snum my">{myGoals}</div>
            <div className="ov-sdash">—</div>
            <div className="ov-snum op">{oppGoals}</div>
          </div>
          <div className="ov-rmatch">{myTeam.name} <span>vs</span> {oppTeam?.name || oppTeam?.team2_name}</div>
          <div className="ov-rewards">
            {[
              {icon:"📊",val:`${eloDelta>=0?"+":""}${eloDelta}`,lbl:"ELO",col:eloDelta>=0?"var(--acc)":"var(--red)",d:"0.18s"},
              {icon:"🪙",val:`+${coins?.toLocaleString('es-ES') || 0}`,lbl:"Monedas",col:"var(--gold)",d:"0.34s"},
              {icon:res==="victory"?"🏆":res==="draw"?"🤝":"💀",val:res==="victory"?"Top 1%":"Sigue!", lbl:"Rango",col:"var(--text)",d:"0.50s"},
            ].map((rw,i)=>(
              <div key={i} className="ov-rw" style={{"--d":rw.d}}>
                <div className="ov-rw-icon">{rw.icon}</div>
                <div className="ov-rw-val" style={{color:rw.col}}>{rw.val}</div>
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
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("battle");
  const [phase, setPhase] = useState(null);
  const [matchResult, setMatchResult] = useState(null);

  const [teams, setTeams] = useState([]);
  const [history, setHistory] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [status, setStatus] = useState(null);

  const [myTeam, setMyTeam] = useState(null);
  const [oppTeam, setOppTeam] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

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
    if (!myTeam || status?.arena_tickets <= 0) return;
    
    setStatus(s => ({...s, arena_tickets: s.arena_tickets - 1}));
    setOppTeam(null);
    setPhase("searching");
    
    const minWait = delay(2300);
    
    let simRes;
    try {
      const res = await arenaAPI.simulate(myTeam.id);
      simRes = res.data;
    } catch(err) {
      toast.error(err.response?.data?.detail || 'Error en el combate');
      setPhase(null);
      setStatus(s => ({...s, arena_tickets: s.arena_tickets + 1}));
      return;
    }

    await minWait;
    
    setOppTeam(simRes);
    setPhase("vs");
    await delay(2500);
    setMatchResult(simRes);
    setPhase("result");
    
    const [freshStatus, freshHistory, freshLb] = await Promise.all([
      arenaAPI.getStatus(),
      arenaAPI.history(20),
      arenaAPI.leaderboard(50)
    ]);
    setStatus(freshStatus.data);
    setHistory(freshHistory.data);
    setLeaderboard(freshLb.data);
  }

  function handleClose() {
    setPhase(null); 
    setMatchResult(null); 
    setOppTeam(null); 
    setTab("history");
  }

  if (loading) {
    return (
      <div className="ar" style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <div style={{color: 'var(--acc)', fontFamily: "'Orbitron', monospace", letterSpacing: '4px', animation: 'blinkAnim 1s ease-in-out infinite alternate'}}>
          CARGANDO ARENA...
        </div>
        <style>{`.ar{min-height:100vh;background:#050d07}@keyframes blinkAnim{from{opacity:0.3}to{opacity:1}}`}</style>
      </div>
    );
  }

  const historyWins = history.filter(h => h.result === "victory").length;
  const historyLosses = history.filter(h => h.result === "defeat").length;
  const historyDraws = history.filter(h => h.result === "draw").length;

  return (
    <>
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
        <div className="ar-grid" />

        <button className="back-btn" onClick={() => navigate('/dashboard')}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M9 2L4 7L9 12" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          VOLVER
        </button>

        <div className="ar-hero">
          <div className="ar-badge">TEMPORADA 2025–26 · JORNADA GLOBAL</div>
          <div className="ar-title">
            FOOT<span className="ar-hl" data-t="ARENA">ARENA</span>
          </div>
          <div className="ar-sub">Elige · Combate · Domina</div>

          <div className="ar-stats">
            {[
              { l:"ELO",      v:<Counter value={status?.global_elo || 0}/>,     cls:"sg", pre:"⚡ " },
              { l:"Tickets",  v:<Counter value={status?.arena_tickets || 0}/>, cls:"sb", pre:"🎟 " },
              { l:"V",v:<Counter value={historyWins}/>,    cls:"sc", pre:"" },
              { l:"E", v:<Counter value={historyDraws}/>,    cls:"sg", pre:"" },
              { l:"D", v:<Counter value={historyLosses}/>,  cls:"sr", pre:"" },
            ].map((s, i) => (
              <div key={i} className="ar-stat">
                <span className="asl">{s.l}</span>
                <span className={`asv ${s.cls}`}>{s.pre}{s.v}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="ar-tabs">
          {[["battle","⚔️ Combate"],["history","📋 Historial"],["rankings","🏅 Rankings"]].map(([id,lbl])=>(
            <button key={id} className={`ar-tab${tab===id?" on":""}`} onClick={()=>setTab(id)}>{lbl}</button>
          ))}
        </div>

        <div className="ar-content">

          {tab === "battle" && <>
            <div className="ar-ttl">Elige tu equipo</div>
            <div className="ar-sub2">Selecciona el equipo que representarás en el combate</div>

            {teams.length === 0 ? (
                <div className="ar-empty">
                    <div className="ar-empty-icon">🛡️</div>
                    <div className="ar-empty-txt">No tienes equipos. Únete a una liga primero.</div>
                </div>
            ) : (
                <div className="ar-teams">
                {teams.map(t => (
                    <TiltCard
                    key={t.id}
                    className={`ar-tc${myTeam?.id===t.id?" sel":""}`}
                    onClick={() => setMyTeam(myTeam?.id===t.id ? null : t)}
                    >
                    <div className="tc-chk">✓</div>
                    <span className="tc-emoji">🛡️</span>
                    <div className="tc-league">{t.league_name || 'Liga Privada'}</div>
                    <div className="tc-name" style={{fontSize: '1.2rem', marginBottom: '8px'}}>{t.name}</div>
                    <div className="tc-orow">
                        <div className="tc-bwrap"><div className="tc-bar" style={{width:`${Math.max(0, (t.overall_rating-60)*2.5)}%`}}/></div>
                        <span className="tc-num">{t.overall_rating?.toFixed(0)}</span>
                    </div>
                    </TiltCard>
                ))}
                </div>
            )}

            {myTeam && <>
              <hr className="ar-div"/>
              <div className="ar-prev">
                <div className="pr-t">
                  <span className="pr-emoji">🛡️</span>
                  <div className="pr-name">{myTeam.name}</div>
                  <div className="pr-league">{myTeam.league_name || 'Privada'}</div>
                  <div className="pr-ovr" style={{color:"var(--acc)"}}>OVR {myTeam.overall_rating?.toFixed(0)}</div>
                </div>
                <div className="pr-vs-col">
                  <div className="pr-vs-line"/>
                  <div className="pr-vs">VS</div>
                  <div className="pr-vs-line"/>
                </div>
                <div className="pr-t r">
                  <div className="mystery">
                    <div className="mq">❓</div>
                    <span className="mtxt">Rival aleatorio</span>
                    <span className="msub">Se revela al combatir</span>
                  </div>
                </div>
              </div>
            </>}

            <div className="ar-cw">
              <button className="ar-cbtn" disabled={!myTeam || (status?.arena_tickets || 0)<=0} onClick={handleFight}>
                {(status?.arena_tickets || 0)<=0 ? "SIN TICKETS" : !myTeam ? "ELIGE TU EQUIPO" : "⚡ COMBATIR"}
              </button>
              <div className="ar-chint">
                {(status?.arena_tickets || 0)>0
                  ? `${status?.arena_tickets} tickets disponibles · cada combate consume 1 ticket`
                  : "Vuelve mañana para recuperar tickets"}
              </div>
            </div>
          </>}

          {tab === "history" && <>
            <div className="ar-ttl">Historial de partidos</div>
            <div className="ar-sub2">{history.length} partidos recientes</div>
            {history.length === 0
              ? <div className="ar-empty"><div className="ar-empty-icon">📋</div><div className="ar-empty-txt">Aún no has jugado ningún partido</div></div>
              : <div className="ar-hlist">
                  {history.map((h,i) => {
                      const diff = h.result === 'victory' ? '+ ELO' : (h.result === 'defeat' ? '- ELO' : '= ELO');
                      return (
                    <div key={h.id} className={`ar-hr ${h.result}`} style={{animationDelay:`${i*0.06}s`}}>
                      <div className={`hbadge ${h.result}`}>
                        {h.result==="victory"?"VICTORIA":h.result==="defeat"?"DERROTA":"EMPATE"}
                      </div>
                      <div className="hmatch">
                        <div className="hscore">{h.my_score} — {h.opponent_score}</div>
                        <span style={{color:"var(--muted)"}}>vs {h.opponent_name}</span>
                      </div>
                      <div className="hmeta">
                        <div className={`helo ${h.result==="victory"?"pos":h.result==="defeat"?"neg":""}`}>{diff}</div>
                        <div className="hdate">{new Date(h.simulated_at).toLocaleString('es-ES', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}</div>
                      </div>
                    </div>
                  )})}
                </div>
            }
          </>}

          {tab === "rankings" && <>
            <div className="ar-ttl">Clasificación global</div>
            <div className="ar-sub2">Top 50 jugadores · Temporada 2025–26</div>
            <div className="ar-rlist">
              <div className="ar-rhead">
                <div/><div>Jugador</div>
                <div style={{textAlign:"center"}}>ELO</div>
                <div style={{textAlign:"center"}}>V</div>
                <div style={{textAlign:"center"}}>E</div>
                <div style={{textAlign:"center"}}>D</div>
              </div>
              {leaderboard.map((r,i) => {
                  const isMe = teams.some(t => t.id === r.team_id);
                  return (
                <div key={r.team_id} className={`ar-rrow${isMe?" me":""}`} style={{animationDelay:`${i*0.07}s`}}>
                  <div className={`rkn${r.rank===1?" g1":r.rank===2?" g2":r.rank===3?" g3":""}`}>
                    {r.rank===1?"🥇":r.rank===2?"🥈":r.rank===3?"🥉":`#${r.rank}`}
                  </div>
                  <div className={`rknm${isMe?" me":""}`}>{r.team_name} {isMe?"👈":""}</div>
                  <div className="rkelo">{r.arena_rating}</div>
                  <div className="rkst" style={{color:"var(--acc)"}}>{r.arena_wins}</div>
                  <div className="rkst" style={{color:"var(--gold)"}}>{r.arena_draws}</div>
                  <div className="rkst" style={{color:"var(--red)"}}>{r.arena_losses}</div>
                </div>
              )})}
            </div>
          </>}

        </div>
      </div>
    </>
  );
}
