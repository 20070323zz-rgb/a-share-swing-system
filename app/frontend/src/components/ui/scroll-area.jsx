import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area";
import { cn } from "@/lib/utils";

export function ScrollArea({ className, children, ...props }) {
  return (
    <ScrollAreaPrimitive.Root className={cn("ui-scroll-area", className)} {...props}>
      <ScrollAreaPrimitive.Viewport className="ui-scroll-area-viewport">{children}</ScrollAreaPrimitive.Viewport>
      <ScrollAreaPrimitive.Scrollbar className="ui-scroll-area-scrollbar" orientation="vertical">
        <ScrollAreaPrimitive.Thumb className="ui-scroll-area-thumb" />
      </ScrollAreaPrimitive.Scrollbar>
      <ScrollAreaPrimitive.Corner />
    </ScrollAreaPrimitive.Root>
  );
}
