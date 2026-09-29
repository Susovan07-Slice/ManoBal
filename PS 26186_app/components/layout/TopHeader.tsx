'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/lib/AuthContext';
import { LogOut, Bell } from 'lucide-react';
import { getUnreadCount } from '@/lib/notifications';
import NotificationDrawer from '@/components/notifications/NotificationDrawer';

export default function TopHeader({ title }: { title: string }) {
  const { user, logout } = useAuth();
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);

  useEffect(() => {
    if (!user) return;
    let isMounted = true;

    const refreshCount = async () => {
      try {
        const count = await getUnreadCount();
        if (isMounted) setUnreadCount(count);
      } catch (err) {
        // silent fail
      }
    };

    refreshCount();
    // Poll unread count every 30 seconds
    const interval = setInterval(refreshCount, 30000);

    const handleEvent = () => refreshCount();
    const handleCountUpdate = (e: any) => {
      if (typeof e.detail?.unreadCount === 'number' && isMounted) {
        setUnreadCount(e.detail.unreadCount);
      }
    };
    const handleOpen = () => {
      if (isMounted) setDrawerOpen(true);
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('manobal:notification_refresh', handleEvent);
      window.addEventListener('manobal:notification_count_updated', handleCountUpdate);
      window.addEventListener('manobal:open_notifications', handleOpen);
    }

    return () => {
      isMounted = false;
      clearInterval(interval);
      if (typeof window !== 'undefined') {
        window.removeEventListener('manobal:notification_refresh', handleEvent);
        window.removeEventListener('manobal:notification_count_updated', handleCountUpdate);
        window.removeEventListener('manobal:open_notifications', handleOpen);
      }
    };
  }, [user]);

  return (
    <>
      <header className="flex items-center justify-between px-5 h-20 bg-black/25 backdrop-blur-2xl border-b border-white/10 shadow-[0_4px_30px_rgba(0,0,0,0.15)] shrink-0 sticky top-0 z-40 transition-all">
        <div className="flex items-center space-x-4">
          <div className="w-20 h-20 flex items-center justify-center">
            <img src="/logo.png" alt="ManoBal Logo" className="w-full h-full object-contain drop-shadow-lg" />
          </div>
          <h1 className="text-[20px] font-bold text-white/95 tracking-tight">{title}</h1>
        </div>

        {user && (
          <div className="flex items-center space-x-3">
            {/* Notification Bell Button */}
            <button
              onClick={() => setDrawerOpen(true)}
              title="Welfare Notifications"
              className="relative w-8 h-8 rounded-lg bg-white/10 border border-white/10 flex items-center justify-center text-white/80 hover:bg-white/20 transition-all"
            >
              <Bell className="w-4 h-4" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 px-1.5 py-0.2 min-w-[18px] h-[18px] text-[10px] font-bold bg-emerald-500 text-slate-950 rounded-full flex items-center justify-center shadow-md animate-pulse">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

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

      <NotificationDrawer
        isOpen={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          getUnreadCount().catch(() => {});
        }}
        onUnreadCountChange={setUnreadCount}
      />
    </>
  );
}
