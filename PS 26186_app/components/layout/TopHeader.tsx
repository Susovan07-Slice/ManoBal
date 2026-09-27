'use client';

import React from 'react';
import { useAuth } from '@/lib/AuthContext';
import { LogOut, User } from 'lucide-react';

export default function TopHeader({ title }: { title: string }) {
  const { user, logout } = useAuth();

  return (
    <header className="flex items-center justify-between px-5 h-16 bg-white/80 backdrop-blur-xl border-b border-gray-200/50 shadow-sm shrink-0 sticky top-0 z-40 transition-all">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-mb-accent to-emerald-400 flex items-center justify-center shadow-sm">
          <span className="text-white font-bold text-xs">MB</span>
        </div>
        <h1 className="text-[17px] font-bold text-gray-800 tracking-tight">{title}</h1>
      </div>

      {user && (
        <div className="flex items-center space-x-3">
          <div className="flex flex-col items-end mr-1 hidden sm:flex">
            <span className="text-xs font-semibold text-gray-700">{user.username}</span>
            <span className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">Active</span>
          </div>
          <button
            title="Profile & Options"
            className="w-8 h-8 rounded-full bg-gray-100 border border-gray-200 flex items-center justify-center text-gray-600 hover:bg-gray-200 transition-colors shadow-inner"
          >
            <User className="w-4 h-4" />
          </button>
          <button
            onClick={logout}
            title="Sign Out"
            className="w-8 h-8 rounded-full bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-500 hover:bg-rose-100 hover:text-rose-600 transition-colors shadow-inner"
          >
            <LogOut className="w-4 h-4 ml-0.5" />
          </button>
        </div>
      )}
    </header>
  );
}


