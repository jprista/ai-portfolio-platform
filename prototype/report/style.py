"""Institutional report stylesheet (print-ready A4)."""

CSS = """
:root {
  --navy: #0f2a43; --navy-2: #16395c; --ink: #1c2833; --muted: #5d6d7e;
  --line: #d5dde5; --bg: #ffffff; --accent: #b08d3e; --soft: #f4f6f8;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Georgia, 'Times New Roman', serif; color: var(--ink);
  background: var(--bg); max-width: 860px; margin: 0 auto; padding: 48px 40px; }
header { border-bottom: 3px solid var(--navy); padding-bottom: 24px; margin-bottom: 32px; }
.org { font-family: Helvetica, Arial, sans-serif; font-size: 12px; letter-spacing: 3px;
  text-transform: uppercase; color: var(--accent); font-weight: bold; }
h1 { font-size: 34px; color: var(--navy); margin: 10px 0 4px; font-weight: normal; }
.family { font-size: 19px; color: var(--navy-2); }
.ref { font-family: Helvetica, Arial, sans-serif; font-size: 12px; color: var(--muted); margin-top: 8px; }
section { margin-bottom: 36px; }
h2 { font-family: Helvetica, Arial, sans-serif; font-size: 13px; letter-spacing: 2px;
  text-transform: uppercase; color: var(--navy); border-bottom: 1px solid var(--line);
  padding-bottom: 8px; margin-bottom: 18px; }
.kpis { display: flex; gap: 16px; }
.kpi { flex: 1; background: var(--soft); border-top: 3px solid var(--navy); padding: 14px 16px; }
.kpi-label { font-family: Helvetica, Arial, sans-serif; font-size: 11px; color: var(--muted);
  text-transform: uppercase; letter-spacing: 1px; }
.kpi-value { font-size: 22px; color: var(--navy); margin-top: 6px; }
.alloc-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.alloc-label { width: 190px; font-size: 14px; }
.alloc-bar-track { flex: 1; background: var(--soft); height: 16px; }
.alloc-bar { background: var(--navy-2); height: 16px; }
.alloc-value { width: 220px; font-family: Helvetica, Arial, sans-serif; font-size: 12px;
  color: var(--muted); text-align: right; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { font-family: Helvetica, Arial, sans-serif; font-size: 11px; text-transform: uppercase;
  letter-spacing: 1px; color: var(--muted); text-align: left; padding: 8px 10px;
  border-bottom: 2px solid var(--navy); }
td { padding: 9px 10px; border-bottom: 1px solid var(--line); }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
tfoot td { border-top: 2px solid var(--navy); border-bottom: none; }
.conf { font-family: Helvetica, Arial, sans-serif; font-size: 11px; white-space: nowrap; }
.conf-A { color: #1e6f45; } .conf-B { color: #4a6fa5; } .conf-C { color: #a8681c; } .conf-D { color: #a83c3c; }
.card { border-left: 4px solid var(--muted); background: var(--soft); padding: 14px 16px; margin-bottom: 12px; }
.card.sev-alta { border-left-color: #a83c3c; }
.card.sev-media { border-left-color: #b08d3e; }
.card.sev-baixa { border-left-color: #4a6fa5; }
.card-sev { font-family: Helvetica, Arial, sans-serif; font-size: 10px; letter-spacing: 2px; color: var(--muted); }
.card-title { font-size: 15px; color: var(--navy); margin: 4px 0 6px; font-weight: bold; }
.card-detail { font-size: 13px; line-height: 1.5; }
.method-note, .disclaimer { font-size: 11.5px; color: var(--muted); line-height: 1.55; margin-top: 12px; }
.disclaimer { border-top: 1px solid var(--line); padding-top: 10px; }
footer { font-family: Helvetica, Arial, sans-serif; font-size: 10px; color: var(--muted);
  border-top: 1px solid var(--line); padding-top: 12px; margin-top: 24px; }
@media print {
  body { padding: 0; max-width: none; }
  .page-break { page-break-before: always; }
  @page { size: A4; margin: 18mm 16mm; }
}
"""
