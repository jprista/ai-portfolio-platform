"""Seeds the real confirmation queue (MVP_SCOPE §3.1 / CONSENSUS with
DOMAIN_MODEL SourceDocument+ExtractionBatch): uploads the 3 real XP
statements to Supabase Storage and creates source_documents +
extraction_batches rows with status='awaiting_confirmation', carrying the
FULLY RECONCILED position data (verified to the cent against each PDF's
own declared totals on 2026-07-07).

Client identities are pseudonymized in the family/holder display names
(minimization — DATA_STRATEGY §7); the underlying numbers are 100% real.

Idempotent (checked by sha256). Usage:  py scripts/seed_confirmation_queue.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import psycopg
import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
ENV = dotenv_values(ROOT / ".env")
PDF_DIR = ROOT / "prototype" / "data" / "real"
BUCKET = "documents"


def _storage_headers(extra: dict | None = None) -> dict:
    return {
        "Authorization": f"Bearer {ENV['SUPABASE_SERVICE_ROLE_KEY']}",
        "apikey": ENV["SUPABASE_SERVICE_ROLE_KEY"],
        **(extra or {}),
    }


def ensure_bucket() -> None:
    r = requests.post(f"{ENV['SUPABASE_URL']}/storage/v1/bucket",
                       json={"id": BUCKET, "name": BUCKET, "public": False},
                       headers=_storage_headers(), timeout=30)
    if r.status_code not in (200, 201):
        if "already exists" in r.text or "Duplicate" in r.text:
            print(f"  bucket '{BUCKET}' ja existe")
        else:
            print(f"  aviso bucket: {r.status_code} {r.text[:150]}")
    else:
        print(f"  bucket '{BUCKET}' criado")


def upload_pdf(local_path: Path, storage_path: str) -> str:
    data = local_path.read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    r = requests.post(
        f"{ENV['SUPABASE_URL']}/storage/v1/object/{BUCKET}/{storage_path}",
        data=data,
        headers=_storage_headers({"Content-Type": "application/pdf", "x-upsert": "true"}),
        timeout=60,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"upload falhou ({r.status_code}): {r.text[:300]}")
    return sha256


# ------------------------------------------------------------------ dataset ----
# Fully reconciled by hand against each PDF's own declared subtotals (2026-07-07).
DOCUMENTS = [
    {
        "file": "Posicao Detalhada - 12919134 (1).pdf",
        "conta": "12919134",
        "family_name": "Família Souza",
        "family_existing": True,
        "holder": "Gustavo B.",
        "profile": "Moderado",
        "reference_date": "2026-07-03",
        "patrimonio_total": "1014202.91",
        "positions": [
            {"name": "BBSE3", "kind": "equity", "issuer": "BB Seguridade", "value": "1977.27", "confidence": "A"},
            {"name": "BRAP4", "kind": "equity", "issuer": "Bradespar", "value": "1884.12", "confidence": "A"},
            {"name": "CPFE3", "kind": "equity", "issuer": "CPFL Energia", "value": "2228.52", "confidence": "A"},
            {"name": "CPLE3", "kind": "equity", "issuer": "Copel", "value": "2661.75", "confidence": "A"},
            {"name": "EQTL3", "kind": "equity", "issuer": "Equatorial Energia", "value": "2097.74", "confidence": "A"},
            {"name": "ITUB4", "kind": "equity", "issuer": "Itaú Unibanco", "value": "2396.80", "confidence": "A"},
            {"name": "PRIO3", "kind": "equity", "issuer": "PRIO", "value": "1845.90", "confidence": "A"},
            {"name": "RADL3", "kind": "equity", "issuer": "Raia Drogasil", "value": "1083.60", "confidence": "A"},
            {"name": "SUZB3", "kind": "equity", "issuer": "Suzano", "value": "1390.26", "confidence": "A"},
            {"name": "DEB ENEVA - SET/2035", "kind": "debenture", "issuer": "Eneva", "value": "2295.00",
             "confidence": "B", "index_kind": "ipca_plus", "valuation_mode": "market",
             "contract_terms": {"aplicacao": "2021-08-16", "vencimento": "2035-09-15",
                                 "taxa_contratada": "4.80", "taxa_mercado": "8.13", "indexador": "IPCA"}},
            {"name": "BNP Paribas Match FIF RF CP RL", "kind": "fund", "issuer": "BNP Paribas Asset Management",
             "value": "12581.45", "confidence": "A", "category": "renda_fixa_pos"},
            {"name": "XP Crédito Estruturado 120 FIC de FIF Multimercado CP RL", "kind": "fund", "issuer": "XP Asset Management",
             "value": "13534.93", "confidence": "A", "category": "renda_fixa_pos"},
            {"name": "Trend Pós-Fixado FIC FIRF Simples RL", "kind": "fund", "issuer": "Trend Asset Management",
             "value": "127420.58", "confidence": "A", "category": "renda_fixa_pos"},
            {"name": "XP Liquidez FIC RF REF DI CP RL", "kind": "fund", "issuer": "XP Asset Management",
             "value": "700447.13", "confidence": "A", "category": "renda_fixa_pos"},
            {"name": "Vinci Valorem FIM", "kind": "fund", "issuer": "Vinci Partners",
             "value": "14783.85", "confidence": "A", "category": "renda_fixa_inflacao"},
            {"name": "Occcam Equity Hedge FIC FIF Multi RL", "kind": "fund", "issuer": "Occam Brasil Gestão de Recursos",
             "value": "7111.89", "confidence": "A", "category": "multimercado"},
            {"name": "Ibiuna Hedge FIF FIM RL", "kind": "fund", "issuer": "Ibiuna Investimentos",
             "value": "19299.81", "confidence": "A", "category": "multimercado"},
            {"name": "Solana Long Short FIF em Cotas FIM", "kind": "fund", "issuer": "Solana Investimentos",
             "value": "13166.60", "confidence": "A", "category": "multimercado"},
            {"name": "Vinland Macro Advisory FIC FIM", "kind": "fund", "issuer": "Vinland Capital",
             "value": "12628.08", "confidence": "A", "category": "multimercado"},
            {"name": "Legacy Capital Advisory FIC FIM RL", "kind": "fund", "issuer": "Legacy Capital",
             "value": "12133.99", "confidence": "A", "category": "multimercado"},
            {"name": "Absolute Vertex Advisory FIC FIF Multimercado RL", "kind": "fund", "issuer": "Absolute Investimentos",
             "value": "12174.56", "confidence": "A", "category": "multimercado"},
            {"name": "Quantitas FIC FIM Mallorca", "kind": "fund", "issuer": "Quantitas Asset Management",
             "value": "11785.79", "confidence": "A", "category": "multimercado"},
            {"name": "Real Investor FIC de FIF em Ações RL", "kind": "fund", "issuer": "Real Investor",
             "value": "17279.49", "confidence": "A", "category": "renda_variavel"},
            {"name": "Western Asset BDR FIF", "kind": "fund", "issuer": "Western Asset Management",
             "value": "19687.51", "confidence": "A", "category": "renda_variavel"},
            {"name": "Saldo em conta corrente", "kind": "cash", "issuer": "XP Investimentos",
             "value": "90.10", "confidence": "A", "category": "caixa"},
            {"name": "Proventos a receber (ações e fundos)", "kind": "other", "issuer": "Diversos",
             "value": "216.19", "confidence": "C", "category": "renda_variavel",
             "note": "Dividendos/JCP provisionados, ainda não pagos — informativo"},
        ],
    },
    {
        "file": "Posicao Detalhada - 4432887.pdf",
        "conta": "4432887",
        "family_name": "Família Ferraz",
        "family_existing": False,
        "holder": "Lucas Coutinho",
        "profile": "Agressivo",
        "reference_date": "2026-07-03",
        "patrimonio_total": "1061063.93",
        "positions": [
            {"name": "CDB NBC BANK - NOV/2027", "kind": "cdb", "issuer": "NBC Bank", "value": "54447.08",
             "confidence": "A", "index_kind": "pre", "valuation_mode": "market",
             "contract_terms": {"aplicacao": "2025-11-05", "vencimento": "2027-11-05", "taxa_contratada": "14.08"}},
            {"name": "CDB Banco C6 Consignado - NOV/2027", "kind": "cdb", "issuer": "Banco C6", "value": "54484.12",
             "confidence": "A", "index_kind": "pre", "valuation_mode": "market",
             "contract_terms": {"aplicacao": "2025-11-05", "vencimento": "2027-11-05", "taxa_contratada": "14.20"}},
            {"name": "LCD BNDES - DEZ/2029", "kind": "lca", "issuer": "BNDES", "value": "123533.57",
             "confidence": "A", "index_kind": "cdi_pct", "valuation_mode": "market",
             "contract_terms": {"aplicacao": "2025-11-05", "vencimento": "2029-12-05", "index_pct": "93.50"}},
            {"name": "CDB Agibank - NOV/2027", "kind": "cdb", "issuer": "Agibank", "value": "109871.06",
             "confidence": "A", "index_kind": "ipca_plus", "valuation_mode": "market",
             "contract_terms": {"aplicacao": "2025-11-05", "vencimento": "2027-11-05", "taxa_contratada": "9.20"}},
            {"name": "Valora Guardian Advisory FIDC RL", "kind": "fund", "issuer": "Valora Investimentos",
             "value": "108999.33", "confidence": "A", "category": "renda_fixa_pos"},
            {"name": "BNP Paribas Rubi FIF RF CP RL", "kind": "fund", "issuer": "BNP Paribas Asset Management",
             "value": "96293.52", "confidence": "A", "category": "renda_fixa_pos"},
            {"name": "Trend DI FIC RF Simples RL", "kind": "fund", "issuer": "Trend Asset Management",
             "value": "108178.91", "confidence": "A", "category": "renda_fixa_pos"},
            {"name": "MAG Cash 10 FIRF", "kind": "fund", "issuer": "MAG Investimentos",
             "value": "75872.87", "confidence": "A", "category": "renda_fixa_pos"},
            {"name": "Capitânia Infra Renda 90 Incentivado Infraestrutura RF CP", "kind": "fund", "issuer": "Capitânia Investimentos",
             "value": "58372.48", "confidence": "A", "category": "renda_fixa_pos"},
            {"name": "Valora Vanguard FIC de FIDC RL", "kind": "fund", "issuer": "Valora Investimentos",
             "value": "58150.00", "confidence": "A", "category": "renda_fixa_pos"},
            {"name": "Trend Investback IV - One", "kind": "fund", "issuer": "Trend Asset Management",
             "value": "2446.04", "confidence": "A", "category": "renda_fixa_pos"},
            {"name": "XP Dividendos FIA RL", "kind": "fund", "issuer": "XP Asset Management",
             "value": "28081.34", "confidence": "A", "category": "renda_variavel"},
            {"name": "Tarpon GT 90 FIF FIA", "kind": "fund", "issuer": "Tarpon Investimentos",
             "value": "73318.29", "confidence": "A", "category": "renda_variavel"},
            {"name": "BRCO11", "kind": "fii", "issuer": "Bresco Logística", "value": "10390.38", "confidence": "A"},
            {"name": "BTHF11", "kind": "fii", "issuer": "BTG Pactual", "value": "10280.79", "confidence": "A"},
            {"name": "BTLG11", "kind": "fii", "issuer": "BTG Pactual Logística", "value": "10359.57", "confidence": "A"},
            {"name": "CPTS11", "kind": "fii", "issuer": "Capitânia", "value": "9585.69", "confidence": "A"},
            {"name": "GARE11", "kind": "fii", "issuer": "Guardian Real Estate", "value": "8555.14", "confidence": "A"},
            {"name": "KNCR11", "kind": "fii", "issuer": "Kinea Rendimentos", "value": "8614.40", "confidence": "A"},
            {"name": "PVBI11", "kind": "fii", "issuer": "VBI Prime Properties", "value": "5907.33", "confidence": "A"},
            {"name": "RBVA11", "kind": "fii", "issuer": "Rio Bravo", "value": "8823.04", "confidence": "A"},
            {"name": "VISC11", "kind": "fii", "issuer": "Vinci Shopping Centers", "value": "9353.01", "confidence": "A"},
            {"name": "XPLG11", "kind": "fii", "issuer": "XP Logística", "value": "9600.24", "confidence": "A"},
            {"name": "XPML11", "kind": "fii", "issuer": "XP Malls", "value": "11391.84", "confidence": "A"},
            {"name": "Saldo em conta corrente", "kind": "cash", "issuer": "XP Investimentos",
             "value": "5601.97", "confidence": "A", "category": "caixa"},
            {"name": "Proventos a receber (FIIs e ações)", "kind": "other", "issuer": "Diversos",
             "value": "551.93", "confidence": "C", "category": "renda_variavel",
             "note": "Rendimentos/JCP provisionados, ainda não pagos — informativo"},
        ],
    },
    {
        "file": "Posicao Detalhada - 3493887.pdf",
        "conta": "3493887",
        "family_name": "Família Nogueira",
        "family_existing": False,
        "holder": "Lucas Dantas",
        "profile": "Agressivo",
        "reference_date": "2026-07-03",
        "patrimonio_total": "268946.64",
        "positions": [
            {"name": "PRIO3", "kind": "equity", "issuer": "PRIO", "value": "3898.32", "confidence": "A"},
            {"name": "CDB Banco C6 Consignado - MAR/2027", "kind": "cdb", "issuer": "Banco C6", "value": "15583.30",
             "confidence": "A", "index_kind": "pre", "valuation_mode": "market",
             "contract_terms": {"aplicacao": "2026-03-19", "vencimento": "2027-03-19", "taxa_contratada": "14.50"}},
            {"name": "CDB Pernambucanas Financiador - AGO/2026", "kind": "cdb", "issuer": "Pernambucanas Financiadora",
             "value": "3509.43", "confidence": "A", "index_kind": "cdi_pct", "valuation_mode": "market",
             "contract_terms": {"aplicacao": "2022-08-26", "vencimento": "2026-08-25", "index_pct": "119.50"}},
            {"name": "CDB Banco XP S.A. - SET/2026", "kind": "cdb", "issuer": "Banco XP", "value": "50314.01",
             "confidence": "A", "index_kind": "cdi_pct", "valuation_mode": "market",
             "contract_terms": {"aplicacao": "2024-09-23", "vencimento": "2026-09-23", "index_pct": "100.00"}},
            {"name": "LCA Original - MAR/2030", "kind": "lca", "issuer": "Banco Original", "value": "15552.28",
             "confidence": "A", "index_kind": "cdi_pct", "valuation_mode": "market",
             "contract_terms": {"aplicacao": "2026-03-19", "vencimento": "2030-03-18", "index_pct": "95.00"}},
            {"name": "CDB Banco C6 Consignado - AGO/2028", "kind": "cdb", "issuer": "Banco C6", "value": "6089.08",
             "confidence": "A", "index_kind": "ipca_plus", "valuation_mode": "market",
             "contract_terms": {"aplicacao": "2024-11-25", "vencimento": "2028-08-15", "taxa_contratada": "7.40"}},
            {"name": "LCA BTG Pactual - MAR/2027", "kind": "lca", "issuer": "BTG Pactual", "value": "7284.38",
             "confidence": "A", "index_kind": "ipca_plus", "valuation_mode": "market",
             "contract_terms": {"aplicacao": "2026-03-19", "vencimento": "2027-03-19", "taxa_contratada": "6.29"}},
            {"name": "Trend Investback FIC FIRF Simples RL", "kind": "fund", "issuer": "Trend Asset Management",
             "value": "2612.25", "confidence": "A", "category": "renda_fixa_pos"},
            {"name": "Valora Vanguard FIC de FIDC RL", "kind": "fund", "issuer": "Valora Investimentos",
             "value": "22837.37", "confidence": "A", "category": "renda_fixa_pos"},
            {"name": "Maua Lajes Corporativas Feeder FII RL - Senior", "kind": "fund", "issuer": "Mauá Capital",
             "value": "26885.81", "confidence": "A", "category": "renda_fixa_inflacao"},
            {"name": "XP Dividendos FIA RL", "kind": "fund", "issuer": "XP Asset Management",
             "value": "8008.45", "confidence": "A", "category": "renda_variavel"},
            {"name": "SPX Patriot FIC FIA", "kind": "fund", "issuer": "SPX Capital",
             "value": "8010.18", "confidence": "A", "category": "renda_variavel"},
            {"name": "XP Logístico Prime Yield FII - I FII RL", "kind": "fund", "issuer": "XP Asset Management",
             "value": "25708.80", "confidence": "A", "category": "renda_variavel"},
            {"name": "Tesouro Selic 2029 (LFT)", "kind": "tesouro", "issuer": "Tesouro Nacional", "value": "28025.61",
             "confidence": "A", "index_kind": "selic", "valuation_mode": "market",
             "contract_terms": {"vencimento": "2029-03-01"}},
            {"name": "Tesouro IPCA+ 2029 (NTN-B Principal)", "kind": "tesouro", "issuer": "Tesouro Nacional", "value": "11490.70",
             "confidence": "A", "index_kind": "ipca_plus", "valuation_mode": "market",
             "contract_terms": {"vencimento": "2029-05-15"}},
            {"name": "Tesouro IPCA+ 2035 (NTN-B Principal)", "kind": "tesouro", "issuer": "Tesouro Nacional", "value": "8129.10",
             "confidence": "A", "index_kind": "ipca_plus", "valuation_mode": "market",
             "contract_terms": {"vencimento": "2035-05-15"}},
            {"name": "URPR11", "kind": "fii", "issuer": "Urca Prime Renda", "value": "360.18", "confidence": "A"},
            {"name": "Saldo em conta corrente", "kind": "cash", "issuer": "XP Investimentos",
             "value": "24642.00", "confidence": "A", "category": "caixa"},
            {"name": "Proventos a receber (FIIs)", "kind": "other", "issuer": "Diversos",
             "value": "5.40", "confidence": "C", "category": "renda_variavel",
             "note": "Rendimento provisionado, ainda não pago — informativo"},
        ],
    },
]


def upsert(cur, sql: str, params: tuple):
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0]


def main() -> None:
    print("== Storage ==")
    ensure_bucket()

    with psycopg.connect(ENV["DATABASE_URL"], connect_timeout=20) as conn:
        conn.autocommit = False
        cur = conn.cursor()

        cur.execute("select id from core.organizations where slug='demo'")
        org_id = cur.fetchone()[0]
        cur.execute("select id from core.app_users where org_id=%s limit 1", (org_id,))
        uploader = cur.fetchone()
        uploader_id = uploader[0] if uploader else None
        cur.execute("select id from core.custodians where name='XP Investimentos'")
        xp = cur.fetchone()[0]
        cur.execute("select id from core.benchmarks where org_id is null and kind='cdi' limit 1")
        cdi_bench = cur.fetchone()[0]

        for doc in DOCUMENTS:
            local_pdf = PDF_DIR / doc["file"]
            print(f"\n-- {doc['file']} ({doc['family_name']}) --")

            # sha256 first, to make the whole thing idempotent
            sha256 = hashlib.sha256(local_pdf.read_bytes()).hexdigest()
            cur.execute("select id, status from core.source_documents where sha256=%s", (sha256,))
            existing = cur.fetchone()
            if existing:
                print(f"  ja existe (status={existing[1]}) — pulando")
                continue

            storage_path = f"demo/{doc['conta']}/{sha256[:16]}.pdf"
            upload_pdf(local_pdf, storage_path)
            print(f"  upload ok -> {storage_path}")

            if doc["family_existing"]:
                cur.execute("select id from core.families where org_id=%s and display_name=%s",
                            (org_id, doc["family_name"]))
                family_id = cur.fetchone()[0]
            else:
                family_id = upsert(cur, """
                    insert into core.families (org_id, display_name, benchmark_id)
                    values (%s,%s,%s) returning id""", (org_id, doc["family_name"], cdi_bench))

            holder_id = upsert(cur, """
                insert into core.holders (org_id, family_id, display_name)
                values (%s,%s,%s) returning id""", (org_id, family_id, doc["holder"]))

            account_id = upsert(cur, """
                insert into core.accounts (org_id, family_id, holder_id, custodian_id, external_ref_masked, source)
                values (%s,%s,%s,%s,%s,'document') returning id""",
                (org_id, family_id, holder_id, xp, f"***{doc['conta'][-4:]}"))

            doc_id = upsert(cur, """
                insert into core.source_documents (org_id, family_id, storage_path, kind, sha256, uploaded_by, status)
                values (%s,%s,%s,'posicao_consolidada_xp',%s,%s,'awaiting_confirmation') returning id""",
                (org_id, family_id, storage_path, sha256, uploader_id))

            raw_output = {
                "conta": doc["conta"], "perfil": doc["profile"], "custodiante": "XP Investimentos",
                "reference_date": doc["reference_date"], "patrimonio_total_declarado": doc["patrimonio_total"],
                "account_id": str(account_id), "holder_id": str(holder_id),
                "positions": doc["positions"],
            }
            declared_sum = sum(float(p["value"]) for p in doc["positions"])
            diffs = {
                "declared_total": doc["patrimonio_total"],
                "sum_of_positions": f"{declared_sum:.2f}",
                "reconciled": abs(declared_sum - float(doc["patrimonio_total"])) < 0.02,
            }
            upsert(cur, """
                insert into core.extraction_batches (org_id, source_document_id, model_id, raw_output, status, diffs)
                values (%s,%s,'claude-vision-document-extraction-2026-07',%s::jsonb,'awaiting_confirmation',%s::jsonb)
                returning id""", (org_id, doc_id, json.dumps(raw_output), json.dumps(diffs)))
            print(f"  fila: {len(doc['positions'])} posições, reconciliado={diffs['reconciled']}")

        conn.commit()
        cur.execute("""select count(*) from core.source_documents
                       where org_id=%s and status='awaiting_confirmation'""", (org_id,))
        print(f"\n== FILA DE CONFIRMAÇÃO: {cur.fetchone()[0]} documento(s) pendente(s) ==")


if __name__ == "__main__":
    main()
