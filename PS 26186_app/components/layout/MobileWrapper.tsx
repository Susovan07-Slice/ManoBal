import { ReactNode } from 'react';

export default function MobileWrapper({ children }: { children: ReactNode }) {
  return (
    <div 
      className="max-w-[420px] mx-auto min-h-screen relative shadow-[0_8px_30px_rgba(0,0,0,0.12)] bg-cover bg-center bg-no-repeat overflow-hidden"
      style={{ backgroundImage: "url('/military_wellness_background.jpg')" }}
    >
      <div className="relative z-10 flex flex-col min-h-screen bg-transparent">
        {children}
      </div>
    </div>
  );
}


