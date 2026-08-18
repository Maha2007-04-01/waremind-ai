import React, { useState, useEffect } from 'react';
import { Cpu, Server, Database, RefreshCw, CheckCircle } from 'lucide-react';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Toast from '../components/common/Toast';
import { fetchDecisionInsights, fetchSystemStatus } from '../services/api';

export default function Settings() {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [mode, setMode] = useState('RULE_BASED');
  const [toast, setToast] = useState({ message: '', type: 'info' });

  const loadSettings = async () => {
    setLoading(true);
    try {
      const [sysRes, insRes] = await Promise.all([
        fetchSystemStatus(),
        fetchDecisionInsights()
      ]);
      setStatus(sysRes.data);
      setMode(insRes.data?.decision_engine_mode || 'RULE_BASED');
    } catch (err) {
      setToast({ message: err.message || 'Failed to load system settings', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  if (loading) {
    return <LoadingSpinner label="Loading WareMind AI system configuration..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-slate-950 p-6 rounded-2xl border border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Control Center & System Settings</h1>
          <p className="text-sm text-slate-400 mt-1">Configure AI decision parameters, API endpoints, database health, and system triggers.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* System Health Panel */}
        <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <Server className="w-5 h-5 text-sky-400" />
            <h3 className="font-bold text-slate-100 text-base">Backend Application Health</h3>
          </div>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-2 border-b border-slate-900">
              <span className="text-slate-400">Application Status</span>
              <Badge variant="success">{status?.application_status || 'ok'}</Badge>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-900">
              <span className="text-slate-400">Database Connection</span>
              <Badge variant="success">{status?.database_status || 'connected'}</Badge>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-900">
              <span className="text-slate-400">Total Products in DB</span>
              <span className="font-bold text-slate-200">{status?.number_of_products || 0}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-900">
              <span className="text-slate-400">Total Orders in DB</span>
              <span className="font-bold text-slate-200">{status?.number_of_orders || 0}</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-400">Active Warehouse Tasks</span>
              <span className="font-bold text-slate-200">{status?.active_warehouse_tasks || 0}</span>
            </div>
          </div>
        </div>

        {/* AI Engine Panel */}
        <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <Cpu className="w-5 h-5 text-purple-400" />
            <h3 className="font-bold text-slate-100 text-base">AI Decision Engine Configuration</h3>
          </div>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-2 border-b border-slate-900">
              <span className="text-slate-400">Active Decision Mode</span>
              <Badge variant={mode === 'GEMINI_ENHANCED' ? 'purple' : 'info'}>{mode}</Badge>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-900">
              <span className="text-slate-400">Fallback Engine</span>
              <span className="font-bold text-slate-200">Deterministic Rule Engine (100% Offline Capable)</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-400">SLA Margin Threshold</span>
              <span className="font-bold text-slate-200">4 Hours</span>
            </div>
          </div>
        </div>
      </div>

      <Toast 
        type={toast.type} 
        message={toast.message} 
        onClose={() => setToast({ message: '', type: 'info' })} 
      />
    </div>
  );
}
