'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/lib/AuthContext';
import { LogOut, MapPin } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function TopHeader({ title }: { title: string }) {
  const { user, logout } = useAuth();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const battalionLocationText = user
    ? [user.battalion, user.location].filter(Boolean).join(' • ')
    : '';

  return (
    <header className={cn("flex items-center justify-between px-5 h-20 shrink-0 sticky top-0 z-40 transition-all", scrolled ? "bg-white/60 backdrop-blur-xl shadow-[0_4px_20px_rgba(31,110,140,0.08)]" : "bg-transparent")}>
      <div className="flex items-center space-x-4">
        <div className="w-14 h-14 rounded-full bg-white shadow-[0_2px_12px_rgba(31,110,140,0.15)] border-2 border-white flex items-center justify-center overflow-hidden">
          <img src="/logo.png" alt="ManoBal Logo" className="w-full h-full object-cover scale-110" />
        </div>
        <h1 className="text-[20px] font-bold text-ink tracking-tight">{title}</h1>
      </div>

      {user && (
        <div className="flex items-center space-x-3">
          <div className="flex flex-col items-end text-right">
            <span className="text-[12px] font-semibold text-ink">{user.username}</span>
            {battalionLocationText && (
              <span className="inline-flex items-center bg-ok-bg text-ok text-[10px] font-semibold px-2.5 py-0.5 rounded-full mt-0.5">
                <MapPin className="w-2.5 h-2.5 mr-1 text-ok shrink-0" />
                {battalionLocationText}
              </span>
            )}
          </div>
          <button
            onClick={logout}
            title="Sign Out"
            className="w-10 h-10 rounded-full bg-white shadow-[0_2px_8px_rgba(31,110,140,0.1)] flex items-center justify-center text-ink-3 hover:text-ink-2 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      )}
    </header>
  );
}
