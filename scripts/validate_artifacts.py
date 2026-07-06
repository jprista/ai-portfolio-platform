"""Validates repo artifacts formally — used locally and by CI.

- db/migrations/*.sql  -> parsed against real PostgreSQL grammar (pglast)
- packages/contracts/openapi.yaml -> OpenAPI 3.1 spec validation
"""
from __future__ import annotations

import sys
from pathlib import Path

import pglast
import yaml
from openapi_spec_validator import validate as validate_openapi

ROOT = Path(__file__).resolve().parents[1]
failed = False

for path in sorted((ROOT / "db" / "migrations").glob("*.sql")):
    try:
        stmts = pglast.parse_sql(path.read_text(encoding="utf-8"))
        print(f"  OK   {path.name}: {len(stmts)} statements")
    except Exception as e:
        print(f"  FAIL {path.name}: {e}")
        failed = True

spec_path = ROOT / "packages" / "contracts" / "openapi.yaml"
try:
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    validate_openapi(spec)
    print(f"  OK   openapi.yaml: {len(spec['paths'])} paths, {len(spec['components']['schemas'])} schemas")
except Exception as e:
    print(f"  FAIL openapi.yaml: {e}")
    failed = True

sys.exit(1 if failed else 0)
