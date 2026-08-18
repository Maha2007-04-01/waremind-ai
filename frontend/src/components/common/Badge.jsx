import React from 'react';

export default function Badge({ children, variant = 'info', className = '' }) {
  const variants = {
    critical: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    danger: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    high: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    medium: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
    low: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    info: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  };

  const key = (variant || 'info').toLowerCase();
  const style = variants[key] || variants.info;

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${style} ${className}`}>
      {children}
    </span>
  );
}
