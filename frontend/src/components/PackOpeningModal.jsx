import React, { useState, useRef } from 'react';
import { resolvePlayerImageUrl } from '../utils/mediaUrl';
import './PackOpeningModal.css';

/* ─────────────────────────────────────────────
   RARITY CONFIG
───────────────────────────────────────────── */
const RARITY_MAP = {
    legend: { label: '⭐ LEYENDA', cls: 'rarity-legend', holo: true },
    gold: { label: '✦ ORO', cls: 'rarity-gold', holo: true },
    silver: { label: 'PLATA', cls: 'rarity-silver', holo: false },
    bronze: { label: 'BRONCE', cls: 'rarity-bronze', holo: false },
    common: { label: 'COMÚN', cls: 'rarity-common', holo: false },
};

function getRarityInfo(rarity) {
    return RARITY_MAP[rarity?.toLowerCase()] || RARITY_MAP.common;
}

/* ─────────────────────────────────────────────
   PACK SVG
───────────────────────────────────────────── */
function PackSVG({ dragProgress, isOpening }) {
    const tearY = 110;
    const flapDeg = dragProgress * 38;

    return (
        <svg
            viewBox="0 0 280 400"
            width="280"
            height="400"
            style={{ overflow: 'visible', filter: 'drop-shadow(0 20px 40px rgba(0,0,0,0.8))' }}
        >
            <defs>
                <linearGradient id="pg-body" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#1e1048" />
                    <stop offset="40%" stopColor="#2e1065" />
                    <stop offset="100%" stopColor="#0f0a20" />
                </linearGradient>
                <linearGradient id="pg-flap" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#3b1c7a" />
                    <stop offset="100%" stopColor="#1a0a3a" />
                </linearGradient>
                <linearGradient id="pg-shine" x1="0" y1="0" x2="0.3" y2="1">
                    <stop offset="0%" stopColor="rgba(255,255,255,0.15)" />
                    <stop offset="100%" stopColor="rgba(255,255,255,0)" />
                </linearGradient>
                <linearGradient id="pg-tear" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#a78bfa" />
                    <stop offset="50%" stopColor="#f0abfc" />
                    <stop offset="100%" stopColor="#a78bfa" />
                </linearGradient>
                <clipPath id="pg-clip-body">
                    <rect x="0" y={tearY} width="280" height={400 - tearY} rx="4" />
                </clipPath>
                <clipPath id="pg-clip-flap">
                    <rect x="0" y="0" width="280" height={tearY + 4} rx="4" />
                </clipPath>
            </defs>

            {/* BODY */}
            <g clipPath="url(#pg-clip-body)">
                <image href="/images/pack-cover.png" x="0" y="0" width="280" height="400" preserveAspectRatio="xMidYMid slice" />
            </g>

            {/* FLAP */}
            <g
                clipPath="url(#pg-clip-flap)"
                style={{
                    transformOrigin: '140px 0px',
                    transform: `perspective(800px) rotateX(${-flapDeg}deg)`,
                    transition: dragProgress > 0 ? 'none' : 'transform 0.4s ease',
                }}
            >
                <image href="/images/pack-cover.png" x="0" y="0" width="280" height="400" preserveAspectRatio="xMidYMid slice" />
            </g>

            {/* TEAR LINE */}
            {isOpening && (
                <path
                    d={`M0,${tearY} Q35,${tearY - 5} 70,${tearY + 3} Q105,${tearY - 3} 140,${tearY + 4} Q175,${tearY - 3} 210,${tearY + 2} Q245,${tearY - 4} 280,${tearY}`}
                    fill="none"
                    stroke="url(#pg-tear)"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeDasharray="300"
                    strokeDashoffset="0"
                    style={{ animation: 'tearLine 0.4s ease-out forwards', filter: 'blur(0.5px)' }}
                />
            )}

            {/* BORDER */}
            <rect x="0.5" y="0.5" width="279" height="399" rx="11.5" fill="none" stroke="rgba(139,92,246,0.5)" strokeWidth="1" />
        </svg>
    );
}

/* ─────────────────────────────────────────────
   PARTICLES
───────────────────────────────────────────── */
function Particles() {
    const COLORS = ['#a78bfa', '#f0abfc', '#60a5fa', '#fcd34d', '#34d399'];
    const items = Array.from({ length: 32 }, (_, i) => ({
        id: i,
        tx: `${(Math.random() - 0.5) * 700}px`,
        ty: `${(Math.random() - 0.5) * 700}px`,
        r: `${Math.random() * 720}deg`,
        delay: `${(Math.random() * 0.15).toFixed(3)}s`,
        size: 6 + Math.random() * 14,
        color: COLORS[i % 5],
        shape: i % 3,
    }));

    return (
        <div className="pack-particles">
            {items.map(p => (
                <div
                    key={p.id}
                    className="pack-particle"
                    style={{
                        width: p.size,
                        height: p.shape === 1 ? p.size * 2.5 : p.size,
                        background: p.color,
                        boxShadow: `0 0 ${p.size}px ${p.color}`,
                        borderRadius: p.shape === 0 ? '50%' : '2px',
                        clipPath: p.shape === 2 ? 'polygon(50% 0%,0% 100%,100% 100%)' : undefined,
                        '--tx': p.tx,
                        '--ty': p.ty,
                        '--r': p.r,
                        animationDelay: p.delay,
                    }}
                />
            ))}
        </div>
    );
}

/* ─────────────────────────────────────────────
   SINGLE CARD REVEAL
───────────────────────────────────────────── */
function RevealCard({ card, isFlipped, onClick }) {
    // Add safety check in case card is null/undefined
    if (!card) return null;

    const info = getRarityInfo(card.base_rarity);
    const [mousePos, setMousePos] = useState({ x: 0.5, y: 0.5 });
    const cardRef = useRef(null);

    const handleMouseMove = (e) => {
        if (!isFlipped || !cardRef.current) return;
        const rect = cardRef.current.getBoundingClientRect();
        setMousePos({
            x: (e.clientX - rect.left) / rect.width,
            y: (e.clientY - rect.top) / rect.height,
        });
    };

    const tiltX = isFlipped ? (mousePos.y - 0.5) * 14 : 0;
    const tiltY = isFlipped ? (mousePos.x - 0.5) * -14 : 0;

    return (
        <div className="reveal-card-area">
            <div
                ref={cardRef}
                className={`reveal-card-wrapper${isFlipped ? ' is-flipped' : ''}`}
                onClick={onClick}
                onMouseMove={handleMouseMove}
                onMouseLeave={() => setMousePos({ x: 0.5, y: 0.5 })}
            >
                <div
                    className="reveal-card-inner"
                    style={isFlipped
                        ? { transform: `rotateX(${tiltX}deg) rotateY(${180 + tiltY}deg)` }
                        : {}
                    }
                >
                    {/* BACK */}
                    <div className="reveal-card-back">
                        <div className="card-back__pattern" />
                        <div className="card-back__inner">
                            <div className="card-back__logo">SPFL</div>
                            <div className="card-back__divider" />
                        </div>
                        {!isFlipped && <div className="card-back__tap">TAP TO REVEAL</div>}
                    </div>

                    {/* FRONT */}
                    <div className={`reveal-card-front ${info.cls}`}>
                        {info.holo && (
                            <div
                                className="card-holo"
                                style={{
                                    background: `radial-gradient(
                    ellipse at ${mousePos.x * 100}% ${mousePos.y * 100}%,
                    rgba(255,255,255,0.25), transparent 65%
                  )`,
                                }}
                            />
                        )}

                        <div className="card-rarity-banner">
                            <span className="card-rarity-label">{info.label}</span>
                        </div>

                        <div className="card-ovr">{card.overall_rating}</div>

                        <div
                            className="card-image-area"
                            style={{
                                background: 'radial-gradient(ellipse at 50% 90%, rgba(255,255,255,0.1), transparent 70%)',
                            }}
                        >
                            <img
                                src={resolvePlayerImageUrl(card.image_url)}
                                alt={card.player_name}
                                loading="lazy"
                                decoding="async"
                                onError={(e) => { e.target.src = '/images/placeholder.png'; }}
                            />
                        </div>

                        <div className="card-info">
                            <div className="card-name">{card.player_name}</div>
                            <div className="card-position">{card.position}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

/* ─────────────────────────────────────────────
   MAIN COMPONENT
   Props:
     cards          - Array of cards from the backend
     remainingCoins – número de monedas restantes
     onClose        – callback al pulsar Continuar
───────────────────────────────────────────── */
export default function PackOpeningModal({ cards, remainingCoins = 0, onClose = () => { } }) {
    // Extract the first card since we only get 1 card per pack now
    const card = cards && cards.length > 0 ? cards[0] : null;

    const [phase, setPhase] = useState('idle');       // 'idle' | 'opening' | 'explode' | 'reveal'
    const [dragProgress, setDragProgress] = useState(0);
    const [revealed, setRevealed] = useState(false);
    const dragRef = useRef({ active: false, startX: 0 });

    const triggerOpen = () => {
        if (phase !== 'idle' && phase !== 'opening') return;
        setPhase('opening');
        setTimeout(() => {
            setPhase('explode');
            setTimeout(() => setPhase('reveal'), 900);
        }, 420);
    };

    const handlePointerDown = (e) => {
        if (phase !== 'idle') return;
        dragRef.current = { active: true, startX: e.clientX ?? e.touches?.[0]?.clientX };
        e.currentTarget.setPointerCapture?.(e.pointerId);
    };

    const handlePointerMove = (e) => {
        if (!dragRef.current.active || phase !== 'idle') return;
        const x = e.clientX ?? e.touches?.[0]?.clientX;
        const dx = x - dragRef.current.startX;
        if (dx > 0) {
            const p = Math.min(dx / 150, 1);
            setDragProgress(p);
            if (p >= 1) triggerOpen();
        }
    };

    const handlePointerUp = (e) => {
        if (!dragRef.current.active) return;
        dragRef.current.active = false;
        if (dragProgress < 1) setDragProgress(0);
        e.currentTarget.releasePointerCapture?.(e.pointerId);
    };

    const rayOpacity = phase === 'idle' ? 0.12 : phase === 'explode' ? 0.55 : 0.2;

    // Render safety check
    if (!card && phase === 'reveal') {
        return (
            <div className="pack-overlay">
                <p style={{ color: 'white' }}>Error: No card found in pack.</p>
                <button className="reveal-continue-btn" onClick={onClose}>Continuar</button>
            </div>
        )
    }

    return (
        <div className="pack-overlay">

            {/* Rayos giratorios */}
            <div className="pack-rays" style={{ opacity: rayOpacity }}>
                <div className="pack-rays__disk" />
            </div>

            {/* FLASH / EXPLOSION */}
            {phase === 'explode' && <div className="pack-flash" />}
            {phase === 'explode' && <div className="pack-explosion" />}

            {/* Partículas */}
            {phase === 'explode' && <Particles />}

            {/* ── SOBRE ── */}
            {(phase === 'idle' || phase === 'opening') && (
                <div className="pack-stage">
                    <span className="pack-stage__label">SPFL Card Pack</span>

                    <div
                        className={`pack-stage__envelope${phase === 'idle' ? ' pack-stage__envelope--floating' : ''}`}
                        onPointerDown={handlePointerDown}
                        onPointerMove={handlePointerMove}
                        onPointerUp={handlePointerUp}
                        onPointerCancel={handlePointerUp}
                        onClick={() => phase === 'idle' && triggerOpen()}
                    >
                        <PackSVG dragProgress={dragProgress} isOpening={phase === 'opening'} />
                    </div>

                    {phase === 'idle' && dragProgress === 0 && (
                        <div className="pack-hint">
                            <span>👆</span>
                            DESLIZA O TOCA PARA ABRIR
                            <span>→</span>
                        </div>
                    )}

                    {dragProgress > 0 && phase === 'idle' && (
                        <div className="pack-progress">
                            <div className="pack-progress__fill" style={{ width: `${dragProgress * 100}%` }} />
                        </div>
                    )}
                </div>
            )}

            {/* ── REVELAR CARTA ── */}
            {phase === 'reveal' && (
                <div className="reveal-stage">
                    <p className="reveal-stage__title">
                        {revealed ? '¡Tu carta! 🎉' : 'TAP PARA REVELAR'}
                    </p>

                    <RevealCard
                        card={card}
                        isFlipped={revealed}
                        onClick={() => !revealed && setRevealed(true)}
                    />

                    {revealed && (
                        <div className="reveal-actions">
                            <div className="reveal-coins">
                                🪙 Saldo restante: {remainingCoins?.toLocaleString()}
                            </div>
                            <button className="reveal-continue-btn" onClick={onClose}>
                                CONTINUAR
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
