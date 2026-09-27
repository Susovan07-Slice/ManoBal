'use client';

import React from 'react';
import { useAuth } from '@/lib/AuthContext';
import { LogOut, Shield } from 'lucide-react';

export default function TopHeader({ title }: { title: string }) {
  const { user, logout } = useAuth();

  return (
    <header className="flex items-center justify-between px-5 h-14 bg-black/25 backdrop-blur-2xl border-b border-white/10 shadow-[0_4px_30px_rgba(0,0,0,0.15)] shrink-0 sticky top-0 z-40 transition-all">
      <div className="flex items-center space-x-2.5">
        <div className="w-7 h-7 rounded-full overflow-hidden shadow-lg shadow-mb-accent/20 border border-white/20">
          <img src="/manobal-logo.jpg" alt="ManoBal" className="w-full h-full object-cover" />
        </div>
        <h1 className="text-[15px] font-semibold text-white/95 tracking-tight">{title}</h1>
      </div>

      {user && (
        <div className="flex items-center space-x-3">
          <span className="text-[11px] font-medium text-white/60 tracking-wide">{user.username}</span>
          <button
            onClick={logout}
            title="Sign Out"
            className="w-7 h-7 rounded-lg bg-white/10 border border-white/10 flex items-center justify-center text-white/50 hover:bg-white/20 hover:text-white/80 transition-all"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </header>
  );
}
