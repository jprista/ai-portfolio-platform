"""Immutable analysis runs — the seed of invariant I2 (ARCHITECTURE.md §3).

A run captures: canonical input hash, engine version, data timestamps and
every output. Re-running with the same inputs must reproduce the outputs.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal

ENGINE_VERSION = "0.1.0-prototype"


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)


def build_run(portfolio_raw: dict, market_raw: dict, outputs: dict) -> dict:
    input_hash = hashlib.sha256(
        (_canonical(portfolio_raw) + _canonical(market_raw) + ENGINE_VERSION).encode("utf-8")
    ).hexdigest()
    return {
        "run_id": input_hash[:16],
        "engine_version": ENGINE_VERSION,
        "input_sha256": input_hash,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "outputs": outputs,
    }


def serialize(run: dict) -> str:
    def _default(o):
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, date):
            return o.isoformat()
        raise TypeError(f"unserializable: {type(o)}")

    return json.dumps(run, indent=2, ensure_ascii=False, default=_default)
