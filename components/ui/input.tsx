import * as React from "react";
import { cn } from "@/lib/utils";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, type, ...props }, ref) => (
  <input
    type={type}
    className={cn(
      "flex h-10 w-full rounded-md border border-blinkit-ink/15 bg-white px-3 py-2 text-sm text-blinkit-ink placeholder:text-blinkit-slate/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blinkit-forest",
      className
    )}
    ref={ref}
    {...props}
  />
));
Input.displayName = "Input";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    className={cn(
      "flex min-h-[100px] w-full rounded-md border border-blinkit-ink/15 bg-white px-3 py-2 text-sm text-blinkit-ink placeholder:text-blinkit-slate/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blinkit-forest",
      className
    )}
    ref={ref}
    {...props}
  />
));
Textarea.displayName = "Textarea";
