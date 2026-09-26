import { cn } from "@/lib/utils";
import { HTMLAttributes, forwardRef } from "react";

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("bg-[var(--color-glass-dark)] backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/40 border border-[var(--color-glass-border)] p-6 transition-all duration-300", className)}
        {...props}
      />
    );
  }
);
Card.displayName = "Card";
