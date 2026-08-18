import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ label = "Loading data from WareMind AI..." }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 space-y-3">
      <Loader2 className="w-8 h-8 text-sky-400 animate-spin" />
      <span className="text-sm font-medium text-slate-400">{label}</span>
    </div>
  );
}
