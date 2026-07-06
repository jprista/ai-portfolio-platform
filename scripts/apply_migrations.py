"""Applies db/migrations/*.sql in order and runs post-apply verification:
schema inventory, RLS isolation probe and immutability probe (both rolled
back — the probes leave zero trace).

Usage:  py scripts/apply_migrations.py [--verify-only]
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import psycopg
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
ENV = dotenv_values(ROOT / ".env")
MIGRATIONS = sorted((ROOT / "db" / "migrations").glob("*.sql"))


def apply(conn: psycopg.Connection) -> None:
    conn.autocommit = True  # files carry their own begin/commit
    with conn.cursor() as cur:
        cur.execute("""
            create table if not exists public.schema_migrations (
                filename text primary key, applied_at timestamptz default now())
        """)
        for path in MIGRATIONS:
            cur.execute("select 1 from public.schema_migrations where filename = %s", (path.name,))
            if cur.fetchone():
                print(f"  skip   {path.name} (ja aplicada)")
                continue
            print(f"  apply  {path.name} ...", end=" ")
            cur.execute(path.read_text(encoding="utf-8"))
            cur.execute("insert into public.schema_migrations (filename) values (%s)", (path.name,))
            print("ok")


def verify(conn: psycopg.Connection) -> None:
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("""
            select table_schema, count(*) from information_schema.tables
            where table_schema in ('core','market','audit') and table_type='BASE TABLE'
            group by 1 order by 1
        """)
        for schema, n in cur.fetchall():
            print(f"  schema {schema}: {n} tabelas")
        cur.execute("select count(*) from pg_type t join pg_namespace n on n.oid=t.typnamespace "
                    "where t.typtype='e' and n.nspname in ('core','audit')")
        print(f"  enums: {cur.fetchone()[0]}")
        cur.execute("select count(*) from core.benchmarks where org_id is null")
        print(f"  benchmarks globais (seed): {cur.fetchone()[0]}")
        cur.execute("select count(*) from core.custodians")
        print(f"  custodiantes (seed): {cur.fetchone()[0]}")

    # ---- RLS isolation probe (rolled back) ----
    # Uses Supabase's pre-existing 'authenticated' role (postgres is a member),
    # avoiding role creation through the pooler. Everything is rolled back.
    org_a, org_b = str(uuid.uuid4()), str(uuid.uuid4())
    conn.autocommit = False
    with conn.cursor() as cur:
        cur.execute("grant usage on schema core to authenticated")
        cur.execute("grant select on core.families, core.organizations to authenticated")
        cur.execute("insert into core.organizations (id,name,slug) values (%s,'Org A','org-a'),(%s,'Org B','org-b')",
                    (org_a, org_b))
        cur.execute("insert into core.families (org_id, display_name) values (%s,'Familia A1'),(%s,'Familia B1')",
                    (org_a, org_b))
        cur.execute("set local role authenticated")
        cur.execute("select set_config('app.current_org_id', %s, true)", (org_a,))
        cur.execute("select count(*) from core.families")
        a = cur.fetchone()[0]
        cur.execute("select set_config('app.current_org_id', %s, true)", (org_b,))
        cur.execute("select count(*) from core.families")
        b = cur.fetchone()[0]
        cur.execute("select set_config('app.current_org_id', '', true)")
        cur.execute("select count(*) from core.families")
        none = cur.fetchone()[0]
    conn.rollback()
    ok = (a, b, none) == (1, 1, 0)
    print(f"  RLS probe: org A ve {a} familia(s), org B ve {b}, sem contexto ve {none} -> "
          f"{'ISOLAMENTO OK' if ok else 'FALHA DE ISOLAMENTO'}")
    if not ok:
        sys.exit(1)

    # ---- immutability probe (rolled back) ----
    with conn.cursor() as cur:
        cur.execute("insert into core.organizations (id,name,slug) values (%s,'Org I','org-i')", (org_a,))
        cur.execute("insert into core.organization_policies (org_id, version) values (%s, 1) returning id", (org_a,))
        pid = cur.fetchone()[0]
        try:
            cur.execute("update core.organization_policies set maturity_window_days = 30 where id = %s", (pid,))
            print("  Immutability probe: UPDATE passou -> FALHA (I2 violada)")
            conn.rollback(); sys.exit(1)
        except psycopg.errors.RaiseException as e:
            print(f"  Immutability probe: UPDATE bloqueado pelo trigger -> OK ({str(e).splitlines()[0][:60]})")
    conn.rollback()


if __name__ == "__main__":
    with psycopg.connect(ENV["DATABASE_URL"], connect_timeout=15) as conn:
        if "--verify-only" not in sys.argv:
            print("== Migracoes ==")
            apply(conn)
        print("== Verificacao ==")
        verify(conn)
    print("== BANCO PRONTO ==")
