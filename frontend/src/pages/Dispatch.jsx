import React, { useState, useEffect } from 'react';
import { Truck, CheckCircle2, FileText, Cpu } from 'lucide-react';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Toast from '../components/common/Toast';
import ConfirmModal from '../components/common/ConfirmModal';
import { fetchOrders, createDispatch, markDispatched } from '../services/api';
import { formatDate } from '../utils/formatters';

export default function Dispatch() {
  const [loading, setLoading] = useState(true);
  const [qcPassedOrders, setQcPassedOrders] = useState([]);
  const [toast, setToast] = useState({ message: '', type: 'info' });
  const [submitting, setSubmitting] = useState(false);

  // Dispatch modal
  const [dispatchModal, setDispatchModal] = useState({ isOpen: false, order: null, carrier: 'FedEx Freight' });

  const loadOrders = async () => {
    setLoading(true);
    try {
      const res = await fetchOrders();
      const passed = (res.data || []).filter(o => ['QC_PASSED', 'DISPATCHED'].includes(o.status));
      setQcPassedOrders(passed);
    } catch (err) {
      setToast({ message: err.message || 'Failed to load dispatch queue', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, []);

  const handleDispatchSubmit = async () => {
    if (!dispatchModal.order) return;
    setSubmitting(true);
    try {
      const dspRes = await createDispatch(dispatchModal.order.id, dispatchModal.carrier);
      const dspId = dspRes.data?.id;
      await markDispatched(dspId);
      setToast({ message: `Order ${dispatchModal.order.order_number} dispatched via ${dispatchModal.carrier}! Tracking: ${dspRes.data?.tracking_number}`, type: 'success' });
      setDispatchModal({ isOpen: false, order: null, carrier: 'FedEx Freight' });
      loadOrders();
    } catch (err) {
      setToast({ message: err.message || 'Dispatch execution failed', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading warehouse dispatch manifest queue..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-slate-950 p-6 rounded-2xl border border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Dispatch & Shipping Station</h1>
          <p className="text-sm text-slate-400 mt-1">Generate shipping manifests, assign logistics carriers, and finalize physical stock deduction upon dispatch.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {qcPassedOrders.length === 0 ? (
          <div className="p-12 text-center text-slate-500 bg-slate-950 rounded-2xl border border-slate-800">
            No orders awaiting dispatch.
          </div>
        ) : (
          qcPassedOrders.map(o => (
            <div key={o.id} className="bg-slate-950 p-5 rounded-2xl border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-3">
                  <span className="font-bold text-slate-100 text-base">{o.order_number}</span>
                  <Badge variant={o.status === 'DISPATCHED' ? 'success' : 'purple'}>
                    {o.status}
                  </Badge>
                  <span className="text-xs font-mono text-slate-400">Customer: {o.customer_name}</span>
                </div>
                <p className="text-xs text-slate-400">Required SLA: <span className="text-amber-400 font-mono">{formatDate(o.required_by)}</span> | Items: {o.items?.length || 0}</p>
              </div>

              <div>
                {o.status === 'QC_PASSED' ? (
                  <Button variant="success" onClick={() => setDispatchModal({ isOpen: true, order: o, carrier: 'FedEx Freight' })} disabled={submitting}>
                    <Truck className="w-4 h-4 mr-1" />
                    <span>Create Manifest & Dispatch</span>
                  </Button>
                ) : (
                  <div className="flex items-center space-x-2 text-xs text-emerald-400 font-semibold bg-emerald-950/40 px-3 py-1.5 rounded-lg border border-emerald-800/40">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Dispatched & Stock Finalized</span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Dispatch Modal */}
      <ConfirmModal
        isOpen={dispatchModal.isOpen}
        title={`Create Dispatch Manifest — ${dispatchModal.order?.order_number}`}
        onConfirm={handleDispatchSubmit}
        onCancel={() => setDispatchModal({ isOpen: false, order: null, carrier: 'FedEx Freight' })}
        confirmText="Finalize Dispatch & Deduct Stock"
        confirmVariant="success"
        loading={submitting}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Carrier Shipping Partner</label>
            <select
              value={dispatchModal.carrier}
              onChange={(e) => setDispatchModal({ ...dispatchModal, carrier: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
            >
              <option value="FedEx Freight">FedEx Freight</option>
              <option value="UPS Supply Chain">UPS Supply Chain</option>
              <option value="DHL Express Logistics">DHL Express Logistics</option>
              <option value="XPO Logistics">XPO Logistics</option>
            </select>
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
