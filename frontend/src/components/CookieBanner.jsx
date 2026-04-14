import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './CookieBanner.css';

export default function CookieBanner() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem('cookie_consent');
    if (!consent) {
      setIsVisible(true);
    }
  }, []);

  const handleAccept = () => {
    // Tanto si clica "Solo necesarias" como "Aceptar todas", 
    // el resultado es el mismo porque solo usamos necesarias.
    localStorage.setItem('cookie_consent', 'accepted');
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div className="cookie-banner-overlay">
      <div className="cookie-banner-content">
        <p className="cookie-banner-text">
          Usamos cookies técnicas necesarias para el funcionamiento del juego (sesión y autenticación). 
          No usamos cookies de publicidad ni analítica. 
          <Link to="/cookies" className="cookie-banner-link">
            Ver Política de cookies
          </Link>
        </p>
        <div className="cookie-banner-actions">
          <button className="btn-cookie-outline" onClick={handleAccept}>
            Solo necesarias
          </button>
          <button className="btn-cookie-solid" onClick={handleAccept}>
            Aceptar todas
          </button>
        </div>
      </div>
    </div>
  );
}
