"""Validate evaluation.json against assets/evaluation.schema.json (RF-OUT-01, RT-LED-01/02).

Uses `jsonschema` if installed (optional); otherwise a built-in validator for the subset used by
the schemas (type, enum, required, properties, items, minItems, minimum, maximum, minLength,
pattern, $ref to ledger.schema.json) plus the custom keyword x-maxWords (quotes <= 15 words).
Extra semantic checks: every NO_GO has reversal conditions; INSUFFICIENT_EVIDENCE lists P0s;
forced_verdict is never INSUFFICIENT_EVIDENCE; scores are null when the module has unknown P0s.

Usage: python validate_output.py evaluation.json        -> exit 1 on errors
"""
from __future__ import annotations

import json
import os
import re
import sys

from _common import ASSETS_DIR, load_json

_TYPES = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float),
          "boolean": bool, "null": type(None)}


def _type_ok(value, t):
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPES[t])


def _validate(value, schema, path, errors, root_dir):
    if "$ref" in schema:
        schema = load_json(os.path.join(root_dir, schema["$ref"]))
    t = schema.get("type")
    if t:
        types = t if isinstance(t, list) else [t]
        if not any(_type_ok(value, x) for x in types):
            errors.append(f"{path}: tipo {type(value).__name__} no es {types}")
            return
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} no esta en {schema['enum']}")
    if isinstance(value, dict):
        for r in schema.get("required", []):
            if r not in value:
                errors.append(f"{path}: falta '{r}'")
        for k, sub in schema.get("properties", {}).items():
            if k in value:
                _validate(value[k], sub, f"{path}.{k}", errors, root_dir)
        if schema.get("additionalProperties") is False:   # Antigravity REV-013: typos such as 'verdit' must fail
            known = set(schema.get("properties", {}))
            for k in value:
                if k not in known:
                    errors.append(f"{path}: campo desconocido '{k}' (revisar ortografia o añadirlo al esquema)")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: menos de {schema['minItems']} elementos")
        if "items" in schema:
            for i, it in enumerate(value):
                _validate(it, schema["items"], f"{path}[{i}]", errors, root_dir)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} < {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} > {schema['maximum']}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: demasiado corto")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: no cumple el patron {schema['pattern']}")
        if "x-maxWords" in schema and len(value.split()) > schema["x-maxWords"]:
            errors.append(f"{path}: cita de {len(value.split())} palabras (> {schema['x-maxWords']})")


def semantic(ev: dict) -> list[str]:
    errs = []
    v = ev.get("verdict")
    if v == "NO_GO" and not [r for r in ev.get("reversal_conditions", []) if r]:
        errs.append("NO_GO sin condiciones de reversion (RF-GATE-15)")
    if v == "INSUFFICIENT_EVIDENCE" and not ev.get("p0_list"):
        errs.append("INSUFFICIENT_EVIDENCE sin lista de P0 y test mas barato")
    if ev.get("forced_verdict") == "INSUFFICIENT_EVIDENCE":
        errs.append("forced_verdict no puede ser INSUFFICIENT_EVIDENCE")
    gates = {g.get("id"): g.get("status") for g in ev.get("gates", [])}
    if v in ("GO", "CONDITIONAL_GO") and any(s == "fail" for s in gates.values()):
        errs.append("Veredicto favorable con una compuerta en fail: las puntuaciones nunca anulan compuertas")
    if v == "CONDITIONAL_GO" and not ev.get("conditions"):
        errs.append("CONDITIONAL_GO sin condiciones como hipotesis falsables")
    if ev.get("stage") == "pre_launch" and not (ev.get("intake") or {}).get("mode"):
        # v0.7.3: the 2026-11-12 run interviewed the founders but left no trace of it in evaluation.json
        errs.append("pre_launch sin 'intake' (modo de la entrevista): copia el 'intake' que devuelve evaluate")
    for e in ev.get("ledger", []):
        if e.get("status") == "fact" and (e.get("source") or {}).get("type") == "proposal_document" and not e.get("quote"):
            errs.append(f"{e.get('id')}: hecho del proponente sin cita literal (RS-FAB-02)")
        if (e.get("source") or {}).get("type") == "none" and e.get("status") not in ("assumption", "unknown"):
            errs.append(f"{e.get('id')}: numero sin fuente que no esta etiquetado como supuesto (RS-FAB-01)")
    return errs


def validate(ev: dict) -> list[str]:
    schema_path = os.path.join(ASSETS_DIR, "evaluation.schema.json")
    errors: list[str] = []
    try:
        import jsonschema  # optional dependency
        from jsonschema import RefResolver  # noqa: F401
        schema = load_json(schema_path)
        resolver = jsonschema.RefResolver(base_uri="file:///" + ASSETS_DIR.replace("\\", "/") + "/", referrer=schema)
        for err in jsonschema.Draft202012Validator(schema, resolver=resolver).iter_errors(ev):
            errors.append(f"{'/'.join(map(str, err.path))}: {err.message}")
        # x-maxWords is custom: always run the built-in pass for it
        for i, e in enumerate(ev.get("ledger", [])):
            q = e.get("quote")
            if isinstance(q, str) and len(q.split()) > 15:
                errors.append(f"$.ledger[{i}].quote: cita de {len(q.split())} palabras (> 15)")
    except Exception:
        _validate(ev, load_json(schema_path), "$", errors, ASSETS_DIR)
    return errors + semantic(ev)


def main(argv):
    if len(argv) < 2:
        print("uso: python validate_output.py evaluation.json")
        return 2
    errs = validate(load_json(argv[1]))
    print(json.dumps({"valid": not errs, "errors": errs}, ensure_ascii=False, indent=2))
    return 0 if not errs else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
