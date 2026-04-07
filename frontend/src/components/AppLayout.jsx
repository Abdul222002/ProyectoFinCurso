import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './AppLayout.css';

const AppLayout = ({ title, backTo, rightContent, children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleBack = () => {
    if (backTo) {
      navigate(backTo);
    } else {
      navigate(-1);
    }
  };

  const navItems = [
    { 
      path: '/dashboard', 
      icon: (
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
      ), 
      label: 'Inicio' 
    },
    { 
      path: '/team', 
      icon: (
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
          <circle cx="19" cy="11" r="2"/>
        </svg>
      ), 
      label: 'Equipo' 
    },
    { 
      path: '/arena', 
      icon: (
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14.5 17.5L3 6l3-3 11.5 11.5"/>
          <path d="M13 19l6-6"/>
          <path d="M8.5 14.5L14.5 8.5"/>
          <path d="M18.5 18.5L22 22"/>
          <path d="M9.5 6.5L1.5 14.5 3.5 16.5 11.5 8.5"/>
        </svg>
      ), 
      label: 'Arena' 
    },
    { 
      path: '/market', 
      icon: (
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
          <line x1="7" y1="7" x2="7.01" y2="7"/>
        </svg>
      ), 
      label: 'Mercado' 
    },
    { 
      path: '/leagues', 
      icon: (
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/>
          <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
          <path d="M4 22h16"/>
          <path d="M10 14.66V17c0 .55.45 1 1 1h2c.55 0 1-.45 1-1v-2.34c3.91-.07 7-3.27 7-7.24V4H3v3.42c0 3.97 3.09 7.17 7 7.24z"/>
        </svg>
      ), 
      label: 'Ligas' 
    }
  ];

  return (
    <div className="app-layout">
      {/* Header Estándar */}
      {(title || backTo || rightContent) && (
        <header className="app-header">
          <div className="header-left">
            {backTo !== null && (
              <button className="back-btn" onClick={handleBack}>
                ← Volver
              </button>
            )}
          </div>
          <div className="header-center">
            {title && <h1 className="header-title">{title}</h1>}
          </div>
          <div className="header-right">
            {rightContent}
          </div>
        </header>
      )}

      {/* Contenido Principal */}
      <main className="app-main-content">
        {children}
      </main>

      {/* Bottom Navigation */}
      <nav className="app-bottom-nav">
        {navItems.map((item) => {
          // Identificar si la ruta actual coincide o empieza con el path
          // Excepción: '/leagues/:id' cuenta como '/leagues'
          const isActive = location.pathname.startsWith(item.path);

          return (
            <button
              key={item.path}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => navigate(item.path)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {isActive && <span className="active-dot"></span>}
            </button>
          );
        })}
      </nav>
    </div>
  );
};

export default AppLayout;
