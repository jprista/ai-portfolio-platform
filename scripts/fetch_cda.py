"""Fetches Brazilian managers' REAL equity portfolios from CVM public data
(CDA — Composição e Diversificação das Aplicações) and loads them into the
market.manager_* tables, joining the SEC 13F global managers in the Radar.

Two public datasets:
  - cad_fi.csv  : fund registry (CNPJ -> GESTOR mapping)
  - cda_fi_YYYYMM.zip -> BLC_4 CSV: equity positions per fund

Regulatory lag: funds may withhold positions up to 90 days (sigilo) — the
Radar declares this by design (CONSENSUS_RADAR.md).

Usage:  py scripts/fetch_cda.py [YYYYMM]   (default: 202605)
"""
from __future__ import annotations

import csv
import io
import sys
import unicodedata
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
ENV = dotenv_values(ROOT / ".env")
CACHE = Path(r"C:\dev\data-cache")
CACHE.mkdir(exist_ok=True)

REG_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip"
CDA_URL = "https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS/cda_fi_{month}.zip"

# (padrão de match no campo Gestor, nome de exibição) — múltiplos padrões
# podem apontar para a mesma casa (braços distintos da mesma gestora)
TARGETS = [
    ("VERDE ASSET", "Verde Asset (Luis Stuhlberger)"),
    ("DYNAMO ADMINISTRACAO", "Dynamo"),
    ("ATMOS CAPITAL", "Atmos Capital"),
    ("SPX GESTAO", "SPX Capital"),
    ("SPX EQUITIES", "SPX Capital"),
    ("SQUADRA INVESTIMENTOS", "Squadra Investimentos"),
    ("IP CAPITAL PARTNERS", "IP Capital Partners"),
    ("KINEA INVESTIMENTOS", "Kinea Investimentos (Itaú)"),
    ("XP GESTAO", "XP Asset Management"),
    ("XP ALLOCATION", "XP Asset Management"),
    ("BTG PACTUAL ASSET", "BTG Pactual Asset Management"),
    ("BTG PACTUAL GESTORA", "BTG Pactual Asset Management"),
    ("BRADESCO ASSET", "Bradesco Asset (BRAM)"),
    ("BRAM - BRADESCO", "Bradesco Asset (BRAM)"),
    ("ITAU UNIBANCO ASSET", "Itaú Asset Management"),
]


def normalize(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().upper()


def digits(s: str) -> str:
    """CNPJ canônico: só dígitos (registro usa 00332266000131; CDA usa 00.332.266/0001-31)."""
    return "".join(ch for ch in (s or "") if ch.isdigit())


def download(url: str, dest: Path) -> Path:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  cache hit: {dest.name}")
        return dest
    print(f"  baixando {url} ...")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    print(f"  ok: {dest.stat().st_size/1e6:.1f} MB")
    return dest


def build_fund_map() -> dict[str, str]:
    """CNPJ (do fundo E de cada classe, pós-RCVM175) -> display do gestor.

    Registro novo da CVM: Gestor vive em registro_fundo.csv; o CDA referencia
    o CNPJ da CLASSE (CNPJ_FUNDO_CLASSE), ligada ao fundo por ID_Registro_Fundo
    em registro_classe.csv.
    """
    path = download(REG_URL, CACHE / "registro_fundo_classe.zip")
    fund_gestor: dict[str, str] = {}   # ID_Registro_Fundo -> display
    cnpj_map: dict[str, str] = {}      # CNPJ (fundo ou classe) -> display

    with zipfile.ZipFile(path) as z:
        with z.open("registro_fundo.csv") as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1"), delimiter=";")
            for row in reader:
                if "CANCEL" in (row.get("Situacao") or "").upper():
                    continue
                gestor = normalize(row.get("Gestor", ""))
                if not gestor:
                    continue
                for pattern, display in TARGETS:
                    if pattern in gestor:
                        fund_gestor[row["ID_Registro_Fundo"]] = display
                        cnpj = digits(row.get("CNPJ_Fundo") or "")
                        if cnpj:
                            cnpj_map[cnpj] = display
                        break
        with z.open("registro_classe.csv") as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1"), delimiter=";")
            for row in reader:
                display = fund_gestor.get(row.get("ID_Registro_Fundo", ""))
                if not display:
                    continue
                if "CANCEL" in (row.get("Situacao") or "").upper():
                    continue
                cnpj = digits(row.get("CNPJ_Classe") or "")
                if cnpj:
                    cnpj_map[cnpj] = display

    print(f"  fundos dos alvos: {len(fund_gestor)} · CNPJs mapeados (fundos+classes): {len(cnpj_map)}")
    return cnpj_map


def aggregate_equities(month: str, cnpj_map: dict[str, str]) -> dict[str, dict[str, dict]]:
    """display do gestor -> { ativo_key -> {name, code, value} } somando as carteiras da casa."""
    path = download(CDA_URL.format(month=month), CACHE / f"cda_fi_{month}.zip")
    agg: dict[str, dict[str, dict]] = {}
    with zipfile.ZipFile(path) as z:
        blc4 = next(n for n in z.namelist() if "BLC_4" in n)
        print(f"  lendo {blc4} ...")
        with z.open(blc4) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1"), delimiter=";")
            cnpj_col = next(c for c in reader.fieldnames if "CNPJ_FUNDO" in c)
            val_col = next(c for c in reader.fieldnames if "VL_MERC_POS_FINAL" in c)
            code_col = next((c for c in reader.fieldnames if c == "CD_ATIVO"), None)
            name_col = next((c for c in reader.fieldnames if c == "DS_ATIVO"), None)
            tipo_col = next((c for c in reader.fieldnames if c == "TP_ATIVO"), None)
            # só renda variável de verdade — o bloco mistura debêntures, opções e futuros
            EQUITY_TYPES = ("ACAO ORDINARIA", "ACAO PREFERENCIAL", "CERTIFICADO DE DEPOSITO DE ACOES",
                            "BDR NIVEL I", "BDR NIVEL II", "BDR NIVEL III", "BDR NAO PATROCINADO", "BDR DE ETF")
            n_rows = 0
            for row in reader:
                display = cnpj_map.get(digits(row[cnpj_col]))
                if not display:
                    continue
                if tipo_col and normalize(row.get(tipo_col, "")) not in EQUITY_TYPES:
                    continue
                raw_val = (row.get(val_col) or "0").replace(",", ".")
                try:
                    value = Decimal(raw_val)
                except Exception:
                    continue
                if value <= 0:
                    continue
                code = (row.get(code_col) or "").strip() if code_col else ""
                name = (row.get(name_col) or "").strip() if name_col else ""
                key = code or name
                if not key:
                    continue
                bucket = agg.setdefault(display, {})
                entry = bucket.setdefault(key, {"code": code, "name": name.title() or code, "value": Decimal(0)})
                entry["value"] += value
                n_rows += 1
            print(f"  linhas de ações agregadas dos alvos: {n_rows}")
    return agg


def main() -> None:
    month = sys.argv[1] if len(sys.argv) > 1 else "202605"
    period_end = date(int(month[:4]), int(month[4:6]), 1)
    # último dia do mês
    period_end = (date(period_end.year + (period_end.month == 12), (period_end.month % 12) + 1, 1)
                  - __import__("datetime").timedelta(days=1))

    print("== Registro de fundos e classes (CVM) ==")
    cnpj_map = build_fund_map()

    print(f"== Carteiras CDA {month} (CVM) ==")
    agg = aggregate_equities(month, cnpj_map)

    print("== Carga no banco ==")
    with psycopg.connect(ENV["DATABASE_URL"], connect_timeout=20) as conn:
        cur = conn.cursor()
        for display, holdings in sorted(agg.items()):
            total = sum(h["value"] for h in holdings.values())
            if total <= 0:
                continue
            if len(holdings) < 5:
                # carteira quase toda em sigilo — exibir 1-2 posições residuais como
                # "a carteira da casa" seria enganoso; melhor omitir e declarar
                print(f"  {display}: apenas {len(holdings)} posição(ões) pública(s) — pulado (sigilo)")
                continue
            cur.execute("""
                insert into market.managers (name, jurisdiction, source, external_ref)
                values (%s,'BR','cvm_cda',%s)
                on conflict (source, external_ref) do update set name = excluded.name
                returning id""", (display, display))
            mgr_id = cur.fetchone()[0]
            cur.execute("""
                insert into market.manager_filings (manager_id, period_end, filed_at, source_url, total_value)
                values (%s,%s,%s,%s,%s)
                on conflict (manager_id, period_end) do update set captured_at = now()
                returning id""",
                (mgr_id, period_end, period_end,
                 f"https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS/cda_fi_{month}.zip", total))
            filing_id = cur.fetchone()[0]
            cur.execute("delete from market.manager_holdings where filing_id=%s", (filing_id,))
            ranked = sorted(holdings.values(), key=lambda h: h["value"], reverse=True)
            for rank, h in enumerate(ranked[:15], start=1):
                pct = (h["value"] / total * 100).quantize(Decimal("0.01"))
                cur.execute("""
                    insert into market.manager_holdings (filing_id, rank, issuer_name, instrument, value, pct_of_total, change_kind)
                    values (%s,%s,%s,%s,%s,%s,null)""",
                    (filing_id, rank, h["name"][:120], h["code"][:40] or None, h["value"], pct))
            conn.commit()
            top = ranked[0]
            print(f"  {display}: {len(holdings)} ativos, R$ {total/Decimal(1e9):.2f} bi em ações · top: {top['code'] or top['name']}")
    print("== RADAR CVM OK ==")


if __name__ == "__main__":
    main()
