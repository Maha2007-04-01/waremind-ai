import React, { useState, useEffect } from 'react';
import OrderTable from '../components/orders/OrderTable';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Toast from '../components/common/Toast';
import Button from '../components/common/Button';
import ConfirmModal from '../components/common/ConfirmModal';
import { fetchOrders, createOrder } from '../services/api';
import { Plus } from 'lucide-react';

export default function Orders() {
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [toast, setToast] = useState({ message: '', type: 'info' });

  // Create Order Modal State
  const [createModal, setCreateModal] = useState(false);
  const [customerName, setCustomerName] = useState('');
  const [priority, setPriority] = useState('NORMAL');
  const [productId, setProductId] = useState('PROD-001');
  const [quantity, setQuantity] = useState(5);
  const [submitting, setSubmitting] = useState(false);

  const loadOrders = async () => {
    setLoading(true);
    try {
      const res = await fetchOrders();
      setOrders(res.data || []);
    } catch (err) {
      setToast({ message: err.message || 'Failed to load orders', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, []);

  const handleCreateOrderSubmit = async () => {
    if (!customerName) {
      setToast({ message: 'Customer name is required', type: 'error' });
      return;
    }
    setSubmitting(true);
    try {
      await createOrder({
        customer_name: customerName,
        priority,
        items: [{ product_id: productId, requested_quantity: parseInt(quantity) || 1 }]
      });
      setToast({ message: 'Order created successfully!', type: 'success' });
      setCreateModal(false);
      setCustomerName('');
      loadOrders();
    } catch (err) {
      setToast({ message: err.message || 'Failed to create order', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading customer orders and priority scores..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-950 p-6 rounded-2xl border border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Customer Order Queue</h1>
          <p className="text-sm text-slate-400 mt-1">Manage incoming order fulfillment lifecycle, SLA urgency, and AI allocation status.</p>
        </div>
        <Button variant="primary" onClick={() => setCreateModal(true)}>
          <Plus className="w-4 h-4 mr-1" />
          <span>New Order</span>
        </Button>
      </div>

      {/* Orders Table */}
      <OrderTable orders={orders} onRefresh={loadOrders} setToast={setToast} />

      {/* Create Order Modal */}
      <ConfirmModal
        isOpen={createModal}
        title="Create New Customer Order"
        onConfirm={handleCreateOrderSubmit}
        onCancel={() => setCreateModal(false)}
        confirmText="Create & Score Order"
        loading={submitting}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Customer Name</label>
            <input
              type="text"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
              placeholder="e.g. Lockheed Martin Robotics"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
              >
                <option value="URGENT">URGENT</option>
                <option value="HIGH">HIGH</option>
                <option value="NORMAL">NORMAL</option>
                <option value="LOW">LOW</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Product SKU</label>
              <select
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
              >
                <option value="PROD-001">PROD-001 (Industrial Sensor)</option>
                <option value="PROD-002">PROD-002 (Smart Router)</option>
                <option value="PROD-003">PROD-003 (Scanner Terminal)</option>
                <option value="PROD-004">PROD-004 (Conveyor Motor)</option>
                <option value="PROD-005">PROD-005 (RFID Labels)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Requested Quantity</label>
            <input
              type="number"
              min="1"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
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
