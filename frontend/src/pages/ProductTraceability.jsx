import React, { useState, useRef } from 'react';
import { Search, Package, ShoppingCart, Clock, MapPin, ArrowRight, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';
import { traceProduct, traceOrder, searchTraceProducts } from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Toast from '../components/common/Toast';

const EVENT_COLORS = {
  STORED:        'border-sky-500/50 bg-sky-500/10 text-sky-400',
  ALLOCATED:     'border-purple-500/50 bg-purple-500/10 text-purple-400',
  PICKING:       'border-amber-500/50 bg-amber-500/10 text-amber-400',
  PACKING:       'border-blue-500/50 bg-blue-500/10 text-blue-400',
  QC_PASSED:     'border-emerald-500/50 bg-emerald-500/10 text-emerald-400',
  QC_FAILED:     'border-red-500/50 bg-red-500/10 text-red-400',
  DISPATCHED:    'border-green-500/50 bg-green-500/10 text-green-400',
  EXCEPTION:     'border-orange-500/50 bg-orange-500/10 text-orange-400',
  ORDER_CREATED: 'border-indigo-500/50 bg-indigo-500/10 text-indigo-400',
  DAMAGE_REPORTED:'border-red-500/50 bg-red-500/10 text-red-400',
  GENERAL:       'border-slate-500/50 bg-slate-500/10 text-slate-400',
};

function formatTimestamp(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return isNaN(d) ? ts : d.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
}

function TimelineEvent({ event, index }) {
  const [expanded, setExpanded] = useState(false);
  const colorClass = EVENT_COLORS[event.event_type] || EVENT_COLORS.GENERAL;

  return (
    <div className="flex gap-4">
      {/* Vertical line + dot */}
      <div className="flex flex-col items-center">
        <div className={`w-8 h-8 rounded-full border flex items-center justify-center text-sm flex-shrink-0 ${colorClass}`}>
          {event.icon}
        </div>
        <div className="w-0.5 flex-1 bg-slate-800 mt-1" />
      </div>

      {/* Event content */}
      <div className={`flex-1 mb-5 rounded-xl border p-4 ${colorClass} bg-opacity-5 cursor-pointer hover:shadow-md transition-all`}
        onClick={() => setExpanded(!expanded)}>
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="font-semibold text-slate-100 text-sm">{event.title}</p>
            <p className="text-xs text-slate-400 mt-0.5">{event.description}</p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {event.timestamp && (
              <span className="text-[10px] text-slate-500 font-mono">{formatTimestamp(event.timestamp)}</span>
            )}
            {event.details && Object.keys(event.details).length > 0 && (
              expanded ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            )}
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mt-2">
          {event.location && (
            <span className="flex items-center gap-1 text-[10px] bg-slate-800/60 px-2 py-0.5 rounded-full text-slate-300">
              <MapPin className="w-2.5 h-2.5" /> {event.location}
            </span>
          )}
          {event.quantity != null && (
            <span className="text-[10px] bg-slate-800/60 px-2 py-0.5 rounded-full text-slate-300">
              Qty: {event.quantity}
            </span>
          )}
          {event.worker && (
            <span className="text-[10px] bg-slate-800/60 px-2 py-0.5 rounded-full text-slate-300">
              👷 {event.worker}
            </span>
          )}
          {event.status && (
            <span className="text-[10px] bg-slate-800/60 px-2 py-0.5 rounded-full text-slate-300">
              {event.status}
            </span>
          )}
        </div>

        {expanded && event.details && Object.keys(event.details).length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-700/40 grid grid-cols-2 gap-2">
            {Object.entries(event.details).map(([k, v]) => (
              v != null && (
                <div key={k}>
                  <p className="text-[9px] uppercase text-slate-500 tracking-wide">{k.replace(/_/g, ' ')}</p>
                  <p className="text-xs text-slate-200 font-medium">{String(v)}</p>
                </div>
              )
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SearchPanel({ onTraceProduct, onTraceOrder }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [orderId, setOrderId] = useState('');
  const [mode, setMode] = useState('product'); // 'product' | 'order'

  const handleSearch = async () => {
    if (!query.trim() || query.trim().length < 2) return;
    setSearching(true);
    try {
      const res = await searchTraceProducts(query);
      setResults(res.data || []);
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setMode('product')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${mode === 'product' ? 'bg-sky-500 text-white' : 'text-slate-400 border border-slate-700 hover:border-slate-600'}`}
        >
          <Package className="w-3.5 h-3.5 inline mr-1.5" />Product / SKU
        </button>
        <button
          onClick={() => setMode('order')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${mode === 'order' ? 'bg-purple-500 text-white' : 'text-slate-400 border border-slate-700 hover:border-slate-600'}`}
        >
          <ShoppingCart className="w-3.5 h-3.5 inline mr-1.5" />Order Trace
        </button>
      </div>

      {mode === 'product' ? (
        <>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
                placeholder="Search product name or SKU (e.g. SKU-101, Gadget)"
                className="w-full bg-slate-800 border border-slate-700 text-slate-100 text-sm pl-9 pr-4 py-2.5 rounded-xl focus:outline-none focus:border-sky-500/60 placeholder-slate-500"
              />
            </div>
            <button onClick={handleSearch} disabled={searching}
              className="px-4 py-2.5 bg-sky-500 hover:bg-sky-400 text-white text-xs font-bold rounded-xl transition-all disabled:opacity-50">
              {searching ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Search'}
            </button>
          </div>
          {results.length > 0 && (
            <div className="mt-3 space-y-2">
              {results.map(r => (
                <button key={r.id} onClick={() => { onTraceProduct(r.id); setResults([]); setQuery(''); }}
                  className="w-full flex items-center justify-between bg-slate-800/60 border border-slate-700/50 hover:border-sky-500/40 p-3 rounded-xl transition-all text-left group">
                  <div>
                    <p className="font-semibold text-slate-100 text-sm group-hover:text-sky-300">{r.name}</p>
                    <p className="text-xs text-slate-400 font-mono">{r.sku} · {r.category} · {r.available} units available</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-sky-400" />
                </button>
              ))}
            </div>
          )}
        </>
      ) : (
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={orderId}
              onChange={e => setOrderId(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && onTraceOrder(orderId)}
              placeholder="Enter Order ID (e.g. ORD-001)"
              className="w-full bg-slate-800 border border-slate-700 text-slate-100 text-sm pl-9 pr-4 py-2.5 rounded-xl focus:outline-none focus:border-purple-500/60 placeholder-slate-500"
            />
          </div>
          <button onClick={() => onTraceOrder(orderId)} disabled={!orderId.trim()}
            className="px-4 py-2.5 bg-purple-500 hover:bg-purple-400 text-white text-xs font-bold rounded-xl transition-all disabled:opacity-50">
            Trace Order
          </button>
        </div>
      )}
    </div>
  );
}

export default function ProductTraceability() {
  const [loading, setLoading] = useState(false);
  const [traceData, setTraceData] = useState(null);
  const [traceType, setTraceType] = useState(null); // 'product' | 'order'
  const [toast, setToast] = useState({ message: '', type: 'info' });
  const resultRef = useRef(null);

  const handleTraceProduct = async (productId) => {
    setLoading(true);
    try {
      const res = await traceProduct(productId);
      setTraceData(res.data);
      setTraceType('product');
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    } catch (err) {
      setToast({ message: err.message || 'Failed to load product trace.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleTraceOrder = async (orderId) => {
    if (!orderId.trim()) return;
    setLoading(true);
    try {
      const res = await traceOrder(orderId.trim().toUpperCase());
      setTraceData(res.data);
      setTraceType('order');
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    } catch (err) {
      setToast({ message: err.message || 'Order not found. Check the Order ID.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-purple-500/10 border border-purple-500/30 rounded-xl">
          <Search className="w-5 h-5 text-purple-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-100">Product Traceability</h2>
          <p className="text-sm text-slate-400">Complete operational journey for any product or order</p>
        </div>
      </div>

      {/* Search Panel */}
      <SearchPanel onTraceProduct={handleTraceProduct} onTraceOrder={handleTraceOrder} />

      {/* Loading */}
      {loading && <LoadingSpinner label="Building traceability timeline..." />}

      {/* Results */}
      {!loading && traceData && (
        <div ref={resultRef} className="space-y-6">
          {/* Entity Header */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            {traceType === 'product' ? (
              <>
                <div className="flex items-center gap-3 mb-4">
                  <Package className="w-5 h-5 text-sky-400" />
                  <div>
                    <h3 className="font-bold text-slate-100 text-lg">{traceData.product?.name}</h3>
                    <p className="text-xs text-slate-400 font-mono">{traceData.product?.sku} · {traceData.product?.category}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { label: 'Total Stock', value: traceData.current_stock?.total, color: 'text-slate-100' },
                    { label: 'Available', value: traceData.current_stock?.available, color: 'text-emerald-400' },
                    { label: 'Reserved', value: traceData.current_stock?.reserved, color: 'text-amber-400' },
                    { label: 'Damaged', value: traceData.current_stock?.damaged, color: 'text-red-400' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-slate-800/60 rounded-xl p-3">
                      <p className="text-xs text-slate-400">{label}</p>
                      <p className={`text-xl font-bold ${color}`}>{value ?? 0}</p>
                    </div>
                  ))}
                </div>
                {traceData.current_locations?.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-slate-700/50">
                    <p className="text-xs text-slate-400 font-semibold uppercase tracking-wide mb-2">Current Locations</p>
                    <div className="flex flex-wrap gap-2">
                      {traceData.current_locations.map((loc, i) => (
                        <span key={i} className="flex items-center gap-1 text-xs bg-slate-800 border border-slate-700 px-2.5 py-1 rounded-full text-slate-300">
                          <MapPin className="w-3 h-3 text-sky-400" />
                          Zone {loc.zone}-{loc.aisle}-{loc.rack}-{loc.bin} ({loc.quantity} units)
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <>
                <div className="flex items-center gap-3 mb-4">
                  <ShoppingCart className="w-5 h-5 text-purple-400" />
                  <div>
                    <h3 className="font-bold text-slate-100 text-lg">{traceData.order?.order_number}</h3>
                    <p className="text-xs text-slate-400">{traceData.order?.customer_name} · {traceData.order?.priority} Priority · {traceData.order?.status}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                  {[
                    { label: 'Created', value: formatTimestamp(traceData.order?.created_at) },
                    { label: 'Required By', value: traceData.order?.required_by || '—' },
                    { label: 'Status', value: traceData.order?.status },
                    { label: 'Total Value', value: traceData.order?.total_value ? `$${traceData.order.total_value}` : '—' },
                  ].map(({ label, value }) => (
                    <div key={label} className="bg-slate-800/60 rounded-xl p-3">
                      <p className="text-xs text-slate-400">{label}</p>
                      <p className="text-sm font-bold text-slate-100">{value}</p>
                    </div>
                  ))}
                </div>
                {traceData.items?.length > 0 && (
                  <div>
                    <p className="text-xs text-slate-400 font-semibold uppercase tracking-wide mb-2">Order Items</p>
                    <div className="space-y-1">
                      {traceData.items.map((item, i) => (
                        <div key={i} className="flex items-center justify-between text-xs bg-slate-800/40 px-3 py-2 rounded-lg">
                          <span className="text-slate-300">{item.product_name} <span className="font-mono text-slate-500">({item.sku})</span></span>
                          <span className="text-slate-400">Req: {item.requested_quantity} | Alloc: {item.allocated_quantity} | Picked: {item.picked_quantity}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Timeline */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-6">
              <Clock className="w-4 h-4 text-slate-400" />
              <h3 className="font-bold text-slate-100">Operation Timeline</h3>
              <span className="text-xs text-slate-500">({traceData.total_events} events)</span>
            </div>

            {traceData.timeline?.length === 0 ? (
              <p className="text-slate-500 text-sm text-center py-8">No timeline events found.</p>
            ) : (
              <div>
                {traceData.timeline.map((event, i) => (
                  <TimelineEvent key={i} event={event} index={i} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <Toast type={toast.type} message={toast.message} onClose={() => setToast({ message: '', type: 'info' })} />
    </div>
  );
}


