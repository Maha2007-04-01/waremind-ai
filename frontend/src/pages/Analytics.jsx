import React, { useState, useEffect } from 'react';
import DashboardCharts from '../components/dashboard/DashboardCharts';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { fetchOrders, fetchInventory, fetchAnalyticsSummary } from '../services/api';

export default function Analytics() {
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [summary, setSummary] = useState({});

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [ordersRes, invRes, sumRes] = await Promise.all([
          fetchOrders(),
          fetchInventory(),
          fetchAnalyticsSummary()
        ]);
        setOrders(ordersRes.data || []);
        setInventory(invRes.data || []);
        setSummary(sumRes.data || {});
      } catch (err) {
        console.error('Analytics load error:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <LoadingSpinner label="Compiling warehouse operational analytics and velocity curves..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-slate-950 p-6 rounded-2xl border border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Fulfillment & Operations Analytics</h1>
          <p className="text-sm text-slate-400 mt-1">Deep-dive visual insights on inventory turnover, queue velocity, and stage workloads.</p>
        </div>
      </div>

      <DashboardCharts orders={orders} inventory={inventory} analyticsData={summary} />
    </div>
  );
}
