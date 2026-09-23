import type { ReactNode } from "react";

export function KpiCard({
  label, value, unit, tone = "neutral", icon,
}: {
  label: string;
  value: ReactNode;
  unit?: string;
  tone?: "healthy" | "warning" | "critical" | "neutral";
  icon?: ReactNode;
}) {
  const toneColor = {
    healthy: "text-healthy",
    warning: "text-warning",
    critical: "text-critical",
    neutral: "text-text",
  }[tone];

  return (
    <div className="bg-surface border border-border rounded-lg p-4 rise-in">
      <div className="flex items-center justify-between text-text-muted text-xs mb-2">
        <span>{label}</span>
        {icon}
      </div>
      <div className={`text-2xl font-semibold font-mono ${toneColor}`}>
        {value}
        {unit && <span className="text-sm text-text-muted ml-1">{unit}</span>}
      </div>
    </div>
  );
}
