"""Fetches a macro snapshot (Selic meta, IPCA 12m, cambio USD/BRL) from
BCB/SGS (public, no key) and stores it in market.macro_snapshot, feeding the
"Contexto macroeconomico" section of the aba Analise.

Same pattern as fetch_13f.py / fetch_cda.py: batch fetch external data ->
store in the database -> the app only ever reads from Postgres, never calls
an external API at request time.

Idempotent (each run inserts a fresh snapshot row; the app reads the latest
by captured_at). Usage:  py scripts/fetch_macro_snapshot.py
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import psycopg
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
ENV = dotenv_values(ROOT / ".env")

SERIES = {
    "selic_meta": 432,    # Meta Selic definida pelo Copom (% a.a.)
    "ipca_12m": 13522,    # IPCA - variacao acumulada em 12 meses (%)
    "usd_brl": 1,         # Dolar americano (venda) - PTAX
}


def latest(codigo: int) -> tuple[Decimal, str]:
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/1?formato=json"
    with urllib.request.urlopen(url, timeout=20) as r:
        row = json.load(r)[0]
    as_of = datetime.strptime(row["data"], "%d/%m/%Y").date().isoformat()
    return Decimal(row["valor"].replace(",", ".")), as_of


def main() -> None:
    selic, selic_as_of = latest(SERIES["selic_meta"])
    ipca, ipca_as_of = latest(SERIES["ipca_12m"])
    usd, usd_as_of = latest(SERIES["usd_brl"])
    print(f"Selic meta {selic}% ({selic_as_of}) · IPCA 12m {ipca}% ({ipca_as_of}) · USD/BRL {usd} ({usd_as_of})")

    with psycopg.connect(ENV["DATABASE_URL"], connect_timeout=20) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into market.macro_snapshot
                    (selic_meta_pct, selic_as_of, ipca_12m_pct, ipca_as_of, usd_brl, usd_as_of)
                values (%s, %s, %s, %s, %s, %s)
                """,
                (selic, selic_as_of, ipca, ipca_as_of, usd, usd_as_of),
            )
        conn.commit()
    print("snapshot gravado em market.macro_snapshot")


if __name__ == "__main__":
    main()
