import React from 'react';
import { Cpu, AlertTriangle, ShieldAlert, Package, Boxes, Truck, ArrowRight, Sparkles } from 'lucide-react';
import Badge from '../common/Badge';

export default function AIOperationsCenter({ insights, onActionClick }) {
  if (!insights) {
    return (
      <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 text-center text-slate-500">
        AI Decision Engine evaluating warehouse metrics...
      </div>
    );
  }

  const recommendations = insights.smart_recommendations || [];
  const mode = insights.decision_engine_mode || 'RULE_BASED';

  const getCategoryIcon = (title = '') => {
    const t = title.toLowerCase();
    if (t.includes('stockout') || t.includes('reorder')) return <Package className="w-5 h-5 text-rose-400" />;
    if (t.includes('relocate') || t.includes('zone')) return <Boxes className="w-5 h-5 text-sky-400" />;
    if (t.includes('bottleneck') || t.includes('picking')) return <AlertTriangle className="w-5 h-5 text-amber-400" />;
    if (t.includes('dispatch') || t.includes('carrier')) return <Truck className="w-5 h-5 text-emerald-400" />;
    return <ShieldAlert className="w-5 h-5 text-purple-400" />;
  };

  return (
    <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-gradient-to-tr from-sky-500 to-indigo-600 rounded-xl text-slate-950 shadow-lg shadow-sky-500/20">
            <Cpu className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-bold text-slate-100">AI Operations Center</h2>
              <span className="flex items-center space-x-1 px-2.5 py-0.5 bg-sky-500/10 text-sky-400 border border-sky-500/20 rounded-full text-xs font-semibold">
                <Sparkles className="w-3 h-3" />
                <span>{mode}</span>
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">Proactive Autonomous Decision & Risk Intelligence Engine</p>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          <span>{recommendations.length} Active Decision Recommendations</span>
        </div>
      </div>

      {recommendations.length === 0 ? (
        <div className="p-8 text-center text-slate-500 text-sm">
          All fulfillment systems operating within optimal parameters. No risk interventions required.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {recommendations.map((rec, idx) => (
            <div 
              key={idx} 
              className="bg-slate-900/90 border border-slate-800 hover:border-slate-700 p-5 rounded-xl flex flex-col justify-between transition-all hover:shadow-xl space-y-4 group"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2">
                    {getCategoryIcon(rec.title)}
                    <Badge variant={rec.severity}>{rec.severity}</Badge>
                  </div>
                  <span className="text-xs font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                    {Math.round((rec.confidence_score || 0.95) * 100)}% Confidence
                  </span>
                </div>

                <h3 className="font-bold text-slate-100 text-sm leading-snug group-hover:text-sky-400 transition-colors">
                  {rec.title}
                </h3>

                <div className="bg-slate-950/80 p-3 rounded-lg border border-slate-800/80 space-y-1.5 text-xs">
                  <p className="text-sky-300 font-semibold flex items-center">
                    <span className="text-slate-500 mr-1.5 font-normal">Action:</span> {rec.recommendation}
                  </p>
                  <p className="text-slate-400">
                    <span className="text-slate-500 mr-1.5">Reason:</span> {rec.reason}
                  </p>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <div className="text-slate-400 truncate max-w-[180px]">
                  <span className="text-slate-500 mr-1">Impact:</span> 
                  <span className="text-emerald-400">{rec.expected_impact || 'Operational optimization'}</span>
                </div>
                {onActionClick && (
                  <button 
                    onClick={() => onActionClick(rec)}
                    className="text-sky-400 hover:text-sky-300 font-semibold flex items-center space-x-1 group-hover:translate-x-0.5 transition-transform"
                  >
                    <span>Execute</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
