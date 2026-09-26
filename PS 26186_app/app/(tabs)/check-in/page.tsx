"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function CheckInRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    // Check-in workflow is fully unified into daily Assessment
    router.replace("/assessment");
  }, [router]);

  return (
    <div className="flex h-full items-center justify-center p-6 text-slate-400">
      <div className="flex flex-col items-center space-y-2">
        <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs font-mono">Redirecting to Daily Assessment...</span>
      </div>
    </div>
  );
}
