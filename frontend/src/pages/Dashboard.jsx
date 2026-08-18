import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardMetrics from '../components/dashboard/DashboardMetrics';
import AIOperationsCenter from '../components/dashboard/AIOperationsCenter';
import ExceptionCenter from '../components/dashboard/ExceptionCenter';
import ZoneWorkloadVisualizer from '../components/dashboard/ZoneWorkloadVisualizer';
import DashboardCharts from '../components/dashboard/DashboardCharts';
import AuditFeed from '../components/dashboard/AuditFeed';
import OrderTable from '../components/orders/OrderTable';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Toast from '../components/common/Toast';
import { 
  fetchDecisionInsights, 
  fetchOrders, 
  fetchInventory, 
  fetchWarehouseTasks, 
  fetchExceptions, 
  fetchAuditLogs 
} from '../services/api';

export default function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [insights, setInsights] = useState(null);
  const [orders, setOrders] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [exceptions, setExceptions] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [toast, setToast] = useState({ message: '', type: 'info' });

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [insightsRes, ordersRes, invRes, tasksRes, excRes, auditRes] = await Promise.all([
        fetchDecisionInsights().catch(() => ({ data: null })),
        fetchOrders().catch(() => ({ data: [] })),
        fetchInventory().catch(() => ({ data: [] })),
        fetchWarehouseTasks().catch(() => ({ data: [] })),
        fetchExceptions().catch(() => ({ data: [] })),
        fetchAuditLogs().catch(() => ({ data: [] }))
      ]);

      setInsights(insightsRes.data);
      setOrders(ordersRes.data || []);
      setInventory(invRes.data || []);
      setTasks(tasksRes.data || []);
      setExceptions(excRes.data || []);
      setAuditLogs(auditRes.data || []);
    } catch (err) {
      setToast({ message: err.message || 'Failed to load dashboard data', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleRecommendationAction = (rec) => {
    setToast({ message: `Executing recommendation: ${rec.title}`, type: 'info' });
    if (rec.affected_entities?.orders?.length > 0) {
      const targetOrder = rec.affected_entities.orders[0];
      navigate(`/orders/${targetOrder}`);
    } else if (rec.affected_entities?.products?.length > 0) {
      navigate('/inventory');
    }
  };

  if (loading) {
    return <LoadingSpinner label="Analyzing warehouse operations and AI insights..." />;
  }

  return (
    <div className="space-y-6">
      {/* 1. Executive Operational KPI Cards */}
      <DashboardMetrics orders={orders} inventory={inventory} tasks={tasks} />

      {/* 2. AI Decision Operations Center */}
      <AIOperationsCenter insights={insights} onActionClick={handleRecommendationAction} />

      {/* 3. Operational Exception Center & Warehouse Zone Capacity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ExceptionCenter exceptions={exceptions} onRefresh={loadDashboardData} setToast={setToast} />
        <ZoneWorkloadVisualizer inventory={inventory} />
      </div>

      {/* 4. Analytics & Fulfillment Velocity Charts */}
      <DashboardCharts orders={orders} inventory={inventory} />

      {/* 5. Live Activity Feed & Active Order Fulfillment Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <AuditFeed logs={auditLogs} />
        </div>
        <div className="lg:col-span-2 space-y-3">
          <div className="flex justify-between items-center bg-slate-950 p-4 rounded-xl border border-slate-800">
            <h3 className="font-bold text-slate-100 text-base">Active Fulfillment Pipeline Queue</h3>
            <button 
              onClick={() => navigate('/orders')} 
              className="text-xs text-sky-400 hover:text-sky-300 font-semibold"
            >
              View All Orders →
            </button>
          </div>
          <OrderTable orders={orders.slice(0, 5)} onRefresh={loadDashboardData} />
        </div>
      </div>

      <Toast 
        type={toast.type} 
        message={toast.message} 
        onClose={() => setToast({ message: '', type: 'info' })} 
      />
    </div>
  );
}
