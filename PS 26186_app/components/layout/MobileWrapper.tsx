import { ReactNode } from 'react';

export default function MobileWrapper({ children }: { children: ReactNode }) {
  return (
    <div 
      className="max-w-md mx-auto min-h-[100dvh] relative shadow-[0_0_60px_rgba(31,110,140,0.08)] overflow-x-hidden w-full min-w-0 z-50"
    >
      <div className="relative z-50 flex flex-col min-h-[100dvh] bg-transparent">
        {children}
      </div>
    </div>
  );
}
