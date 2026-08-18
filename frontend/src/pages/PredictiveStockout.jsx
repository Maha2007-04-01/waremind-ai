import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, TrendingDown, Package, RefreshCw, Calendar, BarChart2, ArrowRight, ChevronDown, ChevronUp } from 'lucide-react';
import { fetchStockoutPredictions } from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Toast from '../components/common/Toast';

const RISK_CONFIG = {
  CRITICAL: { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', dot: 'bg-red-500', label: '🔴 CRITICAL', badge: 'bg-red-500/20 text-red-400 border-red-500/30' },
  HIGH:     { color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30', dot: 'bg-orange-500', label: '🟠 HIGH', badge: 'bg-orange-500/20 text-orange-400 border-orange-500/30' },
  MEDIUM:   { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', dot: 'bg-yellow-500', label: '🟡 MEDIUM', badge: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' },
  LOW:      { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', dot: 'bg-emerald-500', label: '🟢 LOW', badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' },
};

function RiskBadge({ level }) {
  const cfg = RISK_CONFIG[level] || RISK_CONFIG.LOW;
  return (
    <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${cfg.badge}`}>
      {cfg.label}
    </span>
  );
}

function StockBar({ value, max = 100 }) {
  const pct = Math.min(100, (value / Math.max(1, max)) * 100);
  return (
    <div className="w-full bg-slate-800 rounded-full h-1.5 mt-1">
      <div className="h-1.5 rounded-full bg-gradient-to-r from-sky-500 to-indigo-500" style={{ width: `${pct}%` }} />
    </div>
  );
}

function ProductCard({ item, onViewDetails }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = RISK_CONFIG[item.risk_level] || RISK_CONFIG.LOW;
  const daysText = item.projected_days_until_stockout >= 999
    ? '∞ days'
    : `${Math.round(item.projected_days_until_stockout)} days`;

  return (
    <div className={`rounded-2xl border ${cfg.border} ${cfg.bg} p-5 transition-all hover:shadow-lg`}>
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <RiskBadge level={item.risk_level} />
          </div>
          <h3 className="font-bold text-slate-100 text-base">{item.product_name}</h3>
          <p className="text-xs text-slate-400 font-mono">{item.sku} · {item.category}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onViewDetails(item)}
            className="text-xs font-semibold text-sky-400 hover:text-sky-300 flex items-center gap-1 border border-sky-500/30 px-3 py-1.5 rounded-lg hover:bg-sky-500/10 transition-all"
          >
            View Details <ArrowRight className="w-3 h-3" />
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
        <div>
          <p className="text-[10px] text-slate-400 uppercase tracking-wide font-medium">Available Stock</p>
          <p className="text-lg font-bold text-slate-100">{item.net_available}</p>
          <StockBar value={item.net_available} max={item.reorder_level * 3} />
        </div>
        <div>
          <p className="text-[10px] text-slate-400 uppercase tracking-wide font-medium">Daily Demand</p>
          <p className="text-lg font-bold text-slate-100">{item.avg_daily_demand > 0 ? item.avg_daily_demand.toFixed(1) : '—'}</p>
        </div>
        <div>
          <p className="text-[10px] text-slate-400 uppercase tracking-wide font-medium">Days Until Stockout</p>
          <p className={`text-lg font-bold ${cfg.color}`}>{daysText}</p>
        </div>
        <div>
          <p className="text-[10px] text-slate-400 uppercase tracking-wide font-medium">Reorder Qty</p>
          <p className="text-lg font-bold text-sky-400">{item.recommended_reorder_quantity}</p>
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-slate-700/50 space-y-3">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            <div className="bg-slate-900/60 rounded-xl p-3">
              <p className="text-slate-400 mb-0.5">Total Quantity</p>
              <p className="font-bold text-slate-100">{item.current_quantity}</p>
            </div>
            <div className="bg-slate-900/60 rounded-xl p-3">
              <p className="text-slate-400 mb-0.5">Reserved</p>
              <p className="font-bold text-slate-100">{item.reserved_quantity}</p>
            </div>
            <div className="bg-slate-900/60 rounded-xl p-3">
              <p className="text-slate-400 mb-0.5">Damaged</p>
              <p className="font-bold text-red-400">{item.damaged_quantity}</p>
            </div>
            <div className="bg-slate-900/60 rounded-xl p-3">
              <p className="text-slate-400 mb-0.5">Pending Demand</p>
              <p className="font-bold text-orange-400">{item.pending_demand}</p>
            </div>
            <div className="bg-slate-900/60 rounded-xl p-3">
              <p className="text-slate-400 mb-0.5">Safety Stock</p>
              <p className="font-bold text-slate-100">{item.safety_stock}</p>
            </div>
            <div className="bg-slate-900/60 rounded-xl p-3">
              <p className="text-slate-400 mb-0.5">Stockout Date</p>
              <p className="font-bold text-slate-100">{item.projected_stockout_date || '—'}</p>
            </div>
          </div>
          <div className="bg-slate-900/40 rounded-xl p-3 border border-slate-700/40">
            <p className="text-xs text-slate-300">{item.explanation}</p>
            <p className="text-xs font-semibold text-sky-400 mt-1">💡 {item.recommended_action}</p>
          </div>
        </div>
      )}
    </div>
  );
}

const FILTER_OPTIONS = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

export default function PredictiveStockout() {
  const navigate = useNavigate();
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [toast, setToast] = useState({ message: '', type: 'info' });
  const [selectedItem, setSelectedItem] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetchStockoutPredictions();
      setPredictions(res.data || []);
    } catch (err) {
      setToast({ message: 'Failed to load predictions. Is the backend running?', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = filter === 'ALL' ? predictions : predictions.filter(p => p.risk_level === filter);

  const counts = {
    CRITICAL: predictions.filter(p => p.risk_level === 'CRITICAL').length,
    HIGH: predictions.filter(p => p.risk_level === 'HIGH').length,
    MEDIUM: predictions.filter(p => p.risk_level === 'MEDIUM').length,
    LOW: predictions.filter(p => p.risk_level === 'LOW').length,
  };

  const handleViewDetails = (item) => {
    setSelectedItem(item);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (loading) return <LoadingSpinner label="Running predictive stockout analysis..." />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 bg-red-500/10 border border-red-500/30 rounded-xl">
              <TrendingDown className="w-5 h-5 text-red-400" />
            </div>
            <h2 className="text-xl font-bold text-slate-100">Predictive Stockout Alerts</h2>
          </div>
          <p className="text-sm text-slate-400 ml-11">AI-projected inventory depletion based on demand and pending orders</p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 text-xs font-semibold text-sky-400 border border-sky-500/30 px-4 py-2 rounded-xl hover:bg-sky-500/10 transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Analysis
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {Object.entries(counts).map(([level, count]) => {
          const cfg = RISK_CONFIG[level];
          return (
            <button
              key={level}
              onClick={() => setFilter(filter === level ? 'ALL' : level)}
              className={`p-4 rounded-2xl border cursor-pointer transition-all text-left hover:scale-105 ${
                filter === level ? `${cfg.bg} ${cfg.border}` : 'bg-slate-900 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className={`w-2 h-2 rounded-full ${cfg.dot} mb-2`} />
              <p className="text-2xl font-bold text-slate-100">{count}</p>
              <p className="text-xs text-slate-400 font-medium">{level} Risk</p>
            </button>
          );
        })}
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {FILTER_OPTIONS.map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 text-xs font-bold rounded-full whitespace-nowrap transition-all ${
              filter === f ? 'bg-sky-500 text-white shadow-md shadow-sky-500/30' : 'text-slate-400 border border-slate-700 hover:border-slate-600 hover:text-slate-200'
            }`}
          >
            {f === 'ALL' ? `All Products (${predictions.length})` : `${f} (${counts[f]})`}
          </button>
        ))}
      </div>

      {/* Selected Item Detail Panel */}
      {selectedItem && (
        <div className={`rounded-2xl border ${RISK_CONFIG[selectedItem.risk_level]?.border} bg-slate-900 p-6`}>
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-lg font-bold text-slate-100">{selectedItem.product_name}</h3>
              <p className="text-sm text-slate-400 font-mono">{selectedItem.sku}</p>
            </div>
            <button onClick={() => setSelectedItem(null)} className="text-slate-400 hover:text-slate-200 text-xs border border-slate-700 px-3 py-1.5 rounded-lg">
              Close ✕
            </button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
            <div className="bg-slate-800/60 rounded-xl p-3">
              <p className="text-xs text-slate-400">Risk Score</p>
              <p className="text-2xl font-bold text-slate-100">{(selectedItem.stockout_risk_score * 100).toFixed(0)}%</p>
              <p className="text-xs text-slate-500">safety margin</p>
            </div>
            <div className="bg-slate-800/60 rounded-xl p-3">
              <p className="text-xs text-slate-400">Net Available</p>
              <p className="text-2xl font-bold text-slate-100">{selectedItem.net_available}</p>
              <p className="text-xs text-slate-500">units</p>
            </div>
            <div className="bg-slate-800/60 rounded-xl p-3">
              <p className="text-xs text-slate-400">Days Remaining</p>
              <p className={`text-2xl font-bold ${RISK_CONFIG[selectedItem.risk_level]?.color}`}>
                {selectedItem.projected_days_until_stockout >= 999 ? '∞' : Math.round(selectedItem.projected_days_until_stockout)}
              </p>
              <p className="text-xs text-slate-500">projected</p>
            </div>
            <div className="bg-slate-800/60 rounded-xl p-3">
              <p className="text-xs text-slate-400">Recommended Order</p>
              <p className="text-2xl font-bold text-sky-400">{selectedItem.recommended_reorder_quantity}</p>
              <p className="text-xs text-slate-500">units</p>
            </div>
          </div>
          <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
            <p className="text-sm text-slate-300 mb-2">{selectedItem.explanation}</p>
            <p className="text-sm font-semibold text-sky-400">💡 {selectedItem.recommended_action}</p>
          </div>
        </div>
      )}

      {/* Product List */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-500">
          <Package className="w-12 h-12 mb-3 opacity-40" />
          <p className="font-semibold">No products match the selected filter.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-xs text-slate-500 font-medium">{filtered.length} product{filtered.length !== 1 ? 's' : ''} — sorted by risk level</p>
          {filtered.map(item => (
            <ProductCard key={item.product_id} item={item} onViewDetails={handleViewDetails} />
          ))}
        </div>
      )}

      <Toast type={toast.type} message={toast.message} onClose={() => setToast({ message: '', type: 'info' })} />
    </div>
  );
}
