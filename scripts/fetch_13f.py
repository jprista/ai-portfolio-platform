"""Fetches the latest two 13F-HR filings for a set of world-class managers
(SEC EDGAR, public data) and loads top holdings + quarter-over-quarter
changes into market.manager_* tables (CONSENSUS_RADAR.md §2).

Idempotent. Usage:  py scripts/fetch_13f.py
"""
from __future__ import annotations

import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
ENV = dotenv_values(ROOT / ".env")

UA = {"User-Agent": "AI Portfolio Platform research joaopedroprista@gmail.com"}

MANAGERS = [
    ("Berkshire Hathaway (Warren Buffett)", "0001067983"),
    ("Bridgewater Associates (Ray Dalio)", "0001350694"),
    ("Pershing Square (Bill Ackman)", "0001336528"),
    ("Duquesne Family Office (Druckenmiller)", "0001536411"),
    ("Scion Asset Management (Michael Burry)", "0001649339"),
]


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def latest_13f_accessions(cik: str, n: int = 2) -> list[dict]:
    data = json.loads(get(f"https://data.sec.gov/submissions/CIK{cik}.json"))
    recent = data["filings"]["recent"]
    out = []
    for form, acc, rdate, fdate in zip(
        recent["form"], recent["accessionNumber"], recent["reportDate"], recent["filingDate"]
    ):
        if form == "13F-HR":
            out.append({"accession": acc, "period_end": rdate, "filed_at": fdate})
            if len(out) == n:
                break
    return out


def fetch_holdings(cik: str, accession: str) -> list[dict]:
    acc = accession.replace("-", "")
    idx = json.loads(get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/index.json"))
    xml_files = [i["name"] for i in idx["directory"]["item"]
                 if i["name"].lower().endswith(".xml") and "primary_doc" not in i["name"].lower()]
    if not xml_files:
        return []
    raw = get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{xml_files[0]}")
    root = ET.fromstring(raw)
    ns = root.tag.split("}")[0] + "}" if "}" in root.tag else ""
    agg: dict[str, Decimal] = {}
    for it in root.iter(f"{ns}infoTable"):
        name = (it.findtext(f"{ns}nameOfIssuer") or "?").title()
        value = Decimal(it.findtext(f"{ns}value") or "0")
        agg[name] = agg.get(name, Decimal(0)) + value
    total = sum(agg.values()) or Decimal(1)
    ranked = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
    return [
        {"issuer": name, "value": value, "pct": (value / total * 100).quantize(Decimal("0.01")), "total": total}
        for name, value in ranked
    ]


def main() -> None:
    with psycopg.connect(ENV["DATABASE_URL"], connect_timeout=20) as conn:
        cur = conn.cursor()
        for name, cik in MANAGERS:
            cur.execute("""
                insert into market.managers (name, jurisdiction, source, external_ref)
                values (%s,'US','sec_13f',%s)
                on conflict (source, external_ref) do update set name = excluded.name
                returning id""", (name, cik))
            mgr_id = cur.fetchone()[0]

            filings = latest_13f_accessions(cik)
            if not filings:
                print(f"{name}: sem 13F-HR")
                continue
            snapshots = []
            for f in filings:
                holdings = fetch_holdings(cik, f["accession"])
                snapshots.append((f, holdings))
                time.sleep(0.4)  # SEC fair-use

            prev = {h["issuer"]: h["value"] for h in (snapshots[1][1] if len(snapshots) > 1 else [])}
            f, holdings = snapshots[0]
            cur.execute("""
                insert into market.manager_filings (manager_id, period_end, filed_at, source_url, total_value)
                values (%s,%s,%s,%s,%s)
                on conflict (manager_id, period_end) do update set captured_at = now()
                returning id""",
                (mgr_id, f["period_end"], f["filed_at"],
                 f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{f['accession'].replace('-','')}",
                 holdings[0]["total"] if holdings else None))
            filing_id = cur.fetchone()[0]
            cur.execute("delete from market.manager_holdings where filing_id=%s", (filing_id,))
            for rank, h in enumerate(holdings[:15], start=1):
                if h["issuer"] not in prev:
                    change = "new"
                else:
                    delta = (h["value"] - prev[h["issuer"]]) / prev[h["issuer"]] * 100 if prev[h["issuer"]] else Decimal(0)
                    change = "increased" if delta > 5 else "reduced" if delta < -5 else "unchanged"
                cur.execute("""
                    insert into market.manager_holdings (filing_id, rank, issuer_name, value, pct_of_total, change_kind)
                    values (%s,%s,%s,%s,%s,%s)""",
                    (filing_id, rank, h["issuer"], h["value"], h["pct"], change))
            conn.commit()
            top = holdings[0]["issuer"] if holdings else "-"
            print(f"{name}: {f['period_end']} · {len(holdings)} emissores · top: {top}")
    print("== RADAR 13F OK ==")


if __name__ == "__main__":
    main()
