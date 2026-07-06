import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils";

export const Button = React.forwardRef(
  ({ className, variant = "default", size = "default", asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        ref={ref}
        className={cn("ui-button", `ui-button-${variant}`, `ui-button-${size}`, className)}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
