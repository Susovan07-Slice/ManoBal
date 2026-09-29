import React, { useState } from "react";
import { Home, ClipboardList, TrendingUp, LogOut } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/AuthContext";

const tabs = [
  { name: "Home", href: "/", icon: Home },
  { name: "Assessment", href: "/assessment", icon: ClipboardList },
  { name: "Trends", href: "/trends", icon: TrendingUp },
  { name: "Logout", href: "#", icon: LogOut, action: "logout" },
];

export default function BottomTabBar() {
  const pathname = usePathname();
  const { logout } = useAuth();
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  return (
    <>
      <div 
        className="absolute left-4 right-4 flex justify-center z-50 pointer-events-none"
        style={{ bottom: "calc(16px + env(safe-area-inset-bottom, 0px))" }}
      >
        <nav className="flex items-center gap-1 h-16 bg-white/85 backdrop-blur-xl border border-white/60 rounded-full px-2 shadow-[0_16px_40px_rgba(31,110,140,0.22)] pointer-events-auto w-full max-w-[360px]">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = pathname === tab.href && tab.action !== "logout";
            
            if (tab.action === "logout") {
              return (
                <button
                  key={tab.name}
                  onClick={() => setShowLogoutConfirm(true)}
                  className="flex flex-col items-center justify-center flex-1 min-h-[44px] gap-0.5 transition-all duration-200 rounded-2xl py-1.5 text-ink-3 hover:text-alert"
                >
                  <Icon className="w-5 h-5 text-ink-3 hover:text-alert transition-colors" />
                  <span className="tracking-wide text-ink-3 text-[11px] font-medium hover:text-alert transition-colors">
                    {tab.name}
                  </span>
                </button>
              );
            }

            return (
              <Link
                key={tab.name}
                href={tab.href}
                className={cn(
                  "flex flex-col items-center justify-center flex-1 min-h-[44px] gap-0.5 transition-all duration-200 rounded-2xl py-1.5",
                  isActive ? "text-brand-600" : "text-ink-3"
                )}
              >
                {isActive ? (
                  <div className="w-9 h-9 rounded-xl bg-brand-100 flex items-center justify-center">
                    <Icon className="w-5 h-5 text-brand-500" />
                  </div>
                ) : (
                  <Icon className="w-5 h-5 text-ink-3" />
                )}
                <span className={cn(
                  "tracking-wide",
                  isActive ? "text-brand-600 font-semibold text-[11px]" : "text-ink-3 text-[11px] font-medium"
                )}>
                  {tab.name}
                </span>
              </Link>
            );
          })}
        </nav>
      </div>

      {showLogoutConfirm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm px-6 animate-fade-in pointer-events-auto">
          <div className="bg-white rounded-[24px] p-6 w-full max-w-[320px] shadow-2xl animate-fade-up">
            <h3 className="text-[18px] font-bold text-ink mb-1.5">Sign Out</h3>
            <p className="text-[13px] text-ink-2 mb-6 leading-relaxed">Are you sure you want to log out of the ManoBal Portal?</p>
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setShowLogoutConfirm(false)}
                className="flex-1 py-3 px-4 rounded-xl font-bold text-[13px] text-ink-3 bg-gray-100 hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={() => {
                  setShowLogoutConfirm(false);
                  logout();
                }}
                className="flex-1 py-3 px-4 rounded-xl font-bold text-[13px] text-white bg-alert hover:bg-alert/90 shadow-[0_8px_16px_rgba(240,80,140,0.25)] transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
