import React from 'react';
import { Layers, CheckCircle2, AlertCircle } from 'lucide-react';

export default function ZoneWorkloadVisualizer({ inventory = [] }) {
  // Aggregate stock and capacity by Zone
  const zoneStats = {
    'Zone A': { label: 'Fast-Pick Zone', totalItems: 0, damaged: 0, maxCap: 800, color: 'sky' },
    'Zone B': { label: 'Bulk Storage', totalItems: 0, damaged: 0, maxCap: 1700, color: 'indigo' },
    'Zone C': { label: 'Hazmat / Overstock', totalItems: 0, damaged: 0, maxCap: 600, color: 'amber' },
    'Zone D': { label: 'Cold Storage', totalItems: 0, damaged: 0, maxCap: 400, color: 'emerald' },
  };

  inventory.forEach((inv) => {
    const zone = inv.location?.zone || 'Zone A';
    if (zoneStats[zone]) {
      zoneStats[zone].totalItems += inv.quantity || 0;
      zoneStats[zone].damaged += inv.damaged_quantity || 0;
    }
  });

  return (
    <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">Warehouse Zone Capacity & Workload</h3>
            <p className="text-xs text-slate-400">Live storage density and picking zone distribution</p>
          </div>
        </div>
        <span className="text-xs text-slate-400 font-mono">4 Active Zones</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.entries(zoneStats).map(([zoneKey, z]) => {
          const pct = Math.min(100, Math.round((z.totalItems / z.maxCap) * 100));
          const isHigh = pct >= 85;
          return (
            <div key={zoneKey} className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-bold text-slate-100 text-sm">{zoneKey}</h4>
                  <p className="text-[11px] text-slate-400">{z.label}</p>
                </div>
                {isHigh ? (
                  <AlertCircle className="w-4 h-4 text-amber-400" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                )}
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-400">Occupancy</span>
                  <span className={pct > 85 ? 'text-amber-400' : 'text-slate-200'}>{pct}% ({z.totalItems} / {z.maxCap})</span>
                </div>
                <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                  <div 
                    className={`h-full transition-all duration-500 ${
                      pct > 85 ? 'bg-amber-400' : 'bg-gradient-to-r from-sky-500 to-indigo-500'
                    }`} 
                    style={{ width: `${pct}%` }}
                  ></div>
                </div>
              </div>

              <div className="flex justify-between text-[11px] text-slate-400 border-t border-slate-800/80 pt-2">
                <span>Damaged: <strong className="text-rose-400">{z.damaged}</strong></span>
                <span>Status: <strong className="text-emerald-400">Optimal</strong></span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
