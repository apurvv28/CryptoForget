import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "secondary";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-neutral-400 disabled:pointer-events-none disabled:opacity-50",
          {
            "bg-white text-black hover:bg-neutral-200": variant === "default",
            "border border-neutral-700 bg-transparent hover:bg-neutral-800 text-neutral-200":
              variant === "outline",
            "hover:bg-neutral-800 text-neutral-300 hover:text-white":
              variant === "ghost",
            "bg-neutral-800 text-neutral-100 hover:bg-neutral-700":
              variant === "secondary",
            "h-9 px-4 py-2 text-sm rounded-lg": size === "default",
            "h-8 px-3 text-xs rounded-md": size === "sm",
            "h-10 px-8 text-base rounded-lg": size === "lg",
            "h-9 w-9 rounded-lg": size === "icon",
          },
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
