import React, { useState, useEffect } from 'react';
import './PackOpeningModal.css';

export default function PackOpeningModal({ cards, remainingCoins, onClose }) {
    // Phases: 'intro' (suspense/shake), 'explode' (flash/particles), 'reveal' (flip cards)
    const [phase, setPhase] = useState('intro');
    const [flippedCards, setFlippedCards] = useState([]);

    useEffect(() => {
        // Start with intro phase (shaking pack), transition to explode after 3 seconds
        const explodeTimer = setTimeout(() => {
            setPhase('explode');

            // Transition from explode to reveal after 1.5 seconds flash
            setTimeout(() => {
                setPhase('reveal');
            }, 1500);

        }, 3000);

        return () => clearTimeout(explodeTimer);
    }, []);

    const handleCardClick = (idx) => {
        if (phase !== 'reveal') return;
        if (!flippedCards.includes(idx)) {
            setFlippedCards(prev => [...prev, idx]);
        }
    };

    const getRarityClass = (rarity) => {
        switch (rarity?.toLowerCase()) {
            case 'legend': return 'rarity-legend';
            case 'gold': return 'rarity-gold';
            case 'silver': return 'rarity-silver';
            case 'bronze': return 'rarity-bronze';
            default: return 'rarity-common';
        }
    };

    const getRarityLabel = (rarity) => {
        switch (rarity?.toLowerCase()) {
            case 'legend': return '⭐ LEYENDA';
            case 'gold': return 'ORO';
            case 'silver': return 'PLATA';
            case 'bronze': return 'BRONCE';
            default: return 'COMÚN';
        }
    };

    const allRevealed = flippedCards.length === cards.length && phase === 'reveal';

    return (
        <div className="pack-modal-overlay">

            {/* Dynamic Background Effects depending on phase */}
            <div className={`pack-bg-lights phase-${phase}`}>
                <div className="light-beam lb1" />
                <div className="light-beam lb2" />
                <div className="light-beam lb3" />
            </div>

            {/* PHASE 1 & 2: The Pack itself */}
            {(phase === 'intro' || phase === 'explode') && (
                <div className="pack-center-stage">
                    {phase === 'explode' && <div className="pack-explosion-flash" />}

                    <div className={`pack-item ${phase === 'intro' ? 'pack-shake' : 'pack-burst'}`}>
                        <div className="pack-foil">
                            <span className="pack-icon">🏆</span>
                            <h3>SCOTTISH PREMIUM</h3>
                        </div>
                        <div className="pack-glow" />
                    </div>

                    {phase === 'explode' && (
                        <div className="pack-particles">
                            {/* Confetti particles */}
                            {[...Array(20)].map((_, i) => (
                                <div key={i} className={`particle p${i % 5}`} style={{
                                    '--tx': `${(Math.random() - 0.5) * 500}px`,
                                    '--ty': `${(Math.random() - 0.5) * 500}px`,
                                    '--r': `${Math.random() * 360}deg`,
                                    animationDelay: `${Math.random() * 0.1}s`
                                }} />
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* PHASE 3: The Cards Reveal */}
            {phase === 'reveal' && (
                <div className="pack-reveal-stage">
                    <h2 className="reveal-title">¡Toca las cartas para revelarlas!</h2>

                    <div className="reveal-cards-container">
                        {cards.map((card, idx) => {
                            const isFlipped = flippedCards.includes(idx);
                            const rarityCls = getRarityClass(card.base_rarity);

                            return (
                                <div
                                    key={idx}
                                    className={`reveal-card-wrapper ${isFlipped ? 'flipped' : ''}`}
                                    onClick={() => handleCardClick(idx)}
                                >
                                    <div className="reveal-card-inner">
                                        {/* BACK OF CARD */}
                                        <div className="reveal-card-back">
                                            <div className="card-back-pattern">
                                                <span>SPFL</span>
                                            </div>
                                        </div>

                                        {/* FRONT OF CARD */}
                                        <div className={`reveal-card-front ${rarityCls}`}>
                                            <div className="rc-img-wrap">
                                                <img
                                                    src={card.image_url || '/images/placeholder.png'}
                                                    alt={card.player_name}
                                                    onError={(e) => { e.target.src = '/images/placeholder.png'; }}
                                                />
                                                <div className="rc-ovr">{card.overall_rating}</div>
                                            </div>
                                            <div className="rc-details">
                                                <div className="rc-name">{card.player_name}</div>
                                                <div className="rc-pos">{card.position}</div>
                                                <div className="rc-rarity">{getRarityLabel(card.base_rarity)}</div>
                                            </div>
                                            {/* Aura effect on front */}
                                            <div className="rc-glow"></div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    <div className={`reveal-actions ${allRevealed ? 'show' : ''}`}>
                        <div className="reveal-coins">🪙 Saldo restante: {remainingCoins?.toLocaleString()}</div>
                        <button className="reveal-continue-btn" onClick={onClose}>Continuar</button>
                    </div>
                </div>
            )}
        </div>
    );
}
