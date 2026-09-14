import { cn } from "@/lib/utils";
import { HTMLAttributes, forwardRef } from "react";

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("bg-[#1C2530] rounded-2xl shadow-lg border border-slate-800/50 p-6", className)}
        {...props}
      />
    );
  }
);
Card.displayName = "Card";
