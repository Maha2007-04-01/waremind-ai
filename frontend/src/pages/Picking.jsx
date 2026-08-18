import React, { useState, useEffect } from 'react';
import { Boxes, UserCheck, Play, CheckCircle, AlertTriangle } from 'lucide-react';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Toast from '../components/common/Toast';
import ConfirmModal from '../components/common/ConfirmModal';
import { fetchWarehouseTasks, assignPicker, startPicking, completePicking, reportMissingItem, reportDamagedItem } from '../services/api';

export default function Picking() {
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState([]);
  const [toast, setToast] = useState({ message: '', type: 'info' });
  const [submitting, setSubmitting] = useState(false);

  // Exception Modals
  const [missingModal, setMissingModal] = useState({ isOpen: false, task: null, prodId: '', qty: 1, reason: '' });
  const [damagedModal, setDamagedModal] = useState({ isOpen: false, task: null, prodId: '', qty: 1, locId: '', reason: '' });

  const loadTasks = async () => {
    setLoading(true);
    try {
      const res = await fetchWarehouseTasks();
      const pickingTasks = (res.data || []).filter(t => t.task_type === 'PICKING');
      setTasks(pickingTasks);
    } catch (err) {
      setToast({ message: err.message || 'Failed to load picking tasks', type: 'error' });
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
      await startPicking(taskId);
      setToast({ message: 'Picking task started', type: 'info' });
      loadTasks();
    } catch (err) {
      setToast({ message: err.message || 'Failed to start picking', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleComplete = async (taskId) => {
    setSubmitting(true);
    try {
      await completePicking(taskId);
      setToast({ message: 'Picking completed! Order updated to PICKED status.', type: 'success' });
      loadTasks();
    } catch (err) {
      setToast({ message: err.message || 'Failed to complete picking', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleMissingSubmit = async () => {
    if (!missingModal.task || !missingModal.prodId) return;
    setSubmitting(true);
    try {
      await reportMissingItem(missingModal.task.id, missingModal.prodId, missingModal.qty, missingModal.reason);
      setToast({ message: 'Missing item reported! Exception logged for resolution engine.', type: 'warning' });
      setMissingModal({ isOpen: false, task: null, prodId: '', qty: 1, reason: '' });
      loadTasks();
    } catch (err) {
      setToast({ message: err.message || 'Report missing failed', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading warehouse picking task queue..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-slate-950 p-6 rounded-2xl border border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Picking Station</h1>
          <p className="text-sm text-slate-400 mt-1">Execute order item picking, assign workers, and handle missing/damaged item triage.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {tasks.length === 0 ? (
          <div className="p-12 text-center text-slate-500 bg-slate-950 rounded-2xl border border-slate-800">
            No active picking tasks in queue.
          </div>
        ) : (
          tasks.map(t => (
            <div key={t.id} className="bg-slate-950 p-5 rounded-2xl border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-3">
                  <span className="font-bold text-slate-100 text-base">{t.id}</span>
                  <Badge variant={t.status === 'COMPLETED' ? 'success' : t.status === 'IN_PROGRESS' ? 'info' : 'medium'}>
                    {t.status}
                  </Badge>
                  <span className="text-xs font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                    Order: {t.order_number || t.order_id}
                  </span>
                </div>
                <p className="text-xs text-slate-400">Assigned Picker: <span className="text-slate-200 font-semibold">{t.assigned_to || 'Unassigned'}</span> | Customer: {t.customer_name}</p>
              </div>

              <div className="flex items-center space-x-2 w-full md:w-auto">
                {t.status === 'PENDING' && (
                  <Button variant="primary" onClick={() => handleStart(t.id)} disabled={submitting}>
                    <Play className="w-4 h-4 mr-1" />
                    <span>Start Picking</span>
                  </Button>
                )}

                {t.status === 'IN_PROGRESS' && (
                  <>
                    <Button variant="secondary" onClick={() => setMissingModal({ isOpen: true, task: t, prodId: 'PROD-001', qty: 1, reason: '' })}>
                      <AlertTriangle className="w-4 h-4 mr-1 text-amber-400" />
                      <span>Report Missing</span>
                    </Button>

                    <Button variant="success" onClick={() => handleComplete(t.id)} disabled={submitting}>
                      <CheckCircle className="w-4 h-4 mr-1" />
                      <span>Complete Picking</span>
                    </Button>
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Missing Item Modal */}
      <ConfirmModal
        isOpen={missingModal.isOpen}
        title="Report Missing Item During Picking"
        onConfirm={handleMissingSubmit}
        onCancel={() => setMissingModal({ isOpen: false, task: null, prodId: '', qty: 1, reason: '' })}
        confirmText="Log Exception"
        confirmVariant="danger"
        loading={submitting}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Product ID</label>
            <input
              type="text"
              value={missingModal.prodId}
              onChange={(e) => setMissingModal({ ...missingModal, prodId: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-rose-500"
              placeholder="e.g. PROD-001"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Missing Quantity</label>
            <input
              type="number"
              min="1"
              value={missingModal.qty}
              onChange={(e) => setMissingModal({ ...missingModal, qty: parseInt(e.target.value) || 1 })}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-rose-500"
            />
          </div>
        </div>
      </ConfirmModal>

      <Toast 
        type={toast.type} 
        message={toast.message} 
        onClose={() => setToast({ message: '', type: 'info' })} 
      />
    </div>
  );
}
