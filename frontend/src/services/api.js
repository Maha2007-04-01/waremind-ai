const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Safe localStorage helper — never throws even when browser blocks storage access
function safeStorage(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}

async function request(endpoint, options = {}) {

  const url = `${API_BASE_URL}${endpoint}`;
  const token = safeStorage('waremind_token');

  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    },
    ...options,
  };

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }

  let response;
  try {
    response = await fetch(url, config);
  } catch (err) {
    throw new Error('Unable to connect to authentication server');
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg = data?.error?.message || data?.message || `HTTP error ${response.status}`;
    throw new Error(errorMsg);
  }

  return data;
}

// Authentication APIs
export const loginUser = (credentials) => request('/auth/login', { method: 'POST', body: credentials });
export const registerUser = (userData) => request('/auth/register', { method: 'POST', body: userData });
export const fetchCurrentUser = () => request('/auth/me');

// System & Health
export const fetchHealth = () => request('/health');
export const fetchSystemStatus = () => request('/system/status');
export const resetDemoData = () => request('/system/reset-demo', { method: 'POST' });
export const fetchDecisionInsights = () => request('/analytics/decision-insights');
export const fetchAnalyticsSummary = () => request('/analytics/summary');
export const fetchAuditLogs = () => request('/analytics/audit-logs');




// Inventory APIs
export const fetchInventory = () => request('/inventory');
export const fetchInventoryById = (id) => request(`/inventory/${id}`);
export const fetchLowStock = () => request('/inventory/low-stock');
export const fetchOutOfStock = () => request('/inventory/out-of-stock');
export const fetchDamagedInventory = () => request('/inventory/damaged');
export const fetchReorderRecommendations = () => request('/inventory/reorder-recommendations');
export const searchInventory = (q) => request(`/inventory/search?q=${encodeURIComponent(q)}`);
export const patchInventory = (id, data) => request(`/inventory/${id}`, { method: 'PATCH', body: data });
export const adjustStock = (id, quantity_change, reason) => request(`/inventory/${id}/adjust`, { method: 'POST', body: { quantity_change, reason } });
export const reportDamage = (id, damaged_quantity_added, reason) => request(`/inventory/${id}/damage`, { method: 'POST', body: { damaged_quantity_added, reason } });

// Order APIs
export const fetchOrders = () => request('/orders');
export const fetchOrderById = (id) => request(`/orders/${id}`);
export const createOrder = (orderData) => request('/orders', { method: 'POST', body: orderData });
export const allocateOrder = (id) => request(`/orders/${id}/allocate`, { method: 'POST' });
export const fetchOrderDecision = (id) => request(`/orders/${id}/decision`);
export const updateOrderStatus = (id, status) => request(`/orders/${id}/status`, { method: 'PATCH', body: { status } });

// Picking APIs
export const createPickingTask = (order_id, assigned_to) => request('/picking/tasks', { method: 'POST', body: { order_id, assigned_to } });
export const assignPicker = (taskId, assigned_to) => request(`/picking/tasks/${taskId}/assign`, { method: 'POST', body: { assigned_to } });
export const startPicking = (taskId) => request(`/picking/tasks/${taskId}/start`, { method: 'POST' });
export const completePicking = (taskId) => request(`/picking/tasks/${taskId}/complete`, { method: 'POST' });
export const reportMissingItem = (taskId, product_id, missing_quantity, reason) => request(`/picking/tasks/${taskId}/report-missing`, { method: 'POST', body: { product_id, missing_quantity, reason } });
export const reportDamagedItem = (taskId, product_id, damaged_quantity, location_id, reason) => request(`/picking/tasks/${taskId}/report-damaged`, { method: 'POST', body: { product_id, damaged_quantity, location_id, reason } });

// Packing APIs
export const createPackingTask = (order_id, assigned_to) => request('/packing/tasks', { method: 'POST', body: { order_id, assigned_to } });
export const startPacking = (taskId) => request(`/packing/tasks/${taskId}/start`, { method: 'POST' });
export const completePacking = (taskId) => request(`/packing/tasks/${taskId}/complete`, { method: 'POST' });

// Quality Check APIs
export const performQCCheck = (order_id, result = 'PASS', notes = '', inspector = 'Inspector-01') => request('/qc/check', { method: 'POST', body: { order_id, result, notes, inspector } });

// Dispatch APIs
export const createDispatch = (order_id, carrier = 'FedEx Freight') => request('/dispatch', { method: 'POST', body: { order_id, carrier } });
export const assignCarrier = (dispatchId, carrier) => request(`/dispatch/${dispatchId}/assign-carrier`, { method: 'POST', body: { carrier } });
export const markDispatched = (dispatchId) => request(`/dispatch/${dispatchId}/dispatch`, { method: 'POST' });

// Exception & Task APIs
export const fetchExceptions = () => request('/exceptions');
export const fetchExceptionById = (id) => request(`/exceptions/${id}`);
export const resolveException = (id, resolution_action, details) => request(`/exceptions/${id}/resolve`, { method: 'POST', body: { resolution_action, details } });
export const fetchWarehouseTasks = () => request('/warehouse/tasks');
export const fetchWarehouseLayout = () => request('/warehouse/layout');

// ─── NEW: Predictive Stockout APIs ─────────────────────────────────────────
export const fetchStockoutPredictions = () => request('/predictive-stockout');
export const fetchCriticalStockouts = () => request('/predictive-stockout/critical');
export const fetchStockoutByProduct = (productId) => request(`/predictive-stockout/${productId}`);

// ─── NEW: Traceability APIs ─────────────────────────────────────────────────
export const traceProduct = (productId) => request(`/traceability/product/${productId}`);
export const traceOrder = (orderId) => request(`/traceability/order/${orderId}`);
export const searchTraceProducts = (q) => request(`/traceability/search?q=${encodeURIComponent(q)}`);

// ─── NEW: AI Copilot APIs ────────────────────────────────────────────────────
export const askCopilot = (question) => request('/copilot/ask', { method: 'POST', body: { question } });
export const fetchCopilotQuestions = () => request('/copilot/questions');



export default {
  fetchHealth,
  fetchSystemStatus,
  resetDemoData,
  fetchDecisionInsights,
  fetchAnalyticsSummary,
  fetchAuditLogs,

  fetchInventory,
  fetchInventoryById,
  fetchLowStock,
  fetchOutOfStock,
  fetchDamagedInventory,
  fetchReorderRecommendations,
  searchInventory,
  adjustStock,
  reportDamage,
  fetchOrders,
  fetchOrderById,
  createOrder,
  allocateOrder,
  fetchOrderDecision,
  updateOrderStatus,
  createPickingTask,
  assignPicker,
  startPicking,
  completePicking,
  reportMissingItem,
  reportDamagedItem,
  createPackingTask,
  startPacking,
  completePacking,
  performQCCheck,
  createDispatch,
  assignCarrier,
  markDispatched,
  fetchExceptions,
  resolveException,
  fetchWarehouseTasks,
  fetchWarehouseLayout,

  // New features
  fetchStockoutPredictions,
  fetchCriticalStockouts,
  fetchStockoutByProduct,
  traceProduct,
  traceOrder,
  searchTraceProducts,
  askCopilot,
  fetchCopilotQuestions,
};

