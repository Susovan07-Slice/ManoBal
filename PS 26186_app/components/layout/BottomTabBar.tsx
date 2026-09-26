"use client";

import { Home, CheckSquare, ClipboardList, TrendingUp } from "lucide-react";
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
    <div className="absolute bottom-6 left-0 right-0 flex justify-center z-50 pointer-events-none">
      <nav className="flex items-center gap-2 h-16 bg-mb-glass-strong backdrop-blur-xl border border-mb-glass-border rounded-full px-3 shadow-[0_8px_30px_rgba(0,0,0,0.12)] pointer-events-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = pathname === tab.href;
          return (
            <Link
              key={tab.name}
              href={tab.href}
              className={cn(
                "flex flex-col items-center justify-center min-w-[72px] min-h-[48px] gap-1 transition-all duration-300 rounded-full px-3",
                isActive ? "text-mb-accent bg-mb-accent/15 shadow-[inset_0_1px_4px_rgba(0,0,0,0.3)] transform scale-105" : "text-mb-text-secondary hover:text-mb-text-primary hover:bg-white/5"
              )}
            >
              <Icon className={cn("w-5 h-5 transition-transform", isActive && "scale-110")} />
              <span className="text-[10px] font-medium tracking-wide">{tab.name}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}


