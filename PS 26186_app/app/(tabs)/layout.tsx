"use client";

import TopHeader from "@/components/layout/TopHeader";
import BottomTabBar from "@/components/layout/BottomTabBar";
import { usePathname } from "next/navigation";

export default function TabsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  
  let title = "Home";
  if (pathname === "/check-in") title = "Daily Check-In";
  if (pathname === "/assessment") title = "Assessment";
  if (pathname === "/trends") title = "Trends";

  return (
    <div className="flex flex-col h-full overflow-hidden absolute inset-0">
      <TopHeader title={title} />
      <main className="flex-1 overflow-y-auto bg-[#141A22]">
        {children}
      </main>
      <BottomTabBar />
    </div>
  );
}
