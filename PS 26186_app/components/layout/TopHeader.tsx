import { ReactNode } from "react";

export default function TopHeader({ title, showBack }: { title: string, showBack?: boolean }) {
  return (
    <header className="flex items-center justify-center h-16 bg-[#141A22] border-b border-slate-800 shrink-0">
      <h1 className="text-lg font-semibold text-slate-100 tracking-wide">{title}</h1>
    </header>
  );
}
