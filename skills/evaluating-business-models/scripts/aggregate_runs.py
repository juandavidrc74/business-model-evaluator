"""Aggregate N independent runs (6b.3, decision 2 confirmed 2026-11-10).

- Verdict = MODE (a nominal verdict has no median). Ties go to the most conservative verdict
  (TIE_ORDER) and set low_agreement. low_agreement also when the mode has < 4/5 runs (N >= 5)
  or < 2/3 runs (N < 5).
- Module scores 1-5: median with IQR; SD > 0.5 is reported as uncertainty. Verbalised confidence
  is never used: dispersion is the uncertainty signal.
- Figures extracted from the input must be identical in every run (RF-GATE-13): a mismatch is an
  extraction error, not judgement uncertainty.
- Script-computed gate statuses must be identical across runs on the same ledger (RF-GATE-11).

Usage: python aggregate_runs.py aggregate --file runs.json   (runs.json = list of evaluation.json dicts)
"""
from __future__ import annotations

import math
import statistics
from collections import Counter

from _common import cli, res

N_DEFAULT = 3
N_HIGH = 5          # high_impact: true or --calibration mode
TIE_ORDER = ["NO_GO", "INSUFFICIENT_EVIDENCE", "CONDITIONAL_GO", "GO"]   # most conservative first
SD_UNCERTAINTY = 0.5


def runs_required(high_impact=False, calibration=False):
    return res(N_HIGH if (high_impact or calibration) else N_DEFAULT, "ejecuciones")


def aggregate_verdicts(verdicts=None):
    raw = list(verdicts or [])
    verdicts = [v for v in raw if v]
    if not verdicts:
        return res(None, "veredicto", ["Sin ejecuciones"])
    incomplete = len(raw) - len(verdicts)
    counts = Counter(verdicts)
    top = max(counts.values())
    tied = [v for v, c in counts.items() if c == top]
    winner = sorted(tied, key=TIE_ORDER.index)[0]
    n = len(verdicts)
    need = math.ceil(0.8 * n) if n >= 5 else math.ceil(2 * n / 3)
    low = len(tied) > 1 or top < need
    w = []
    if len(tied) > 1:
        w.append(f"Empate entre {tied}: gana el mas conservador ({winner})")
    if top < need:
        w.append(f"Veredicto modal en {top}/{n} ejecuciones (< {need}/{n}): low_agreement")
    if incomplete:
        # An incomplete run is reported, never silently dropped (audit R8).
        w.append(f"{incomplete} ejecucion(es) incompleta(s) sin veredicto: excluidas del recuento y marcadas")
        low = True
    return res(winner, "veredicto", w, counts=dict(counts), low_agreement=low, modal_share=top / n,
               incomplete_runs=incomplete)


def _iqr(vals):
    if len(vals) < 2:
        return None
    q = statistics.quantiles(vals, n=4, method="inclusive")
    return q[2] - q[0]


def aggregate_scores(module_scores=None):
    """module_scores: {"M7": [4, 4, 5], ...}; nulls (unknown) are kept out of the median and counted."""
    out = {}
    for mid, vals in (module_scores or {}).items():
        known = [v for v in vals if v is not None]
        if not known:
            out[mid] = {"median": None, "iqr": None, "sd": None, "unknown_runs": len(vals), "uncertain": True}
            continue
        sd = statistics.pstdev(known) if len(known) > 1 else 0.0
        out[mid] = {"median": statistics.median(known), "iqr": _iqr(known), "sd": sd,
                    "unknown_runs": len(vals) - len(known), "uncertain": sd > SD_UNCERTAINTY}
    return res(out, "puntuaciones", [])


def check_extraction(extracted=None):
    """extracted: list (one per run) of {field: value}. Any mismatch is an extraction error."""
    runs = extracted or []
    errors = []
    fields = set().union(*[set(r) for r in runs]) if runs else set()
    for f in sorted(fields):
        vals = [r.get(f) for r in runs]
        if len({repr(v) for v in vals}) > 1:
            errors.append({"field": f, "values": vals})
    return res(not errors, "booleano", [f"Error de extraccion en {e['field']}: {e['values']}" for e in errors],
               extraction_errors=errors)


def check_script_gates(gate_runs=None):
    """gate_runs: list (one per run) of [{"id", "status", "computed_by"}]; script gates must not vary."""
    diffs = []
    for gid in sorted({g["id"] for run in (gate_runs or []) for g in run}):
        st = [next((g for g in run if g["id"] == gid), {}) for run in gate_runs]
        if any("script" in (g.get("computed_by") or "") and not (g.get("computed_by") or "").startswith("judgment")
               for g in st):
            if len({g.get("status") for g in st}) > 1:
                diffs.append({"gate": gid, "statuses": [g.get("status") for g in st]})
    return res(not diffs, "booleano", [f"Compuerta de script {d['gate']} distinta entre ejecuciones: {d['statuses']}"
                                       " (revisar el ledger: debe ser identica)" for d in diffs], script_gate_diffs=diffs)


def _norm(x):
    return " ".join(str(x or "").lower().split())


def merge_ledgers(ledgers=None):
    """Merge ledger entries from several sources (domain researchers, runs) without averaging.

    Key = claim + source url + publication date + country + definition/unit. Exact duplicates (same key and
    value) are collapsed keeping every origin id. Same claim/definition with different values -> a
    `conflict_group` with status 'contradiction' for each member: shown, never averaged (RT-BMK-08)."""
    merged, by_key = [], {}
    for li, ledger in enumerate(ledgers or []):
        for e in ledger:
            src = e.get("source") or {}
            key = (_norm(e.get("claim")), _norm(src.get("url")), _norm(e.get("publication_date")),
                   _norm(e.get("country")), _norm(e.get("unit")))
            sig = (key, repr(e.get("value")))
            if sig in by_key:
                by_key[sig].setdefault("merged_from", []).append(e.get("id"))
                continue
            entry = dict(e, origin_ledger=li)
            by_key[sig] = entry
            merged.append(entry)
    groups = {}
    for e in merged:
        src = e.get("source") or {}
        gkey = (_norm(e.get("claim")), _norm(e.get("country")), _norm(e.get("unit")))
        groups.setdefault(gkey, []).append(e)
    conflicts = []
    for gi, (gkey, members) in enumerate(groups.items()):
        values = {repr(m.get("value")) for m in members}
        if len(values) > 1:
            gid = f"CG{gi + 1:03d}"
            for m in members:
                m["conflict_group"] = gid
                m["status"] = "contradiction"
            nums = [m.get("value") for m in members
                    if isinstance(m.get("value"), (int, float)) and not isinstance(m.get("value"), bool)]
            conflict = {"conflict_group": gid, "claim": members[0].get("claim"),
                        "values": [{"id": m.get("id"), "value": m.get("value"),
                                    "source": (m.get("source") or {}).get("url")} for m in members]}
            if len(nums) >= 2:
                # Antigravity audit, fusion protocol: a numeric conflict becomes a P0 range for G6, which
                # recomputes the gate at both bounds; it is never averaged.
                conflict["bounds"] = {"low": min(nums), "high": max(nums)}
                conflict["suggested_p0_unknown"] = {"field": members[0].get("claim"), "low": min(nums),
                                                    "high": max(nums), "gate": members[0].get("gate"),
                                                    "path": None, "cheapest_test": "Documento primario que "
                                                    "resuelva la discrepancia"}
            conflicts.append(conflict)
    return res(merged, "ledger", [f"{len(conflicts)} grupos en conflicto: mostrar todas las cifras, no promediar"]
               if conflicts else [], conflicts=conflicts, duplicates_collapsed=sum(len(ledger) for ledger in
                                                                                  (ledgers or [])) - len(merged))


def aggregate(runs=None):
    """Full aggregation of evaluation.json dicts from N runs."""
    runs = runs or []
    agg_v = aggregate_verdicts([r.get("verdict") for r in runs])
    scores = {}
    for r in runs:
        for m in r.get("modules", []):
            scores.setdefault(m["id"], []).append(m.get("score"))
    agg_s = aggregate_scores(scores)
    ext = check_extraction([r.get("extracted_figures", {}) for r in runs])
    sg = check_script_gates([r.get("gates", []) for r in runs])
    differing = []
    for gid in sorted({g["id"] for r in runs for g in r.get("gates", [])}):
        st = {next((g.get("status") for g in r.get("gates", []) if g["id"] == gid), None) for r in runs}
        if len(st) > 1:
            differing.append(gid)
    for mid, v in agg_s["value"].items():
        if v["uncertain"]:
            differing.append(mid)
    forced = aggregate_verdicts([r.get("forced_verdict") for r in runs])["value"]
    return res(agg_v["value"], "veredicto", agg_v["warnings"] + ext["warnings"] + sg["warnings"],
               runs=len(runs), counts=agg_v.get("counts"), low_agreement=agg_v.get("low_agreement"),
               forced_verdict=forced, modules=agg_s["value"], differing=differing,
               extraction_ok=ext["value"], script_gates_consistent=sg["value"])


PUBLIC = ["aggregate", "aggregate_verdicts", "aggregate_scores", "check_extraction", "check_script_gates",
          "runs_required", "merge_ledgers"]

if __name__ == "__main__":
    cli(globals(), PUBLIC)
