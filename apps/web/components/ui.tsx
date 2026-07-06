import type { ReactNode } from "react";

export type MeetingStatus =
  | "scheduled"
  | "preparing"
  | "material_generated"
  | "material_sent"
  | "held"
  | "cancelled";

const statusMeta: Record<MeetingStatus, { label: string; cls: string; dot: string }> = {
  scheduled: { label: "Agendada", cls: "bg-paper text-muted", dot: "bg-faint" },
  preparing: { label: "Em preparação", cls: "bg-info-soft text-info", dot: "bg-info" },
  material_generated: { label: "Material gerado", cls: "bg-navy-soft text-navy", dot: "bg-navy" },
  material_sent: { label: "Material enviado", cls: "bg-gold-soft text-gold", dot: "bg-gold" },
  held: { label: "Realizada", cls: "bg-ok-soft text-ok", dot: "bg-ok" },
  cancelled: { label: "Cancelada", cls: "bg-paper text-faint line-through", dot: "bg-faint" },
};

export function StatusChip({ status }: { status: MeetingStatus }) {
  const m = statusMeta[status];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11.5px] font-medium ${m.cls}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${m.dot}`} />
      {m.label}
    </span>
  );
}

const sealCls: Record<string, string> = {
  A: "bg-ok-soft text-ok ring-ok/20",
  B: "bg-info-soft text-info ring-info/20",
  C: "bg-warn-soft text-warn ring-warn/25",
  D: "bg-bad-soft text-bad ring-bad/25",
};

export function Seal({ grade, title }: { grade: string; title?: string }) {
  return (
    <span
      title={title}
      className={`inline-flex h-[19px] w-[19px] cursor-help items-center justify-center rounded-full text-[10px] font-bold ring-1 ${sealCls[grade] ?? sealCls.D}`}
    >
      {grade}
    </span>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h2 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
      {children}
    </h2>
  );
}

export function Card({
  children,
  className = "",
  hover = false,
}: {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <div
      className={`rounded-2xl border border-hairline bg-surface shadow-card ${
        hover ? "transition-shadow duration-200 hover:shadow-card-hover" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}

const sevMeta: Record<string, { label: string; bar: string; badge: string }> = {
  alta: { label: "Alta", bar: "bg-bad", badge: "bg-bad-soft text-bad" },
  média: { label: "Média", bar: "bg-warn", badge: "bg-warn-soft text-warn" },
  baixa: { label: "Baixa", bar: "bg-info", badge: "bg-info-soft text-info" },
};

export function InsightCard({
  severity,
  title,
  children,
}: {
  severity: "alta" | "média" | "baixa";
  title: string;
  children: ReactNode;
}) {
  const m = sevMeta[severity];
  return (
    <div className="relative overflow-hidden rounded-xl border border-hairline bg-surface p-4 pl-5 shadow-card">
      <span className={`absolute inset-y-0 left-0 w-1 ${m.bar}`} />
      <div className="flex items-start justify-between gap-3">
        <div className="text-[13.5px] font-semibold text-navy">{title}</div>
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10.5px] font-semibold ${m.badge}`}>
          {m.label}
        </span>
      </div>
      <p className="mt-1.5 text-[13px] leading-relaxed text-ink/80">{children}</p>
    </div>
  );
}
