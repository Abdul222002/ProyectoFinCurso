/**
 * API Service Functions — All backend endpoints
 */
import api from './api';

// ==========================================
// TEAMS
// ==========================================

export const teamsAPI = {
  getMy: (leagueId) => {
    if (leagueId) return api.get('/teams/my', { params: { league_id: leagueId } });
    return api.get('/teams/my');
  },
  update: (leagueId, data) => api.put('/teams/my', data, { params: { league_id: leagueId } }),
  setLineup: (leagueId, cardIds) => api.put('/teams/my/lineup', { lineup_card_ids: cardIds }, { params: { league_id: leagueId } }),
};

// ==========================================
// PLAYERS
// ==========================================

export const playersAPI = {
  list: (params = {}) => api.get('/players/', { params }),
  getDetail: (id) => api.get(`/players/${id}`),
  myCards: () => api.get('/players/my-cards/all'),
};

// ==========================================
// MARKET
// ==========================================

export const marketAPI = {
  list: (params = {}) => api.get('/market/', { params }),
  buy: (playerId) => api.post(`/market/buy/${playerId}`),
  sell: (cardId) => api.post(`/market/sell/${cardId}`),
};

// ==========================================
// ARENA
// ==========================================

export const arenaAPI = {
  simulate: () => api.post('/arena/simulate'),
  history: (limit = 20) => api.get('/arena/history', { params: { limit } }),
  leaderboard: (limit = 50) => api.get('/arena/leaderboard', { params: { limit } }),
};

// ==========================================
// LEAGUES
// ==========================================

export const leaguesAPI = {
  create: (data) => api.post('/leagues/', data),
  myLeagues: () => api.get('/leagues/'),
  getDetail: (id) => api.get(`/leagues/${id}`),
  invite: (leagueId, data) => api.post(`/leagues/${leagueId}/invite`, data),
  joinByCode: (code) => api.post(`/leagues/join/${code}`),
  pendingInvitations: () => api.get('/leagues/invitations/pending'),
  acceptInvitation: (id) => api.post(`/leagues/invitations/${id}/accept`),
  rejectInvitation: (id) => api.post(`/leagues/invitations/${id}/reject`),
  leave: (leagueId) => api.delete(`/leagues/${leagueId}/leave`),
};
