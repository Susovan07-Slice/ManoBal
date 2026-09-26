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
    <nav className="flex items-center justify-around h-20 bg-[#1C2530] border-t border-slate-800 shrink-0 px-2 pb-4">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = pathname === tab.href;
        return (
          <Link
            key={tab.name}
            href={tab.href}
            className={cn(
              "flex flex-col items-center justify-center min-w-[64px] min-h-[44px] gap-1 transition-colors rounded-xl px-2 py-1",
              isActive ? "text-teal-400" : "text-slate-400 hover:text-slate-300 hover:bg-slate-800/50"
            )}
          >
            <Icon className="w-6 h-6" />
            <span className="text-[10px] font-medium">{tab.name}</span>
          </Link>
        );
      })}
    </nav>
  );
}
