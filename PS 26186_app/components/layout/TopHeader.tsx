'use client';

import React from 'react';
import { useAuth } from '@/lib/AuthContext';
import { LogOut, User } from 'lucide-react';

export default function TopHeader({ title }: { title: string }) {
  const { user, logout } = useAuth();

  return (
    <header className="flex items-center justify-between px-6 h-16 bg-[rgba(20,35,28,0.55)] backdrop-blur-[16px] border-b border-white/10 shrink-0 sticky top-0 z-40">
      <div className="flex items-center space-x-2">
        <h1 className="text-lg font-semibold text-[#f5f5f0] tracking-wide">{title}</h1>
      </div>

      {user && (
        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1">
            <User className="w-3.5 h-3.5 text-mb-accent" />
            <span className="font-mono text-[11px] text-[#f5f5f0]/80">{user.username}</span>
          </div>
          <button
            onClick={logout}
            title="Sign Out"
            className="p-1 hover:bg-white/10 rounded text-[#f5f5f0]/60 hover:text-mb-danger transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      )}
    </header>
  );
}


