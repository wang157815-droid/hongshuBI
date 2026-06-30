import { request } from '@/utils'

const getWithRepeatedParams = (url, params = {}) =>
  request.get(url, { params, paramsSerializer: { indexes: null } })

export default {
  login: (data) => request.post('/base/access_token', data, { noNeedToken: true }),
  getUserInfo: () => request.get('/base/userinfo'),
  getUserMenu: () => request.get('/base/usermenu'),
  getUserApi: () => request.get('/base/userapi'),
  // profile
  updatePassword: (data = {}) => request.post('/base/update_password', data),
  // users
  getUserList: (params = {}) => request.get('/user/list', { params }),
  getUserById: (params = {}) => request.get('/user/get', { params }),
  createUser: (data = {}) => request.post('/user/create', data),
  updateUser: (data = {}) => request.post('/user/update', data),
  deleteUser: (params = {}) => request.delete(`/user/delete`, { params }),
  resetPassword: (data = {}) => request.post(`/user/reset_password`, data),
  // role
  getRoleList: (params = {}) => request.get('/role/list', { params }),
  createRole: (data = {}) => request.post('/role/create', data),
  updateRole: (data = {}) => request.post('/role/update', data),
  deleteRole: (params = {}) => request.delete('/role/delete', { params }),
  updateRoleAuthorized: (data = {}) => request.post('/role/authorized', data),
  getRoleAuthorized: (params = {}) => request.get('/role/authorized', { params }),
  // menus
  getMenus: (params = {}) => request.get('/menu/list', { params }),
  createMenu: (data = {}) => request.post('/menu/create', data),
  updateMenu: (data = {}) => request.post('/menu/update', data),
  deleteMenu: (params = {}) => request.delete('/menu/delete', { params }),
  // apis
  getApis: (params = {}) => request.get('/api/list', { params }),
  createApi: (data = {}) => request.post('/api/create', data),
  updateApi: (data = {}) => request.post('/api/update', data),
  deleteApi: (params = {}) => request.delete('/api/delete', { params }),
  refreshApi: (data = {}) => request.post('/api/refresh', data),
  // depts
  getDepts: (params = {}) => request.get('/dept/list', { params }),
  createDept: (data = {}) => request.post('/dept/create', data),
  updateDept: (data = {}) => request.post('/dept/update', data),
  deleteDept: (params = {}) => request.delete('/dept/delete', { params }),
  // auditlog
  getAuditLogList: (params = {}) => request.get('/auditlog/list', { params }),
  // redbook projects
  getRedbookProjects: (params = {}) => request.get('/redbook/projects/list', { params }),
  getRedbookProject: (params = {}) => request.get('/redbook/projects/get', { params }),
  createRedbookProject: (data = {}) => request.post('/redbook/projects/create', data),
  updateRedbookProject: (data = {}) => request.post('/redbook/projects/update', data),
  deleteRedbookProject: (params = {}) => request.delete('/redbook/projects/delete', { params }),
  // redbook files
  uploadRedbookFile: (data = {}) => request.post('/redbook/files/upload', data, { timeout: 120000 }),
  getRedbookFiles: (params = {}) => request.get('/redbook/files/list', { params }),
  getRedbookFile: (params = {}) => request.get('/redbook/files/get', { params }),
  parseRedbookFile: (params = {}) => request.post('/redbook/files/parse', null, { params, timeout: 120000 }),
  reparseRedbookFile: (params = {}) => request.post('/redbook/files/reparse', null, { params, timeout: 120000 }),
  deleteRedbookFile: (params = {}) => request.delete('/redbook/files/delete', { params, timeout: 120000 }),
  getRedbookParseReport: (params = {}) => request.get('/redbook/files/parse-report', { params }),
  getRedbookParseErrors: (params = {}) => request.get('/redbook/files/errors', { params }),
  getRedbookUnmatchedNotes: (params = {}) => request.get('/redbook/files/unmatched-notes', { params }),
  getRedbookUnmatchedOrders: (params = {}) => request.get('/redbook/files/unmatched-orders', { params }),
  // redbook mappings
  getRedbookMappingOptions: (params = {}) => request.get('/redbook/mappings/options', { params }),
  getRedbookNoteMappings: (params = {}) => request.get('/redbook/mappings/notes/list', { params }),
  createRedbookNoteMapping: (data = {}) => request.post('/redbook/mappings/notes/create', data),
  updateRedbookNoteMapping: (data = {}) => request.post('/redbook/mappings/notes/update', data),
  deleteRedbookNoteMapping: (params = {}) => request.delete('/redbook/mappings/notes/delete', { params }),
  getRedbookTaskMappings: (params = {}) => request.get('/redbook/mappings/tasks/list', { params }),
  getRedbookPgyTaskOptions: (params = {}) => request.get('/redbook/mappings/tasks/pgy-task-options', { params }),
  createRedbookTaskMapping: (data = {}) => request.post('/redbook/mappings/tasks/create', data),
  updateRedbookTaskMapping: (data = {}) => request.post('/redbook/mappings/tasks/update', data),
  deleteRedbookTaskMapping: (params = {}) => request.delete('/redbook/mappings/tasks/delete', { params }),
  getRedbookTaskNoteBridge: (params = {}) => request.get('/redbook/mappings/task-note-bridge/list', { params }),
  // redbook rebuild and dashboards
  rebuildRedbookFacts: (data = {}) => request.post('/redbook/rebuild/facts', data),
  rebuildRedbookMarts: (data = {}) => request.post('/redbook/rebuild/marts', data),
  rebuildRedbookAll: (data = {}) => request.post('/redbook/rebuild/all', data),
  getRedbookProductOptions: (params = {}) => request.get('/redbook/dashboards/product-options', { params }),
  getRedbookTaskGroupOptions: (params = {}) => getWithRepeatedParams('/redbook/dashboards/task-group-options', params),
  getRedbookDashboardOverview: (params = {}) => getWithRepeatedParams('/redbook/dashboards/overview', params),
  getRedbookXiaohongxingDashboard: (params = {}) => getWithRepeatedParams('/redbook/dashboards/xiaohongxing', params),
  getRedbookKeywordSearchDashboard: (params = {}) => getWithRepeatedParams('/redbook/dashboards/keyword-search', params),
  getRedbookAdsEfficiency: (params = {}) => getWithRepeatedParams('/redbook/dashboards/ads-efficiency', params),
  getRedbookSearchFunnel: (params = {}) => request.get('/redbook/dashboards/search-funnel', { params }),
  getRedbookConversionFunnel: (params = {}) => request.get('/redbook/dashboards/conversion-funnel', { params }),
  getRedbookTaskPerformance: (params = {}) => request.get('/redbook/dashboards/task-performance', { params }),
  // redbook kpis
  getRedbookKpiMetrics: (params = {}) => request.get('/redbook/kpis/metrics', { params }),
  getRedbookKpiConfigs: (params = {}) => request.get('/redbook/kpis/configs', { params }),
  createRedbookKpiConfig: (data = {}) => request.post('/redbook/kpis/configs/create', data),
  updateRedbookKpiConfig: (data = {}) => request.post('/redbook/kpis/configs/update', data),
  deleteRedbookKpiConfig: (params = {}) => request.delete('/redbook/kpis/configs/delete', { params }),
  getRedbookKpiProgress: (params = {}) => getWithRepeatedParams('/redbook/kpis/progress', params),
}
