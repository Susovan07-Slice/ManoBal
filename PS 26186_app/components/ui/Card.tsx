import { cn } from "@/lib/utils";
import { HTMLAttributes, forwardRef } from "react";

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("bg-mb-glass-strong backdrop-blur-xl rounded-3xl shadow-[0_8px_30px_rgba(0,0,0,0.12)] shadow-black/40 border border-mb-glass-border p-6 transition-all duration-300", className)}
        {...props}
      />
    );
  }
);
Card.displayName = "Card";


