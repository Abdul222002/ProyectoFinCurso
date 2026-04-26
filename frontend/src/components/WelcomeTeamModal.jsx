import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { resolvePlayerImageUrl } from '../utils/mediaUrl';
import './WelcomeTeamModal.css';

/* ─────────────────────────────────────────────
   HELPERS
───────────────────────────────────────────── */
const RARITY_META = {
  legend: { label: '⭐ LEYENDA', cls: 'wtm-rarity-legend', holo: true, dot: 'legend' },
  gold:   { label: '✦ ORO',     cls: 'wtm-rarity-gold',   holo: true,  dot: 'gold'   },
  silver: { label: 'PLATA',     cls: 'wtm-rarity-silver', holo: false, dot: 'silver' },
  bronze: { label: 'BRONCE',    cls: 'wtm-rarity-bronze', holo: false, dot: 'bronze' },
  common: { label: 'COMÚN',     cls: 'wtm-rarity-common', holo: false, dot: 'common' },
};
function meta(rarity) {
  return RARITY_META[rarity?.toLowerCase()] || RARITY_META.common;
}

/* ─────────────────────────────────────────────
   PARTICLES
───────────────────────────────────────────── */
function Particles() {
  const COLORS = ['#c9a84c', '#fef08a', '#f0abfc', '#60a5fa', '#34d399'];
  const items = Array.from({ length: 28 }, (_, i) => ({
    id: i,
    tx: `${(Math.random() - 0.5) * 600}px`,
    ty: `${(Math.random() - 0.5) * 600}px`,
    r: `${Math.random() * 720}deg`,
    delay: `${(Math.random() * 0.12).toFixed(3)}s`,
    size: 5 + Math.random() * 12,
    color: COLORS[i % 5],
    shape: i % 3,
  }));
  return (
    <div className="wtm-particles">
      {items.map(p => (
        <div key={p.id} className="wtm-particle" style={{
          width: p.size,
          height: p.shape === 1 ? p.size * 2.5 : p.size,
          background: p.color,
          boxShadow: `0 0 ${p.size}px ${p.color}`,
          borderRadius: p.shape === 0 ? '50%' : '2px',
          clipPath: p.shape === 2 ? 'polygon(50% 0%,0% 100%,100% 100%)' : undefined,
          '--tx': p.tx, '--ty': p.ty, '--r': p.r,
          animationDelay: p.delay,
        }} />
      ))}
    </div>
  );
}

/* ─────────────────────────────────────────────
   SINGLE CARD REVEAL
   Key trick: key={cardId} forces unmount/remount
   when card changes → eliminates the flip-back glitch
───────────────────────────────────────────── */
function RevealCard({ card, isFlipped, onClick }) {
  const [mousePos, setMousePos] = useState({ x: 0.5, y: 0.5 });
  const ref = useRef(null);
  const m = meta(card.base_rarity);

  const tiltX = isFlipped ? (mousePos.y - 0.5) * 12 : 0;
  const tiltY = isFlipped ? (mousePos.x - 0.5) * -12 : 0;

  const imgSrc = resolvePlayerImageUrl(card.image_url, card.player_name);

  return (
    <div className="wtm-card-area">
      <div
        ref={ref}
        className={`wtm-card-wrapper${isFlipped ? ' is-flipped' : ''}`}
        onClick={onClick}
        onMouseMove={e => {
          if (!isFlipped || !ref.current) return;
          const r = ref.current.getBoundingClientRect();
          setMousePos({ x: (e.clientX - r.left) / r.width, y: (e.clientY - r.top) / r.height });
        }}
        onMouseLeave={() => setMousePos({ x: 0.5, y: 0.5 })}
      >
        <div
          className="wtm-card-inner"
          style={isFlipped ? { transform: `rotateX(${tiltX}deg) rotateY(${180 + tiltY}deg)` } : {}}
        >
          {/* BACK */}
          <div className="wtm-card-back">
            <div className="wtm-card-back__pattern" />
            <div className="wtm-card-back__inner">
              <div className="wtm-card-back__logo">UFL</div>
            </div>
            <div className="wtm-card-back__tap">TOCA PARA REVELAR</div>
          </div>

          {/* FRONT */}
          <div className={`wtm-card-front ${m.cls}`}>
            {m.holo && (
              <div className="wtm-card-holo" style={{
                background: `radial-gradient(ellipse at ${mousePos.x * 100}% ${mousePos.y * 100}%, rgba(255,255,255,0.22), transparent 65%)`,
              }} />
            )}
            {card.is_in_lineup && <div className="wtm-lineup-badge">TITULAR</div>}
            <div className="wtm-card-rarity-banner">
              <span className="wtm-card-rarity-label">{m.label}</span>
            </div>
            <div className="wtm-card-ovr">{Math.round(card.overall_rating)}</div>
            <div className="wtm-card-image-area">
              <img
                src={imgSrc}
                alt={card.player_name}
                onError={e => { 
                  e.target.onerror = null;
                  e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(card.player_name || 'UFL')}&background=152e20&color=25f478&bold=true`; 
                }}
              />
            </div>
            <div className="wtm-card-info">
              <div className="wtm-card-name">{card.player_name}</div>
              <div className="wtm-card-pos">{card.position}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   MINI CARD (summary grid)
───────────────────────────────────────────── */
function MiniCard({ card, idx }) {
  const m = meta(card.base_rarity);
  const imgSrc = resolvePlayerImageUrl(card.image_url);

  return (
    <div className={`wtm-mini-card${card.is_in_lineup ? ' starter' : ''}`} style={{ animationDelay: `${idx * 0.04}s` }}>
      <div className={`wtm-mini-rarity-dot ${m.dot}`} />
      <img
        src={imgSrc}
        alt={card.player_name}
        onError={e => { 
          e.target.onerror = null;
          e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(card.player_name || 'UFL')}&background=152e20&color=25f478&bold=true`; 
        }}
      />
      <div className="wtm-mini-card__ovr">{Math.round(card.overall_rating)}</div>
      <div className="wtm-mini-card__name">{card.player_name}</div>
      <div className="wtm-mini-card__pos">{card.position}</div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   MAIN COMPONENT
───────────────────────────────────────────── */
export default function WelcomeTeamModal({ leagueName, leagueId, players = [], onClose = () => { } }) {
  const navigate = useNavigate();

  // Phase: 'intro' → 'flash' → 'reveal' → 'summary'
  const [phase, setPhase] = useState('intro');
  const [currentIdx, setCurrentIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [showParticles, setShowParticles] = useState(false);
  // Separate key to force full remount of RevealCard when card changes
  const [cardKey, setCardKey] = useState(0);

  const card = players[currentIdx];
  const rayOpacity = phase === 'intro' ? 0.08 : phase === 'flash' ? 0.5 : 0.05;

  /* Launch reveal sequence */
  const handleStart = () => {
    setPhase('flash');
    setShowParticles(true);
    setTimeout(() => {
      setShowParticles(false);
      setPhase('reveal');
      setCurrentIdx(0);
      setFlipped(false);
      setCardKey(0);
    }, 900);
  };

  /* Flip current card */
  const handleFlip = () => {
    if (flipped) return;
    setFlipped(true);
  };

  /* Advance to next card or finish */
  const handleNext = () => {
    if (!flipped) {
      setFlipped(true);
      setTimeout(() => advanceOrFinish(), 700);
      return;
    }
    advanceOrFinish();
  };

  const advanceOrFinish = () => {
    const next = currentIdx + 1;
    if (next >= players.length) {
      setPhase('summary');
    } else {
      // Increment key FIRST so React unmounts old RevealCard before showing new one
      setCardKey(k => k + 1);
      setCurrentIdx(next);
      setFlipped(false);
    }
  };

  const handleSkip = () => setPhase('summary');

  /* Close + navigate to team management */
  const handleGoToTeam = () => {
    const path = leagueId ? `/team?league_id=${leagueId}` : '/team';
    // Navigate first, then close — avoids navigating from a unmounted component
    navigate(path);
    onClose();
  };

  return (
    <div className="wtm-overlay">
      {/* Rotating rays */}
      <div className="wtm-rays" style={{ opacity: rayOpacity }}>
        <div className="wtm-rays__disk" />
      </div>

      {phase === 'flash' && <div className="wtm-flash" />}
      {showParticles && <Particles />}

      {/* ─── INTRO ─── */}
      {phase === 'intro' && (
        <div className="wtm-intro">
          <div className="wtm-intro__trophy">🏆</div>
          <h1 className="wtm-intro__title">¡Bienvenido a<br />{leagueName}!</h1>
          <p className="wtm-intro__subtitle">
            Te hemos asignado {players.length} jugadores.<br />
            ¡Descubre tu nueva plantilla!
          </p>
          <button className="wtm-intro__btn" onClick={handleStart}>
            🃏 VER MI PLANTILLA
          </button>
        </div>
      )}

      {/* ─── REVEAL ONE BY ONE ─── */}
      {phase === 'reveal' && card && (
        <div className="wtm-reveal-stage">
          <div className="wtm-counter">
            <span className="wtm-counter__text">{currentIdx + 1} / {players.length}</span>
            <div className="wtm-counter__dots">
              {players.map((_, i) => (
                <div key={i} className={`wtm-counter__dot${i <= currentIdx ? ' revealed' : ''}`} />
              ))}
            </div>
          </div>

          {/* key prop forces fresh mount → no flip-back glitch */}
          <RevealCard
            key={cardKey}
            card={card}
            isFlipped={flipped}
            onClick={handleFlip}
          />

          <div className="wtm-reveal-controls">
            {!flipped ? (
              <div className="wtm-reveal-hint">👆 TOCA LA CARTA PARA REVELAR</div>
            ) : (
              <button
                className="wtm-intro__btn"
                style={{ padding: '10px 32px', fontSize: '0.9rem' }}
                onClick={handleNext}
              >
                {currentIdx + 1 < players.length ? 'SIGUIENTE CARTA →' : 'VER MI PLANTILLA →'}
              </button>
            )}
            <button className="wtm-reveal-skip" onClick={handleSkip}>
              Saltar todo
            </button>
          </div>
        </div>
      )}

      {/* ─── SUMMARY ─── */}
      {phase === 'summary' && (
        <div className="wtm-summary">
          <h2 className="wtm-summary__title">¡Tu Plantilla Lista!</h2>
          <p className="wtm-summary__subtitle">
            {players.filter(p => p.is_in_lineup).length} titulares · {players.filter(p => !p.is_in_lineup).length} suplentes
          </p>

          <div className="wtm-summary-grid">
            {players.map((p, i) => (
              <MiniCard key={p.id} card={p} idx={i} />
            ))}
          </div>

          <button className="wtm-summary__cta" onClick={handleGoToTeam}>
            ⚽ VER MI EQUIPO
          </button>
        </div>
      )}
    </div>
  );
}
