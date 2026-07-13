import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { text } from "../format.js";

function clampSummary(value) {
  const body = typeof value === "string" ? value : value ? JSON.stringify(value, null, 2) : "";
  return body.split("\n").filter(Boolean).slice(0, 2).join("\n");
}

export default function ReportCard({ title, file, status = "present", summary, children }) {
  const body = typeof summary === "string" ? summary : summary ? JSON.stringify(summary, null, 2) : "";
  const brief = clampSummary(summary) || "报告暂时不可用，请稍后刷新。";
  return (
    <Collapsible className="report-list-item">
      <div className="report-list-main">
        <div>
          <strong>{title}</strong>
          <p>{brief}</p>
          <small>{status === "present" ? "已生成" : text(status, "等待更新")} · {file || "本地报告"}</small>
        </div>
        <CollapsibleTrigger asChild>
          <Button variant="secondary" size="sm" type="button">查看</Button>
        </CollapsibleTrigger>
      </div>
      <CollapsibleContent>
        <Separator />
        <ScrollArea className="report-list-detail">
          {children ? children : <pre>{body || "报告暂时不可用，请稍后刷新。"}</pre>}
        </ScrollArea>
      </CollapsibleContent>
    </Collapsible>
  );
}
