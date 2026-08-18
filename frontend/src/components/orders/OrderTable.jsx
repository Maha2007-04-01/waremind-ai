import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Eye, Cpu, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';
import Badge from '../common/Badge';
import Button from '../common/Button';
import { allocateOrder, updateOrderStatus } from '../../services/api';
import { formatDate, formatCurrency } from '../../utils/formatters';

export default function OrderTable({ orders = [], onRefresh, setToast }) {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [allocatingId, setAllocatingId] = useState(null);

  const filteredOrders = orders.filter(o => {
    const matchSearch = 
      o.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      o.customer_name?.toLowerCase().includes(searchTerm.toLowerCase());

    if (!matchSearch) return false;
    if (statusFilter !== 'ALL' && o.status !== statusFilter) return false;
    return true;
  });

  const getPriorityBadge = (o) => {
    const evalData = o.priority_evaluation || {};
    const level = evalData.priority_level || o.priority || 'NORMAL';
    const score = evalData.priority_score;

    return (
      <div className="flex items-center space-x-1.5" title={evalData.reasons?.join(' | ')}>
        <Badge variant={level}>{level}</Badge>
        {score !== undefined && (
          <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
            {score}pts
          </span>
        )}
      </div>
    );
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PENDING':
        return <Badge variant="medium">PENDING</Badge>;
      case 'PARTIALLY_ALLOCATED':
        return <Badge variant="high">PARTIAL ALLOCATION</Badge>;
      case 'ALLOCATED':
        return <Badge variant="info">ALLOCATED</Badge>;
      case 'PICKING':
        return <Badge variant="info">PICKING</Badge>;
      case 'PICKED':
        return <Badge variant="info">PICKED</Badge>;
      case 'PACKING':
        return <Badge variant="purple">PACKING</Badge>;
      case 'PACKED':
        return <Badge variant="purple">PACKED</Badge>;
      case 'QC_PASSED':
        return <Badge variant="success">QC PASSED</Badge>;
      case 'QC_FAILED':
        return <Badge variant="critical">QC FAILED</Badge>;
      case 'DISPATCHED':
      case 'COMPLETED':
        return <Badge variant="success">DISPATCHED</Badge>;
      case 'CANCELLED':
        return <Badge variant="low">CANCELLED</Badge>;
      default:
        return <Badge variant="low">{status}</Badge>;
    }
  };

  const calculateAllocationProgress = (items = []) => {
    if (!items || items.length === 0) return 0;
    const totalRequested = items.reduce((sum, i) => sum + (i.requested_quantity || 0), 0);
    const totalAllocated = items.reduce((sum, i) => sum + (i.allocated_quantity || 0), 0);
    if (totalRequested === 0) return 0;
    return Math.min(100, Math.round((totalAllocated / totalRequested) * 100));
  };

  const handleAllocate = async (orderId) => {
    setAllocatingId(orderId);
    try {
      const res = await allocateOrder(orderId);
      const decision = res.data?.decision;
      if (setToast) {
        setToast({ message: `Smart Allocation decision executed: ${decision}`, type: 'success' });
      }
      if (onRefresh) onRefresh();
    } catch (err) {
      if (setToast) {
        setToast({ message: err.message || 'Allocation failed', type: 'error' });
      }
    } finally {
      setAllocatingId(null);
    }
  };

  return (
    <div className="bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden space-y-4">
      {/* Controls Bar */}
      <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row justify-between items-center gap-4 bg-slate-900/50">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by Order # or Customer..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
          />
        </div>

        <div className="flex items-center space-x-2 overflow-x-auto w-full sm:w-auto">
          {['ALL', 'PENDING', 'PARTIALLY_ALLOCATED', 'ALLOCATED', 'PICKING', 'PACKING', 'QC_PASSED', 'DISPATCHED'].map(st => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
                statusFilter === st
                  ? 'bg-sky-500/20 text-sky-400 border-sky-500/40'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-semibold bg-slate-900/30">
              <th className="py-3 px-4">Order # / Customer</th>
              <th className="py-3 px-4">Priority Score</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Required SLA</th>
              <th className="py-3 px-4">Allocation %</th>
              <th className="py-3 px-4">Total Value</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300 font-medium">
            {filteredOrders.length === 0 ? (
              <tr>
                <td colSpan="7" className="py-12 text-center text-slate-500">
                  No orders match your filter criteria.
                </td>
              </tr>
            ) : (
              filteredOrders.map((o) => {
                const allocPct = calculateAllocationProgress(o.items);
                const isAllocating = allocatingId === o.id;
                return (
                  <tr key={o.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-100">{o.order_number}</div>
                      <div className="text-slate-400 text-[11px]">{o.customer_name}</div>
                    </td>
                    <td className="py-3 px-4">{getPriorityBadge(o)}</td>
                    <td className="py-3 px-4">{getStatusBadge(o.status)}</td>
                    <td className="py-3 px-4 text-slate-400">
                      <div className="flex items-center space-x-1">
                        <Clock className="w-3.5 h-3.5 text-amber-400" />
                        <span>{formatDate(o.required_by)}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="w-32">
                        <div className="flex justify-between text-[10px] text-slate-400 mb-1 font-mono">
                          <span>{allocPct}%</span>
                          <span>{o.items?.length || 0} items</span>
                        </div>
                        <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
                          <div 
                            className={`h-full transition-all ${
                              allocPct === 100 ? 'bg-emerald-400' : allocPct > 0 ? 'bg-amber-400' : 'bg-slate-700'
                            }`}
                            style={{ width: `${allocPct}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-bold text-slate-200">{formatCurrency(o.total_value)}</td>
                    <td className="py-3 px-4 text-right space-x-2">
                      {['PENDING', 'PARTIALLY_ALLOCATED'].includes(o.status) && (
                        <button
                          onClick={() => handleAllocate(o.id)}
                          disabled={isAllocating}
                          className="px-2.5 py-1 bg-sky-500 hover:bg-sky-400 text-slate-950 rounded font-semibold transition-colors text-[11px] inline-flex items-center space-x-1"
                        >
                          <Cpu className="w-3 h-3" />
                          <span>{isAllocating ? 'Allocating...' : 'Smart Allocate'}</span>
                        </button>
                      )}
                      <button
                        onClick={() => navigate(`/orders/${o.id}`)}
                        className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition-colors text-[11px] inline-flex items-center space-x-1 font-semibold"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Details</span>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
