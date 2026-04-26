/**
 * Resuelve URL de imagen de jugador o estático del backend.
 * - En Docker/producción: nginx hace proxy de /static/ → backend:8000/static/
 *   Por eso las rutas /static/... se dejan relativas (sin añadir origen).
 * - En dev (Vite): vite.config.js tiene proxy /static/ → http://localhost:8000
 * - URL absolutas (http/https) pasan tal cual.
 */
export function resolveBackendMediaUrl(url) {
  if (!url || typeof url !== 'string') return null;
  const t = url.trim();
  if (!t) return null;
  // URL absoluta → devolver tal cual
  if (t.startsWith('http://') || t.startsWith('https://')) return t;
  // Ruta relativa con / → funciona en dev (proxy vite) y prod (proxy nginx)
  if (t.startsWith('/')) return t;
  return `/${t}`;
}

export function resolvePlayerImageUrl(url, playerName = '') {
  const resolved = resolveBackendMediaUrl(url);
  if (resolved) return resolved;
  // Fallback dinámico con iniciales del jugador
  const name = encodeURIComponent(playerName || 'UFL');
  return `https://ui-avatars.com/api/?name=${name}&background=152e20&color=25f478&bold=true&size=128`;
}
