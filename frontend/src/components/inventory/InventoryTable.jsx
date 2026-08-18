import React, { useState } from 'react';
import { Search, Filter, SlidersHorizontal, AlertTriangle, ShieldAlert, Wrench } from 'lucide-react';
import Badge from '../common/Badge';
import Button from '../common/Button';
import ConfirmModal from '../common/ConfirmModal';
import { adjustStock, reportDamage } from '../../services/api';

export default function InventoryTable({ inventory = [], onRefresh, setToast }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // all, low_stock, out_of_stock, damaged

  // Modal States
  const [adjustModal, setAdjustModal] = useState({ isOpen: false, item: null, qtyChange: 0, reason: '' });
  const [damageModal, setDamageModal] = useState({ isOpen: false, item: null, dmgAdd: 1, reason: '' });
  const [submitting, setSubmitting] = useState(false);

  // Filter & Search Logic
  const filteredInventory = inventory.filter(item => {
    const prod = item.product || {};
    const loc = item.location || {};
    const matchSearch = 
      prod.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      prod.sku?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      prod.category?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      `${loc.zone}-${loc.aisle}-${loc.bin}`.toLowerCase().includes(searchTerm.toLowerCase());

    const avail = item.available_quantity;
    const reorder = prod.reorder_level || 10;

    if (!matchSearch) return false;

    if (filterType === 'low_stock') return avail <= reorder && avail > 0;
    if (filterType === 'out_of_stock') return avail <= 0;
    if (filterType === 'damaged') return item.damaged_quantity > 0;
    return true;
  });

  const getItemBadge = (item) => {
    const avail = item.available_quantity;
    const reorder = item.product?.reorder_level || 10;

    if (avail <= 0) return <Badge variant="critical">OUT OF STOCK</Badge>;
    if (avail <= reorder) return <Badge variant="high">LOW STOCK</Badge>;
    if (item.damaged_quantity > 0) return <Badge variant="purple">DAMAGED STOCK</Badge>;
    return <Badge variant="success">IN STOCK</Badge>;
  };

  const handleAdjustSubmit = async () => {
    if (!adjustModal.item) return;
    setSubmitting(true);
    try {
      await adjustStock(adjustModal.item.id, adjustModal.qtyChange, adjustModal.reason || 'Manual stock adjustment');
      setToast({ message: `Successfully adjusted stock for ${adjustModal.item.product?.sku}`, type: 'success' });
      setAdjustModal({ isOpen: false, item: null, qtyChange: 0, reason: '' });
      if (onRefresh) onRefresh();
    } catch (err) {
      setToast({ message: err.message || 'Stock adjustment failed', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDamageSubmit = async () => {
    if (!damageModal.item) return;
    setSubmitting(true);
    try {
      await reportDamage(damageModal.item.id, damageModal.dmgAdd, damageModal.reason || 'Damaged stock reported');
      setToast({ message: `Reported ${damageModal.dmgAdd} damaged units. Exception logged.`, type: 'warning' });
      setDamageModal({ isOpen: false, item: null, dmgAdd: 1, reason: '' });
      if (onRefresh) onRefresh();
    } catch (err) {
      setToast({ message: err.message || 'Damage report failed', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden space-y-4">
      {/* Controls Bar */}
      <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row justify-between items-center gap-4 bg-slate-900/50">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by SKU, Product, Category..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
          />
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-2 w-full sm:w-auto overflow-x-auto">
          <SlidersHorizontal className="w-4 h-4 text-slate-400 mr-1 flex-shrink-0" />
          <button
            onClick={() => setFilterType('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
              filterType === 'all'
                ? 'bg-sky-500/20 text-sky-400 border-sky-500/40'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            All ({inventory.length})
          </button>
          <button
            onClick={() => setFilterType('low_stock')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
              filterType === 'low_stock'
                ? 'bg-amber-500/20 text-amber-400 border-amber-500/40'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            Low Stock
          </button>
          <button
            onClick={() => setFilterType('out_of_stock')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
              filterType === 'out_of_stock'
                ? 'bg-rose-500/20 text-rose-400 border-rose-500/40'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            Out of Stock
          </button>
          <button
            onClick={() => setFilterType('damaged')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
              filterType === 'damaged'
                ? 'bg-purple-500/20 text-purple-400 border-purple-500/40'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            Damaged
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-semibold bg-slate-900/30">
              <th className="py-3 px-4">SKU / Product Name</th>
              <th className="py-3 px-4">Category</th>
              <th className="py-3 px-4">Location</th>
              <th className="py-3 px-4">Total Qty</th>
              <th className="py-3 px-4">Reserved</th>
              <th className="py-3 px-4">Damaged</th>
              <th className="py-3 px-4">Available</th>
              <th className="py-3 px-4">Reorder Lvl</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300 font-medium">
            {filteredInventory.length === 0 ? (
              <tr>
                <td colSpan="10" className="py-12 text-center text-slate-500">
                  No inventory records match your criteria.
                </td>
              </tr>
            ) : (
              filteredInventory.map((item) => {
                const prod = item.product || {};
                const loc = item.location || {};
                return (
                  <tr key={item.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-100">{prod.name || 'Unnamed Product'}</div>
                      <div className="text-slate-500 font-mono text-[11px]">{prod.sku}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{prod.category || 'General'}</td>
                    <td className="py-3 px-4 font-mono text-sky-400 font-semibold">
                      {loc.zone}-{loc.aisle}-{loc.bin}
                    </td>
                    <td className="py-3 px-4 text-slate-200 font-bold">{item.quantity}</td>
                    <td className="py-3 px-4 text-amber-400 font-semibold">{item.reserved_quantity}</td>
                    <td className="py-3 px-4 text-rose-400 font-semibold">{item.damaged_quantity}</td>
                    <td className="py-3 px-4">
                      <span className={`font-bold ${item.available_quantity <= 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {item.available_quantity}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{prod.reorder_level}</td>
                    <td className="py-3 px-4">{getItemBadge(item)}</td>
                    <td className="py-3 px-4 text-right space-x-1">
                      <button
                        onClick={() => setAdjustModal({ isOpen: true, item, qtyChange: 0, reason: '' })}
                        className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition-colors text-[11px] font-semibold"
                        title="Adjust Stock Quantity"
                      >
                        Adjust
                      </button>
                      <button
                        onClick={() => setDamageModal({ isOpen: true, item, dmgAdd: 1, reason: '' })}
                        className="px-2 py-1 bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 rounded border border-rose-800/60 transition-colors text-[11px] font-semibold"
                        title="Report Damaged Stock"
                      >
                        Damage
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Adjust Stock Modal */}
      <ConfirmModal
        isOpen={adjustModal.isOpen}
        title={`Adjust Stock — ${adjustModal.item?.product?.name}`}
        onConfirm={handleAdjustSubmit}
        onCancel={() => setAdjustModal({ isOpen: false, item: null, qtyChange: 0, reason: '' })}
        confirmText="Save Adjustment"
        loading={submitting}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Adjustment Quantity (+ or -)</label>
            <input
              type="number"
              value={adjustModal.qtyChange}
              onChange={(e) => setAdjustModal({ ...adjustModal, qtyChange: parseInt(e.target.value) || 0 })}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
              placeholder="e.g. +10 or -5"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Reason for Adjustment</label>
            <input
              type="text"
              value={adjustModal.reason}
              onChange={(e) => setAdjustModal({ ...adjustModal, reason: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
              placeholder="e.g. Restock shipment arrival / Physical count audit"
            />
          </div>
        </div>
      </ConfirmModal>

      {/* Report Damage Modal */}
      <ConfirmModal
        isOpen={damageModal.isOpen}
        title={`Report Damaged Stock — ${damageModal.item?.product?.name}`}
        onConfirm={handleDamageSubmit}
        onCancel={() => setDamageModal({ isOpen: false, item: null, dmgAdd: 1, reason: '' })}
        confirmText="Log Exception & Report"
        confirmVariant="danger"
        loading={submitting}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Damaged Quantity Added</label>
            <input
              type="number"
              min="1"
              value={damageModal.dmgAdd}
              onChange={(e) => setDamageModal({ ...damageModal, dmgAdd: parseInt(e.target.value) || 1 })}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-rose-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Damage Incident Reason</label>
            <input
              type="text"
              value={damageModal.reason}
              onChange={(e) => setDamageModal({ ...damageModal, reason: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-rose-500"
              placeholder="e.g. Water leak on shelf / Forklift impact"
            />
          </div>
        </div>
      </ConfirmModal>
    </div>
  );
}
