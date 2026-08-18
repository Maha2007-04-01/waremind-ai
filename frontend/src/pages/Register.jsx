import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Layers, User, Mail, Lock, ShieldCheck, ArrowRight, UserCheck, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthProvider';

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('Manager'); // Manager, Admin, Customer

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !username.trim() || !password) {
      setError('Please fill in all required fields.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      await register({ 
        name: name.trim(), 
        email: email.trim(), 
        username: username.trim(), 
        password, 
        role 
      });
      setLoading(false);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] flex items-center justify-center p-4 sm:p-6 relative overflow-hidden font-sans text-slate-100">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-sky-500/10 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="w-full max-w-[480px] relative z-10 space-y-5">
        {/* Brand Header */}
        <div className="text-center space-y-2">
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
              Create your account for WareMind Operations Control
            </p>
          </div>
        </div>

        {/* Register Card */}
        <div className="bg-slate-900/80 border border-slate-800/90 backdrop-blur-2xl p-6 sm:p-7 rounded-2xl shadow-2xl space-y-5">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-slate-100">Register Operational Account</h2>
            <p className="text-xs text-slate-400 mt-0.5">Select your role and enter your details to gain access.</p>
          </div>

          {error && (
            <div className="p-3 bg-rose-950/80 border border-rose-500/40 rounded-xl text-rose-300 text-xs font-medium flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Role Selection Tabs */}
            <div className="space-y-1.5 text-left">
              <label className="block text-xs font-semibold text-slate-300">
                Select Account Role
              </label>
              <div className="grid grid-cols-3 gap-2">
                {['Manager', 'Admin', 'Customer'].map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRole(r)}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-all text-center ${
                      role === r
                        ? 'bg-sky-500/10 border-sky-500/50 text-sky-300'
                        : 'bg-slate-950/80 border-slate-800 hover:border-slate-700 text-slate-400'
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>

            {/* Full Name */}
            <div className="space-y-1 text-left">
              <label className="block text-xs font-semibold text-slate-300">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    setError('');
                  }}
                  className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-sky-500 font-medium"
                  placeholder="e.g. Mahalakshmi"
                  required
                />
              </div>
            </div>

            {/* Email Address & Username */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1 text-left">
                <label className="block text-xs font-semibold text-slate-300">Work Email</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      setError('');
                    }}
                    className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-10 pr-3 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-sky-500 font-medium"
                    placeholder="maha401@gmail.com"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1 text-left">
                <label className="block text-xs font-semibold text-slate-300">Username</label>
                <div className="relative">
                  <UserCheck className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => {
                      setUsername(e.target.value);
                      setError('');
                    }}
                    className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-10 pr-3 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-sky-500 font-medium"
                    placeholder="Maha"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Password & Confirm Password */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1 text-left">
                <label className="block text-xs font-semibold text-slate-300">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      setError('');
                    }}
                    className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-10 pr-3 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-sky-500 font-medium"
                    placeholder="••••••••••"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1 text-left">
                <label className="block text-xs font-semibold text-slate-300">Confirm Password</label>
                <div className="relative">
                  <ShieldCheck className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      setError('');
                    }}
                    className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-10 pr-3 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-sky-500 font-medium"
                    placeholder="••••••••••"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Submit Action */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-sky-500 to-sky-400 hover:from-sky-400 hover:to-sky-300 text-slate-950 font-extrabold text-sm rounded-xl shadow-lg shadow-sky-500/20 transition-all flex items-center justify-center space-x-2 mt-2 disabled:opacity-50"
            >
              {loading ? (
                <span>Creating Account...</span>
              ) : (
                <>
                  <span>Register & Access Command Center</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Back to Login Link */}
        <div className="text-center text-xs text-slate-400 pt-1">
          <span>Already have an account? </span>
          <Link to="/login" className="text-sky-400 hover:text-sky-300 font-bold underline underline-offset-4">
            Sign In Here &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
