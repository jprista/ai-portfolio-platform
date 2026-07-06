/** Display-only formatting of engine-born decimal strings (I1: engine computes,
 *  UI formats). pt-BR conventions. */

export function brl(value: string | number): string {
  const n = typeof value === "string" ? Number(value) : value;
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function pct(value: string | number, digits = 2): string {
  const n = typeof value === "string" ? Number(value) : value;
  return n.toFixed(digits).replace(".", ",") + "%";
}

export function dateBR(d: string | Date): string {
  return new Date(d).toLocaleDateString("pt-BR", { timeZone: "America/Sao_Paulo" });
}

export function dayParts(d: string | Date) {
  const dt = new Date(d);
  const day = dt.toLocaleDateString("pt-BR", { day: "2-digit", timeZone: "America/Sao_Paulo" });
  const mon = dt.toLocaleDateString("pt-BR", { month: "short", timeZone: "America/Sao_Paulo" }).replace(".", "");
  const wd = dt.toLocaleDateString("pt-BR", { weekday: "short", timeZone: "America/Sao_Paulo" }).replace(".", "");
  const time = dt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", timeZone: "America/Sao_Paulo" });
  return { day, rest: `${mon} · ${wd} · ${time}` };
}
