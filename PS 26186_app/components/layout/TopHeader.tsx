'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/lib/AuthContext';
import { LogOut, MapPin, Bell } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getUnreadCount } from '@/lib/notifications';
import NotificationDrawer from '@/components/notifications/NotificationDrawer';

export default function TopHeader({ title }: { title: string }) {
  const { user, logout } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);
  const [isTitleHovered, setIsTitleHovered] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

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

  const battalionLocationText = user
    ? [user.battalion, user.location].filter(Boolean).join(' • ')
    : '';

  return (
    <>
      <header
        className={cn(
          "flex items-center justify-between px-3 sm:px-5 h-16 shrink-0 sticky top-0 z-40 transition-all",
          scrolled ? "bg-white/60 backdrop-blur-xl shadow-[0_4px_20px_rgba(31,110,140,0.08)]" : "bg-transparent"
        )}
      >
        <div 
          className="flex items-center space-x-2 sm:space-x-4 flex-1 min-w-0 transition-all duration-500 ease-out"
          onMouseEnter={() => setIsTitleHovered(true)}
          onMouseLeave={() => setIsTitleHovered(false)}
        >
          <div className="w-14 h-14 sm:w-20 sm:h-20 shrink-0 flex items-center justify-center transition-all duration-500 ease-out">
            <img src="/logo.png" alt="ManoBal Logo" className="w-full h-full object-contain" />
          </div>
          <h1 
            className="text-lg sm:text-2xl font-bold text-ink tracking-wide leading-tight truncate transition-all duration-500 ease-out"
            title={title}
          >
            {title}
          </h1>
        </div>

        {user && (
          <div className="flex items-center space-x-3 shrink-0 pl-2">
            <div 
              className={cn(
                "flex-col items-end text-right transition-all duration-500 ease-out overflow-hidden hidden sm:flex",
                isTitleHovered ? "max-w-0 opacity-0 space-x-0" : "max-w-[200px] opacity-100"
              )}
            >
              <span className="text-[12px] font-semibold text-ink whitespace-nowrap">{user.username}</span>
              {battalionLocationText && (
                <span className="inline-flex items-center bg-ok-bg text-ok text-[10px] font-semibold px-2.5 py-0.5 rounded-full mt-0.5 whitespace-nowrap">
                  <MapPin className="w-2.5 h-2.5 mr-1 text-ok shrink-0" />
                  {battalionLocationText}
                </span>
              )}
            </div>

            <div 
              className={cn(
                "flex-col items-end text-right transition-all duration-500 ease-out overflow-hidden sm:hidden flex",
                isTitleHovered ? "max-w-0 opacity-0" : "max-w-[100px] opacity-100"
              )}
            >
              <span className="text-[11px] font-semibold text-ink whitespace-nowrap">{user.username}</span>
            </div>

            {/* Notification Bell Button */}
            <button
              onClick={() => setDrawerOpen(true)}
              title="Welfare Notifications"
              className="relative w-10 h-10 shrink-0 rounded-full bg-white/80 backdrop-blur-md border border-white/60 shadow-[0_4px_12px_rgba(31,110,140,0.08)] flex items-center justify-center text-ink-2 hover:text-brand-600 hover:bg-white transition-all duration-200"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 px-1.5 py-0.5 min-w-[20px] h-[20px] text-[10px] font-bold bg-alert text-white rounded-full flex items-center justify-center shadow-md animate-pulse">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
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
