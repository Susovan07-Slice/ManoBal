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
          "flex items-center justify-center h-[52px] px-6 rounded-full font-semibold transition-all duration-200 disabled:opacity-50 disabled:pointer-events-none disabled:shadow-none active:scale-[.97]",
          {
            "bg-gradient-to-r from-brand-500 to-brand-600 text-white shadow-[0_16px_40px_rgba(31,110,140,0.22)] hover:shadow-[0_16px_40px_rgba(31,110,140,0.30)]": variant === "primary",
            "bg-white/70 backdrop-blur-md border border-brand-500/20 text-brand-600 hover:bg-white/90 shadow-[0_10px_30px_rgba(31,110,140,0.12)]": variant === "secondary",
            "bg-gradient-to-r from-alert to-danger text-white shadow-[0_16px_40px_rgba(240,80,140,0.22)]": variant === "danger",
            "bg-transparent text-ink-2 hover:text-ink hover:bg-sky-50": variant === "ghost",
          },
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";


