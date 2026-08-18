import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  CheckCircle2, 
  Clock, 
  ArrowLeft, 
  Cpu, 
  Boxes, 
  PackageCheck, 
  ShieldCheck, 
  Truck, 
  AlertTriangle,
  FileText
} from 'lucide-react';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Toast from '../components/common/Toast';
import ConfirmModal from '../components/common/ConfirmModal';
import { 
  fetchOrderById, 
  allocateOrder, 
  createPickingTask, 
  createPackingTask, 
  performQCCheck, 
  createDispatch, 
  markDispatched 
} from '../services/api';
import { formatDate, formatCurrency } from '../utils/formatters';

export default function OrderDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [order, setOrder] = useState(null);
  const [toast, setToast] = useState({ message: '', type: 'info' });
  const [submitting, setSubmitting] = useState(false);

  // Workflow action modals
  const [qcModal, setQcModal] = useState({ isOpen: false, result: 'PASS', notes: '' });
  const [dispatchModal, setDispatchModal] = useState({ isOpen: false, carrier: 'FedEx Freight' });

  const loadOrder = async () => {
    setLoading(true);
    try {
      const res = await fetchOrderById(id);
      setOrder(res.data);
    } catch (err) {
      setToast({ message: err.message || 'Failed to load order details', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrder();
  }, [id]);

  if (loading) {
    return <LoadingSpinner label={`Loading order details for ${id}...`} />;
  }

  if (!order) {
    return (
      <div className="p-8 text-center text-slate-400">
        Order not found.
      </div>
    );
  }

  // Workflow Timeline Logic
  const workflowStages = [
    { key: 'CREATED', label: 'Order Created', icon: FileText },
    { key: 'PRIORITY', label: 'Priority Evaluated', icon: Cpu },
    { key: 'ALLOCATED', label: 'Stock Allocated', icon: Boxes },
    { key: 'PICKING', label: 'Picking Stage', icon: Boxes },
    { key: 'PACKING', label: 'Packing Stage', icon: PackageCheck },
    { key: 'QC_PASSED', label: 'Quality Check', icon: ShieldCheck },
    { key: 'DISPATCHED', label: 'Dispatched', icon: Truck },
  ];

  const getStageStatus = (stageKey) => {
    const status = order.status;
    const orderIndex = ['PENDING', 'PARTIALLY_ALLOCATED', 'ALLOCATED', 'PICKING', 'PICKED', 'PACKING', 'PACKED', 'QC_PASSED', 'DISPATCHED', 'COMPLETED'].indexOf(status);

    switch (stageKey) {
      case 'CREATED':
        return 'completed';
      case 'PRIORITY':
        return 'completed';
      case 'ALLOCATED':
        return orderIndex >= 2 ? 'completed' : (status === 'PARTIALLY_ALLOCATED' ? 'current' : 'pending');
      case 'PICKING':
        return orderIndex >= 4 ? 'completed' : (['ALLOCATED', 'PICKING'].includes(status) ? 'current' : 'pending');
      case 'PACKING':
        return orderIndex >= 6 ? 'completed' : (['PICKED', 'PACKING'].includes(status) ? 'current' : 'pending');
      case 'QC_PASSED':
        return orderIndex >= 7 ? 'completed' : (status === 'PACKED' ? 'current' : (status === 'QC_FAILED' ? 'failed' : 'pending'));
      case 'DISPATCHED':
        return ['DISPATCHED', 'COMPLETED'].includes(status) ? 'completed' : (status === 'QC_PASSED' ? 'current' : 'pending');
      default:
        return 'pending';
    }
  };

  // Workflow Actions
  const handleAllocate = async () => {
    setSubmitting(true);
    try {
      const res = await allocateOrder(order.id);
      setToast({ message: `Allocation decision: ${res.data?.decision}`, type: 'success' });
      loadOrder();
    } catch (err) {
      setToast({ message: err.message || 'Allocation failed', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartPicking = async () => {
    setSubmitting(true);
    try {
      await createPickingTask(order.id, 'Worker-01');
      setToast({ message: 'Picking task created successfully!', type: 'success' });
      navigate('/picking');
    } catch (err) {
      setToast({ message: err.message || 'Failed to create picking task', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartPacking = async () => {
    setSubmitting(true);
    try {
      await createPackingTask(order.id, 'Worker-02');
      setToast({ message: 'Packing task created successfully!', type: 'success' });
      navigate('/packing');
    } catch (err) {
      setToast({ message: err.message || 'Failed to create packing task', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleQCSubmit = async () => {
    setSubmitting(true);
    try {
      await performQCCheck(order.id, qcModal.result, qcModal.notes, 'Inspector-01');
      setToast({ message: `QC Inspection executed: ${qcModal.result}`, type: qcModal.result === 'PASS' ? 'success' : 'error' });
      setQcModal({ isOpen: false, result: 'PASS', notes: '' });
      loadOrder();
    } catch (err) {
      setToast({ message: err.message || 'QC submission failed', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDispatchSubmit = async () => {
    setSubmitting(true);
    try {
      const res = await createDispatch(order.id, dispatchModal.carrier);
      const dispatchId = res.data?.id;
      await markDispatched(dispatchId);
      setToast({ message: `Order dispatched! Tracking: ${res.data?.tracking_number}`, type: 'success' });
      setDispatchModal({ isOpen: false, carrier: 'FedEx Freight' });
      loadOrder();
    } catch (err) {
      setToast({ message: err.message || 'Dispatch failed', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-950 p-6 rounded-2xl border border-slate-800">
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => navigate('/orders')} 
            className="p-2 bg-slate-900 hover:bg-slate-800 rounded-xl text-slate-400 hover:text-slate-200 border border-slate-800"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-slate-100">{order.order_number}</h1>
              <Badge variant={order.priority_evaluation?.priority_level || order.priority}>
                {order.priority_evaluation?.priority_level || order.priority}
              </Badge>
              <Badge variant={order.status === 'QC_PASSED' ? 'success' : 'info'}>
                {order.status}
              </Badge>
            </div>
            <p className="text-sm text-slate-400 mt-1">Customer: <span className="text-slate-200 font-semibold">{order.customer_name}</span> | Required SLA: <span className="text-amber-400 font-mono">{formatDate(order.required_by)}</span></p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2">
          {['PENDING', 'PARTIALLY_ALLOCATED'].includes(order.status) && (
            <Button variant="primary" onClick={handleAllocate} disabled={submitting}>
              <Cpu className="w-4 h-4 mr-1" />
              <span>Smart Allocate</span>
            </Button>
          )}

          {['ALLOCATED', 'PARTIALLY_ALLOCATED'].includes(order.status) && (
            <Button variant="primary" onClick={handleStartPicking} disabled={submitting}>
              <Boxes className="w-4 h-4 mr-1" />
              <span>Start Picking</span>
            </Button>
          )}

          {order.status === 'PICKED' && (
            <Button variant="primary" onClick={handleStartPacking} disabled={submitting}>
              <PackageCheck className="w-4 h-4 mr-1" />
              <span>Start Packing</span>
            </Button>
          )}

          {order.status === 'PACKED' && (
            <Button variant="primary" onClick={() => setQcModal({ isOpen: true, result: 'PASS', notes: '' })}>
              <ShieldCheck className="w-4 h-4 mr-1" />
              <span>Perform QC</span>
            </Button>
          )}

          {order.status === 'QC_PASSED' && (
            <Button variant="success" onClick={() => setDispatchModal({ isOpen: true, carrier: 'FedEx Freight' })}>
              <Truck className="w-4 h-4 mr-1" />
              <span>Create Dispatch</span>
            </Button>
          )}
        </div>
      </div>

      {/* Visual Workflow Timeline & AI Decision Reasoning Side-by-Side */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline (2 Cols) */}
        <div className="lg:col-span-2 bg-slate-950 p-6 rounded-2xl border border-slate-800 space-y-6">
          <h3 className="font-bold text-slate-100 text-base">Fulfillment Pipeline Timeline</h3>
          <div className="relative border-l-2 border-slate-800 ml-4 space-y-6">
            {workflowStages.map((st, idx) => {
              const state = getStageStatus(st.key);
              const Icon = st.icon;

              return (
                <div key={idx} className="relative pl-8 group">
                  <div 
                    className={`absolute -left-3.5 top-0 w-7 h-7 rounded-full flex items-center justify-center border transition-all ${
                      state === 'completed'
                        ? 'bg-emerald-950 border-emerald-500 text-emerald-400'
                        : state === 'current'
                        ? 'bg-sky-950 border-sky-500 text-sky-400 animate-pulse'
                        : state === 'failed'
                        ? 'bg-rose-950 border-rose-500 text-rose-400'
                        : 'bg-slate-900 border-slate-800 text-slate-600'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h4 className={`text-sm font-semibold ${state === 'completed' ? 'text-slate-100' : state === 'current' ? 'text-sky-400 font-bold' : 'text-slate-500'}`}>
                      {st.label}
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {state === 'completed' ? 'Stage completed successfully' : state === 'current' ? 'Active stage in progress' : 'Awaiting upstream stage completion'}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* AI Decision Reasoning Panel (1 Col) */}
        <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <Cpu className="w-5 h-5 text-sky-400" />
            <h3 className="font-bold text-slate-100 text-base">AI Decision Reasoning</h3>
          </div>

          <div className="space-y-3 text-xs">
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400 block font-medium">Priority Score Calculation</span>
              <div className="text-slate-100 font-bold text-sm">
                Score: {order.priority_evaluation?.priority_score || 0} pts ({order.priority_evaluation?.priority_level})
              </div>
              <ul className="list-disc list-inside text-slate-400 mt-1 space-y-0.5">
                {order.priority_evaluation?.reasons?.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400 block font-medium">Allocation Decision Summary</span>
              <p className="text-slate-300">
                {order.allocations?.length > 0 
                  ? `Allocated ${order.allocations.reduce((sum, a) => sum + a.quantity, 0)} units across ${order.allocations.length} bin locations.`
                  : 'Stock unallocated. Click Smart Allocate to execute location pathing.'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Order Line Items Table */}
      <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="font-bold text-slate-100 text-base">Order Line Items</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-semibold bg-slate-900/30">
                <th className="py-3 px-4">SKU / Product</th>
                <th className="py-3 px-4">Requested Qty</th>
                <th className="py-3 px-4">Allocated Qty</th>
                <th className="py-3 px-4">Picked Qty</th>
                <th className="py-3 px-4">Packed Qty</th>
                <th className="py-3 px-4">Unit Price</th>
                <th className="py-3 px-4 text-right">Total Price</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300 font-medium">
              {order.items?.map((item) => {
                const prod = item.product || {};
                const totalPrice = (prod.unit_price || 0) * (item.requested_quantity || 0);
                return (
                  <tr key={item.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-100">{prod.name || 'Product'}</div>
                      <div className="text-slate-500 font-mono text-[11px]">{prod.sku}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-100 font-bold">{item.requested_quantity}</td>
                    <td className="py-3 px-4 text-amber-400 font-semibold">{item.allocated_quantity}</td>
                    <td className="py-3 px-4 text-sky-400 font-semibold">{item.picked_quantity}</td>
                    <td className="py-3 px-4 text-indigo-400 font-semibold">{item.packed_quantity}</td>
                    <td className="py-3 px-4 text-slate-400">{formatCurrency(prod.unit_price || 0)}</td>
                    <td className="py-3 px-4 text-right font-bold text-emerald-400">{formatCurrency(totalPrice)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* QC Modal */}
      <ConfirmModal
        isOpen={qcModal.isOpen}
        title="Execute Quality Control (QC) Inspection"
        onConfirm={handleQCSubmit}
        onCancel={() => setQcModal({ isOpen: false, result: 'PASS', notes: '' })}
        confirmText="Submit Inspection"
        loading={submitting}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Inspection Verdict</label>
            <select
              value={qcModal.result}
              onChange={(e) => setQcModal({ ...qcModal, result: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
            >
              <option value="PASS">PASS — All Seals & Barcodes Verified</option>
              <option value="FAIL">FAIL — Damaged Packaging / Missing Component</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Inspector Notes</label>
            <input
              type="text"
              value={qcModal.notes}
              onChange={(e) => setQcModal({ ...qcModal, notes: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
              placeholder="e.g. Visual check complete, seal intact"
            />
          </div>
        </div>
      </ConfirmModal>

      {/* Dispatch Modal */}
      <ConfirmModal
        isOpen={dispatchModal.isOpen}
        title="Create Dispatch Shipping Manifest"
        onConfirm={handleDispatchSubmit}
        onCancel={() => setDispatchModal({ isOpen: false, carrier: 'FedEx Freight' })}
        confirmText="Generate Manifest & Finalize Dispatch"
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
