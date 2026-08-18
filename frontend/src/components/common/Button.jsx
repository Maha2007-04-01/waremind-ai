import React from 'react';

export default function Button({ children, onClick, variant = 'primary', className = '', ...props }) {
  const base = "px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center space-x-2";
  const variants = {
    primary: "bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold",
    secondary: "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700",
    danger: "bg-rose-500 hover:bg-rose-400 text-white font-semibold"
  };

  return (
    <button 
      onClick={onClick} 
      className={`${base} ${variants[variant] || variants.primary} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
