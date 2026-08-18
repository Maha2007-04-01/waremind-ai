import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Bell, Activity, Sparkles, RotateCcw, Database, LogOut, User } from 'lucide-react';
import ConfirmModal from '../common/ConfirmModal';
import Toast from '../common/Toast';
import { fetchSystemStatus, resetDemoData } from '../../services/api';
import { useAuth } from '../../context/AuthProvider';

export default function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const [systemStatus, setSystemStatus] = useState({ online: true, dbStatus: 'connected' });
  const [resetModalOpen, setResetModalOpen] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [toast, setToast] = useState({ type: '', message: '' });
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const checkStatus = async () => {
      try {
        const res = await fetchSystemStatus();
        if (isMounted && res.data) {
          setSystemStatus({
            online: res.data.application_status === 'ok',
            dbStatus: res.data.database_status
          });
        }
      } catch (err) {
        if (isMounted) {
          setSystemStatus({ online: false, dbStatus: 'disconnected' });
        }
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleResetDemo = async () => {
    setResetting(true);
    try {
      await resetDemoData();
      setToast({ type: 'success', message: 'Demo database reset successfully! Clean seed state restored.' });
      setResetModalOpen(false);
      setTimeout(() => {
        window.location.reload();
      }, 800);
    } catch (err) {
      setToast({ type: 'error', message: `Reset failed: ${err.message}` });
    } finally {
      setResetting(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getPageTitle = (path) => {
    if (path === '/') return 'Dashboard Control Center';
    if (path.startsWith('/inventory')) return 'Stock & Inventory Management';
    if (path.startsWith('/orders')) return 'Customer Order Queue';
    if (path.startsWith('/picking')) return 'Picking Station Workflow';
    if (path.startsWith('/packing')) return 'Packing & Barcode Verification';
    if (path.startsWith('/dispatch')) return 'Dispatch & Shipping Manifests';
    if (path.startsWith('/alerts')) return 'Exception & Risk Triage';
    if (path.startsWith('/analytics')) return 'Fulfillment Operations Analytics';
    if (path.startsWith('/settings')) return 'System Control & AI Settings';
    return 'WareMind AI Operations';
  };

  return (
    <>
      <header className="h-16 bg-slate-950 border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-40 backdrop-blur-md bg-slate-950/80">
        <div className="flex items-center space-x-3">
          <h2 className="text-lg font-bold text-slate-100">{getPageTitle(location.pathname)}</h2>
        </div>

        <div className="flex items-center space-x-3">
          {/* System Health Indicator */}
          <div className="flex items-center space-x-2 px-3 py-1 bg-slate-900 border border-slate-800 rounded-full text-xs">
            <span className={`w-2 h-2 rounded-full ${systemStatus.online ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`}></span>
            <span className="text-slate-300 font-medium">
              {systemStatus.online ? 'System Online' : 'System Offline'}
            </span>
            <span className="text-slate-600">|</span>
            <Database className="w-3 h-3 text-slate-400" />
            <span className="text-slate-400 font-mono capitalize">{systemStatus.dbStatus}</span>
          </div>

          {/* AI Active Indicator */}
          <div className="hidden lg:flex items-center space-x-2 px-3 py-1 bg-sky-500/10 text-sky-400 border border-sky-500/20 rounded-full text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 animate-pulse text-sky-400" />
            <span>AI Decision Engine</span>
          </div>

          {/* Reset Demo Button */}
          <button
            onClick={() => setResetModalOpen(true)}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-purple-950/60 hover:bg-purple-900/80 text-purple-300 border border-purple-800/60 rounded-xl text-xs font-semibold transition-colors"
            title="Reset Demo Seed Data"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Demo</span>
          </button>

          {/* Exception Bell */}
          <button 
            onClick={() => navigate('/alerts')}
            className="p-2 text-slate-400 hover:text-slate-200 bg-slate-900 hover:bg-slate-800 rounded-xl border border-slate-800 relative transition-colors"
            title="View Active Exceptions"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-rose-500 rounded-full animate-ping"></span>
          </button>

          {/* User Profile Avatar & Dropdown */}
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center space-x-2 p-1.5 bg-slate-900 hover:bg-slate-800 rounded-xl border border-slate-800 transition-colors"
            >
              <div className="w-7 h-7 bg-gradient-to-tr from-sky-500 to-indigo-600 rounded-lg flex items-center justify-center text-slate-950 font-bold text-xs shadow">
                {user?.name ? user.name.charAt(0) : 'A'}
              </div>
              <span className="hidden md:inline text-xs font-semibold text-slate-200 max-w-[100px] truncate">
                {user?.name || 'Alex Mercer'}
              </span>
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-3 z-50 space-y-2 text-xs">
                <div className="px-2 py-1.5 border-b border-slate-800">
                  <div className="font-bold text-slate-100">{user?.name || 'Alex Mercer'}</div>
                  <div className="text-[11px] text-slate-400 truncate">{user?.email || 'alex.mercer@waremind.ai'}</div>
                  <div className="mt-1 inline-block px-2 py-0.5 bg-sky-500/10 text-sky-400 border border-sky-500/20 rounded-full text-[10px] font-semibold">
                    {user?.role || 'Operations Lead'}
                  </div>
                </div>

                <button
                  onClick={handleLogout}
                  className="w-full flex items-center space-x-2 px-3 py-2 text-rose-400 hover:bg-rose-950/60 rounded-xl font-semibold transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out of Session</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Reset Confirmation Modal */}
      <ConfirmModal
        isOpen={resetModalOpen}
        title="Reset Demo Seed Data?"
        onConfirm={handleResetDemo}
        onCancel={() => setResetModalOpen(false)}
        confirmText="Reset Database"
        loading={resetting}
        confirmVariant="danger"
      >
        <p className="text-sm text-slate-300">
          This action will purge current runtime modifications and restore clean initial demo seed data (25 products, 15 locations, 41 inventory items, 15 orders, and 12 decision scenarios).
        </p>
      </ConfirmModal>

      {/* Toast Notification */}
      <Toast
        type={toast.type}
        message={toast.message}
        onClose={() => setToast({ type: '', message: '' })}
      />
    </>
  );
}
