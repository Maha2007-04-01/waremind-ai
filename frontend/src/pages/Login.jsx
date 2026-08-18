import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Layers, User, Lock, ArrowRight, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthProvider';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [username, setUsername] = useState('manager');
  const [password, setPassword] = useState('waremind2026');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const executeLogin = async (userVal, passVal) => {
    setError('');
    setLoading(true);

    try {
      await login(userVal, passVal);
      setLoading(false);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Authentication failed. Please try again.');
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('Please enter both username/email and password.');
      return;
    }
    executeLogin(username.trim(), password);
  };

  const handle1ClickFillAndLogin = (userKey) => {
    setUsername(userKey);
    setPassword('waremind2026');
    executeLogin(userKey, 'waremind2026');
  };

  return (
    <div className="min-h-screen bg-[#090d16] flex items-center justify-center p-4 sm:p-6 relative overflow-hidden font-sans text-slate-100">
      {/* Background ambient lighting effects */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-sky-500/10 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="w-full max-w-[440px] relative z-10 space-y-6">
        {/* Brand Header & Logo Stack */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center justify-center p-3.5 bg-gradient-to-tr from-sky-500 to-blue-600 rounded-2xl shadow-xl shadow-sky-500/25">
            <Layers className="w-9 h-9 text-slate-950" />
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-center space-x-2">
              <h1 className="text-3xl font-extrabold text-slate-100 tracking-tight">
                WareMind
              </h1>
              <span className="px-2 py-0.5 bg-sky-500 text-slate-950 text-xs font-black rounded-md tracking-wider">
                AI
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Intelligent Decisions. Faster Fulfillment. Smarter Warehouses.
            </p>
          </div>
        </div>

        {/* Main Card Container */}
        <div className="bg-slate-900/80 border border-slate-800/90 backdrop-blur-2xl p-6 sm:p-7 rounded-2xl shadow-2xl space-y-5">
          {error && (
            <div className="p-3.5 bg-rose-950/80 border border-rose-500/40 rounded-xl text-rose-300 text-xs font-medium flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username Input */}
            <div className="space-y-1.5 text-left">
              <label className="block text-xs font-semibold text-slate-300">
                Username or Email
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    setError('');
                  }}
                  className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 font-medium transition-all"
                  placeholder="e.g. manager or admin"
                  required
                />
              </div>
            </div>

            {/* Password Input */}
            <div className="space-y-1.5 text-left">
              <label className="block text-xs font-semibold text-slate-300">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setError('');
                  }}
                  className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 font-medium transition-all"
                  placeholder="••••••••••••"
                  required
                />
              </div>
            </div>

            {/* Main Submit Action Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-sky-500 to-sky-400 hover:from-sky-400 hover:to-sky-300 text-slate-950 font-extrabold text-sm rounded-xl shadow-lg shadow-sky-500/20 transition-all flex items-center justify-center space-x-2 mt-2 disabled:opacity-50"
            >
              {loading ? (
                <span>Entering Command Center...</span>
              ) : (
                <>
                  <span>Enter Operations Command Center</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Accounts Grid (1-Click Fill & Real Login) */}
          <div className="pt-3 border-t border-slate-800/80 space-y-2.5">
            <h4 className="text-[11px] font-bold text-slate-400 tracking-wider text-center uppercase">
              QUICK DEMO ACCOUNTS (1-CLICK FILL)
            </h4>

            <div className="grid grid-cols-2 gap-2 text-left">
              {/* Manager Card */}
              <button
                type="button"
                onClick={() => handle1ClickFillAndLogin('manager')}
                className="p-3 rounded-xl border bg-slate-950/80 hover:bg-sky-500/10 border-slate-800/80 hover:border-sky-500/50 text-slate-300 transition-all group"
              >
                <div className="font-bold text-xs group-hover:text-sky-300">Manager</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Full WH Access</div>
              </button>

              {/* Admin Card */}
              <button
                type="button"
                onClick={() => handle1ClickFillAndLogin('admin')}
                className="p-3 rounded-xl border bg-slate-950/80 hover:bg-sky-500/10 border-slate-800/80 hover:border-sky-500/50 text-slate-300 transition-all group"
              >
                <div className="font-bold text-xs group-hover:text-sky-300">Admin</div>
                <div className="text-[10px] text-slate-400 mt-0.5">System Config</div>
              </button>

              {/* Customer Card */}
              <button
                type="button"
                onClick={() => handle1ClickFillAndLogin('customer')}
                className="p-3 rounded-xl border bg-slate-950/80 hover:bg-sky-500/10 border-slate-800/80 hover:border-sky-500/50 text-slate-300 transition-all group"
              >
                <div className="font-bold text-xs group-hover:text-sky-300">Customer</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Order Tracking</div>
              </button>

              {/* Quality Control / Picker Card */}
              <button
                type="button"
                onClick={() => handle1ClickFillAndLogin('picker')}
                className="p-3 rounded-xl border bg-slate-950/80 hover:bg-sky-500/10 border-slate-800/80 hover:border-sky-500/50 text-slate-300 transition-all group"
              >
                <div className="font-bold text-xs group-hover:text-sky-300">Quality Control</div>
                <div className="text-[10px] text-slate-400 mt-0.5">QC Checklist</div>
              </button>
            </div>
          </div>
        </div>

        {/* Link to Register Page */}
        <div className="text-center text-xs text-slate-400 pt-1">
          <span>Need a new account? </span>
          <Link to="/register" className="text-sky-400 hover:text-sky-300 font-bold underline underline-offset-4">
            Register Here &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
