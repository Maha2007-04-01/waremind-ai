import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function AlertBanner({ message = "System running normally. No critical bottlenecks detected." }) {
  return (
    <div className="bg-sky-500/10 border border-sky-500/20 p-4 rounded-xl flex items-center space-x-3 text-sky-400">
      <AlertCircle className="w-5 h-5 flex-shrink-0" />
      <span className="text-sm font-medium">{message}</span>
    </div>
  );
}
