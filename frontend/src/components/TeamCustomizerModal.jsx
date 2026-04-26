import { useState } from 'react';
import { teamsAPI } from '../services/endpoints';
import './TeamCustomizerModal.css';

// Famous club shields — locally resolved to avoid CORS / broken external links
const PRESET_SHIELDS = [
    { name: 'FC Barcelona', url: 'https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg' },
    { name: 'Real Madrid', url: 'https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg' },
    { name: 'Manchester United', url: 'https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg' },
    { name: 'Manchester City', url: 'https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg' },
    { name: 'Liverpool', url: 'https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg' },
    { name: 'Bayern München', url: 'https://upload.wikimedia.org/wikipedia/commons/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg' },
    { name: 'Paris Saint-Germain', url: 'https://upload.wikimedia.org/wikipedia/en/a/a7/Paris_Saint-Germain_F.C..svg' },
    { name: 'Juventus', url: 'https://upload.wikimedia.org/wikipedia/commons/b/bc/Juventus_FC_2017_icon_%28black%29.svg' },
    { name: 'Chelsea', url: 'https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg' },
    { name: 'Arsenal', url: 'https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg' },
    { name: 'Atletico Madrid', url: 'https://upload.wikimedia.org/wikipedia/en/f/f9/Atletico_Madrid_Logo_2024.svg' },
    { name: 'Borussia Dortmund', url: 'https://upload.wikimedia.org/wikipedia/commons/6/67/Borussia_Dortmund_logo.svg' },
    { name: 'Inter Milan', url: 'https://upload.wikimedia.org/wikipedia/commons/0/05/FC_Internazionale_Milano_2021.svg' },
    { name: 'AC Milan', url: 'https://upload.wikimedia.org/wikipedia/commons/d/d0/Logo_of_AC_Milan.svg' },
    { name: 'Tottenham', url: 'https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg' },
    { name: 'Ajax', url: 'https://upload.wikimedia.org/wikipedia/en/7/79/Ajax_Amsterdam.svg' },
    { name: 'Bayer Leverkusen', url: 'https://upload.wikimedia.org/wikipedia/en/5/59/Bayer_04_Leverkusen_logo.svg' },
    { name: 'AS Roma', url: 'https://upload.wikimedia.org/wikipedia/en/f/f7/AS_Roma_logo_%282017%29.svg' },
    { name: 'SSC Napoli', url: 'https://upload.wikimedia.org/wikipedia/commons/2/2d/SSC_Neapel.svg' },
    { name: 'Flamengo', url: 'https://upload.wikimedia.org/wikipedia/commons/9/93/Flamengo-RJ_%28BRA%29.png' },
    { name: 'Benfica', url: 'https://upload.wikimedia.org/wikipedia/en/a/a2/SL_Benfica_logo.svg' },
    { name: 'Porto', url: 'https://upload.wikimedia.org/wikipedia/en/f/f1/FC_Porto.svg' },
    { name: 'Sevilla FC', url: 'https://upload.wikimedia.org/wikipedia/en/3/3b/Sevilla_FC_logo.svg' },
    { name: 'Valencia CF', url: 'https://upload.wikimedia.org/wikipedia/en/c/ce/Valenciacf.svg' },
    // Scottish Premiership clubs
    { name: 'Celtic FC', url: 'https://upload.wikimedia.org/wikipedia/en/3/35/Celtic_FC_crest.svg' },
    { name: 'Rangers FC', url: 'https://upload.wikimedia.org/wikipedia/en/7/76/Rangers_FC_logo.svg' },
    { name: 'Heart of Midlothian', url: 'https://upload.wikimedia.org/wikipedia/en/5/5e/Heart_of_Midlothian_FC_logo.svg' },
];


export default function TeamCustomizerModal({ team, leagueId, onClose, onSaved }) {
    const [name, setName] = useState(team?.name || '');
    const [selectedShield, setSelectedShield] = useState(team?.shield_url || '');
    const [customShield, setCustomShield] = useState('');
    const [color, setColor] = useState(team?.kit_color_primary || '#ff0000');
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    // Track which shields have loaded so we can hide the skeleton
    const [loadedImgs, setLoadedImgs] = useState(new Set());

    const handleSave = async () => {
        if (!name.trim() || name.trim().length < 3) {
            setError('El nombre debe tener al menos 3 caracteres');
            return;
        }
        setSaving(true);
        setError('');
        try {
            const payload = {
                name: name.trim(),
                shield_url: customShield.trim() || selectedShield || null,
                kit_color_primary: color,
            };
            await teamsAPI.update(leagueId, payload);
            onSaved && onSaved(payload);
            onClose();
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al guardar');
        } finally {
            setSaving(false);
        }
    };

    const shieldToShow = customShield.trim() || selectedShield;

    return (
        <div className="tcm-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
            <div className="tcm-modal">
                <div className="tcm-header">
                    <div>
                        <h2 className="tcm-title">Personalizar Equipo</h2>
                        <p className="tcm-subtitle">Nombre, escudo y color del kit</p>
                    </div>
                    <button className="tcm-close" onClick={onClose}>✕</button>
                </div>

                {/* Preview */}
                <div className="tcm-preview">
                    <div className="tcm-shield-preview" style={{ borderColor: color, boxShadow: `0 0 20px ${color}44` }}>
                        {shieldToShow ? (
                            <img src={shieldToShow} alt="Escudo" className="tcm-shield-img" decoding="async" />
                        ) : (
                            <span className="tcm-shield-placeholder">🛡️</span>
                        )}
                    </div>
                    <div className="tcm-preview-text">
                        <span className="tcm-preview-name">{name || 'Mi Equipo'}</span>
                        <span className="tcm-preview-color" style={{ color }}>● Color del kit</span>
                    </div>
                </div>

                {/* Name */}
                <div className="tcm-field">
                    <label className="tcm-label">Nombre del Equipo</label>
                    <input
                        className="tcm-input"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Ej: Real Madrid FC"
                        maxLength={60}
                    />
                </div>

                {/* Kit Color */}
                <div className="tcm-field">
                    <label className="tcm-label">Color del Kit</label>
                    <div className="tcm-color-row">
                        <input type="color" value={color} onChange={(e) => setColor(e.target.value)} className="tcm-color-input" />
                        <span className="tcm-color-hex">{color}</span>
                    </div>
                </div>

                {/* Preset Shields */}
                <div className="tcm-field">
                    <label className="tcm-label">Escudo del Equipo</label>
                    <div className="tcm-shields-grid">
                        {PRESET_SHIELDS.map((shield) => {
                            const isLoaded = loadedImgs.has(shield.name);
                            return (
                                <button
                                    key={shield.name}
                                    className={`tcm-shield-btn ${selectedShield === shield.url ? 'selected' : ''}`}
                                    onClick={() => { setSelectedShield(shield.url); setCustomShield(''); }}
                                    title={shield.name}
                                >
                                    {/* Skeleton shown until image loads */}
                                    {!isLoaded && <div className="tcm-shield-skeleton" />}
                                    <img
                                        src={shield.url}
                                        alt={shield.name}
                                        className="tcm-shield-thumb"
                                        loading="lazy"
                                        decoding="async"
                                        width={44}
                                        height={44}
                                        style={{ opacity: isLoaded ? 1 : 0, position: isLoaded ? 'static' : 'absolute' }}
                                        onLoad={() => setLoadedImgs(prev => new Set([...prev, shield.name]))}
                                        onError={(e) => { e.currentTarget.style.opacity = '0.35'; setLoadedImgs(prev => new Set([...prev, shield.name])); }}
                                    />
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Custom URL */}
                <div className="tcm-field">
                    <label className="tcm-label">URL de escudo personalizado (opcional)</label>
                    <input
                        className="tcm-input"
                        value={customShield}
                        onChange={(e) => { setCustomShield(e.target.value); setSelectedShield(''); }}
                        placeholder="https://..."
                    />
                </div>

                {error && <p className="tcm-error">{error}</p>}

                <div className="tcm-actions">
                    <button className="tcm-btn-cancel" onClick={onClose}>Cancelar</button>
                    <button className="tcm-btn-save" onClick={handleSave} disabled={saving}>
                        {saving ? 'Guardando...' : '✓ Guardar Cambios'}
                    </button>
                </div>
            </div>
        </div>
    );
}
