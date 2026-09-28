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
      <div className="h-screen w-screen bg-background flex flex-col items-center justify-center space-y-4 text-textPrimary">
        <div className="w-10 h-10 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-mono text-textSecondary uppercase tracking-widest">
          Authenticating Command Session...
        </p>
        <a
          href="/login"
          className="mt-2 text-xs font-mono text-accent hover:underline cursor-pointer"
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

        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
