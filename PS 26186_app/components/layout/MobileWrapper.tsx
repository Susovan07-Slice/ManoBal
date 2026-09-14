import { ReactNode } from 'react';

export default function MobileWrapper({ children }: { children: ReactNode }) {
  return (
    <div className="max-w-[420px] mx-auto min-h-screen bg-background relative shadow-2xl overflow-hidden">
      {children}
    </div>
  );
}
