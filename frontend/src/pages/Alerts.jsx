import React, { useState, useEffect } from 'react';
import { AlertTriangle, ShieldAlert, Cpu, CheckCircle } from 'lucide-react';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Toast from '../components/common/Toast';
import { fetchExceptions, resolveException } from '../services/api';
import { formatDate } from '../utils/formatters';

export default function Alerts() {
  const [loading, setLoading] = useState(true);
  const [exceptions, setExceptions] = useState([]);
  const [toast, setToast] = useState({ message: '', type: 'info' });
  const [resolvingId, setResolvingId] = useState(null);

  const loadExceptions = async () => {
    setLoading(true);
    try {
      const res = await fetchExceptions();
      setExceptions(res.data || []);
    } catch (err) {
      setToast({ message: err.message || 'Failed to load exceptions', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExceptions();
  }, []);

  const handleResolve = async (excId) => {
    setResolvingId(excId);
    try {
      const res = await resolveException(excId);
      const resolution = res.data?.resolution;
      setToast({ message: `Exception resolved: ${resolution}`, type: 'success' });
      loadExceptions();
    } catch (err) {
      setToast({ message: err.message || 'Resolution failed', type: 'error' });
    } finally {
      setResolvingId(null);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading active warehouse exceptions and alerts..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-slate-950 p-6 rounded-2xl border border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Exception & Alert Triage</h1>
          <p className="text-sm text-slate-400 mt-1">Review operational bottlenecks, stock shortages, damaged inventory alerts, and automated resolutions.</p>
        </div>
      </div>

      <div className="bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-semibold bg-slate-900/30">
                <th className="py-3 px-4">Exception Type</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Order / Product</th>
                <th className="py-3 px-4">Description</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Created At</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300 font-medium">
              {exceptions.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500">
                    No active exceptions detected. All operations running smoothly!
                  </td>
                </tr>
              ) : (
                exceptions.map(exc => (
                  <tr key={exc.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-100">{exc.exception_type}</td>
                    <td className="py-3 px-4">
                      <Badge variant={exc.severity}>{exc.severity}</Badge>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-200">{exc.order_number || exc.order_id || 'N/A'}</div>
                      <div className="text-slate-500 font-mono text-[11px]">{exc.product_sku || exc.product_id}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-300 max-w-xs">{exc.description}</td>
                    <td className="py-3 px-4">
                      <Badge variant={exc.status === 'RESOLVED' ? 'success' : 'medium'}>{exc.status}</Badge>
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-mono">{formatDate(exc.created_at)}</td>
                    <td className="py-3 px-4 text-right">
                      {exc.status !== 'RESOLVED' ? (
                        <button
                          onClick={() => handleResolve(exc.id)}
                          disabled={resolvingId === exc.id}
                          className="px-2.5 py-1 bg-sky-500 hover:bg-sky-400 text-slate-950 rounded font-semibold transition-colors text-[11px] inline-flex items-center space-x-1"
                        >
                          <Cpu className="w-3 h-3" />
                          <span>{resolvingId === exc.id ? 'Resolving...' : 'Auto-Resolve'}</span>
                        </button>
                      ) : (
                        <span className="text-emerald-400 font-semibold text-[11px] flex items-center justify-end">
                          <CheckCircle className="w-3.5 h-3.5 mr-1" /> Resolved
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <Toast 
        type={toast.type} 
        message={toast.message} 
        onClose={() => setToast({ message: '', type: 'info' })} 
      />
    </div>
  );
}
