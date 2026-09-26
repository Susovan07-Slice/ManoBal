'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { Info, ShieldAlert } from 'lucide-react';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [isLoading, user, router]);

  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-background flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-mono text-textSecondary uppercase tracking-widest">
          Authenticating Command Session...
        </p>
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
        <div className="bg-surfaceHighlight/50 border-b border-surfaceHighlight px-6 py-1.5 flex items-center justify-between text-[11px] text-textSecondary">
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
