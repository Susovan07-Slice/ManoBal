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
          "flex items-center justify-center min-h-[48px] px-6 rounded-xl font-medium transition-colors disabled:opacity-50 disabled:pointer-events-none active:scale-95",
          {
            "bg-teal-500 text-slate-900 hover:bg-teal-400": variant === "primary",
            "bg-slate-800 text-slate-100 hover:bg-slate-700": variant === "secondary",
            "bg-red-600/90 text-white hover:bg-red-500": variant === "danger",
            "bg-transparent text-slate-300 hover:bg-slate-800": variant === "ghost",
          },
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
