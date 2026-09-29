import React from "react";
import { Home, ClipboardList, TrendingUp, User } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const tabs = [
  { name: "Home", href: "/", icon: Home },
  { name: "Assessment", href: "/assessment", icon: ClipboardList },
  { name: "Trends", href: "/trends", icon: TrendingUp },
  { name: "Account", href: "/account", icon: User },
];

export default function BottomTabBar() {
  const pathname = usePathname();

  return (
    <>
      <div 
        className="absolute left-4 right-4 flex justify-center z-50 pointer-events-none"
        style={{ bottom: "calc(16px + env(safe-area-inset-bottom, 0px))" }}
      >
        <nav className="flex items-center gap-1 h-16 bg-white/85 backdrop-blur-xl border border-white/60 rounded-full px-2 shadow-[0_16px_40px_rgba(31,110,140,0.22)] pointer-events-auto w-full max-w-[360px]">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = pathname === tab.href;

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
    </>
  );
}
