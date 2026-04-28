import { useState } from 'react';
import { teamsAPI } from '../services/endpoints';
import './TeamCustomizerModal.css';

// Famous club shields — served locally from /images/shields/ for reliability
const PRESET_SHIELDS = [
    { name: 'FC Barcelona',       url: '/images/shields/barcelona.svg' },
    { name: 'Real Madrid',        url: '/images/shields/real-madrid.svg' },
    { name: 'Manchester United',  url: '/images/shields/manchester-united.svg' },
    { name: 'Manchester City',    url: '/images/shields/manchester-city.svg' },
    { name: 'Liverpool',          url: '/images/shields/liverpool.svg' },
    { name: 'Bayern München',     url: '/images/shields/bayern.svg' },
    { name: 'Paris Saint-Germain',url: '/images/shields/psg.svg' },
    { name: 'Juventus',           url: '/images/shields/juventus.svg' },
    { name: 'Chelsea',            url: '/images/shields/chelsea.svg' },
    { name: 'Arsenal',            url: '/images/shields/arsenal.svg' },
    { name: 'Atlético Madrid',    url: '/images/shields/atletico.svg' },
    { name: 'Borussia Dortmund',  url: '/images/shields/dortmund.svg' },
    { name: 'Inter Milan',        url: '/images/shields/inter.svg' },
    { name: 'AC Milan',           url: '/images/shields/milan.svg' },
    { name: 'Tottenham',          url: '/images/shields/tottenham.svg' },
    { name: 'Ajax',               url: '/images/shields/ajax.svg' },
    { name: 'Bayer Leverkusen',   url: '/images/shields/leverkusen.svg' },
    { name: 'AS Roma',            url: '/images/shields/roma.svg' },
    { name: 'SSC Napoli',         url: '/images/shields/napoli.svg' },
    { name: 'Flamengo',           url: '/images/shields/flamengo.png' },
    { name: 'Benfica',            url: '/images/shields/benfica.svg' },
    { name: 'Porto',              url: '/images/shields/porto.svg' },
    { name: 'Sevilla FC',         url: '/images/shields/sevilla.svg' },
    { name: 'Valencia CF',        url: '/images/shields/valencia.svg' },
    { name: 'Celtic FC',          url: '/images/shields/celtic.svg' },
    { name: 'Rangers FC',         url: '/images/shields/rangers.svg' },
    { name: 'Heart of Midlothian',url: '/images/shields/hearts.svg' },
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
