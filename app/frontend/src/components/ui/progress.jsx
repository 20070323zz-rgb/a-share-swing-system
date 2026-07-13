import * as ProgressPrimitive from "@radix-ui/react-progress";
import { cn } from "@/lib/utils";

export function Progress({ className, value = 0, ...props }) {
  const safeValue = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <ProgressPrimitive.Root className={cn("ui-progress", className)} {...props}>
      <ProgressPrimitive.Indicator className="ui-progress-indicator" style={{ transform: `translateX(-${100 - safeValue}%)` }} />
    </ProgressPrimitive.Root>
  );
}
