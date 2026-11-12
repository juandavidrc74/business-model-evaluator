"""Prospective evaluation log (RQ-EVAL-10, RS-SEC-03) - the asset that will calibrate the [P] thresholds.

`freeze` stores a frozen record (SHA-256 of evaluation.json + date, verdict, forced_verdict,
2-4 resolvable binary forecasts, CONDITIONAL_GO conditions with deadline, missing P0s). The log
lives in the USER'S project (default ./bme-evaluation-log/ under the current directory), never
inside the skill folder, because it contains proposal data.

`resolve` records outcomes; `score` computes Brier and BSS = 1 - BS/BS_ref with BS_ref = p(1-p)
(p = base rate of resolved events), Wilson intervals for counts, and refuses calibration curves
below ~50 resolved forecasts (VAL-106 [P]).

Usage:
    python log_evaluation.py freeze evaluation.json [--log-dir DIR] [--proceeded yes|no|unknown]
    python log_evaluation.py resolve <record_id> <forecast_index> <0|1> [--log-dir DIR]
    python log_evaluation.py score [--log-dir DIR]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import sys

from _common import SKILL_DIR, load_json

MIN_FOR_CALIBRATION = 50


def _log_dir(arg):
    d = os.path.abspath(arg or os.path.join(os.getcwd(), "bme-evaluation-log"))
    if os.path.commonpath([d, SKILL_DIR]) == SKILL_DIR:
        raise SystemExit("El registro no puede vivir dentro de la carpeta de la Skill (RS-SEC-03)")
    os.makedirs(d, exist_ok=True)
    return d


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def freeze(evaluation_path, log_dir=None, proceeded="unknown"):
    ev = load_json(evaluation_path)
    digest = sha256_file(evaluation_path)
    rec = {
        "record_id": f"{ev.get('evaluation_date', dt.date.today().isoformat())}-{digest[:12]}",
        "frozen_at": dt.datetime.now().isoformat(timespec="seconds"),
        "sha256": digest,
        "proposal_title": ev.get("proposal_title"),
        "verdict": ev.get("verdict"), "forced_verdict": ev.get("forced_verdict"),
        "low_agreement": ev.get("low_agreement"),
        "forecasts": [dict(f, outcome=None) for f in ev.get("forecasts", [])],
        "conditions": ev.get("conditions", []), "missing_p0": ev.get("p0_list", []),
        "user_proceeded": proceeded,
        "resolution_checkpoints": ["90d", "12m", "36m"],
    }
    if not 2 <= len(rec["forecasts"]) <= 4:
        rec["warning"] = "Se esperan 2-4 pronosticos binarios resolubles (evento, fecha y fuente definidos antes)"
    d = _log_dir(log_dir)
    path = os.path.join(d, rec["record_id"] + ".json")
    if os.path.exists(path):
        raise SystemExit(f"Registro ya congelado: {path}")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=2)
    return {"frozen": path, "sha256": digest}


def resolve(record_id, idx, outcome, log_dir=None):
    path = os.path.join(_log_dir(log_dir), record_id + ".json")
    rec = load_json(path)
    rec["forecasts"][int(idx)]["outcome"] = int(outcome)
    rec["forecasts"][int(idx)]["resolved_at"] = dt.date.today().isoformat()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=2)
    return {"resolved": record_id, "forecast": int(idx), "outcome": int(outcome)}


def wilson(k, n, z=1.959964):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def brier(pairs):
    """pairs: [(probability, outcome)] -> BS, base rate, BS_ref = p(1-p), BSS."""
    if not pairs:
        return None
    bs = sum((p - o) ** 2 for p, o in pairs) / len(pairs)
    base = sum(o for _, o in pairs) / len(pairs)
    ref = base * (1 - base)
    return {"n": len(pairs), "brier": bs, "base_rate": base, "bs_ref": ref,
            "bss": (1 - bs / ref) if ref > 0 else None}


def score(log_dir=None):
    d = _log_dir(log_dir)
    pairs, verdicts = [], {}
    for fn in os.listdir(d):
        if not fn.endswith(".json"):
            continue
        rec = load_json(os.path.join(d, fn))
        verdicts.setdefault(rec.get("verdict"), 0)
        verdicts[rec.get("verdict")] += 1
        for f in rec.get("forecasts", []):
            if f.get("outcome") is not None and f.get("probability") is not None:
                pairs.append((float(f["probability"]), int(f["outcome"])))
    out = {"verdict_counts": verdicts, "brier": brier(pairs)}
    if len(pairs) < MIN_FOR_CALIBRATION:
        out["calibration_curve"] = f"No se calcula: {len(pairs)} pronosticos resueltos < {MIN_FOR_CALIBRATION} (VAL-106)"
    n = sum(verdicts.values())
    out["verdict_share_wilson"] = {k: wilson(v, n) for k, v in verdicts.items()}
    out["note"] = "Comparacion descriptiva, no causal: un GO induce inversion y cambia el resultado (6j.3)"
    return out


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("evaluation")
    f.add_argument("--log-dir")
    f.add_argument("--proceeded", default="unknown")
    r = sub.add_parser("resolve")
    r.add_argument("record_id")
    r.add_argument("index")
    r.add_argument("outcome", choices=["0", "1"])
    r.add_argument("--log-dir")
    s = sub.add_parser("score")
    s.add_argument("--log-dir")
    a = ap.parse_args(argv[1:])
    if a.cmd == "freeze":
        out = freeze(a.evaluation, a.log_dir, a.proceeded)
    elif a.cmd == "resolve":
        out = resolve(a.record_id, a.index, a.outcome, a.log_dir)
    else:
        out = score(a.log_dir)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
