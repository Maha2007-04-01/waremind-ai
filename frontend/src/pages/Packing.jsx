import React, { useState, useEffect } from 'react';
import { PackageCheck, Play, CheckCircle } from 'lucide-react';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Toast from '../components/common/Toast';
import { fetchWarehouseTasks, startPacking, completePacking } from '../services/api';

export default function Packing() {
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState([]);
  const [toast, setToast] = useState({ message: '', type: 'info' });
  const [submitting, setSubmitting] = useState(false);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const res = await fetchWarehouseTasks();
      const packingTasks = (res.data || []).filter(t => t.task_type === 'PACKING');
      setTasks(packingTasks);
    } catch (err) {
      setToast({ message: err.message || 'Failed to load packing tasks', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleStart = async (taskId) => {
    setSubmitting(true);
    try {
      await startPacking(taskId);
      setToast({ message: 'Packing task started', type: 'info' });
      loadTasks();
    } catch (err) {
      setToast({ message: err.message || 'Failed to start packing', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleComplete = async (taskId) => {
    setSubmitting(true);
    try {
      await completePacking(taskId);
      setToast({ message: 'Packing completed! Order updated to PACKED status.', type: 'success' });
      loadTasks();
    } catch (err) {
      setToast({ message: err.message || 'Failed to complete packing', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading warehouse packing task queue..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-slate-950 p-6 rounded-2xl border border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Packing Station</h1>
          <p className="text-sm text-slate-400 mt-1">Pack picked order items, verify barcode quantities, and prepare for QC inspection.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {tasks.length === 0 ? (
          <div className="p-12 text-center text-slate-500 bg-slate-950 rounded-2xl border border-slate-800">
            No active packing tasks in queue.
          </div>
        ) : (
          tasks.map(t => (
            <div key={t.id} className="bg-slate-950 p-5 rounded-2xl border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-3">
                  <span className="font-bold text-slate-100 text-base">{t.id}</span>
                  <Badge variant={t.status === 'COMPLETED' ? 'success' : t.status === 'IN_PROGRESS' ? 'purple' : 'medium'}>
                    {t.status}
                  </Badge>
                  <span className="text-xs font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                    Order: {t.order_number || t.order_id}
                  </span>
                </div>
                <p className="text-xs text-slate-400">Packer: <span className="text-slate-200 font-semibold">{t.assigned_to || 'Worker-02'}</span> | Customer: {t.customer_name}</p>
              </div>

              <div className="flex items-center space-x-2 w-full md:w-auto">
                {t.status === 'PENDING' && (
                  <Button variant="primary" onClick={() => handleStart(t.id)} disabled={submitting}>
                    <Play className="w-4 h-4 mr-1" />
                    <span>Start Packing</span>
                  </Button>
                )}

                {t.status === 'IN_PROGRESS' && (
                  <Button variant="success" onClick={() => handleComplete(t.id)} disabled={submitting}>
                    <CheckCircle className="w-4 h-4 mr-1" />
                    <span>Complete Packing</span>
                  </Button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <Toast 
        type={toast.type} 
        message={toast.message} 
        onClose={() => setToast({ message: '', type: 'info' })} 
      />
    </div>
  );
}
