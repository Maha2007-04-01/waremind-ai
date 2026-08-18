import React, { useEffect } from 'react';
import { CheckCircle, AlertTriangle, XCircle, Info, X } from 'lucide-react';

export default function Toast({ type = 'info', message, onClose, duration = 4000 }) {
  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(() => {
      onClose();
    }, duration);
    return () => clearTimeout(timer);
  }, [message, duration, onClose]);

  if (!message) return null;

  const styles = {
    success: 'bg-emerald-950/90 border-emerald-500/40 text-emerald-300',
    error: 'bg-rose-950/90 border-rose-500/40 text-rose-300',
    warning: 'bg-amber-950/90 border-amber-500/40 text-amber-300',
    info: 'bg-sky-950/90 border-sky-500/40 text-sky-300',
  };

  const icons = {
    success: <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0" />,
    error: <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />,
    warning: <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />,
    info: <Info className="w-5 h-5 text-sky-400 flex-shrink-0" />,
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 animate-bounce-in max-w-md shadow-2xl">
      <div className={`px-4 py-3 rounded-xl border backdrop-blur-md flex items-center space-x-3 ${styles[type] || styles.info}`}>
        {icons[type] || icons.info}
        <span className="text-sm font-medium flex-1">{message}</span>
        <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg text-slate-400 hover:text-slate-200">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
