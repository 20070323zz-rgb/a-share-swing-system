import * as React from "react";
import { cn } from "@/lib/utils";

export const Separator = React.forwardRef(({ className, orientation = "horizontal", ...props }, ref) => (
  <div ref={ref} className={cn("ui-separator", `ui-separator-${orientation}`, className)} {...props} />
));
Separator.displayName = "Separator";
