import type { ReactNode } from "react";

function Dot({ color }: { color: string }) {
  return <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />;
}

const SEVERITY_STYLES: Record<string, { bg: string; text: string; dot: string }> = {
  Critical: { bg: "bg-[#3a1420]", text: "text-[#f0465b]", dot: "#f0465b" },
  High: { bg: "bg-[#3a2712]", text: "text-[#f5a524]", dot: "#f5a524" },
  Medium: { bg: "bg-[#182b3a]", text: "text-[#5b9dfa]", dot: "#5b9dfa" },
  Low: { bg: "bg-[#132a22]", text: "text-[#34d399]", dot: "#34d399" },
};

export function SeverityBadge({ severity }: { severity: string }) {
  const s = SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.Low;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium font-mono ${s.bg} ${s.text}`}>
      <Dot color={s.dot} />
      {severity}
    </span>
  );
}

const STATUS_STYLES: Record<string, string> = {
  Detected: "text-[#f5a524]",
  Investigating: "text-[#f5a524]",
  Assigned: "text-[#5b9dfa]",
  "In Progress": "text-[#5b9dfa]",
  Resolved: "text-[#34d399]",
  Closed: "text-text-muted",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`text-xs font-medium font-mono ${STATUS_STYLES[status] ?? "text-text-muted"}`}>
      {status}
    </span>
  );
}

const HEALTH_COLORS: Record<string, string> = {
  healthy: "#34d399",
  degraded: "#f5a524",
  offline: "#f0465b",
};

export function HealthDot({ health, label }: { health: string; label?: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-mono">
      <Dot color={HEALTH_COLORS[health] ?? "#5b6b7a"} />
      {label ?? health}
    </span>
  );
}
