import { ReactNode } from 'react';

export default function MobileWrapper({ children }: { children: ReactNode }) {
  return (
    <div className="max-w-[420px] mx-auto min-h-screen relative shadow-2xl">
      <div className="relative z-10 flex flex-col min-h-screen">
        {children}
      </div>
    </div>
  );
}
