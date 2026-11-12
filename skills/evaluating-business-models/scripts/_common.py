"""Shared helpers for the evaluating-business-models scripts (Python stdlib only).

Every formula function returns the same shape (RT-FIN-01):
    {"value": <number|str|None>, "unit": str, "warnings": [str], "inputs_ledger_ids": [str], ...extra}
`value` is None when a P0 input is missing or when the function refuses to produce a number
(e.g. multi-root IRR, payback that never arrives). Refusals always carry an explanatory warning.

CLI convention shared by all calculators:
    python <script>.py <function_name> '<json kwargs>'
    python <script>.py <function_name> --file kwargs.json
    python <script>.py --list
"""
from __future__ import annotations

import inspect
import json
import math
import os
import sys
from typing import Any, Callable, Iterable

try:  # Windows consoles default to cp1252; outputs contain Spanish text and symbols.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

SKILL_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ASSETS_DIR = os.path.join(SKILL_DIR, "assets")


class MissingInput(Exception):
    """Raised internally when a P0 input is None; converted to value=None by `safe`."""


def res(value: Any, unit: str = "", warnings: Iterable[str] | None = None,
        ids: Iterable[str] | None = None, **extra: Any) -> dict:
    out = {"value": value, "unit": unit, "warnings": list(warnings or []),
           "inputs_ledger_ids": list(ids or [])}
    out.update(extra)
    return out


def missing(unit: str, names: Iterable[str], ids: Iterable[str] | None = None) -> dict:
    names = list(names)
    return res(None, unit, [f"P0 ausente: {', '.join(names)} -> unknown (no se estima)"], ids,
               missing_inputs=names)


def need(unit: str, ids, **kwargs) -> dict | None:
    """Return a `missing` result if any kwarg is None, else None."""
    absent = [k for k, v in kwargs.items() if v is None]
    return missing(unit, absent, ids) if absent else None


def isnum(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def invalid(unit: str, problems: Iterable[str], ids: Iterable[str] | None = None) -> dict:
    """Structured refusal for out-of-domain inputs (never complex numbers, crashes or non-physical values)."""
    return res(None, unit, [f"Entrada fuera de dominio: {p}" for p in problems], ids, invalid_inputs=True)


def check_domain(unit: str, ids=None, **specs) -> dict | None:
    """Validate numeric inputs. specs: name=(value, rule) with rule in
    'rate' [0,1], 'rate_lt1' [0,1), 'prob' [0,1], 'nonneg' >= 0, 'pos' > 0, 'num' finite number.
    None values are skipped (missing P0 is handled by `need`). Returns an `invalid` result or None."""
    problems = []
    for name, (v, rule) in specs.items():
        if v is None:
            continue
        if not isnum(v):
            problems.append(f"{name}={v!r} no es un numero finito")
            continue
        if rule in ("rate", "prob") and not 0 <= v <= 1:
            problems.append(f"{name}={v} debe estar en [0, 1] (fraccion, no porcentaje)")
        elif rule == "rate_lt1" and not 0 <= v < 1:
            problems.append(f"{name}={v} debe estar en [0, 1)")
        elif rule == "nonneg" and v < 0:
            problems.append(f"{name}={v} no puede ser negativo")
        elif rule == "pos" and v <= 0:
            problems.append(f"{name}={v} debe ser > 0")
    return invalid(unit, problems, ids) if problems else None


def sig2(x: float | None) -> float | None:
    """Round to two significant figures (RT-SENS-06: no false precision in ranges)."""
    if x is None or x == 0 or not isnum(x):
        return x
    return round(x, -int(math.floor(math.log10(abs(x)))) + 1)


def load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def asset(name: str) -> Any:
    return load_json(os.path.join(ASSETS_DIR, name))


def cli(module_globals: dict, public: Iterable[str]) -> None:
    """Minimal JSON CLI dispatcher used by every calculator script."""
    public = list(public)
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "--list"):
        print(json.dumps({"functions": public}, ensure_ascii=False, indent=2))
        return
    name = args[0]
    if name not in public:
        print(json.dumps({"error": f"funcion desconocida: {name}", "functions": public},
                         ensure_ascii=False))
        sys.exit(2)
    if len(args) >= 3 and args[1] == "--file":
        kwargs = load_json(args[2])
    elif len(args) >= 2:
        kwargs = json.loads(args[1])
    else:
        kwargs = {}
    fn: Callable = module_globals[name]
    try:
        out = fn(**kwargs)
    except TypeError as exc:
        sig = str(inspect.signature(fn))
        print(json.dumps({"error": str(exc), "signature": f"{name}{sig}"}, ensure_ascii=False))
        sys.exit(2)
    except (ValueError, ArithmeticError) as exc:
        # Structured error, never a traceback: the evaluation records the input as invalid/unknown.
        print(json.dumps({"value": None, "error": f"{type(exc).__name__}: {exc}", "recorded_as": "unknown"},
                         ensure_ascii=False))
        sys.exit(1)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
