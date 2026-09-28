'use client';

import React, { useEffect } from 'react';
import TopHeader from '@/components/layout/TopHeader';
import BottomTabBar from '@/components/layout/BottomTabBar';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';

export default function TabsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isLoading } = useAuth();
  
  let title = "Home";
  if (pathname === "/assessment") title = "Daily Assessment";
  if (pathname === "/trends") title = "Personal Trends";

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [isLoading, user, router]);

  if (isLoading) {
    return (
      <div className="flex flex-col h-full items-center justify-center bg-transparent p-6 space-y-3">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-[12px] font-semibold text-ink-3 tracking-wide">
          Verifying Service Token...
        </span>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex flex-col h-full overflow-hidden absolute inset-0">
      <TopHeader title={title} />
      <main className="flex-1 overflow-y-auto overflow-x-hidden bg-transparent pb-40 min-w-0">
        {children}
      </main>
      <BottomTabBar />
    </div>
  );
}
