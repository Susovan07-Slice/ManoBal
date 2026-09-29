import { ReactNode } from 'react';

export default function MobileWrapper({ children }: { children: ReactNode }) {
  return (
    <div 
      className="max-w-md w-full mx-auto min-h-screen relative overflow-x-hidden shadow-2xl flex flex-col bg-white z-50"
    >
      {/* Background gradient strictly contained within the mobile view */}
      <div className="app-gradient-bg" aria-hidden="true" />

      <div className="relative z-50 flex flex-col min-h-screen bg-transparent">
        {children}
      </div>
    </div>
  );
}
