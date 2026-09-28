'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { Info } from 'lucide-react';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isLoading && !user) {
      router.replace('/login');
    }
  }, [mounted, isLoading, user, router]);

  // Safety fallback: if authentication resolution takes > 2.5 seconds, redirect to /login
  useEffect(() => {
    if (!mounted) return;
    const timer = setTimeout(() => {
      if (!user) {
        window.location.href = '/login';
      }
    }, 2500);
    return () => clearTimeout(timer);
  }, [mounted, user]);

  if (!mounted || isLoading) {
    return (
      <div
        className="h-screen w-screen bg-[#070b09] flex flex-col items-center justify-center space-y-4 text-white"
        style={{ backgroundColor: '#070b09', color: '#ffffff', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
      >
        <div
          className="w-10 h-10 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"
          style={{ width: '40px', height: '40px', borderRadius: '50%', border: '2px solid #10b981', borderTopColor: 'transparent' }}
        />
        <p className="text-sm font-mono text-zinc-400 uppercase tracking-widest" style={{ color: '#a1a1aa', fontFamily: 'monospace' }}>
          Authenticating Command Session...
        </p>
        <a
          href="/login"
          className="mt-2 text-xs font-mono text-emerald-400 hover:text-emerald-300 underline cursor-pointer"
          style={{ color: '#34d399', fontSize: '12px', textDecoration: 'underline', marginTop: '8px' }}
        >
          Click here if not redirected automatically
        </a>
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect via useEffect
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Topbar />
        
        {/* Persistent Prototype Notice */}
        <div className="bg-surface/80 border-b border-surfaceBorder px-6 py-1.5 flex items-center justify-between text-[11px] text-textSecondary">
          <div className="flex items-center space-x-2">
            <Info className="w-3.5 h-3.5 text-accent shrink-0" />
            <span>
              <strong className="text-textPrimary">Research Prototype:</strong> Synthetically augmented data only. Not actual CRPF records. Operational decision-support only.
            </span>
          </div>
          <span className="font-mono text-accent hidden sm:inline-block">ENV: LOCAL_SECURE</span>
        </div>

        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
