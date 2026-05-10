import request from './request'

export const authAPI = {
  login: (data) => request.post('/auth/login', data),
  register: (data) => request.post('/auth/register', data),
  me: () => request.get('/auth/me'),
  updateMe: (data) => request.put('/auth/me', data),
  logout: () => request.post('/auth/logout')
}

export const userAPI = {
  getList: (params) => request.get('/users', { params }),
  getDetail: (id) => request.get(`/users/${id}`),
  update: (id, data) => request.put(`/users/${id}`, data),
  delete: (id) => request.delete(`/users/${id}`),
  assignRoles: (id, roleIds) => request.post(`/users/${id}/roles`, { role_ids: roleIds })
}

export const roleAPI = {
  getList: () => request.get('/roles'),
  create: (data) => request.post('/roles', data),
  update: (id, data) => request.put(`/roles/${id}`, data),
  delete: (id) => request.delete(`/roles/${id}`),
  getPermissions: (id) => request.get(`/roles/${id}/permissions`),
  setPermissions: (id, permIds) => request.put(`/roles/${id}/permissions`, { perm_ids: permIds })
}

export const permissionAPI = {
  getList: () => request.get('/permissions')
}

export const studyroomAPI = {
  getList: (params) => request.get('/studyrooms', { params }),
  create: (data) => request.post('/studyrooms', data),
  getDetail: (id) => request.get(`/studyrooms/${id}`),
  update: (id, data) => request.put(`/studyrooms/${id}`, data),
  delete: (id) => request.delete(`/studyrooms/${id}`),
  getAvailabilitySummary: (id) => request.get(`/studyrooms/${id}/availability-summary`),
  getCheckinCode: (id, date) => request.get(`/studyrooms/${id}/checkin-code`, { params: { date } }),
  refreshCheckinCode: (id) => request.post(`/studyrooms/${id}/checkin-code/refresh`)
}

export const seatAPI = {
  getList: (roomId, params) => request.get(`/studyrooms/${roomId}/seats`, { params }),
  create: (roomId, data) => request.post(`/studyrooms/${roomId}/seats`, data),
  getDetail: (id) => request.get(`/seats/${id}`),
  update: (id, data) => request.put(`/seats/${id}`, data),
  delete: (id) => request.delete(`/seats/${id}`),
  getAvailability: (id, date) => request.get(`/seats/${id}/availability`, { params: { date } })
}

export const reservationAPI = {
  create: (data) => request.post('/reservations', data),
  getMyList: (params) => request.get('/reservations/my', { params }),
  getDetail: (id) => request.get(`/reservations/${id}`),
  cancel: (id) => request.put(`/reservations/${id}/cancel`),
  checkin: (id, code) => request.post(`/reservations/${id}/checkin`, { checkin_code: code }),
  complete: (id) => request.put(`/reservations/${id}/complete`),
  getAdminList: (params) => request.get('/reservations/admin/reservations', { params })
}

export const violationAPI = {
  getList: (params) => request.get('/violations', { params })
}

export const systemConfigAPI = {
  getList: () => request.get('/system-configs'),
  update: (key, value) => request.put(`/system-configs/${key}`, { config_value: value }),
  getPublicConfigs: () => request.get('/system-configs/public')
}

export const statisticsAPI = {
  getOverview: () => request.get('/statistics/overview')
}

export const aiAPI = {
  ask: (question) => request.post('/ai/ask', { question })
}