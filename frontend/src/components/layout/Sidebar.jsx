import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Package, 
  ShoppingCart, 
  Boxes, 
  PackageCheck, 
  Truck, 
  Bell, 
  BarChart3, 
  Settings,
  Brain,
  TrendingDown,
  Search,
  Bot
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Inventory', path: '/inventory', icon: Package },
  { name: 'Orders', path: '/orders', icon: ShoppingCart },
  { name: 'Picking Station', path: '/picking', icon: Boxes },
  { name: 'Packing Station', path: '/packing', icon: PackageCheck },
  { name: 'Dispatch & Shipping', path: '/dispatch', icon: Truck },
  { name: 'Alerts & Triage', path: '/alerts', icon: Bell },
  { name: 'Analytics', path: '/analytics', icon: BarChart3 },
  { name: 'System Settings', path: '/settings', icon: Settings },
];

// New AI-powered features
const aiNavigation = [
  { name: 'AI Copilot', path: '/copilot', icon: Bot },
  { name: 'Predictive Stockout', path: '/predictive-stockout', icon: TrendingDown },
  { name: 'Product Traceability', path: '/traceability', icon: Search },
];


export default function Sidebar() {
  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col h-screen sticky top-0">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800 flex items-center space-x-3">
        <div className="p-2 bg-gradient-to-tr from-sky-500 to-indigo-600 rounded-xl text-slate-950 font-bold shadow-lg shadow-sky-500/20">
          <Brain className="w-6 h-6 text-slate-950" />
        </div>
        <div>
          <h1 className="font-bold text-lg text-slate-100 tracking-tight">WareMind AI</h1>
          <p className="text-[11px] font-mono text-sky-400">Control Center v1.0</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                `w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30 shadow-md shadow-sky-500/5'
                    : 'text-slate-400 hover:bg-slate-900/80 hover:text-slate-200'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}

        {/* AI Features Divider */}
        <div className="pt-3 pb-1">
          <p className="text-[9px] uppercase tracking-widest text-slate-600 font-bold px-1 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-500 animate-pulse inline-block" />
            AI Features
          </p>
        </div>

        {aiNavigation.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                `w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-sky-500/10 to-indigo-500/10 text-sky-400 border border-sky-500/30 shadow-md shadow-sky-500/5'
                    : 'text-slate-400 hover:bg-slate-900/80 hover:text-slate-200'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>


      {/* Footer System Status */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/60">
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-mono text-[11px]">System Online: 100% OK</span>
        </div>
      </div>
    </aside>
  );
}
