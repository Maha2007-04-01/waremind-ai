import React from 'react';
import { Activity, Clock, Shield, CheckCircle2, Box, Truck, AlertCircle } from 'lucide-react';

export default function AuditFeed({ logs = [] }) {
  const getActionIcon = (action = '') => {
    const act = action.toUpperCase();
    if (act.includes('ALLOCATION')) return <Box className="w-3.5 h-3.5 text-sky-400" />;
    if (act.includes('PICKING') || act.includes('PACKING')) return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
    if (act.includes('DISPATCH')) return <Truck className="w-3.5 h-3.5 text-purple-400" />;
    if (act.includes('EXCEPTION') || act.includes('DAMAGE')) return <AlertCircle className="w-3.5 h-3.5 text-rose-400" />;
    return <Shield className="w-3.5 h-3.5 text-slate-400" />;
  };

  const formatTimestamp = (ts) => {
    if (!ts) return 'Just now';
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return ts;
    }
  };

  return (
    <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-sky-500/10 text-sky-400 rounded-xl border border-sky-500/20">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">Operational Audit & Event Stream</h3>
            <p className="text-xs text-slate-400">Live chronological system decision and inventory activity log</p>
          </div>
        </div>
        <span className="text-xs text-slate-400 font-mono">Live Feed</span>
      </div>

      {logs.length === 0 ? (
        <div className="py-6 text-center text-slate-500 text-xs">
          No recent audit events recorded.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
          {logs.slice(0, 8).map((log) => (
            <div 
              key={log.id} 
              className="p-3 bg-slate-900/60 border border-slate-800/80 rounded-xl flex items-start justify-between space-x-3 text-xs"
            >
              <div className="flex items-start space-x-2.5 min-w-0">
                <div className="mt-0.5 p-1 bg-slate-950 rounded border border-slate-800">
                  {getActionIcon(log.action)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-slate-200 font-mono">{log.action}</span>
                    <span className="text-[10px] px-1.5 py-0.5 bg-slate-950 text-slate-400 rounded font-mono border border-slate-800">{log.entity_type}</span>
                  </div>
                  <p className="text-slate-400 mt-0.5 truncate">{log.description}</p>
                </div>
              </div>
              <div className="flex items-center space-x-1 text-slate-500 text-[11px] flex-shrink-0">
                <Clock className="w-3 h-3" />
                <span>{formatTimestamp(log.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
