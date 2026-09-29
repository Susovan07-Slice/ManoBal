"use client";

import React from "react";
import { Activity, HeartPulse, TrendingUp, Shield, ChevronRight } from "lucide-react";

/**
 * A CSS-only phone-frame mockup showing a miniature Home dashboard.
 * Used on onboarding slide 3 to preview the app experience.
 */
export function PhoneFrame({
  isActive,
  reducedMotion,
}: {
  isActive: boolean;
  reducedMotion: boolean;
}) {
  return (
    <div
      className="pointer-events-none"
      style={{
        perspective: "800px",
      }}
    >
      <div
        style={{
          transform: "rotateY(-15deg) rotateX(5deg) rotateZ(-2deg)",
          transformStyle: "preserve-3d",
          transition: reducedMotion
            ? "none"
            : "opacity 500ms cubic-bezier(.32,.72,0,1), transform 500ms cubic-bezier(.32,.72,0,1)",
          opacity: isActive ? 1 : 0,
          ...(isActive
            ? {}
            : {
                transform:
                  "rotateY(-22deg) rotateX(8deg) rotateZ(-4deg) scale(1.08)",
              }),
        }}
      >
        {/* Phone device shell */}
        <div
          className="relative rounded-[20px] bg-[#1a1a1e] p-[6px] shadow-[0_20px_50px_rgba(0,0,0,0.25)]"
          style={{ width: "120px", height: "220px" }}
        >
          {/* Top notch */}
          <div className="absolute top-[3px] left-1/2 -translate-x-1/2 w-10 h-[5px] bg-[#1a1a1e] rounded-b-md z-20" />

          {/* Side button notches */}
          <div className="absolute top-[40px] -right-[2px] w-[2px] h-5 bg-[#2a2a2e] rounded-l-sm" />
          <div className="absolute top-[55px] -left-[2px] w-[2px] h-4 bg-[#2a2a2e] rounded-r-sm" />
          <div className="absolute top-[72px] -left-[2px] w-[2px] h-4 bg-[#2a2a2e] rounded-r-sm" />

          {/* Inner screen */}
          <div
            className="relative w-full h-full rounded-[14px] overflow-hidden"
            style={{
              background:
                "linear-gradient(180deg, #DDF1F8 0%, #BFE3F0 50%, #8FCBE2 100%)",
            }}
          >
            {/* Mini header bar */}
            <div className="flex items-center justify-between px-2 pt-2.5 pb-1">
              <div className="flex items-center gap-1">
                <div className="w-4 h-4 rounded-full bg-white/80 flex items-center justify-center">
                  <HeartPulse className="w-2.5 h-2.5 text-[#2A9BC8]" />
                </div>
                <span className="text-[5px] font-bold text-[#14232E] tracking-tight">
                  ManoBal
                </span>
              </div>
              <div className="w-3 h-3 rounded-full bg-white/50" />
            </div>

            {/* Welcome text */}
            <div className="px-2 mt-0.5">
              <div className="text-[4.5px] text-[#4B6272] font-medium">
                Good Morning
              </div>
              <div className="text-[6px] font-bold text-[#14232E] mt-0.5">
                Constable Verma
              </div>
            </div>

            {/* Score card */}
            <div className="mx-2 mt-1.5 rounded-lg bg-white/70 border border-white/80 p-1.5 backdrop-blur-sm">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-[4px] text-[#4B6272] font-medium uppercase tracking-wider">
                    Wellness Score
                  </div>
                  <div className="flex items-baseline gap-0.5 mt-0.5">
                    <span className="text-[10px] font-bold text-[#14232E] leading-none">
                      30.7
                    </span>
                    <span className="text-[4px] text-[#8AA1AF]">/100</span>
                  </div>
                </div>
                <div className="flex flex-col items-center">
                  <svg className="w-7 h-7 -rotate-90" viewBox="0 0 32 32">
                    <circle
                      cx="16"
                      cy="16"
                      r="12"
                      fill="none"
                      stroke="#E0F2F9"
                      strokeWidth="3"
                    />
                    <circle
                      cx="16"
                      cy="16"
                      r="12"
                      fill="none"
                      stroke="#2FBF8F"
                      strokeWidth="3"
                      strokeDasharray="75.4"
                      strokeDashoffset={isActive ? 75.4 * 0.7 : 75.4}
                      strokeLinecap="round"
                      className="transition-all duration-700 ease-out delay-500"
                    />
                  </svg>
                  <span className="text-[3.5px] font-bold text-[#2FBF8F] mt-0.5">
                    LOW
                  </span>
                </div>
              </div>
            </div>

            {/* Quick action row */}
            <div className="flex gap-1 mx-2 mt-1.5">
              {[
                {
                  icon: Activity,
                  label: "Check In",
                  color: "#2A9BC8",
                },
                {
                  icon: TrendingUp,
                  label: "Trends",
                  color: "#2FBF8F",
                },
                {
                  icon: Shield,
                  label: "Support",
                  color: "#F5A623",
                },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="flex-1 rounded-md bg-white/60 border border-white/70 py-1 flex flex-col items-center gap-0.5"
                >
                  <item.icon
                    className="w-2.5 h-2.5"
                    style={{ color: item.color }}
                  />
                  <span className="text-[3.5px] font-semibold text-[#14232E]">
                    {item.label}
                  </span>
                </div>
              ))}
            </div>

            {/* Recent activity list */}
            <div className="mx-2 mt-1.5">
              <div className="text-[4px] font-bold text-[#4B6272] uppercase tracking-wider mb-1">
                Recent
              </div>
              {["Assessment Done", "Welfare Update"].map((text, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between bg-white/50 rounded-md px-1.5 py-1 mb-0.5 border border-white/60"
                >
                  <span className="text-[3.5px] font-medium text-[#14232E]">
                    {text}
                  </span>
                  <ChevronRight className="w-2 h-2 text-[#8AA1AF]" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
