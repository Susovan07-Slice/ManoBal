import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "flex items-center justify-center min-h-[48px] px-6 rounded-xl font-medium transition-all duration-300 disabled:opacity-50 disabled:pointer-events-none active:scale-95",
          {
            "bg-mb-accent text-mb-text-primary hover:bg-mb-accent shadow-lg shadow-teal-600/20": variant === "primary",
            "bg-mb-glass-strong backdrop-blur-md border border-mb-glass-border text-mb-text-primary hover:bg-white/10 shadow-lg shadow-black/20": variant === "secondary",
            "bg-red-500/80 backdrop-blur-md text-mb-text-primary hover:bg-red-400 border border-red-500/30": variant === "danger",
            "bg-transparent text-mb-text-secondary hover:bg-white/10": variant === "ghost",
          },
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";


