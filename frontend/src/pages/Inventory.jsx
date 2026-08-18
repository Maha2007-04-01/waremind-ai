import React, { useState, useEffect } from 'react';
import InventoryTable from '../components/inventory/InventoryTable';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Toast from '../components/common/Toast';
import { fetchInventory, fetchReorderRecommendations } from '../services/api';
import Badge from '../components/common/Badge';

export default function Inventory() {
  const [loading, setLoading] = useState(true);
  const [inventory, setInventory] = useState([]);
  const [reorderRecs, setReorderRecs] = useState([]);
  const [toast, setToast] = useState({ message: '', type: 'info' });

  const loadInventory = async () => {
    setLoading(true);
    try {
      const [invRes, recsRes] = await Promise.all([
        fetchInventory(),
        fetchReorderRecommendations()
      ]);
      setInventory(invRes.data || []);
      setReorderRecs(recsRes.data || []);
    } catch (err) {
      setToast({ message: err.message || 'Failed to load inventory', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInventory();
  }, []);

  if (loading) {
    return <LoadingSpinner label="Loading warehouse inventory stock and reorder requirements..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-950 p-6 rounded-2xl border border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Stock & Inventory Management</h1>
          <p className="text-sm text-slate-400 mt-1">Real-time SKU stock levels, reserved quantities, bin allocations, and safety thresholds.</p>
        </div>
        {reorderRecs.length > 0 && (
          <div className="bg-amber-500/10 border border-amber-500/20 px-4 py-2.5 rounded-xl flex items-center space-x-3 text-amber-400 text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>
            <span>{reorderRecs.length} Reorder Recommendations Generated</span>
          </div>
        )}
      </div>

      {/* Main Inventory Table */}
      <InventoryTable inventory={inventory} onRefresh={loadInventory} setToast={setToast} />

      <Toast 
        type={toast.type} 
        message={toast.message} 
        onClose={() => setToast({ message: '', type: 'info' })} 
      />
    </div>
  );
}
