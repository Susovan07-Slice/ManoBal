import { cn } from "@/lib/utils";
import { HTMLAttributes, forwardRef } from "react";

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("bg-white/75 backdrop-blur-xl rounded-[24px] shadow-[0_10px_30px_rgba(31,110,140,.12)] border border-white/80 p-5 transition-all duration-200", className)}
        {...props}
      />
    );
  }
);
Card.displayName = "Card";


