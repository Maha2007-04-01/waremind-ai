import React from 'react';
import { Package, ShoppingCart, AlertTriangle, Cpu } from 'lucide-react';

export default function SummaryCards() {
  const cards = [
    { title: 'Total SKUs', value: '0', icon: Package, color: 'text-sky-400' },
    { title: 'Active Orders', value: '0', icon: ShoppingCart, color: 'text-indigo-400' },
    { title: 'System Alerts', value: '0', icon: AlertTriangle, color: 'text-amber-400' },
    { title: 'AI Decisions Today', value: '0', icon: Cpu, color: 'text-emerald-400' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div key={idx} className="bg-slate-950 p-5 rounded-xl border border-slate-800 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-400">{card.title}</p>
              <h3 className="text-2xl font-bold text-slate-100 mt-1">{card.value}</h3>
            </div>
            <div className={`p-3 bg-slate-900 rounded-lg ${card.color}`}>
              <Icon className="w-6 h-6" />
            </div>
          </div>
        );
      })}
    </div>
  );
}
