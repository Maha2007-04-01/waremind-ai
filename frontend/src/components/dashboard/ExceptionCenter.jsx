import React, { useState } from 'react';
import { AlertCircle, AlertTriangle, ShieldAlert, CheckCircle, ArrowUpRight } from 'lucide-react';
import Badge from '../common/Badge';
import { resolveException } from '../../services/api';

export default function ExceptionCenter({ exceptions = [], onRefresh, setToast }) {
  const [resolvingId, setResolvingId] = useState(null);

  const activeExceptions = exceptions.filter(e => e.status !== 'RESOLVED');

  const handleQuickResolve = async (excId) => {
    setResolvingId(excId);
    try {
      await resolveException(excId, 'AUTO_TRIAGE', 'Automated exception triage applied by AI Decision Center');
      if (setToast) setToast({ type: 'success', message: `Exception ${excId} resolved successfully.` });
      if (onRefresh) onRefresh();
    } catch (err) {
      if (setToast) setToast({ type: 'error', message: `Failed to resolve exception: ${err.message}` });
    } finally {
      setResolvingId(null);
    }
  };

  return (
    <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-rose-500/10 text-rose-400 rounded-xl border border-rose-500/20">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">Operational Exception Center</h3>
            <p className="text-xs text-slate-400">Real-time fulfillment alerts, stock deficits, and SLA risk triage</p>
          </div>
        </div>
        <span className="px-2.5 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-full text-xs font-semibold">
          {activeExceptions.length} Unresolved
        </span>
      </div>

      {activeExceptions.length === 0 ? (
        <div className="py-8 text-center text-slate-500 text-sm flex flex-col items-center space-y-2">
          <CheckCircle className="w-8 h-8 text-emerald-400/80" />
          <span>No active exceptions detected. Fulfillment lines running smoothly.</span>
        </div>
      ) : (
        <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
          {activeExceptions.slice(0, 5).map((exc) => (
            <div 
              key={exc.id} 
              className="p-3.5 bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-xl flex items-center justify-between space-x-3 transition-colors"
            >
              <div className="flex items-start space-x-3 min-w-0 flex-1">
                <AlertTriangle className={`w-4 h-4 mt-0.5 flex-shrink-0 ${exc.severity === 'CRITICAL' ? 'text-rose-400' : 'text-amber-400'}`} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                    <span className="font-mono text-xs text-slate-400 font-semibold">{exc.id}</span>
                    <Badge variant={exc.severity}>{exc.severity}</Badge>
                    <span className="text-xs font-semibold text-slate-300 font-mono">{exc.exception_type}</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1 truncate">{exc.description}</p>
                </div>
              </div>

              <button
                onClick={() => handleQuickResolve(exc.id)}
                disabled={resolvingId === exc.id}
                className="px-3 py-1.5 bg-sky-950/80 hover:bg-sky-900/80 text-sky-300 border border-sky-800/60 rounded-lg text-xs font-semibold transition-colors flex-shrink-0 flex items-center space-x-1"
              >
                <span>{resolvingId === exc.id ? 'Resolving...' : 'Triage & Resolve'}</span>
                <ArrowUpRight className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
