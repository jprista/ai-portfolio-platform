"""Seeds the São Paulo database with the demo organization end-to-end:
org, policy v1, professional bootstrap, families, holders, accounts,
instruments, positions (real Família Almeida data) and meetings — then
computes a REAL AnalysisRun via engine_core and links it to the meeting.

Idempotent: safe to re-run (upserts by natural keys).
Usage:  py scripts/seed_demo.py
"""
from __future__ import annotations

import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "engine"))

from engine_core import benchmark, insights, metrics  # noqa: E402
from engine_core import run as run_mod  # noqa: E402
from engine_core.models import Flow, Position, Valuation  # noqa: E402

ENV = dotenv_values(ROOT / ".env")
DATA = ROOT / "services" / "engine" / "tests" / "data"

PORTFOLIO = json.loads((DATA / "portfolio_familia_almeida.json").read_text(encoding="utf-8"))
CDI = json.loads((DATA / "cdi_daily_2026S1.json").read_text(encoding="utf-8"))

CLASS_BY_TYPE = {
    "caixa": "cdb", "renda_fixa_pos": "cdb", "renda_fixa_inflacao": "cdb",
    "multimercado": "fund", "renda_variavel": "equity", "previdencia": "pension_fund",
}
LIQ_MAP = {"D0": "D0", "D+2": "D+2", "D+30": "D+30", "D+60": "D+60", "vencimento": "vencimento"}


def upsert(cur, sql: str, params: tuple):
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0]


def main() -> None:
    with psycopg.connect(ENV["DATABASE_URL"], connect_timeout=20) as conn:
        conn.autocommit = False
        cur = conn.cursor()

        org_id = upsert(cur, """
            insert into core.organizations (name, slug, brand)
            values ('Demo Wealth Advisors', 'demo', '{"accent":"#B08C3D"}')
            on conflict (slug) do update set name = excluded.name
            returning id""", ())
        print(f"org: {org_id}")

        cur.execute("select id from core.organization_policies where org_id=%s and version=1", (org_id,))
        row = cur.fetchone()
        if row:
            policy_id = row[0]
        else:
            policy_id = upsert(cur, """
                insert into core.organization_policies (org_id, version) values (%s, 1)
                returning id""", (org_id,))
        print(f"policy v1: {policy_id}")

        cur.execute("select id from core.benchmarks where org_id is null and kind='cdi' limit 1")
        cdi_bench_id = cur.fetchone()[0]

        def family(name: str) -> str:
            return upsert(cur, """
                insert into core.families (org_id, display_name, benchmark_id)
                select %s, %s, %s
                where not exists (select 1 from core.families where org_id=%s and display_name=%s)
                returning id""", (org_id, name, cdi_bench_id, org_id, name)) if not _existing_family(cur, org_id, name) else _existing_family(cur, org_id, name)

        def _existing_family(cur, org, name):
            cur.execute("select id from core.families where org_id=%s and display_name=%s", (org, name))
            r = cur.fetchone()
            return r[0] if r else None

        fam_almeida = _existing_family(cur, org_id, "Família Almeida") or upsert(
            cur, "insert into core.families (org_id, display_name, benchmark_id) values (%s,%s,%s) returning id",
            (org_id, "Família Almeida", cdi_bench_id))
        fam_souza = _existing_family(cur, org_id, "Família Souza") or upsert(
            cur, "insert into core.families (org_id, display_name, benchmark_id) values (%s,%s,%s) returning id",
            (org_id, "Família Souza", cdi_bench_id))
        fam_castro = _existing_family(cur, org_id, "Família Castro") or upsert(
            cur, "insert into core.families (org_id, display_name, benchmark_id) values (%s,%s,%s) returning id",
            (org_id, "Família Castro", cdi_bench_id))
        print(f"families: almeida={fam_almeida}")

        def holder(fam: str, name: str, doc: str) -> str:
            cur.execute("select id from core.holders where family_id=%s and display_name=%s", (fam, name))
            r = cur.fetchone()
            if r:
                return r[0]
            return upsert(cur, """
                insert into core.holders (org_id, family_id, display_name, document_masked)
                values (%s,%s,%s,%s) returning id""", (org_id, fam, name, doc))

        jose = holder(fam_almeida, "José Almeida", "***.482.117-**")
        maria = holder(fam_almeida, "Maria Almeida", "***.909.334-**")

        cur.execute("select id from core.custodians where name='XP Investimentos'")
        xp = cur.fetchone()[0]

        def account(fam: str, hold: str | None, ref: str) -> str:
            cur.execute("select id from core.accounts where family_id=%s and external_ref_masked=%s", (fam, ref))
            r = cur.fetchone()
            if r:
                return r[0]
            return upsert(cur, """
                insert into core.accounts (org_id, family_id, holder_id, custodian_id, external_ref_masked, source)
                values (%s,%s,%s,%s,%s,'document') returning id""", (org_id, fam, hold, xp, ref))

        acc_jose = account(fam_almeida, jose, "***4432")
        acc_maria = account(fam_almeida, maria, "***1291")
        acc_souza = account(fam_souza, None, "***7810")
        acc_castro = account(fam_castro, None, "***3355")

        def issuer(name: str, kind: str) -> str:
            cur.execute("select id from core.issuers where name=%s", (name,))
            r = cur.fetchone()
            if r:
                return r[0]
            return upsert(cur, "insert into core.issuers (name, kind) values (%s,%s) returning id", (name, kind))

        def instrument(name: str, itype: str, issuer_id: str, index_kind: str, maturity) -> str:
            cur.execute("select id from core.instruments where name=%s", (name,))
            r = cur.fetchone()
            if r:
                return r[0]
            return upsert(cur, """
                insert into core.instruments (kind, name, issuer_id, index_kind, maturity)
                values (%s,%s,%s,%s,%s) returning id""", (itype, name, issuer_id, index_kind, maturity))

        issuer_kind = {
            "Banco Beta": "bank", "Banco Gama": "bank", "Banco Delta": "bank",
            "Tesouro Nacional": "sovereign", "Órion Asset": "asset_manager",
            "Vértice Capital": "asset_manager", "B3 / iShares": "asset_manager",
            "Itaú Unibanco": "company", "CSHG": "asset_manager", "Zafira Seguros": "insurer",
        }
        index_map = {"100% CDI": "cdi_pct", "110% CDI": "cdi_pct", "93% CDI": "cdi_pct",
                     "IPCA + 6,20%": "ipca_plus", "IPCA + taxa de mercado": "ipca_plus", "SELIC": "selic"}

        holder_by_name = {"José Almeida": acc_jose, "Maria Almeida": acc_maria}
        as_of = date.fromisoformat(PORTFOLIO["meta"]["reference_date"])
        n_pos = 0
        for p in PORTFOLIO["positions"]:
            iss = issuer(p["issuer"], issuer_kind[p["issuer"]])
            itype = CLASS_BY_TYPE[p["asset_class"]]
            if "Tesouro" in p["name"]:
                itype = "tesouro"
            if p["name"].startswith("LCA"):
                itype = "lca"
            if "ETF" in p["name"]:
                itype = "etf"
            if "FII" in p["name"]:
                itype = "fii"
            inst = instrument(p["name"], itype, iss, index_map.get(p.get("index_desc", ""), "none"),
                              p.get("maturity"))
            acc = holder_by_name.get(p.get("holder", ""), acc_jose)
            cur.execute("""
                insert into core.position_snapshots
                    (org_id, account_id, instrument_id, as_of, value, source, confidence, valuation_mode, contract_terms)
                values (%s,%s,%s,%s,%s,'document',%s,'curve','{}')
                on conflict (org_id, account_id, instrument_id, as_of) do update set value = excluded.value
            """, (org_id, acc, inst, as_of, p["value"], p["confidence"]))
            n_pos += 1
        print(f"positions: {n_pos}")

        # cenográficas (demo): uma posição agregada informada por família
        for fam, acc, total in ((fam_souza, acc_souza, "1480220.00"), (fam_castro, acc_castro, "5104870.33")):
            iss = issuer("Consolidado (demo)", "company")
            inst = instrument(f"Carteira consolidada (demo) {str(fam)[:6]}", "other", iss, "none", None)
            cur.execute("""
                insert into core.position_snapshots
                    (org_id, account_id, instrument_id, as_of, value, source, confidence, valuation_mode, contract_terms)
                values (%s,%s,%s,%s,%s,'manual','B','curve','{}')
                on conflict (org_id, account_id, instrument_id, as_of) do update set value = excluded.value
            """, (org_id, acc, inst, as_of, total))

        # ---- run real do motor ----
        positions = [Position.from_dict(d) for d in PORTFOLIO["positions"]]
        valuations = [Valuation.from_dict(d) for d in PORTFOLIO["history"]["valuations"]]
        flows = [Flow.from_dict(d) for d in PORTFOLIO["history"]["flows"]]
        from datetime import timedelta
        returns = metrics.chained_returns(valuations, flows)
        bench_total = benchmark.accumulate(benchmark.DEFAULT_CDI, valuations[0].day + timedelta(days=1), as_of, {"cdi": CDI})
        outputs = {
            "total_value": metrics.total_value(positions),
            "allocation": metrics.allocation_by_class(positions),
            "liquidity": metrics.liquidity_ladder(positions, as_of),
            "returns": returns,
            "benchmark_pct": bench_total,
            "benchmark_comparison": metrics.benchmark_comparison(returns["total_return_pct"], bench_total),
            "insights": insights.generate(positions, as_of),
            "history": PORTFOLIO["history"],
            "meta": {"last_meeting_date": PORTFOLIO["meta"]["last_meeting_date"]},
        }
        # blocos narrativos prontos para exibição (mesma lógica do demo.py, gerados junto do run)
        val_at_meeting = max((v for v in valuations if v.day <= date.fromisoformat(PORTFOLIO["meta"]["last_meeting_date"])), key=lambda v: v.day)
        factor = Decimal("1")
        for pr in returns["periods"]:
            if pr["start"] >= val_at_meeting.day:
                factor *= Decimal("1") + pr["return_pct"] / Decimal("100")
        ret_since = ((factor - 1) * Decimal("100")).quantize(Decimal("0.01"))
        risk_alloc = sum((outputs["allocation"][c]["pct"] for c in ("multimercado", "renda_variavel") if c in outputs["allocation"]), Decimal("0"))
        outputs["narrative"] = {
            "risk_assets_alloc_pct": str(risk_alloc),
            "changes": [
                f"Patrimônio passou de R$ 2.883.450,00 (31/03/2026) para R$ 2.913.933,80 (30/06/2026).",
                f"Retorno no período entre reuniões: {str(ret_since).replace('.', ',')}%.",
                "Resgate de R$ 30.000,00 em 10/05/2026.",
            ],
            "agenda": [
                "Exposições acima do FGC por titular (2 casos)",
                "Concentração da família em Banco Beta",
                "Destino da LCA que vence em 15/08",
                "Custo do FIM Órion vs. mediana da classe",
                "Objetivos e horizonte das parcelas de risco",
            ],
            "class_readings": {
                "renda_fixa_pos": "Carrego médio ponderado de ≈104% do CDI. A LCA Banco Gama vence em 46 dias — decidir destino nesta reunião evita recurso parado.",
                "renda_variavel": "Quatro veículos, maior posição no FIA Vértice (8,63% da carteira). Semestre abaixo do CDI — comportamento esperado do horizonte da classe.",
                "renda_fixa_inflacao": "Proteção real de longo prazo com vencimentos 2028 e 2035. CDB Banco Delta responde pelo estouro de FGC da titular Maria.",
                "multimercado": "Taxa de administração de 1,90% a.a. contra mediana de 1,50% da classe — impacto anual estimado de R$ 1.795,04.",
                "caixa": "Liquidez imediata concentrada no mesmo emissor do maior CDB (Banco Beta).",
                "previdencia": "Fonte com selo C (extrato parseado, não reconciliado) — atualizar antes da reunião.",
            },
            "concentrations": [
                {"label": "Banco Beta (família)", "value": "19,30%", "note": "limite da política: 15%", "bad": True},
                {"label": "José em Banco Beta (FGC)", "value": "R$ 562.350,75", "note": "R$ 312.350,75 acima do teto", "bad": True},
                {"label": "Maria em Banco Delta (FGC)", "value": "R$ 262.110,45", "note": "R$ 12.110,45 acima do teto", "bad": True},
                {"label": "Banco Gama (família)", "value": "4,17%", "note": "dentro da política", "bad": False},
            ],
        }
        # analysis_runs is immutable (I2, trigger-enforced) — a new seed execution
        # always inserts a fresh run rather than mutating an existing one, even
        # when the content hash repeats (e.g. only narrative code changed).
        run = run_mod.build_run(PORTFOLIO, {"cdi": "bcb/sgs.12", "seed_version": 2}, outputs)
        run_id = upsert(cur, """
            insert into core.analysis_runs
                (org_id, family_id, run_hash, engine_version, policy_id, input_snapshot_ref, outputs)
            values (%s,%s,%s,%s,%s,%s,%s::jsonb) returning id
        """, (org_id, fam_almeida, run["input_sha256"], run["engine_version"], policy_id,
              f"seed:{run['run_id']}", run_mod.serialize(run)))
        print(f"analysis run: {run_id} (engine {run['engine_version']}, short {run['run_id']})")
        # reuniões apontam sempre para o run mais recente do seed
        cur.execute("update core.meetings set analysis_run_id=%s where org_id=%s and family_id=%s",
                    (run_id, org_id, fam_almeida))

        def meeting(fam: str, when: str, status: str, run_ref=None, sent=None) -> None:
            cur.execute("select id from core.meetings where org_id=%s and family_id=%s and scheduled_for=%s",
                        (org_id, fam, when))
            if cur.fetchone():
                return
            cur.execute("""
                insert into core.meetings (org_id, family_id, professional_id, scheduled_for, status,
                                           analysis_run_id, material_sent_at)
                values (%s,%s,
                        (select id from core.app_users where org_id=%s limit 1),
                        %s,%s,%s,%s)
            """, (org_id, fam, org_id, when, status, run_ref, sent))

        # professional bootstrap placeholder (linked on first Clerk login)
        cur.execute("select id from core.app_users where org_id=%s", (org_id,))
        if not cur.fetchone():
            cur.execute("""
                insert into core.app_users (org_id, auth_external_id, name, email, role)
                values (%s, 'pending-first-login', 'João Pedro Prista', 'joaopedroprista@gmail.com', 'admin')
            """, (org_id,))

        meeting(fam_almeida, "2026-07-09T10:00:00-03:00", "preparing", run_id)
        meeting(fam_souza, "2026-07-10T14:30:00-03:00", "scheduled")
        meeting(fam_castro, "2026-07-14T09:00:00-03:00", "material_sent", None, "2026-07-02T17:12:00-03:00")

        conn.commit()
        cur.execute("select count(*) from core.meetings where org_id=%s", (org_id,))
        print(f"meetings: {cur.fetchone()[0]}")
        print("== SEED OK ==")


if __name__ == "__main__":
    main()
