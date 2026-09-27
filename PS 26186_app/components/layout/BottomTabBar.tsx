"use client";

import { Home, ClipboardList, TrendingUp } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const tabs = [
  { name: "Home", href: "/", icon: Home },
  { name: "Assessment", href: "/assessment", icon: ClipboardList },
  { name: "Trends", href: "/trends", icon: TrendingUp },
];

export default function BottomTabBar() {
  const pathname = usePathname();

  return (
    <div className="absolute bottom-5 left-4 right-4 flex justify-center z-50 pointer-events-none">
      <nav className="flex items-center gap-1 h-[60px] bg-black/40 backdrop-blur-2xl border border-white/15 rounded-2xl px-2 shadow-[0_8px_40px_rgba(0,0,0,0.25)] pointer-events-auto w-full max-w-[320px]">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = pathname === tab.href;
          return (
            <Link
              key={tab.name}
              href={tab.href}
              className={cn(
                "flex flex-col items-center justify-center flex-1 min-h-[44px] gap-0.5 transition-all duration-300 rounded-xl py-1.5",
                isActive
                  ? "text-white"
                  : "text-white/40 hover:text-white/60"
              )}
            >
              <Icon className={cn("w-5 h-5 transition-transform", isActive && "scale-110")} />
              <span className={cn(
                "text-[10px] font-medium tracking-wide",
                isActive ? "text-white/90" : "text-white/40"
              )}>
                {tab.name}
              </span>
              {isActive && (
                <div className="w-1 h-1 rounded-full bg-mb-accent mt-0.5 shadow-[0_0_6px_rgba(0,168,150,0.6)]" />
              )}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
