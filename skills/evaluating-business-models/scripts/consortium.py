"""Consortium controls in PRODUCTION code (closing the final-audit blockers 1-3).

1. validate_specialist_response: runtime enforcement of specialist_response.schema.json without the
   jsonschema dependency - oneOf branch by status, required fields, no extra fields, the module
   jurisdiction per agent_id (read from the schema's allOf/if/then, not hard-coded) and the required
   fields of every measurement, claim and score entry.
2. RemandLoop: the devil's-advocate objection loop as a finite state machine - SHA-256 fingerprint
   deduplication (a repeated objection does not consume quota), MAX_REMANDS = 1 (2 for critical
   deals), append-only history and a terminal verdict that can never be a complacent GO.
3. adverse_polarity: lexical check of a predicate claimed 'true' against the text of the ledger entry
   it cites; adverse wording ("sin presupuesto", "rechazado", "not signed"...) degrades it to unknown.
Stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata

from _common import ASSETS_DIR, load_json

SCHEMA_PATH = os.path.join(ASSETS_DIR, "schemas", "specialist_response.schema.json")
MAX_REMANDS = 1
MAX_REMANDS_CRITICAL = 2
CONSERVATIVE = ["NO_GO", "INSUFFICIENT_EVIDENCE", "CONDITIONAL_GO", "GO"]

_SCHEMA = None


def _schema():
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = load_json(SCHEMA_PATH)
    return _SCHEMA


def jurisdictions() -> dict:
    """agent_id -> sorted list of the modules it must (and may only) score, read from the schema."""
    out = {}
    for rule in _schema()["oneOf"][0].get("allOf", []):
        agent = rule.get("if", {}).get("properties", {}).get("agent_id", {}).get("const")
        mods = rule.get("then", {}).get("properties", {}).get("module_scores", {}).get("required", [])
        if agent:
            out[agent] = list(mods)
    return out


def _check_entry(entry, def_name, path, errors):
    d = _schema()["$defs"][def_name]
    if not isinstance(entry, dict):
        errors.append(f"{path}: debe ser objeto")
        return
    for r in d.get("required", []):
        if r not in entry or entry[r] in (None, ""):
            errors.append(f"{path}: falta '{r}'")
    for k, spec in d.get("properties", {}).items():
        if k not in entry:
            continue
        v = entry[k]
        enum = spec.get("enum") or _schema()["$defs"].get(spec.get("$ref", "").split("/")[-1], {}).get("enum")
        if enum and v not in enum:
            errors.append(f"{path}.{k}: {v!r} fuera del catalogo")
        if spec.get("type") == "integer" and (not isinstance(v, int) or isinstance(v, bool)
                                              or not spec.get("minimum", v) <= v <= spec.get("maximum", v)):
            errors.append(f"{path}.{k}: entero fuera de rango")
        if "pattern" in spec and isinstance(v, str) and not re.search(spec["pattern"], v):
            errors.append(f"{path}.{k}: no cumple {spec['pattern']}")
        if spec.get("type") == "array":
            if not isinstance(v, list):
                errors.append(f"{path}.{k}: debe ser lista")
                continue
            if len(v) < spec.get("minItems", 0):
                errors.append(f"{path}.{k}: menos de {spec['minItems']} elementos")
            item_pat = spec.get("items", {}).get("pattern")
            for it in v:
                if item_pat and not (isinstance(it, str) and re.search(item_pat, it)):
                    errors.append(f"{path}.{k}: elemento {it!r} no cumple {item_pat}")
        if spec.get("type") == "string" and not isinstance(v, str):
            errors.append(f"{path}.{k}: debe ser texto")
        if "maxLength" in spec and isinstance(v, str) and len(v) > spec["maxLength"]:
            errors.append(f"{path}.{k}: supera {spec['maxLength']} caracteres")
    if d.get("additionalProperties") is False:
        extra = set(entry) - set(d.get("properties", {}))
        if extra:
            errors.append(f"{path}: campos no permitidos {sorted(extra)}")


def validate_specialist_response(resp) -> list[str]:
    """Return the list of violations (empty = valid). Fail-closed: the compiler discards invalid responses."""
    errors: list[str] = []
    if not isinstance(resp, dict):
        return ["respuesta no es un objeto JSON"]
    status = resp.get("status")
    branch = _schema()["oneOf"][0 if status == "SUCCESS" else 1]
    if status not in ("SUCCESS", "FAILED", "DEGRADED"):
        return [f"status invalido {status!r}"]
    for r in branch.get("required", []):
        if r not in resp:
            errors.append(f"falta '{r}' (rama {status})")
    extra = set(resp) - set(branch.get("properties", {}))
    if extra:
        errors.append(f"campos no permitidos en la rama {status}: {sorted(extra)}")
    for k, spec in branch.get("properties", {}).items():
        if k not in resp:
            continue
        v = resp[k]
        if "const" in spec and v != spec["const"]:
            errors.append(f"{k}: debe ser {spec['const']!r}, recibido {v!r}")
        if "enum" in spec and v not in spec["enum"]:
            errors.append(f"{k}: {v!r} fuera del catalogo")
        if "pattern" in spec and not (isinstance(v, str) and re.search(spec["pattern"], v)):
            errors.append(f"{k}: no cumple {spec['pattern']}")
        expected = {"array": list, "object": dict, "string": str}.get(spec.get("type"))
        if expected and not isinstance(v, expected):
            errors.append(f"{k}: debe ser {spec['type']}")
        if "maxLength" in spec and isinstance(v, str) and len(v) > spec["maxLength"]:
            errors.append(f"{k}: supera {spec['maxLength']} caracteres")
        item_pat = spec.get("items", {}).get("pattern") if isinstance(spec.get("items"), dict) else None
        if item_pat and isinstance(v, list):
            errors += [f"{k}: elemento {it!r} no cumple {item_pat}" for it in v
                       if not (isinstance(it, str) and re.search(item_pat, it))]
    if status != "SUCCESS":
        return errors
    juris = jurisdictions()
    agent = resp.get("agent_id")
    if agent not in juris:
        errors.append(f"agent_id {agent!r} sin jurisdiccion definida")
    else:
        mods = set((resp.get("module_scores") or {}).keys())
        if mods != set(juris[agent]):
            errors.append(f"{agent}: module_scores debe ser exactamente {juris[agent]}, recibido {sorted(mods)}")
    for mid, entry in (resp.get("module_scores") or {}).items():
        _check_entry(entry, "module_score_entry", f"module_scores.{mid}", errors)
    for i, m in enumerate(resp.get("atomic_measurements") or []):
        _check_entry(m, "atomic_measurement_entry", f"atomic_measurements[{i}]", errors)
    for i, c in enumerate(resp.get("predicate_claims") or []):
        _check_entry(c, "predicate_claim_entry", f"predicate_claims[{i}]", errors)
    for i, c in enumerate(resp.get("challenges") or []):
        _check_entry(c, "challenge_entry", f"challenges[{i}]", errors)
    return errors


# ---------------------------------------------------------------- adverse polarity (blocker 3)

ADVERSE_PATTERNS = [
    r"\bsin (presupuesto|firma|firmar|contrato|aprobacion|evidencia|documento|plan)\b", r"\bno (firmad[oa]|aprobad[oa]|"
    r"tiene|existe|consta|probad[oa]|vigente|cumple)\b", r"\brechazad[oa]s?\b", r"\bpendiente(s)? de\b",
    r"\bborrador\b", r"\bverbal(mente)?\b", r"\bpropuest[oa] (no|sin)\b", r"\ben negociacion\b", r"\bvencid[oa]\b",
    r"\bcancelad[oa]\b", r"\brescindid[oa]\b", r"\bwithout (budget|contract|signature|approval|evidence)\b",
    r"\bnot (signed|approved|in place|compliant|proven)\b", r"\brejected\b", r"\bpending\b", r"\bdraft\b",
    r"\bunsigned\b", r"\bexpired\b", r"\bterminated\b",
]
_ADVERSE = [re.compile(p) for p in ADVERSE_PATTERNS]


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return " ".join(t.split())


def adverse_polarity(ledger_entry: dict | None) -> list[str]:
    """Adverse phrases found in the ledger entry's claim and quote (empty list = no conflict)."""
    if not ledger_entry:
        return []
    text = _norm(" ".join(str(ledger_entry.get(k) or "") for k in ("claim", "quote", "value")))
    return [m.group(0) for rx in _ADVERSE for m in [rx.search(text)] if m]


# ---------------------------------------------------------------- remand loop (blocker 2)

def fingerprint(objection: dict) -> str:
    key = {k: _norm(str(objection.get(k) or "")) for k in
           ("target_gate_or_module", "finding_title", "proposed_predicate_impact", "evidence_locator")}
    return hashlib.sha256(json.dumps(key, sort_keys=True).encode("utf-8")).hexdigest()


class RemandLoop:
    """Finite state machine: OPEN -> (submit/resolve)* -> CLOSED. History is append-only."""

    def __init__(self, critical_deal: bool = False):
        self.max_remands = MAX_REMANDS_CRITICAL if critical_deal else MAX_REMANDS
        self.used = 0
        self.history: list[dict] = []
        self.objections: dict[str, dict] = {}
        self.closed = False

    def submit(self, objection: dict) -> str:
        if self.closed:
            raise RuntimeError("Bucle cerrado: no admite objeciones nuevas")
        fp = fingerprint(objection)
        if fp in self.objections:
            self.history.append({"event": "duplicate", "fingerprint": fp})
            return "duplicate"                       # never consumes quota
        material = bool(objection.get("material", True))
        self.objections[fp] = {"objection": objection, "material": material, "state": "open"}
        if self.used >= self.max_remands:
            self.history.append({"event": "quota_exhausted", "fingerprint": fp})
            return "quota_exhausted"                 # recorded, stays open -> affects the terminal verdict
        self.used += 1
        self.history.append({"event": "remanded", "fingerprint": fp, "remand_no": self.used})
        return "remanded"

    def resolve(self, fp: str, outcome: str, ledger_ids: list[str] | None = None):
        """outcome: 'refuted' (new ledger evidence answers it), 'confirmed' (the objection is right) or 'open'."""
        if outcome not in ("refuted", "confirmed", "open"):
            raise ValueError(outcome)
        if fp not in self.objections:
            raise KeyError(f"Objecion no registrada con submit(): {fp}")
        if outcome == "refuted" and not ledger_ids:
            raise ValueError("Refutar exige ids de ledger nuevos (no basta con argumentar)")
        self.objections[fp]["state"] = outcome
        self.history.append({"event": outcome, "fingerprint": fp, "ledger_ids": ledger_ids or []})

    def terminal_verdict(self, gate_verdict: str) -> dict:
        """Combine the gate verdict with the objections. Never upgrades; a material objection that is
        confirmed -> NO_GO; still open -> at most INSUFFICIENT_EVIDENCE."""
        self.closed = True
        material = [o for o in self.objections.values() if o["material"]]
        confirmed = [o for o in material if o["state"] == "confirmed"]
        open_ = [o for o in material if o["state"] == "open"]
        verdict = gate_verdict
        if confirmed:
            verdict = "NO_GO"
        elif open_:
            verdict = min(gate_verdict, "INSUFFICIENT_EVIDENCE", key=CONSERVATIVE.index)
        self.history.append({"event": "closed", "verdict": verdict})
        return {"verdict": verdict, "remands_used": self.used, "max_remands": self.max_remands,
                "confirmed": len(confirmed), "open": len(open_),
                "reversal_conditions": [o["objection"].get("finding_title") for o in confirmed + open_]}


# ---------------------------------------------------------------- CLI

def run_remand_file(data: dict) -> dict:
    """data = {"gate_verdict": ..., "critical_deal": bool, "objections": [{...objection, "outcome": ...,
    "ledger_ids": [...]}]} -> terminal verdict plus the full append-only history."""
    loop = RemandLoop(critical_deal=bool(data.get("critical_deal")))
    for obj in data.get("objections", []):
        if loop.submit(obj) == "remanded" and obj.get("outcome") in ("refuted", "confirmed", "open"):
            loop.resolve(fingerprint(obj), obj["outcome"], obj.get("ledger_ids"))
    out = loop.terminal_verdict(data.get("gate_verdict", "INSUFFICIENT_EVIDENCE"))
    out["history"] = loop.history
    return out


def main(argv=None):
    import argparse
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Controles del modo consorcio")
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="Valida una respuesta de especialista contra el esquema")
    v.add_argument("response")
    r = sub.add_parser("remand", help="Cierra el bucle de objeciones y devuelve el veredicto terminal")
    r.add_argument("objections")
    a = ap.parse_args(argv)
    if a.cmd == "validate":
        errs = validate_specialist_response(load_json(a.response))
        print(json.dumps({"valid": not errs, "errors": errs}, ensure_ascii=False, indent=2))
        return 0 if not errs else 1
    print(json.dumps(run_remand_file(load_json(a.objections)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
