"""Sensitivity SA-01 ... SA-04: tornado, coherent scenarios, archetype stress and gated Monte Carlo.

Fixed sequence (RT-SENS-01): tornado -> 3 coherent scenarios + archetype stress -> Monte Carlo
ONLY if the evidence gate passes (RT-SENS-02). Models are arithmetic expressions over driver
names, evaluated with a restricted AST evaluator (no attribute access, no calls except
min/max/abs/round, no imports), so the CLI never executes arbitrary code.

Driver spec: {"name", "base", "min", "max", "mode"?, "status": fact|estimate|assumption|unknown,
              "ledger_id", "dist": pert|triangular|uniform|lognormal|normal, "kind": rate|money|count}
"""
from __future__ import annotations

import ast
import math
import operator
import random
from statistics import NormalDist
from typing import Sequence

from _common import cli, need, res, sig2

SEED = 20261109
N_DEFAULT = 10_000
MC_GATE_SWING_SHARE = 0.80   # drivers summing >= 80 % of the tornado swing must be evidenced [P]
MC_GATE_MIN_DRIVERS = 3      # >= 3 drivers with a documented range [P]
ASSUMPTION_SWING_CAP = 0.50  # > 50 % of swing from assumptions -> verdict <= CONDITIONAL_GO and G6 [P]
REJECT_MSG = "MC rechazado: evidencia insuficiente en drivers dominantes"
EVIDENCED = {"fact", "estimate"}

ARCHETYPE_STRESS = {
    # RT-SENS-01 archetype-specific stress (6e.5)
    "S1": ["deflacion de tarifas del 3-5 % anual por IA", "perdida del mayor cliente"],
    "S2": ["deflacion de tarifas del 3-5 % anual por IA", "perdida del mayor cliente"],
    "S3": ["deflacion de tarifas del 3-5 % anual por IA", "perdida del mayor cliente"],
    "S4": ["perdida del mayor cliente", "fin de creditos cloud"],
    "P-AI-APP": ["precio del proveedor de modelo x2,0", "fin de creditos de IA"],
    "AIX": ["precio del proveedor de modelo x2,0", "fin de creditos de IA"],
    "P-SAAS-SS": ["fin de creditos cloud"], "P-SAAS-SL": ["fin de creditos cloud"],
    "P-USAGE": ["fin de creditos cloud"], "P-INFRA": ["subida del coste de GPU/infraestructura"],
}

# ---------------------------------------------------------------- safe expression evaluator

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod}
_UN = {ast.USub: operator.neg, ast.UAdd: operator.pos}
_FUNCS = {"min": min, "max": max, "abs": abs, "round": round}


def safe_eval(expr: str, variables: dict) -> float:
    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise ValueError(f"variable desconocida en el modelo: {node.id}")
            return variables[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            return _BIN[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UN:
            return _UN[type(node.op)](ev(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS \
                and not node.keywords:
            return _FUNCS[node.func.id](*[ev(a) for a in node.args])
        raise ValueError(f"expresion no permitida: {ast.dump(node)[:60]}")
    return ev(ast.parse(expr, mode="eval"))


# ---------------------------------------------------------------- SA-01 tornado

def tornado(model=None, drivers: Sequence[dict] | None = None, ledger_ids=None):
    """SA-01: output with each driver at min and max, others at base; swing ranked with cumulative share."""
    m = need("tabla", ledger_ids, model=model, drivers=drivers)
    if m:
        return m
    base_vars = {d["name"]: d["base"] for d in drivers}
    base_out = safe_eval(model, base_vars)
    rows = []
    for d in drivers:
        lo = safe_eval(model, {**base_vars, d["name"]: d["min"]})
        hi = safe_eval(model, {**base_vars, d["name"]: d["max"]})
        rows.append({"driver": d["name"], "low_output": lo, "high_output": hi, "swing": abs(hi - lo),
                     "status": d.get("status", "unknown"), "ledger_id": d.get("ledger_id")})
    rows.sort(key=lambda r: r["swing"], reverse=True)
    total = sum(r["swing"] for r in rows) or 1.0
    cum = 0.0
    for r in rows:
        r["share"] = r["swing"] / total
        cum += r["share"]
        r["cumulative_share"] = cum
    assumption_share = sum(r["share"] for r in rows if r["status"] not in EVIDENCED)
    warnings = []
    if assumption_share > ASSUMPTION_SWING_CAP:
        warnings.append(f"{assumption_share:.0%} del swing procede de supuestos sin evidencia: veredicto maximo "
                        "CONDITIONAL_GO y G6 marcada (RT-SENS-06)")
    ids = [d.get("ledger_id") for d in drivers if d.get("ledger_id")]
    return res(rows, "tabla", warnings, ids, base_output=base_out, assumption_swing_share=assumption_share,
               cap_conditional_go=assumption_share > ASSUMPTION_SWING_CAP,
               dominant_drivers=[r["driver"] for r in _dominant(rows)])


def _dominant(rows):
    out, cum = [], 0.0
    for r in rows:
        out.append(r)
        cum += r["share"]
        if cum >= MC_GATE_SWING_SHARE - 1e-12:
            break
    return out


# ---------------------------------------------------------------- scenarios & stress

def scenarios(model=None, drivers: Sequence[dict] | None = None, sets: dict | None = None, narrative: dict | None = None,
              archetype=None, ledger_ids=None):
    """Three coherent scenarios (drivers move together under a declared narrative) + archetype stress list.

    sets = {"base": {...overrides}, "optimistic": {...}, "pessimistic": {...}, "stress:<name>": {...}}
    """
    m = need("tabla", ledger_ids, model=model, drivers=drivers, sets=sets)
    if m:
        return m
    warnings = []
    for name in ("base", "optimistic", "pessimistic"):
        if name not in sets:
            warnings.append(f"Falta el escenario coherente '{name}'")
    if not narrative:
        warnings.append("Escenarios sin narrativa declarada: no son coherentes por construccion")
    base_vars = {d["name"]: d["base"] for d in drivers}
    out = {name: safe_eval(model, {**base_vars, **over}) for name, over in sets.items()}
    required_stress = ARCHETYPE_STRESS.get(archetype, [])
    present = [k for k in sets if k.startswith("stress:")]
    if required_stress and not present:
        warnings.append("Falta el estres del arquetipo: " + "; ".join(required_stress))
    return res(out, "salida del modelo", warnings, ledger_ids, narrative=narrative or {},
               required_stress=required_stress)


# ---------------------------------------------------------------- SA-02 distributions

def pert_params(a=None, m=None, b=None, ledger_ids=None):
    """SA-02: PERT mean = (a + 4m + b)/6; alpha = 1 + 4(m-a)/(b-a); beta = 1 + 4(b-m)/(b-a)."""
    mi = need("parametros", ledger_ids, a=a, m=m, b=b)
    if mi:
        return mi
    if not a <= m <= b or a == b:
        return res(None, "parametros", ["Se requiere a <= m <= b con a < b"], ledger_ids)
    alpha = 1 + 4 * (m - a) / (b - a)
    beta = 1 + 4 * (b - m) / (b - a)
    return res((a + 4 * m + b) / 6, "media", [], ledger_ids, alpha=alpha, beta=beta)


def _validate_driver(d):
    dist = d.get("dist", "pert")
    if not d.get("ledger_id"):
        raise ValueError(f"Driver '{d.get('name')}' sin id de ledger: rechazado (RT-FIN-05)")
    if dist == "normal" and d.get("kind") == "rate":
        raise ValueError(f"Distribucion normal no permitida para la tasa '{d['name']}' (RT-SENS-03)")
    if dist in ("pert", "triangular") and d.get("mode") is None:
        raise ValueError(f"'{d['name']}': {dist} exige minimo, moda y maximo documentados")
    if dist == "lognormal" and not (d.get("median") or d.get("base")):
        raise ValueError(f"'{d['name']}': lognormal exige mediana")
    return dist


def sample_driver(d: dict, n: int, rng: random.Random) -> list[float]:
    dist = _validate_driver(d)
    if dist == "pert":
        p = pert_params(d["min"], d["mode"], d["max"])
        return [d["min"] + rng.betavariate(p["alpha"], p["beta"]) * (d["max"] - d["min"]) for _ in range(n)]
    if dist == "triangular":
        return [rng.triangular(d["min"], d["max"], d["mode"]) for _ in range(n)]
    if dist == "uniform":
        return [rng.uniform(d["min"], d["max"]) for _ in range(n)]
    if dist == "lognormal":
        mu, s = math.log(d.get("median") or d["base"]), d.get("sigma", 1.0)
        return [rng.lognormvariate(mu, s) for _ in range(n)]
    if dist == "normal":
        return [rng.gauss(d["base"], d["sd"]) for _ in range(n)]
    raise ValueError(f"distribucion desconocida: {dist}")


def sample_pert(a=None, m=None, b=None, n=1000, seed=SEED, ledger_id=None):
    """SA-02 sampler. Refuses without a ledger id (RT-FIN-05)."""
    if not ledger_id:
        return res(None, "muestras", ["Sin id de ledger: rechazado"], [])
    rng = random.Random(seed)
    s = sample_driver({"name": "x", "min": a, "mode": m, "max": b, "dist": "pert", "ledger_id": ledger_id}, n, rng)
    return res(s, "muestras", [], [ledger_id])


def sample_triangular(a=None, m=None, b=None, n=1000, seed=SEED, ledger_id=None):
    if not ledger_id:
        return res(None, "muestras", ["Sin id de ledger: rechazado"], [])
    rng = random.Random(seed)
    return res([rng.triangular(a, b, m) for _ in range(n)], "muestras", [], [ledger_id])


# ---------------------------------------------------------------- SA-03 correlation

def cholesky(matrix: Sequence[Sequence[float]]) -> list[list[float]]:
    n = len(matrix)
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = sum(L[i][k] * L[j][k] for k in range(j))
            if i == j:
                val = matrix[i][i] - s
                if val <= 1e-12:
                    raise ValueError("Matriz de correlacion no definida positiva (RT-FIN-05)")
                L[i][j] = math.sqrt(val)
            else:
                L[i][j] = (matrix[i][j] - s) / L[j][j]
    return L


def correlated_uniforms(corr: Sequence[Sequence[float]] | None = None, n=1000, seed=SEED, ledger_ids=None):
    """SA-03: Gaussian copula via Cholesky. Raises on a non positive-definite matrix."""
    m = need("muestras", ledger_ids, corr=corr)
    if m:
        return m
    L = cholesky(corr)
    rng, nd, k = random.Random(seed), NormalDist(), len(corr)
    out = []
    for _ in range(n):
        z = [rng.gauss(0, 1) for _ in range(k)]
        x = [sum(L[i][j] * z[j] for j in range(i + 1)) for i in range(k)]
        out.append([nd.cdf(v) for v in x])
    return res(out, "uniformes", [], ledger_ids)


def _reorder(samples: dict[str, list[float]], names, corr, rng):
    """Iman-Conover (simplified): impose the rank order of correlated normals on independent samples."""
    L = cholesky(corr)
    n, k = len(next(iter(samples.values()))), len(names)
    normals = []
    for _ in range(n):
        z = [rng.gauss(0, 1) for _ in range(k)]
        normals.append([sum(L[i][j] * z[j] for j in range(i + 1)) for i in range(k)])
    out = {}
    for j, name in enumerate(names):
        order = sorted(range(n), key=lambda r: normals[r][j])
        sorted_s = sorted(samples[name])
        col = [0.0] * n
        for rank, row in enumerate(order):
            col[row] = sorted_s[rank]
        out[name] = col
    return out


# ---------------------------------------------------------------- SA-04 summary & Monte Carlo

def _pct(sorted_vals, q):
    if not sorted_vals:
        return None
    pos = q * (len(sorted_vals) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def mc_summary(samples: Sequence[float] | None = None, p=None, n=None, threshold=0.0, ledger_ids=None):
    """SA-04: P10/P50/P90 (2 significant figures), P(output < threshold) and its standard error.

    With only (p, n) returns the standard error sqrt(p(1-p)/N) (T22)."""
    if samples is None:
        mi = need("fraccion", ledger_ids, p=p, n=n)
        if mi:
            return mi
        if not 0 <= p <= 1 or n <= 0:
            return res(None, "error estandar", ["p debe estar en [0, 1] y n > 0"], ledger_ids)
        return res(math.sqrt(p * (1 - p) / n), "error estandar", [], ledger_ids)
    s = sorted(x for x in samples if isinstance(x, (int, float)) and math.isfinite(x))
    n = len(s)
    if n == 0:
        return res(None, "salida del modelo", ["Sin muestras validas: no hay resumen"], ledger_ids)
    dropped = len(samples) - n
    prob = sum(1 for x in s if x < threshold) / n
    w = [] if n >= N_DEFAULT else [f"N = {n} < {N_DEFAULT}: precision insuficiente"]
    if dropped:
        w.append(f"{dropped} muestras no numericas o no finitas descartadas")
    return res({"p10": sig2(_pct(s, 0.10)), "p50": sig2(_pct(s, 0.50)), "p90": sig2(_pct(s, 0.90))},
               "salida del modelo", w + ["P50 es un percentil, no una prevision; mostrar junto al escenario pesimista"],
               ledger_ids, prob_below_threshold=prob, threshold=threshold,
               standard_error=math.sqrt(prob * (1 - prob) / n), n=n)


def mc_gate(model=None, drivers: Sequence[dict] | None = None, ledger_ids=None):
    """RT-SENS-02 gate: >= 3 evidenced ranges AND every dominant (80 % swing) driver evidenced."""
    t = tornado(model, drivers)
    if t["value"] is None:
        return t
    by_name = {d["name"]: d for d in drivers}
    evidenced = [d for d in drivers if d.get("status") in EVIDENCED and d.get("ledger_id")
                 and d.get("min") is not None and d.get("max") is not None]
    dominant = t["dominant_drivers"]
    bad = [n for n in dominant if by_name[n].get("status") not in EVIDENCED]
    reasons = []
    if len(evidenced) < MC_GATE_MIN_DRIVERS:
        reasons.append(f"solo {len(evidenced)} drivers con rango documentado (minimo {MC_GATE_MIN_DRIVERS})")
    if bad:
        reasons.append("drivers dominantes sin evidencia: " + ", ".join(bad))
    passed = not reasons
    return res(passed, "booleano", [] if passed else [REJECT_MSG + " (" + "; ".join(reasons) + ")"],
               [d.get("ledger_id") for d in evidenced], tornado=t["value"], dominant_drivers=dominant,
               reasons=reasons)


def monte_carlo(model=None, drivers: Sequence[dict] | None = None, n=N_DEFAULT, seed=SEED, corr=None,
                threshold=0.0, force=False, ledger_ids=None):
    """Gated Monte Carlo. Without correlation evidence, runs rho = 0, +0.5 and -0.5 (RT-SENS-04)."""
    gate = mc_gate(model, drivers)
    if gate["value"] is not True and not force:
        return res(None, "salida del modelo", gate["warnings"] or [REJECT_MSG], gate["inputs_ledger_ids"],
                   gate=gate)
    names = [d["name"] for d in drivers]
    k = len(names)
    blocks = {}
    # A uniform negative correlation is only feasible down to -1/(k-1); with k >= 3 drivers -0.5 is
    # singular or impossible, so the closest feasible value is used and labelled explicitly.
    neg = -0.5 if k <= 2 else max(-0.5, round(-1.0 / (k - 1) + 0.05, 2))
    corr_sets = {"given": corr} if corr else {
        "rho=0": None,
        "rho=+0.5": [[1.0 if i == j else 0.5 for j in range(k)] for i in range(k)],
        f"rho={neg:+.2f}": [[1.0 if i == j else neg for j in range(k)] for i in range(k)],
    }
    for label, cm in corr_sets.items():
        rng = random.Random(seed)
        samples = {d["name"]: sample_driver(d, n, rng) for d in drivers}
        try:
            if cm is not None:
                samples = _reorder(samples, names, cm, rng)
        except ValueError as exc:
            blocks[label] = {"error": str(exc)}
            continue
        outs = [safe_eval(model, {nm: samples[nm][i] for nm in names}) for i in range(n)]
        blocks[label] = mc_summary(outs, threshold=threshold)
    return res(blocks, "salida del modelo", [] if corr else ["Sin evidencia de correlacion: se reportan rho 0 y +/-0,5"],
               [d.get("ledger_id") for d in drivers], seed=seed, n=n, gate=gate["value"])


PUBLIC = ["tornado", "scenarios", "pert_params", "sample_pert", "sample_triangular", "correlated_uniforms",
          "mc_summary", "mc_gate", "monte_carlo", "safe_eval"]

if __name__ == "__main__":
    cli(globals(), PUBLIC)
