"""Staleness check (RS-FAB-05, RT-BMK-06): a benchmark, price card or country parameter whose
next_review is on or before the evaluation date is expired. Expired records are context only
("dato pendiente de revision desde AAAA-MM-DD") and cannot feed gates until refreshed.
Records with status 'proposal' are reviewed by event, never blocked (ambiguity A10).

Usage:
    python check_staleness.py --date 2026-12-10                      # whole benchmark DB + assets
    python check_staleness.py --date 2026-12-10 --ids AI-001 GEO-007 # specific ids
    python check_staleness.py --date 2026-12-10 --evaluation evaluation.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

from _common import ASSETS_DIR, load_json

ALWAYS_REFRESH = {"GEO-007", "GEO-008", "GEO-010", "GEO-011", "GEO-023"}   # macro data re-queried before use


def _date(x):
    try:
        return dt.date.fromisoformat(str(x)[:10])
    except (TypeError, ValueError):
        return None


def check(evaluation_date: str, ids=None, evaluation=None) -> dict:
    today = dt.date.fromisoformat(evaluation_date)
    db = {b["id"]: b for b in load_json(os.path.join(ASSETS_DIR, "benchmarks.json"))["benchmarks"]}
    wanted = set(ids or [])
    if evaluation:
        for e in evaluation.get("ledger", []):
            if e.get("benchmark_id"):
                wanted.add(e["benchmark_id"])
    targets = [db[i] for i in wanted if i in db] if wanted else list(db.values())
    expired, event, refresh = [], [], []
    for b in targets:
        if b.get("status") == "proposal":
            event.append(b["id"])
            continue
        nr = _date(b.get("next_review"))
        if nr and nr <= today:
            expired.append({"id": b["id"], "next_review": str(nr), "metric": b.get("metric"),
                            "message": f"dato pendiente de revision desde {nr}"})
        if b["id"] in ALWAYS_REFRESH:
            refresh.append(b["id"])
    cards = []
    pc = os.path.join(ASSETS_DIR, "price_cards.json")
    if os.path.exists(pc):
        for c in load_json(pc).get("cards", []):
            nr = _date(c.get("next_review"))
            used = not wanted or bool(set(c.get("benchmark_ids") or [c.get("benchmark_id")]) & wanted) \
                or c["id"] in wanted
            if nr and nr <= today and used:
                cards.append({"card": c["id"], "next_review": str(nr)})
    geo = []
    gp = os.path.join(ASSETS_DIR, "geo_params_CO.json")
    if os.path.exists(gp):
        for p in load_json(gp).get("params", []):
            nr = _date(p.get("next_review"))
            if nr and nr <= today and (not wanted or p["key"] in wanted):
                geo.append({"param": p["key"], "next_review": str(nr)})
    # REV-014: in inventory mode (no ids, no evaluation) the answer is a maintenance list, not a gate verdict:
    # a stale record that the evaluation does not use must not block it.
    inventory = not wanted
    blocking = [e["id"] for e in expired] + [c["card"] for c in cards]
    return {"evaluation_date": evaluation_date, "mode": "inventory" if inventory else "evaluation",
            "expired": expired, "expired_price_cards": cards, "expired_geo_params": geo,
            "event_review_proposals": sorted(event), "refresh_before_use": sorted(refresh),
            "ok_for_gates": None if inventory else not blocking,
            "blocking_for_gates": [] if inventory else blocking,
            "note": ("Inventario de mantenimiento: refrescar los vencidos antes de usarlos" if inventory else
                     "Los registros vencidos solo son contexto y no alimentan compuertas hasta refrescarse")}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--evaluation")
    a = ap.parse_args(argv[1:])
    ev = load_json(a.evaluation) if a.evaluation else None
    print(json.dumps(check(a.date, a.ids, ev), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
