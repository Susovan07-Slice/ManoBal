import React from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Skeleton } from '@/components/ui/Skeleton';

export default function DashboardLoading() {
  return (
    <div className="h-screen w-screen bg-[#070b09] flex flex-col items-center justify-center space-y-4 text-white">
      <div className="w-10 h-10 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      <p className="text-sm font-mono text-zinc-400 uppercase tracking-widest">
        Authenticating Command Session...
      </p>
    </div>
  );
}
