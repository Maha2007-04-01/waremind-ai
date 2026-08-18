import React from 'react';
import { PackageX } from 'lucide-react';
import Button from './Button';

export default function EmptyState({ icon: Icon = PackageX, title = "No Data Available", description = "No items match the selected filter or query.", actionLabel, onAction }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-slate-950/50 rounded-2xl border border-slate-800 space-y-4">
      <div className="p-4 bg-slate-900 rounded-full text-slate-400">
        <Icon className="w-8 h-8" />
      </div>
      <div>
        <h3 className="text-lg font-semibold text-slate-200">{title}</h3>
        <p className="text-sm text-slate-400 mt-1 max-w-sm">{description}</p>
      </div>
      {actionLabel && onAction && (
        <Button variant="primary" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
