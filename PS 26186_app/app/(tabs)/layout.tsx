'use client';

import React, { useEffect, useState } from 'react';
import TopHeader from '@/components/layout/TopHeader';
import BottomTabBar from '@/components/layout/BottomTabBar';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { getStoredToken } from '@/lib/api';

export default function TabsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isLoading } = useAuth();
  
  let title = "Home";
  if (pathname === "/assessment") title = "Daily Assessment";
  if (pathname === "/trends") title = "Personal Trends";

  const [mounted, setMounted] = useState(false);
  // Check localStorage immediately to avoid flashing spinner for returning users
  const hasStoredSession = typeof window !== 'undefined' ? !!getStoredToken() : false;

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isLoading && !user) {
      router.replace('/login');
    }
  }, [mounted, isLoading, user, router]);

  // Only block render on first visit (no stored session) or when loading without any user data
  const shouldBlock = !mounted || (isLoading && !hasStoredSession && !user);

  if (shouldBlock) {
    return (
      <div className="flex flex-col h-full items-center justify-center bg-transparent backdrop-blur-sm text-mb-text-secondary p-6 space-y-3">
        <div className="w-8 h-8 border-2 border-mb-accent border-t-transparent rounded-full animate-spin" />
        <span className="text-xs font-mono tracking-widest uppercase">
          Verifying Service Token...
        </span>
        <a
          href="/login"
          className="text-xs font-mono text-emerald-400 hover:text-emerald-300 underline mt-2"
        >
          Click here if not redirected automatically
        </a>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex flex-col h-full overflow-hidden absolute inset-0">
      <TopHeader title={title} />
      <main className="flex-1 overflow-y-auto bg-transparent pb-28">
        {children}
      </main>
      <BottomTabBar />
    </div>
  );
}


