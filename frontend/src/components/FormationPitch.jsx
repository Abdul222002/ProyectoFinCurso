import './FormationPitch.css';

/* ── Formation slot counts (for position validation) ── */
const FORMATION_MAP = {
    '4-4-2': { DEF: 4, MID: 4, FWD: 2 },
    '4-3-3': { DEF: 4, MID: 3, FWD: 3 },
    '3-5-2': { DEF: 3, MID: 5, FWD: 2 },
    '4-2-3-1': { DEF: 4, MID: 5, FWD: 1 },
    '3-4-3': { DEF: 3, MID: 4, FWD: 3 },
    '5-3-2': { DEF: 5, MID: 3, FWD: 2 },
    '5-4-1': { DEF: 5, MID: 4, FWD: 1 },
};

/*
 * Row layout: [slotCount, positionType, displayLabel]
 * ALL formations use only GK / DEF / MID / FWD — no MCD/MCO
 */
const FORMATION_ROWS = {
    '4-4-2': [[2, 'FWD', 'DEL'], [4, 'MID', 'MC'], [4, 'DEF', 'DFC']],
    '4-3-3': [[3, 'FWD', 'DEL'], [3, 'MID', 'MC'], [4, 'DEF', 'DFC']],
    '3-5-2': [[2, 'FWD', 'DEL'], [5, 'MID', 'MC'], [3, 'DEF', 'DFC']],
    '4-2-3-1': [[1, 'FWD', 'DEL'], [5, 'MID', 'MC'], [4, 'DEF', 'DFC']],
    '3-4-3': [[3, 'FWD', 'DEL'], [4, 'MID', 'MC'], [3, 'DEF', 'DFC']],
    '5-3-2': [[2, 'FWD', 'DEL'], [3, 'MID', 'MC'], [5, 'DEF', 'DFC']],
    '5-4-1': [[1, 'FWD', 'DEL'], [4, 'MID', 'MC'], [5, 'DEF', 'DFC']],
};

export function getFormationSlots(formation) {
    return FORMATION_MAP[formation] || FORMATION_MAP['4-3-3'];
}

/**
 * Build formation rows from lineup players.
 * Safe with null/undefined/empty input.
 */
function buildFormationRows(players, formation) {
    const rowConfig = FORMATION_ROWS[formation] || FORMATION_ROWS['4-3-3'];
    const safeList = Array.isArray(players) ? players : [];

    // Group by position
    const byPos = { GK: [], DEF: [], MID: [], FWD: [] };
    for (const p of safeList) {
        if (p && p.position && byPos[p.position]) {
            byPos[p.position].push(p);
        }
    }

    const used = new Set();

    // GK
    const gk = byPos.GK.length > 0 ? byPos.GK[0] : null;
    if (gk) used.add(gk.id);

    // Outfield rows
    const rows = [];
    for (const [count, pos, label] of rowConfig) {
        const row = [];
        for (const p of byPos[pos]) {
            if (row.length >= count) break;
            if (!used.has(p.id)) {
                row.push({ type: 'player', player: p, slotPos: pos });
                used.add(p.id);
            }
        }
        while (row.length < count) {
            row.push({ type: 'empty', slotPos: pos, label });
        }
        rows.push(row);
    }

    return { gk, rows };
}


export default function FormationPitch({
    lineup,
    formation,
    onPlayerClick,
    onRemovePlayer,
    onSlotClick,
}) {
    // Always safe — never crashes
    const safeLineup = Array.isArray(lineup) ? lineup : [];
    const safeFormation = formation || '4-3-3';
    const { gk, rows } = buildFormationRows(safeLineup, safeFormation);

    return (
        <div className="pitch">
            <div className="pitch-field">
                <div className="pitch-center-circle" />
                <div className="pitch-center-line" />
                <div className="pitch-penalty-area pitch-penalty-top" />
                <div className="pitch-penalty-area pitch-penalty-bottom" />

                {rows.map((row, i) => (
                    <div key={i} className="pitch-row">
                        {row.map((slot, j) =>
                            slot.type === 'player' && slot.player ? (
                                <PlayerNode
                                    key={slot.player.id}
                                    player={slot.player}
                                    onPlayerClick={onPlayerClick}
                                    onRemove={onRemovePlayer}
                                />
                            ) : (
                                <EmptySlotNode
                                    key={`empty-${i}-${j}`}
                                    label={slot.label || ''}
                                    position={slot.slotPos}
                                    onSlotClick={onSlotClick}
                                />
                            )
                        )}
                    </div>
                ))}

                <div className="pitch-row pitch-row-gk">
                    {gk ? (
                        <PlayerNode player={gk} onPlayerClick={onPlayerClick} onRemove={onRemovePlayer} />
                    ) : (
                        <EmptySlotNode label="POR" position="GK" onSlotClick={onSlotClick} />
                    )}
                </div>
            </div>
        </div>
    );
}


function EmptySlotNode({ label, position, onSlotClick }) {
    return (
        <div className="pitch-slot" onClick={() => onSlotClick && onSlotClick(position)}>
            <div className="pitch-slot-circle">+</div>
            <div className="pitch-slot-label">
                <span className="pitch-slot-pos">{label}</span>
                <span className="pitch-slot-text">AÑADIR JUGADOR</span>
            </div>
        </div>
    );
}


function PlayerNode({ player, onPlayerClick, onRemove }) {
    if (!player) return null;
    const name = player.player_name || '???';
    const short = name.length > 12 ? name.split(' ').pop() : name;

    return (
        <div className="pitch-player" data-rarity={player.base_rarity || 'bronze'}>
            <div className="pitch-player-badge">{player.current_overall || '?'}</div>
            <div
                className="pitch-player-avatar"
                onClick={() => onPlayerClick && onPlayerClick(player)}
            >
                <img
                    src={player.image_url || '/images/placeholder.png'}
                    alt={name}
                    className="pitch-player-img"
                    onError={(e) => { e.target.src = '/images/placeholder.png'; }}
                />
            </div>
            <div className="pitch-player-label">
                <span className="pitch-player-name">{short}</span>
            </div>
            {onRemove && (
                <button
                    className="pitch-player-remove"
                    onClick={(e) => { e.stopPropagation(); onRemove(player.id); }}
                    title="Quitar del 11"
                >✕</button>
            )}
        </div>
    );
}
