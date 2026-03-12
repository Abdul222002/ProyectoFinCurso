/**
 * API Service Functions — All backend endpoints
 */
import api from './api';

// ==========================================
// AUTH
// ==========================================
export const authAPI = {
  searchUsers: (q) => api.get('/auth/search', { params: { q, limit: 5 } }),
  updateProfile: (data) => api.put('/auth/profile', data, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
};

// ==========================================
// TEAMS
// ==========================================

export const teamsAPI = {
  getMy: (leagueId) => {
    if (leagueId) return api.get('/teams/my', { params: { league_id: leagueId } });
    return api.get('/teams/my');
  },
  getUserTeam: (leagueId, userId) => api.get(`/teams/${leagueId}/user/${userId}`),
  update: (leagueId, data) => api.put('/teams/my', data, { params: { league_id: leagueId } }),
  setLineup: (leagueId, cardIds) => api.put('/teams/my/lineup', { lineup_card_ids: cardIds }, { params: { league_id: leagueId } }),
  getActiveGameweek: () => api.get('/teams/active-gameweek'),
  getGameweekLineup: (leagueId, gameweekId) => api.get('/teams/my/gameweek-lineup', { params: { league_id: leagueId, gameweek_id: gameweekId } }),
  releasePlayer: (leagueId, cardId) => api.post(`/teams/my/release/${cardId}`, {}, { params: { league_id: leagueId } }),
};

// ==========================================
// PLAYERS
// ==========================================

export const playersAPI = {
  list: (params = {}) => api.get('/players/', { params }),
  getDetail: (id) => api.get(`/players/${id}`),
  myCards: () => api.get('/players/my-cards/all'),
  getHistory: (id) => api.get(`/players/${id}/history`),
};

// ==========================================
// MARKET
// ==========================================

export const marketAPI = {
  list: (params = {}) => api.get('/market/', { params: { limit: 200, ...params } }),
  buy: (playerId) => api.post(`/market/buy/${playerId}`),
  sell: (cardId) => api.post(`/market/sell/${cardId}`),
};

// ==========================================
// ARENA
// ==========================================

export const arenaAPI = {
  getStatus: () => api.get('/arena/status'),
  simulate: (teamId) => api.post('/arena/simulate', { team_id: teamId }),
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
  list: (leagueId) => api.get(`/leagues/${leagueId}/members`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  invite: (leagueId, data) => api.post(`/leagues/${leagueId}/invite`, data, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  joinByCode: (code) => api.post(`/leagues/join/${code}`),
  pendingInvitations: () => api.get('/leagues/invitations/pending'),
  acceptInvitation: (id) => api.post(`/leagues/invitations/${id}/accept`),
  rejectInvitation: (id) => api.post(`/leagues/invitations/${id}/reject`),
  leave: (leagueId) => api.delete(`/leagues/${leagueId}/leave`),
  kickMember: (leagueId, userId) => api.delete(`/leagues/${leagueId}/kick/${userId}`),
};

// ==========================================
// AUCTION
// ==========================================

export const auctionAPI = {
  getAuction: (leagueId) => api.get(`/market/${leagueId}/auction`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  placeBid: (leagueId, slotId, amount) => api.post(`/market/${leagueId}/bid/${slotId}`, { amount }, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  withdrawBid: (leagueId, slotId) => api.delete(`/market/${leagueId}/bid/${slotId}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  sellCard: (leagueId, cardId) => api.post(`/market/${leagueId}/sell/${cardId}`, {}, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  // User listings
  listCard: (leagueId, cardId, askingPrice) => api.post(`/market/${leagueId}/list/${cardId}`, { asking_price: askingPrice }, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  cancelListing: (leagueId, listingId) => api.delete(`/market/${leagueId}/list/${listingId}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  getListings: (leagueId) => api.get(`/market/${leagueId}/listings`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  buyListing: (leagueId, listingId) => api.post(`/market/${leagueId}/buy-listing/${listingId}`, {}, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  getOffers: (leagueId) => api.get(`/market/${leagueId}/my-offers`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  acceptOffer: (leagueId, offerId) => api.post(`/market/${leagueId}/accept-offer/${offerId}`, {}, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  payClause: (leagueId, cardId) => api.post(`/market/${leagueId}/clause/${cardId}`, {}, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  protectPlayer: (leagueId, cardId, amount) => api.post(`/market/${leagueId}/protect/${cardId}`, { amount }, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
};

// ==========================================
// PACKS (Sobres)
// ==========================================

export const packsAPI = {
  openIcon: (leagueId) => api.post('/packs/open', null, {
    params: { league_id: leagueId },
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }),
  history: (leagueId) => api.get('/packs/history', {
    params: { league_id: leagueId },
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  })
};

// ==========================================
// ADMIN
// ==========================================

export const adminAPI = {
  getStats: () => api.get('/admin/stats'),
  getUsers: (search) => api.get('/admin/users', { params: search ? { search } : {} }),
  deleteUser: (userId) => api.delete(`/admin/users/${userId}`),
  getLeagues: (search) => api.get('/admin/leagues', { params: search ? { search } : {} }),
  deleteLeague: (leagueId) => api.delete(`/admin/leagues/${leagueId}`),
  getPlayers: (params = {}) => api.get('/admin/players', { params }),
  updatePlayer: (playerId, data) => api.put(`/admin/players/${playerId}`, data),
  getTeams: (search) => api.get('/admin/teams', { params: search ? { search } : {} }),
  getUserLeagueCoins: (userId) => api.get(`/admin/users/${userId}/league-coins`),
  updateUserLeagueCoins: (userId, data) => api.put(`/admin/users/${userId}/league-coins`, data),
};
