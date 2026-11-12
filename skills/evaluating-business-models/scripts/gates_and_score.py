"""CEST core: archetype classification (6a.3, H0-H8), gates G0-G7 + G2b (6b.1), the deterministic
gate -> verdict mapping (6b.2), module/dimension bands and benchmark-usage rules (RT-BMK-02..08).

Arithmetic gates (G2, G2b, G7 and the numeric parts of G3/G4) are computed here from the
structured input and are NEVER voted across runs (RF-GATE-11). Judgement gates (G1 evidence
levels, G4 rows, G5 tests) arrive as structured judgements extracted to the ledger and are
mapped deterministically. Confirmed user decisions (2026-11-10) are the module constants below.

Usage:
    python gates_and_score.py evaluate --file gate_input.json      -> gates, verdict, conditions
    python gates_and_score.py classify_line '<json line>'
    python gates_and_score.py benchmark '{"benchmark_id": "PRD-021", "archetype": "P-AI-APP"}'
The input format is documented in references/gates.md (section "Formato de entrada").
"""
from __future__ import annotations

import copy
import datetime as dt
import math
import statistics

from _common import asset, cli, res

# ---------------------------------------------------------------- confirmed decisions & constants
G1_ALL_LOW_STATUS = "unknown"        # decision 1: no buyer evidence above level 2 -> unknown, not fail
G3_FAIL_SHARE = 0.50                 # decision 4
G3_ALERT_SHARE = 0.25
G3_TOP3_ALERT = 0.50
G3_DISCLOSURE = 0.10                 # disclosure anchor only (DD-001/002 are NOT gate-usable)
COND_GO_MODULE_FLOOR = 2             # decision 3 (a): median <= 2 in M7, M8 or M9
COND_GO_ASSUMPTION_SWING = 0.50      # decision 3 (b)
COND_GO_DOMINANT_SHARE = 0.80        # decision 3 (c) bounded: untested critical assumption on an 80 %-swing driver
G5_MAX_DAYS = 90
SEGMENT_SHARE = 0.20                 # H0 / H8 threshold
FTE_PER_SEAT_MIN = 8760 / 1900       # 4.61 FTE for a 24x7 seat with 1,900 productive hours
HOURS_PER_MONTH = 730.0
VERDICTS = ("GO", "CONDITIONAL_GO", "NO_GO", "INSUFFICIENT_EVIDENCE")
# v0.7.0 (user decision 2026-11-11): the skill decides whether a business that has NOT started selling is worth
# opening. In stage "pre_launch" (default) what can only be measured after launch (paying customers, real
# concentration, churn, measured availability) becomes a "conditional" gate with a test, never a blocker;
# negative evidence and real KOs still fail. Stage "operating" keeps the original rules.
STAGES = ("pre_launch", "operating")
DEFAULT_STAGE = "pre_launch"
G1_TEST_DAYS = 60
DEMAND_TEST = (f"Conseguir al menos un compromiso firmado o un pago adelantado (nivel >= 4) de un comprador "
               f"economico en <= {G1_TEST_DAYS} dias")
# v0.7.3 (user decision 2026-11-12): before opening, "there are no customers yet" is the starting point, not a
# finding. G1 estimates how likely it is to win the customers the business needs (demand.reachability): customers
# needed per year (break-even), proof that the market already pays, reachable accounts counted in a registry, and
# the sales funnel (contacts per month x conversion, as ranges). A signed commitment still passes directly.
G1_MAX_PENETRATION = 0.10   # [P] needing > 10 % of the reachable accounts every year is implausible for a new firm
G1_MIN_TEST_CONTACTS = 20
G1_MAX_TEST_CONTACTS = 200
ARCHETYPES = ("S1", "S2", "S3", "S4", "P-SAAS-SS", "P-SAAS-SL", "P-USAGE", "P-AI-APP", "P-INFRA", "P-MKT")
MODIFIERS = ("V", "AIX")
G4_KO_CODES = {"N11", "N12", "N13", "T04", "T07", "T14", "C01", "C03", "C04", "C05", "C06", "IA05", "IA08", "IA09"}
G7_KO_CODES = {"N02", "N10", "T10", "T11", "IA02"}
G3_KO_CODES = {"N04", "N06", "IA06"}
DIMENSIONS = {  # module -> dimension map (6d) used for banded dimensions, never to override gates.
    # M1 classifies and M16 synthesises: neither is scored.
    "viability": ["M2", "M3", "M4", "M10", "M15"],
    "profitability": ["M6", "M7", "M8", "M9", "M11"],
    "competitiveness": ["M5", "M12", "M13"],
    "scalability": ["M14"],
}


# ---------------------------------------------------------------- availability helpers (G7)

def downtime_min_month(availability=None):
    """Allowed downtime per 730-hour month: 0.999 -> 43.8 min."""
    return res((1 - availability) * HOURS_PER_MONTH * 60, "min/mes")


def fte_per_seat(productive_hours=1900):
    """8,760 h / productive hours per FTE: 1,900 -> 4.61, 1,700 -> 5.15."""
    return res(8760 / productive_hours, "FTE/puesto 24x7")


# ---------------------------------------------------------------- classification (6a.3, RF-ARQ-03..08)

def classify_line(line=None, **kw):
    """Classify one business line by its revenue MECHANISM, not its label.

    line: {id, mechanisms: {tm, fixed, managed, subscription, usage, resale} (shares 0-1),
           sells_expertise, acv_median, self_serve_majority, inference_cost_share,
           price_tied_to_model_usage, owns_capacity, agents, human_share_cogs,
           human_cost_decreasing, recurring_or_sla, ip_assigned_to_client, vertical, embedded_payments,
           pass_through_share}
    """
    line = dict(line or {}, **kw)
    mech = line.get("mechanisms")
    if not mech:
        return res(None, "arquetipo", ["G0 unknown: falta el % de ingresos por mecanismo (RF-ARQ-02)"],
                   missing_inputs=["mechanisms"])
    bad = {k: v for k, v in mech.items() if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float))
                                                              or not 0 <= v <= 1)}
    if bad or not isinstance(mech, dict):
        return res(None, "arquetipo", [f"Mecanismos invalidos {bad}: cada valor debe ser una fraccion en [0, 1] "
                                       "(0.8, no '80%') -> G0 unknown"], invalid_inputs=True)
    mech = {k: (v or 0.0) for k, v in mech.items()}
    if sum(mech.values()) > 1.0001:
        return res(None, "arquetipo", [f"Los mecanismos suman {sum(mech.values()):.2f} > 1: corregir el desglose"],
                   invalid_inputs=True)
    warnings, modifiers, extra = [], [], {}
    code = None
    if line.get("agents"):
        modifiers.append("AIX")
        hs = line.get("human_share_cogs")
        if hs is None:
            warnings.append("AIX sin % humano del COGS por tarea: enrutamiento T5 pendiente (unknown)")
        elif hs > 0.40 or line.get("human_cost_decreasing") is False:
            code = "S4" if (line.get("recurring_or_sla") or mech.get("managed", 0) >= 0.5) else "S2"
            extra["routing"] = f"T5: humanos {hs:.0%} del COGS por tarea -> servicio, comparar con S4 (no SaaS)"
        else:
            code = "P-AI-APP"
            extra["routing"] = "T5: humanos <= 40 % con coste decreciente -> P-AI-APP"
    if code is None:
        if line.get("ip_assigned_to_client") and mech.get("fixed", 0) + mech.get("tm", 0) >= 0.5:
            code = "S2"  # H5: custom development with IP assignment
        elif mech.get("tm", 0) >= 0.5:
            code = "S3" if line.get("sells_expertise") else "S1"
        elif mech.get("fixed", 0) >= 0.5:
            code = "S3" if line.get("sells_expertise") else "S2"
        elif mech.get("managed", 0) >= 0.5:
            code = "S4"
        elif mech.get("usage", 0) > 0.5:
            code = "P-USAGE"
        elif mech.get("resale", 0) >= 0.5:
            code = "S4" if not line.get("owns_capacity") else "P-INFRA"
        elif mech.get("subscription", 0) >= 0.5:
            code = None  # resolved below between SaaS variants and P-AI-APP
        elif line.get("sells_expertise"):
            code = "S3"
        else:
            warnings.append("Ningun mecanismo >= 50 %: tratar como hibrido (H0) y clasificar por linea")
        if line.get("owns_capacity") and mech.get("usage", 0) + mech.get("subscription", 0) + mech.get("managed", 0) >= 0.5:
            code = "P-INFRA"
        if code is None and mech.get("subscription", 0) >= 0.5:
            inf = line.get("inference_cost_share")
            if line.get("price_tied_to_model_usage") or (inf is not None and inf > 0.15):
                code = "P-AI-APP"
            elif inf is not None and inf >= 0.10:
                code, extra["boundary_case"] = "P-AI-APP", True
                warnings.append("Inferencia 10-15 % de ingresos: caso frontera; mostrar metricas SaaS y P-AI-APP (A3)")
            elif line.get("self_serve_majority") or (line.get("acv_median") is not None and line["acv_median"] < 12000):
                code = "P-SAAS-SS"
            elif line.get("acv_median") is None and line.get("self_serve_majority") is None:
                code = "P-SAAS-SL"
                warnings.append("Sin ACV ni motion: P-SAAS-SL por defecto; confirmar (G0)")
            else:
                code = "P-SAAS-SL"
    if code == "P-USAGE" and (line.get("pass_through_share") or 0) > 0.30:
        extra["subtype"] = "pass_through"
    if line.get("vertical") and code in ("P-SAAS-SS", "P-SAAS-SL"):
        modifiers.append("V")
        if line.get("embedded_payments") and not line.get("software_margin_separate"):
            warnings.append("Modificador V con pagos embebidos sin margen de software separado -> unknown (RF-ARQ-09)")
    return res(code, "arquetipo", warnings, line.get("ledger_ids", []), modifiers=modifiers, line_id=line.get("id"),
               **extra)


def hybrid_check(lines=None):
    """H0: hybrid if >= 2 mechanisms each >= 20 % of revenue or gross margin, or a small line is the thesis."""
    lines = lines or []
    big = [ln for ln in lines if (ln.get("revenue_share") or 0) >= SEGMENT_SHARE
           or (ln.get("gross_margin_share") or 0) >= SEGMENT_SHARE]
    thesis = [ln.get("id") for ln in lines if ln.get("thesis_line") and (ln.get("revenue_share") or 0) < SEGMENT_SHARE]
    is_h = len(big) >= 2 or bool(thesis)
    return res(is_h, "booleano", [], segments=[ln.get("id") for ln in big], thesis_line=thesis or None)


# ---------------------------------------------------------------- benchmark usage (RT-BMK-02..06)

_DB = None


def _db():
    global _DB
    if _DB is None:
        _DB = {b["id"]: b for b in asset("benchmarks.json")["benchmarks"]}
    return _DB


def benchmark(benchmark_id=None, archetype=None, modifiers=None, as_gate_threshold=False, evaluation_date=None):
    """Fetch a benchmark applying status, archetype, staleness and gate-usability rules."""
    db = _db()
    b = db.get(benchmark_id)
    if not b:
        return res(None, "", [f"ID inexistente en la base: {benchmark_id}"])
    w = []
    if b["status"] == "superseded" and b.get("superseded_by"):
        new = b["superseded_by"][0] if isinstance(b["superseded_by"], list) else b["superseded_by"]
        w.append(f"{benchmark_id} esta superseded: se usa {new} (A11)")
        b = db[new]
    if b["status"] == "withdrawn":
        return res(None, "", [f"{benchmark_id} retirado: no se usa como dato vigente"], [benchmark_id])
    if b["status"] == "conflict":
        w.append(f"{b['id']} en conflicto: mostrar ambas cifras con su explicacion, nunca promediar (RT-BMK-08)")
    allowed = set([archetype, "general"]) if archetype else None
    mods = set(modifiers or [])
    arch = set(b.get("archetype") or [])
    if allowed and not (arch & allowed) and not ("AIX" in mods and "AIX" in (b.get("modifiers") or [])):
        w.append(f"{b['id']} es de arquetipo {sorted(arch)}: no aplicable a {archetype} (RT-BMK-05)")
        return res(None, "", w, [b["id"]], record=b, archetype_mismatch=True)
    today = dt.date.fromisoformat(evaluation_date) if evaluation_date else dt.date.today()
    expired = False
    try:
        expired = b["status"] != "proposal" and dt.date.fromisoformat(str(b["next_review"])[:10]) <= today
    except ValueError:
        pass
    if expired:
        w.append(f"Dato pendiente de revision desde {b['next_review']}: solo contexto, no alimenta compuertas")
    if as_gate_threshold:
        if not b.get("usable_as_gate_threshold"):
            raise ValueError(f"{b['id']} no es apto como umbral de compuerta (RT-BMK-02): usar solo como contexto")
        if expired:
            raise ValueError(f"{b['id']} vencido ({b['next_review']}): refrescar antes de usarlo en una compuerta")
    if b.get("sample_size") == 1:
        w.append("Muestra de una sola empresa: no es objetivo para una pyme")
    return res(b.get("value") if b.get("value") is not None else b.get("value_text"), b.get("unit", ""), w,
               [b["id"]], record=b, expired=expired, cite=f"{b['id']} ({b.get('publication_date')}; datos "
               f"{b.get('reference_period')})")


# ---------------------------------------------------------------- individual gates

def _gate(gid, status, computed_by, reason, inputs=None, reversal=None, segment=None, **extra):
    g = {"id": gid, "status": status, "computed_by": computed_by, "reason": reason, "inputs": inputs or [],
         "reversal_condition": reversal, "segment": segment, "resolved_by_bounds": False}
    g.update(extra)
    return g


def _cond(gid, computed_by, reason, conditions, inputs=None, segment=None, **extra):
    """Pre-launch: the gate cannot be proven before opening, so it becomes a falsifiable condition."""
    conds = [c if isinstance(c, dict) else {"condition": c} for c in conditions]
    return _gate(gid, "conditional", computed_by, reason, inputs, reversal=conds[0]["condition"] if conds else None,
                 segment=segment, conditions=conds, **extra)


def gate_g0(scope):
    need_fields = ["archetype_per_line", "country_customer", "country_delivery", "currency", "horizon_m", "seeks_vc"]
    if scope is None:
        return _gate("G0", "unknown", "judgment+schema", "Sin alcance", questions=need_fields)
    if scope.get("out_of_domain"):
        return _gate("G0", "declined", "judgment", "Fuera de dominio: no es un negocio tecnologico; se declina sin veredicto")
    missing_f = [f for f in need_fields if scope.get(f) in (None, "", [])]
    if missing_f:
        return _gate("G0", "unknown", "judgment+schema", "Faltan campos de alcance: " + ", ".join(missing_f),
                     inputs=scope.get("ledger_ids", []), questions=missing_f,
                     reversal="Responder: " + ", ".join(missing_f))
    return _gate("G0", "pass", "judgment+schema", "Alcance completo", scope.get("ledger_ids", []))


def _range(x):
    """A number or {"low", "high"} -> (low, high); anything else -> None."""
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x), float(x)
    if isinstance(x, dict) and isinstance(x.get("low"), (int, float)) and isinstance(x.get("high"), (int, float)):
        lo, hi = float(x["low"]), float(x["high"])
        return (lo, hi) if lo <= hi else (hi, lo)
    return None


def _pct(x):
    v = x * 100
    return f"{v:.2g} %" if 0 < v < 1 else f"{v:.1f} %"


def demand_likelihood(r):
    """v0.7.3: how likely the business is to win the customers it needs in a year (pre-launch G1).

    r = {"clients_needed_per_year": n  |  "fixed_costs_per_year" + "contribution_per_client",
         "reachable_accounts": n (counted in a registry, M2), "market_pays": true | false (others already
         charge for this: competitors with published prices, spending data),
         "contacts_per_month": n | {"low", "high"}, "conversion": p | {"low", "high"} (contact -> customer),
         "ledger_ids": [...]}
    Returns status pass (alta) | conditional (media / sin estimar) | fail (baja) with the numbers behind it."""
    r = r or {}
    out = {"missing": []}
    needed = r.get("clients_needed_per_year")
    if not isinstance(needed, (int, float)) or isinstance(needed, bool):
        fixed, contrib = r.get("fixed_costs_per_year"), r.get("contribution_per_client")
        if isinstance(fixed, (int, float)) and isinstance(contrib, (int, float)) and contrib > 0:
            needed = max(1, math.ceil(fixed / contrib))
        else:
            needed = None
    elif needed <= 0:
        needed = None
    reach = r.get("reachable_accounts")
    reach = reach if isinstance(reach, (int, float)) and not isinstance(reach, bool) and reach > 0 else None
    contacts, conv = _range(r.get("contacts_per_month")), _range(r.get("conversion"))
    pays = r.get("market_pays") if isinstance(r.get("market_pays"), bool) else None
    for name, val in (("clientes necesarios al ano", needed), ("cuentas alcanzables", reach),
                      ("prueba de que el mercado ya paga", pays), ("contactos al mes", contacts),
                      ("conversion de contacto a cliente", conv)):
        if val is None:
            out["missing"].append(name)
    if needed is not None:
        out["clients_needed_per_year"] = needed
    if needed is not None and reach is not None:
        out["penetration"] = round(needed / reach, 6)
    if contacts and conv:
        out["expected_clients_per_year"] = {"low": round(contacts[0] * 12 * conv[0], 2),
                                            "high": round(contacts[1] * 12 * conv[1], 2)}
    if needed is not None and contacts and contacts[0] > 0:
        out["min_conversion"] = round(needed / (contacts[0] * 12), 6)
    out["market_pays"] = pays
    if out.get("penetration") is not None and out["penetration"] > G1_MAX_PENETRATION:
        out.update(status="fail", likelihood="baja",
                   reason=f"Harian falta {needed} clientes al ano, el {_pct(out['penetration'])} de las {reach:.0f} "
                          f"cuentas alcanzables (maximo plausible {_pct(G1_MAX_PENETRATION)})",
                   reversal="Ampliar el segmento alcanzable o subir el margen por cliente para necesitar menos clientes")
        return out
    exp = out.get("expected_clients_per_year")
    if needed is not None and exp and exp["high"] < needed:
        out.update(status="fail", likelihood="baja",
                   reason=f"Ni en el escenario optimista se llega: se esperan como mucho {exp['high']:g} clientes al "
                          f"ano y hacen falta {needed}",
                   reversal=f"Mas contactos al mes o un canal que convierta al menos el {_pct(out['min_conversion'])}"
                            if out.get("min_conversion") else "Mas capacidad comercial o un canal con mas conversion")
        return out
    if out["missing"]:
        out.update(status="conditional", likelihood="sin estimar",
                   reason="Probabilidad de conseguir clientes sin estimar: falta " + ", ".join(out["missing"]))
        return out
    if exp["low"] >= needed and pays:
        out.update(status="pass", likelihood="alta",
                   reason=f"Es probable conseguir los clientes necesarios: hacen falta {needed} al ano y, incluso en "
                          f"el escenario pesimista, se esperan {exp['low']:g} (optimista {exp['high']:g}); son el "
                          f"{_pct(out['penetration'])} de las cuentas alcanzables y el mercado ya paga por esto")
        return out
    conds = []
    if exp["low"] < needed:
        n_test = min(G1_MAX_TEST_CONTACTS, max(G1_MIN_TEST_CONTACTS, math.ceil(3 / out["min_conversion"])))
        conds.append({"condition": f"Viable si la conversion de contacto a cliente es >= {_pct(out['min_conversion'])} "
                                   f"(rango estimado {_pct(conv[0])}-{_pct(conv[1])}); medirla en los primeros "
                                   f"{n_test} contactos",
                      "threshold": out["min_conversion"], "direction": ">=", "field": "conversion",
                      "cheapest_test": f"Contactar {n_test} cuentas del segmento y contar cuantas compran o firman"})
    if not pays:
        conds.append({"condition": "Comprobar que el segmento ya paga por esto: un competidor con precio publicado y "
                                   "clientes, o un pago adelantado propio",
                      "field": "market_pays", "cheapest_test": DEMAND_TEST})
    out.update(status="conditional", likelihood="media", conditions=conds,
               reason=f"Conseguir los clientes depende de la conversion: hacen falta {needed} al ano y se esperan "
                      f"entre {exp['low']:g} y {exp['high']:g}" if exp["low"] < needed else
                      "Los numeros del embudo alcanzan, pero falta prueba de que el segmento ya paga por esto")
    return out


def _g1_from_likelihood(lk, ids):
    extra = {"likelihood": {k: v for k, v in lk.items() if k not in ("status", "reason", "reversal", "conditions")}}
    extra["likelihood"]["level"] = lk["likelihood"]
    if lk["status"] == "pass":
        return _gate("G1", "pass", "script+judgment", lk["reason"], ids, **extra)
    if lk["status"] == "fail":
        return _gate("G1", "fail", "script+judgment", lk["reason"], ids, reversal=lk["reversal"], **extra)
    return _cond("G1", "script+judgment", lk["reason"], lk.get("conditions") or [DEMAND_TEST], ids, **extra)


def gate_g1(demand, stage="operating"):
    """Decision 1: all accounts <= level 2 with no negative evidence -> unknown (not fail).
    Pre-launch (v0.7.0): missing or weak demand is the first condition to test, not a blocker. Only a
    signed commitment or a prepayment (level >= 4) passes; negative evidence still fails."""
    pre = stage == "pre_launch"
    if not demand:
        if pre:
            return _cond("G1", "judgment", "Probabilidad de conseguir clientes sin estimar (falta "
                         "demand.reachability): es la primera condicion a probar", [DEMAND_TEST])
        return _gate("G1", "unknown", "judgment", "Sin evidencia de demanda registrada",
                     reversal="Conseguir >= 1 cuenta en nivel >= 4 o >= 3 en nivel 3 del mismo segmento")
    ids = demand.get("ledger_ids", [])
    contacted = demand.get("contacted_buyers", 0) or 0
    rejected = demand.get("rejections", 0) or 0
    pilots, converted = demand.get("paid_pilots", 0) or 0, demand.get("paid_pilots_converted", 0) or 0
    if (contacted >= 5 and rejected >= math.ceil(2 * contacted / 3)) or (pilots >= 2 and converted == 0):
        return _gate("G1", "fail", "judgment", f"Evidencia negativa: {rejected}/{contacted} rechazos; "
                     f"pilotos pagados convertidos {converted}/{pilots}", ids,
                     reversal="Nuevo segmento o propuesta con >= 1 cuenta en nivel >= 4")
    accounts = [a for a in demand.get("accounts", []) if a.get("economic_buyer")]
    if any(a.get("level", 0) >= 4 for a in accounts):
        return _gate("G1", "pass", "judgment", "Cuenta en nivel >= 4 con comprador economico", ids)
    if pre and demand.get("reachability"):
        r = demand["reachability"]
        return _g1_from_likelihood(demand_likelihood(r), sorted(set(ids) | set(r.get("ledger_ids") or [])))
    by_seg = {}
    for a in accounts:
        if a.get("level", 0) == 3:
            by_seg[a.get("segment")] = by_seg.get(a.get("segment"), 0) + 1
    if any(v >= 3 for v in by_seg.values()):
        if pre:
            return _cond("G1", "judgment", ">= 3 cuentas del mismo segmento en nivel 3: interes confirmado, sin "
                         "compromiso todavia", [f"Convertir al menos una en compromiso firmado o pago adelantado "
                                                f"en <= {G1_TEST_DAYS} dias"], ids)
        return _gate("G1", "pass", "judgment", ">= 3 cuentas del mismo segmento en nivel 3", ids)
    if pre:
        return _cond("G1", "judgment", "Ninguna cuenta con compromiso firmado o pago adelantado todavia",
                     [DEMAND_TEST], ids)
    return _gate("G1", G1_ALL_LOW_STATUS, "judgment",
                 "Ninguna cuenta con comprador economico en nivel >= 4 ni 3 en nivel 3 (decision 1: unknown)", ids,
                 reversal="LOI con presupuesto, piloto pagado o contrato con un comprador economico (nivel >= 4)")


def gate_g2(line):
    """Contribution margin at a realistic rate, on the R4-recalculated margin. Per segment."""
    e = line.get("economics") or {}
    ids, seg = e.get("ledger_ids", []), line.get("id")
    kind = e.get("kind")
    if kind == "services":
        rate, real = e.get("rate"), e.get("realisation")
        if rate is None and e.get("price_per_project") is not None and e.get("hours_per_project"):
            # v0.7.0: fixed-price projects are estimated as price / hours; the realisation is already inside.
            rate = e["price_per_project"] / e["hours_per_project"]
            real = 1.0 if real is None else real
        cost_bh = e.get("loaded_cost_per_billable_hour")
        if cost_bh is None and e.get("loaded_cost_per_paid_hour") is not None and e.get("utilisation"):
            cost_bh = e["loaded_cost_per_paid_hour"] / e["utilisation"]
        if None in (rate, real, cost_bh):
            return _gate("G2", "unknown", "script", "Falta tarifa, realizacion o coste cargado por hora facturable", ids,
                         segment=seg)
        eff = rate * real
        if eff < cost_bh:
            return _gate("G2", "fail", "script", f"Tarifa efectiva {eff:.2f} < coste por hora facturable {cost_bh:.2f}",
                         ids, reversal=f"Tarifa efectiva >= {cost_bh:.2f} o coste/hora facturable <= {eff:.2f} "
                         "(subir utilizacion o tarifa)", segment=seg, effective_rate=eff, cost_per_billable_hour=cost_bh)
        return _gate("G2", "pass", "script", f"Tarifa efectiva {eff:.2f} >= coste {cost_bh:.2f}", ids, segment=seg,
                     effective_rate=eff, cost_per_billable_hour=cost_bh)
    if kind == "product":
        arpa, margin = e.get("arpa_m"), e.get("margin_recalculated", e.get("margin"))
        var = e.get("variable_cost_m", 0.0)
        if arpa is None or margin is None:
            return _gate("G2", "unknown", "script", "Falta ARPA o margen (recalculado por R4)", ids, segment=seg)
        cm = arpa * margin - var
        if cm < 0:
            return _gate("G2", "fail", "script", f"Margen de contribucion por cliente {cm:.2f} < 0", ids,
                         reversal="Precio o coste variable que deje el margen de contribucion >= 0", segment=seg)
        return _gate("G2", "pass", "script", f"Margen de contribucion por cliente {cm:.2f}", ids, segment=seg)
    if kind == "aix":
        price = e.get("price_per_task")
        if e.get("pass1") is None or e.get("human_cost_per_task") is None and e.get("c_task_p90") is None:
            return _gate("G2", "unknown", "script", "AIX sin pass^1 o sin coste humano medido: 'no evaluable'",
                         ids, segment=seg, reversal="Medir pass^1/pass^k y minutos humanos por tarea")
        c90 = e.get("c_task_p90")
        if c90 is None:
            c90 = (e.get("inference_p90", 0) + e.get("other_cost_per_task", 0) + e.get("human_cost_per_task", 0))
        if price is None:
            return _gate("G2", "unknown", "script", "Falta precio por tarea u outcome", ids, segment=seg)
        if price < c90:
            return _gate("G2", "fail", "script", f"T1: precio {price:.2f} < C_task p90 {c90:.2f}", ids, segment=seg,
                         reversal=f"Precio >= {c90:.2f} o reducir escalado/supervision hasta C_task p90 <= {price:.2f}",
                         c_task_p90=c90)
        return _gate("G2", "pass", "script", f"T1: precio {price:.2f} >= C_task p90 {c90:.2f}", ids, segment=seg,
                     c_task_p90=c90)
    return _gate("G2", "unknown", "script", "Economia de la linea no declarada (kind services|product|aix)", ids,
                 segment=seg)


def _payback_vs_life(cac, arpa, margin, churn):
    m = arpa * margin
    if m <= 0:
        return "fail", "Margen mensual <= 0"
    if churn <= 0:
        return "pass", "Churn 0"
    if cac * churn / m >= 1:
        return "fail", f"CAC*c/m = {cac * churn / m:.2f} >= 1: payback 'nunca'"
    payback, life = cac / m, 1 / churn
    if payback > life:
        return "fail", f"Payback {payback:.1f} meses > vida esperada {life:.1f}"
    return "pass", f"Payback {payback:.1f} meses <= vida esperada {life:.1f}"


def gate_g2b(line, stage="operating"):
    """CAC recoverable: only recurring lines with CAC. Churn interval bounds when not estimable.
    Fail-closed: absence of CAC in recurring lines yields 'unknown', never silent 'not_applicable'.
    Pre-launch (v0.7.0): CAC and churn are estimated from the plan with a range (p0_unknowns for the CAC,
    churn_interval from sector references); when the result flips inside the range it becomes a condition
    with the break-even churn (payback = expected life  <=>  churn = monthly margin / CAC).
    """
    pre = stage == "pre_launch"
    e = line.get("economics") or {}
    ids, seg = e.get("ledger_ids", []), line.get("id")
    if not e.get("recurring"):
        return _gate("G2b", "not_applicable", "script", "Linea no recurrente", ids, segment=seg)
    if e.get("cac_not_applicable") is True:
        return _gate("G2b", "not_applicable", "script", "CAC no aplicable probado con evidencia (sin gasto de adquisicion)", ids, segment=seg)
    if e.get("cac") is None:
        return _gate("G2b", "unknown", "script", "Linea recurrente sin CAC declarado ni exencion probada: CAC desconocido",
                     ids, segment=seg, reversal="Estimar el CAC con rango desde el plan comercial (p0_unknowns)" if pre
                     else "Aportar CAC total cargado o demostrar exencion documentada")
    if e["cac"] <= 0:
        # Final audit: CAC = 0 is the exemption by another name and must meet the same proof (tier-1 claim).
        return _gate("G2b", "unknown", "script", "CAC 0 o negativo declarado sin exencion probada: tratar como desconocido",
                     ids, segment=seg, reversal="Aportar CAC total cargado (incluido el tiempo comercial del fundador) "
                     "o la exencion PRED_CAC_NOT_APPLICABLE_PROVEN con documento tier 1")
    arpa, margin = e.get("arpa_m"), e.get("margin_recalculated", e.get("margin"))
    if arpa is None or margin is None:
        return _gate("G2b", "unknown", "script", "Falta ARPA o margen", ids, segment=seg)
    churn = e.get("churn_m")
    if churn is None and e.get("churn_interval"):
        lo, hi = e["churn_interval"]
        s_lo, r_lo = _payback_vs_life(e["cac"], arpa, margin, lo)
        s_hi, r_hi = _payback_vs_life(e["cac"], arpa, margin, hi)
        if s_lo == s_hi:
            return _gate("G2b", s_lo, "script", f"Churn no estimable; ambas cotas: {r_hi}", ids, segment=seg,
                         resolved_by_bounds=True)
        if pre:
            max_churn = arpa * margin / e["cac"]
            return _cond("G2b", "script", f"El resultado cambia dentro del rango de churn ({r_lo} / {r_hi})",
                         [{"condition": f"Viable si el churn mensual es <= {max_churn:.2%} (CAC {e['cac']:.0f} "
                                        f"recuperado antes de la vida media del cliente)",
                           "threshold": max_churn, "direction": "<=", "field": "churn_m",
                           "cheapest_test": "Medir las bajas de los primeros clientes durante 90 dias"}],
                         ids, segment=seg)
        return _gate("G2b", "unknown", "script", f"Churn no estimable y el resultado cambia entre cotas ({r_lo} / {r_hi})",
                     ids, segment=seg, reversal="Mas historia de churn (>= 30 cliente-periodos y >= 3 bajas)")
    if churn is None:
        return _gate("G2b", "unknown", "script", "Falta churn", ids, segment=seg,
                     reversal="Estimar churn_interval con referencias del sector (antes de abrir no hay historia)"
                     if pre else None)
    floor_note = ""
    if churn <= 0:
        # Final audit: zero churn used to pass automatically. RT-FIN-08 floors churn at 1 %/month.
        churn, floor_note = 0.01, " (churn declarado 0: se aplica el suelo de 1 %/mes, RT-FIN-08)"
    status, reason = _payback_vs_life(e["cac"], arpa, margin, churn)
    reason += floor_note
    rev = None
    if status == "fail":
        rev = f"CAC <= {arpa * margin / churn:.0f} (vida x margen mensual) o menos churn"
    return _gate("G2b", status, "script", reason, ids, segment=seg, reversal=rev)


G3_PLAN_MAX_MONTHS = 12   # a diversification plan only mitigates if it lands within 12 months [P]


def verifiable_plan(plan, evaluation_date=None):
    """REV-004: a diversification plan mitigates G3 only if it is VERIFIABLE: a dict with
    target_top1_share < 0.50, by_date within 12 months of the evaluation, ledger_ids and an
    evidence status other than a bare assumption (e.g. signed pipeline, LOIs, contracts).
    A boolean or free-text plan is a declaration, not evidence."""
    if not isinstance(plan, dict):
        return False, "plan declarado sin estructura verificable (objetivo, fecha y evidencia)"
    tgt, by, ids = plan.get("target_top1_share"), plan.get("by_date"), plan.get("ledger_ids")
    if not isinstance(tgt, (int, float)) or tgt >= G3_FAIL_SHARE:
        return False, "el plan no fija un objetivo de cliente principal < 50 %"
    try:
        start = dt.date.fromisoformat(evaluation_date) if evaluation_date else dt.date.today()
        months = (dt.date.fromisoformat(by) - start).days / 30.44
    except (TypeError, ValueError):
        return False, "el plan no tiene fecha valida (by_date)"
    if not 0 < months <= G3_PLAN_MAX_MONTHS:
        return False, f"el plan vence en {months:.0f} meses (maximo {G3_PLAN_MAX_MONTHS})"
    if not ids or plan.get("evidence_status") not in ("fact", "estimate"):
        return False, "el plan no tiene evidencia en el ledger (estado fact o estimate)"
    return True, f"plan verificable: cliente principal < {tgt:.0%} antes de {by}"


PLAN_DIVERSIFY = ("Plan de diversificacion con fecha: cliente principal < 50 % de los ingresos antes de 12 meses "
                  "desde el primer contrato, con la lista de cuentas objetivo")


def gate_g3(conc, segment=None, evaluation_date=None, stage="operating"):
    """Decision 4 (confirmed 2026-11-10): fail with one client >= 50 % unless the contract is multi-year
    without termination for convenience, or a VERIFIABLE diversification plan exists (REV-004).
    Pre-launch (v0.7.0): depending on 1-2 clients at the start is normal, so concentration, an untested supplier
    alternative and an untested model fallback become conditions with a date; due-diligence KOs still fail."""
    pre = stage == "pre_launch"
    t1 = (conc or {}).get("top1_share")
    if t1 is None and not pre:
        return _gate("G3", "unknown", "script+judgment", "Faltan los ingresos por cliente", segment=segment,
                     reversal="Aportar ingresos por cliente de los ultimos 12-24 meses")
    conc = conc or {}
    ids, alerts, fails, kos = conc.get("ledger_ids", []), [], [], []
    t3 = conc.get("top3_share")
    if t1 is not None and (not isinstance(t1, (int, float)) or isinstance(t1, bool) or not 0 <= t1 <= 1):
        return _gate("G3", "unknown", "script+judgment", f"top1_share invalido ({t1!r}): debe ser fraccion en [0, 1]",
                     ids, segment=segment)
    c = conc.get("top1_contract") or {}
    protected = bool(c.get("multi_year")) and not c.get("termination_for_convenience", True)
    plan_ok, plan_why = verifiable_plan(c.get("diversification_plan"), evaluation_date)
    if t1 is None:   # pre-launch only: no revenue yet
        if not plan_ok:
            fails.append("Sin ingresos todavia: con 1-2 clientes al inicio la concentracion sera alta")
        else:
            alerts.append(f"Concentracion inicial mitigada por {plan_why}")
    elif t1 >= G3_FAIL_SHARE and not protected and not plan_ok:
        detail = f"; {plan_why}" if c.get("diversification_plan") else ""
        fails.append(f"Cliente principal {t1:.0%} >= 50 % sin contrato plurianual protegido ni plan de "
                     f"diversificacion verificable{detail}")
    elif t1 >= G3_FAIL_SHARE and plan_ok and not protected:
        alerts.append(f"Concentracion {t1:.0%} mitigada solo por {plan_why}: convertir en condicion con fecha")
    for s in conc.get("critical_suppliers", []):
        if not s.get("alternative_tested"):
            fails.append(f"Proveedor unico critico sin alternativa probada: {s.get('name')}")
    mp = conc.get("model_provider") or {}
    if mp and not mp.get("fallback_tested") and mp.get("cm_at_x2") is not None and mp["cm_at_x2"] < 0:
        fails.append("Un solo proveedor de modelo sin fallback probado y margen < 0 con precio x2,0 (T3)")
    for code in conc.get("ko_codes", []):
        if code in G3_KO_CODES:
            kos.append(f"KO de due diligence {code}")
    if pre and not kos and fails:
        conds = []
        for f in fails:
            if f.startswith("Proveedor"):
                conds.append(f"Probar la alternativa antes del primer contrato: {f.split(': ', 1)[-1]}")
            elif f.startswith("Un solo proveedor de modelo"):
                conds.append("Probar un segundo proveedor de modelo con el margen >= 0 a precio x2,0")
            elif PLAN_DIVERSIFY not in conds:
                conds.append(PLAN_DIVERSIFY)
        return _cond("G3", "script+judgment", "; ".join(fails), conds, ids, segment=segment, alerts=alerts)
    fails += kos
    t1 = 0.0 if t1 is None else t1
    if t1 >= G3_ALERT_SHARE:
        alerts.append(f"Cliente principal {t1:.0%} >= 25 %")
    elif t1 >= G3_DISCLOSURE:
        alerts.append(f"Cliente >= 10 % (paridad con divulgacion ASC 280/IFRS 8; DD-001/002 solo contexto)")
    if t3 is not None and t3 >= G3_TOP3_ALERT:
        alerts.append(f"Top-3 {t3:.0%} >= 50 %")
    if conc.get("relationship_years") is not None and conc["relationship_years"] < 2 and t1 >= G3_ALERT_SHARE:
        alerts.append("Concentracion alta con relacion < 2 anios")
    if (conc.get("credits_share") or 0) >= 0.20:
        alerts.append("Creditos o subsidios >= 20 % de los costes (R5)")
    if fails:
        return _gate("G3", "fail", "script+judgment", "; ".join(fails), ids, segment=segment, alerts=alerts,
                     reversal="Contrato plurianual sin terminacion por conveniencia, plan de diversificacion "
                     "o fallback probado, segun el motivo")
    return _gate("G3", "pass", "script+judgment", "Sin dependencia fatal", ids, segment=segment, alerts=alerts)


def written_plan(plan):
    """v0.7.0: a compliance plan counts only if it is written down with an owner and a date (a dict with
    'owner' and 'by_date'). An intention ("hay que revisar las obligaciones") or a bare True is not a plan;
    this removes the run-to-run variance seen in the 2026-11-11 field test."""
    return isinstance(plan, dict) and bool(plan.get("owner")) and bool(plan.get("by_date"))


def gate_g4(comp, regulated=False, stage="operating"):
    """Reformulated G4: certifications are not universal; only legal duties or declared-segment demands.
    Pre-launch (v0.7.0): a duty without a written plan (owner + date) is a condition to meet before the first
    contract, not a fail; due-diligence KOs (activity not allowed, IP not owned...) still fail."""
    pre = stage == "pre_launch"
    if not comp:
        return _gate("G4", "unknown", "judgment+table", "Sin analisis de compliance",
                     reversal="Declarar residencia de los titulares de datos y exigencias del segmento objetivo")
    ids, fails, conds = comp.get("ledger_ids", []), [], []
    for r in comp.get("rows", []):
        if not r.get("applies") or r.get("compliant"):
            continue
        if r.get("type") == "Legal":
            if pre and not written_plan(r.get("plan")):
                conds.append(f"Plan escrito, con responsable y fecha, antes del primer contrato: {r.get('row')}")
            elif not pre and not r.get("plan"):
                fails.append(f"Obligacion legal sin cumplimiento ni plan: {r.get('row')}")
        if r.get("type") == "Contractual" and r.get("demanded_by_segment") and not (r.get("plan") and r.get("budget")):
            if pre:
                conds.append(f"Plan y presupuesto antes de vender a ese segmento: {r.get('row')}")
            else:
                fails.append(f"El segmento declarado exige {r.get('row')} sin plan ni presupuesto")
    for code in comp.get("ko_codes", []):
        if code in G4_KO_CODES:
            fails.append(f"KO de due diligence {code}")
    if fails:
        return _gate("G4", "fail", "judgment+table", "; ".join(fails), ids,
                     reversal="Plan y presupuesto de cumplimiento para cada fila citada")
    regulated_open = comp.get("sector_compliance_proven") is False or (
        (regulated or comp.get("regulated_sector")) and comp.get("sector_compliance_proven") is not True)
    if comp.get("data_residence_known") is False or comp.get("segment_requirements_known") is False:
        return _gate("G4", "unknown", "judgment+table", "No se sabe donde residen los titulares o que exige el segmento",
                     ids, reversal="Declarar residencia de datos y requisitos del segmento")
    if pre and regulated_open:
        conds.append("Sector regulado: obtener el documento de nivel 1 que pruebe el cumplimiento sectorial "
                     "(licencia, registro o concepto) antes de operar (P0-MOD-V1)")
    if conds:
        return _cond("G4", "judgment+table", "Obligaciones por cumplir antes de abrir", conds, ids)
    if regulated_open:
        return _gate("G4", "unknown", "judgment+table",
                     "Sector regulado (modificador V) sin cumplimiento sectorial probado", ids,
                     reversal="Documento de nivel 1 que pruebe el cumplimiento regulatorio sectorial (P0-MOD-V1)")
    return _gate("G4", "pass", "judgment+table", "Sin obligaciones incumplidas (las filas 'Voluntario' nunca son KO)", ids)


def gate_g5(assumptions, explicit_none=False):
    if assumptions is None and not explicit_none:
        return _gate("G5", "unknown", "judgment", "Supuestos criticos no listados (error de extraccion)",
                     reversal="Listar los supuestos criticos con su test")
    bad = [a.get("id") for a in (assumptions or []) if not a.get("test") or (a.get("days") or 10 ** 6) > G5_MAX_DAYS]
    ids = [a.get("ledger_id") for a in (assumptions or []) if a.get("ledger_id")]
    if bad:
        return _gate("G5", "fail", "judgment", "Supuestos criticos sin test resoluble en <= 90 dias: " + ", ".join(map(str, bad)),
                     ids, reversal="Disenar un test de <= 90 dias para cada supuesto citado")
    return _gate("G5", "pass", "judgment", "Cada supuesto critico tiene test de <= 90 dias", ids,
                 tests=[{"assumption": a.get("id"), "test": a.get("test"), "days": a.get("days")} for a in (assumptions or [])])


def gate_g7(d, stage="operating"):
    """Delivery capacity. v0.7.0: due-diligence KOs (e.g. N02 key person) are checked BEFORE the early pass for
    'no SLA and no 24x7' (field-test bug: N02 could never fail). Pre-launch: availability cannot be measured and
    a 24x7 rota cannot exist yet, so those gaps become conditions; arithmetic fails still fail."""
    pre = stage == "pre_launch"
    if d is None:
        return _gate("G7", "unknown", "script+judgment", "Sin datos de operacion ni SLA (omision)",
                     reversal="Declarar si existen compromisos de SLA o necesidad de operacion 24x7")
    kos = [f"KO de due diligence {code}" for code in d.get("ko_codes", []) if code in G7_KO_CODES]
    if not d.get("sla_promised") and not d.get("needs_24x7"):
        if kos:
            return _gate("G7", "fail", "script+judgment", "; ".join(kos), d.get("ledger_ids", []),
                         reversal="Resolver el KO citado (p. ej. N02: documentar y repartir el conocimiento clave)")
        return _gate("G7", "pass", "script+judgment", "Sin SLA ni operacion 24x7 prometidos")
    ids, fails = d.get("ledger_ids", []), []
    sla, measured = d.get("sla_promised"), d.get("availability_measured")
    if d.get("needs_24x7") and d.get("oncall_fte") is not None and d["oncall_fte"] < FTE_PER_SEAT_MIN - 1e-9:
        fails.append(f"24x7 con {d['oncall_fte']} FTE < {FTE_PER_SEAT_MIN:.2f} por puesto")
    staffed = bool(d.get("oncall_fte")) or d.get("shift_schedule_proven") is True
    if sla and d.get("sla_architecture_supported") is False:
        fails.append("La arquitectura documentada no respalda el SLA prometido")
    if sla and sla >= 0.9999 and d.get("needs_24x7") is not False and not staffed:
        fails.append("SLA 99,99 % (4,4 min/mes) sin guardia 24x7")
    if sla and measured is not None and sla > measured:
        fails.append(f"SLA {sla:.4%} mas exigente que la disponibilidad medida {measured:.4%}")
    if d.get("penalties_capped") is False:
        fails.append("Penalizaciones sin tope")
    fails += kos
    if fails:
        return _gate("G7", "fail", "script+judgment", "; ".join(fails), ids,
                     reversal="SLA alcanzable con la operacion medida, dotacion 24x7 y penalizaciones con tope")
    if pre:
        conds = []
        if d.get("needs_24x7") and not d.get("oncall_fte") and d.get("shift_schedule_proven") is not True:
            conds.append(f"Cuadrante de guardia 24x7 con >= {FTE_PER_SEAT_MIN:.2f} FTE por puesto antes de "
                         "prometer operacion 24x7")
        if sla and measured is None:
            conds.append(f"No firmar el SLA de {sla:.2%} hasta medir la disponibilidad en un piloto de >= 30 dias")
        if conds:
            return _cond("G7", "script+judgment", "Capacidad de entrega por demostrar antes de abrir", conds, ids)
    if d.get("needs_24x7") and not d.get("oncall_fte") and d.get("shift_schedule_proven") is not True:
        # C2: omission (None) is not proof; only a staffed rota or a documented shift schedule passes.
        return _gate("G7", "unknown", "script+judgment", "Operacion 24x7 sin dotacion ni cuadrante de turnos probado",
                     ids, reversal=f"Aportar dotacion de guardia (>= {FTE_PER_SEAT_MIN:.2f} FTE por puesto) o un "
                                   "cuadrante de turnos con evidencia de nivel 1-2")
    if sla and (measured is None or (d.get("needs_24x7") and d.get("oncall_fte") is None and not staffed)):
        return _gate("G7", "unknown", "script+judgment", "Falta la disponibilidad historica o la dotacion", ids,
                     reversal="Aportar disponibilidad medida y dotacion de guardia")
    return _gate("G7", "pass", "script+judgment", "SLA soportado por la operacion", ids)


# ---------------------------------------------------------------- tier-4 rule (RT-LED-03)

def _tier4_only(ids, ledger_index):
    entries = [ledger_index[i] for i in ids if i in ledger_index]
    if not entries:
        return False
    return all((e.get("source") or {}).get("tier") == 4 or
               ((e.get("source") or {}).get("type") == "web" and not e.get("retrieved_by_tool")) for e in entries)


# ---------------------------------------------------------------- compute all gates

def stage_of(inp) -> str:
    """'pre_launch' (default since v0.7.0) or 'operating'. An invalid value is treated as pre_launch."""
    st = (inp or {}).get("stage") or DEFAULT_STAGE
    return st if st in STAGES else DEFAULT_STAGE


def _documented(ids, ledger_index):
    """A demand level >= 4 (signed commitment, payment) needs a document: a tier-1 ledger entry, or a tier-2
    entry that is not self-declared by the proponent (evidence-rules: the proponent's figures are self_declared
    unless a contract, invoice or statement is attached)."""
    for i in ids or []:
        e = ledger_index.get(i)
        if not e:
            continue
        tier = (e.get("source") or {}).get("tier")
        if tier == 1 or (tier == 2 and not e.get("self_declared")):
            return True
    return False


def cap_undocumented_demand(demand, ledger_index):
    """v0.7.0 (field test 2026-11-11: the same self-declared past project read as level 5 in two runs and as
    unknown in the third): an account at level >= 4 whose evidence is only the proponent's word is read as
    level 3. Applies only when the gate input carries the ledger."""
    if not demand or not ledger_index:
        return demand, []
    demand, notes = copy.deepcopy(demand), []
    for a in demand.get("accounts", []):
        if (a.get("level") or 0) >= 4:
            ids = a.get("ledger_ids") or ([a["ledger_id"]] if a.get("ledger_id") else demand.get("ledger_ids", []))
            if not _documented(ids, ledger_index):
                notes.append(f"Cuenta {a.get('id') or '?'}: nivel {a['level']} declarado sin documento (contrato, "
                             "factura o extracto): se lee como nivel 3")
                a["level_declared"], a["level"] = a["level"], 3
    return demand, notes


def compute_gates(inp: dict) -> list[dict]:
    stage = stage_of(inp)
    lines = inp.get("lines", [])
    ledger_index = {e["id"]: e for e in inp.get("ledger", []) if "id" in e}
    demand, demand_notes = cap_undocumented_demand(inp.get("demand"), ledger_index)
    g1 = gate_g1(demand, stage=stage)
    if demand_notes:
        g1["alerts"] = g1.get("alerts", []) + demand_notes
    gates = [gate_g0(inp.get("scope")), g1]
    segs = [ln for ln in lines if (ln.get("revenue_share") or 0) >= SEGMENT_SHARE] or lines[:1]
    per = [gate_g2(ln) for ln in segs] if segs else [gate_g2({})]
    gates.append(_combine(per, "G2"))
    per = [gate_g2b(ln, stage=stage) for ln in segs] if segs else [gate_g2b({}, stage=stage)]
    gates.append(_combine(per, "G2b"))
    conc = inp.get("concentration")
    gates.append(gate_g3(conc, evaluation_date=inp.get("evaluation_date"), stage=stage))
    regulated = any("V" in (classify_line(ln).get("modifiers") or []) or "V" in (ln.get("modifiers") or [])
                    for ln in lines)
    gates.append(gate_g4(inp.get("compliance"), regulated=regulated, stage=stage))
    gates.append(gate_g5(inp.get("critical_assumptions"), inp.get("no_critical_assumptions", False)))
    gates.append(gate_g7(inp.get("delivery"), stage=stage))
    for g in gates:
        if g["status"] in ("pass", "fail") and g["inputs"] and _tier4_only(g["inputs"], ledger_index):
            g["status"] = "unknown"
            g["reason"] += " | Solo fuentes tier 4 (conocimiento del modelo): no sostiene compuertas (RT-LED-03)"
    return gates


def _combine(per, gid):
    """H8: per-segment evaluation; any failing segment with >= 20 % of revenue fails the gate."""
    per = [p for p in per if p["status"] != "not_applicable"] or per
    for status in ("fail", "unknown", "conditional"):
        hit = [p for p in per if p["status"] == status]
        if hit:
            g = dict(hit[0])
            g["id"] = gid
            g["segments"] = per
            return g
    g = dict(per[0])
    g["id"] = gid
    g["segments"] = per
    return g


def _verdict_from_gates(gates, unknown_invertible_ids):
    statuses = {g["id"]: g["status"] for g in gates}
    if statuses.get("G0") == "declined":
        return "DECLINED"
    if any(s == "fail" for s in statuses.values()):
        return "NO_GO"
    if any(g["status"] == "unknown" and (g["id"] in unknown_invertible_ids or not g.get("resolved_by_bounds"))
           for g in gates):
        return "INSUFFICIENT_EVIDENCE"
    if any(g["status"] == "conditional" for g in gates):
        return "CONDITIONAL"
    return "PASS_ALL"


def _set_path(d, path, value):
    keys = path.split(".")
    cur = d
    for k in keys[:-1]:
        if k.isdigit():
            cur = cur[int(k)]
        else:
            cur = cur.setdefault(k, {})
    last = keys[-1]
    if last.isdigit():
        cur[int(last)] = value
    else:
        cur[last] = value


def _status_at(inp, path, value, gid):
    alt = copy.deepcopy(inp)
    _set_path(alt, path, value)
    alt.pop("p0_unknowns", None)
    return next((g for g in compute_gates(alt) if g["id"] == gid), {})


def break_even(inp, p, gid, iters=40):
    """Bisection on the P0 range for the value where the gate stops passing (the break-even threshold).
    Returns (threshold, direction): direction '<=' if the gate passes at the low end, '>=' otherwise."""
    lo, hi = float(p["low"]), float(p["high"])
    pass_low = _status_at(inp, p["path"], lo, gid).get("status") == "pass"
    good, bad = (lo, hi) if pass_low else (hi, lo)
    for _ in range(iters):
        mid = (good + bad) / 2
        if _status_at(inp, p["path"], mid, gid).get("status") == "pass":
            good = mid
        else:
            bad = mid
    return good, ("<=" if pass_low else ">=")


def _g6(inp, gates):
    """Recompute gates with each P0 unknown at both plausible extremes (A5). Never fails: abstains.
    Pre-launch (v0.7.0): when the gate passes at one end of a documented range and not at the other, the
    break-even value becomes a falsifiable condition ("viable si horas por proyecto <= 117") instead of
    INSUFFICIENT_EVIDENCE. A P0 without a range is still invertible: those are the basic data to ask for."""
    pre = stage_of(inp) == "pre_launch"
    p0s = inp.get("p0_unknowns", [])
    invertible, resolved, details, thresholds = set(), [], [], {}
    for p in p0s:
        gid = p.get("gate")
        if p.get("low") is None or p.get("high") is None:
            invertible.add(gid)
            details.append({"p0": p.get("field"), "gate": gid, "invertible": True, "why": "sin rango documentado",
                            "cheapest_test": p.get("cheapest_test")})
            continue
        alts = [_status_at(inp, p["path"], bound, gid) for bound in (p["low"], p["high"])]
        outs = [a.get("status") for a in alts]
        numeric = all(isinstance(b, (int, float)) and not isinstance(b, bool) for b in (p["low"], p["high"]))
        if outs[0] == outs[1] and outs[0] in ("pass", "fail"):
            resolved.append((gid, outs[0], None))
            details.append({"p0": p.get("field"), "gate": gid, "invertible": False, "status_both_bounds": outs[0]})
        elif pre and outs[0] == outs[1] == "conditional":
            resolved.append((gid, "conditional", alts[0].get("conditions")))
            details.append({"p0": p.get("field"), "gate": gid, "invertible": False, "status_both_bounds": outs[0]})
        elif pre and numeric and "pass" in outs and set(outs) <= {"pass", "fail", "conditional"}:
            thr, direction = break_even(inp, p, gid)
            cond = {"condition": f"Viable si {p.get('field') or p['path']} {direction} {thr:.4g} (rango estimado "
                                 f"{p['low']}-{p['high']})", "threshold": round(thr, 6), "direction": direction,
                    "field": p.get("field"), "path": p["path"], "cheapest_test": p.get("cheapest_test")}
            thresholds.setdefault(gid, []).append(cond)
            details.append({"p0": p.get("field"), "gate": gid, "invertible": False, "statuses": outs,
                            "break_even": round(thr, 6), "direction": direction})
        else:
            invertible.add(gid)
            details.append({"p0": p.get("field"), "gate": gid, "invertible": True, "statuses": outs,
                            "cheapest_test": p.get("cheapest_test")})
    for gid, st, conds in resolved:
        for g in gates:
            if g["id"] == gid and g["status"] == "unknown" and gid not in invertible and gid not in thresholds:
                g["status"], g["resolved_by_bounds"] = st, True
                g["reason"] += f" | Resuelta por cotas: {st} en ambos extremos"
                if conds:
                    g["conditions"] = conds
    for gid, conds in thresholds.items():
        for g in gates:
            if g["id"] != gid or gid in invertible:
                continue
            if g["status"] == "unknown":
                g["status"], g["resolved_by_bounds"] = "conditional", True
                g["reason"] += " | El resultado depende de un dato estimado: se convierte en condicion con umbral"
                g["conditions"] = conds
                g["reversal_condition"] = conds[0]["condition"]
            elif g["status"] == "conditional":
                g["conditions"] = g.get("conditions", []) + conds
    if inp.get("high_impact_domain_without_eval_set"):
        invertible.add("G6")
        details.append({"p0": "eval set propio", "gate": "G6", "invertible": True, "why": "IA03"})
    status = "unknown" if invertible & {g["id"] for g in gates if g["status"] == "unknown"} or "G6" in invertible else "pass"
    return _gate("G6", status, "script", "P0 desconocido capaz de invertir el veredicto" if status == "unknown"
                 else "Ningun P0 desconocido invierte el veredicto", details=details), invertible


# ---------------------------------------------------------------- modules & conditional rules

def _median(vals):
    vals = [v for v in vals if v is not None]
    return statistics.median(vals) if vals else None


def conditional_rules(modules, tornado=None, critical_assumptions=None, stage="operating"):
    """Decision 3: CONDITIONAL_GO if (a) median <= 2 in M7/M8/M9, (b) > 50 % swing from assumptions,
    (c) an untested critical assumption affects a driver within the 80 % tornado swing (bounded).
    Pre-launch (v0.7.0): rule (b) does not apply. Before opening almost every driver is an assumption, so (b)
    would forbid GO for every new business; the pessimistic end of each estimated range (G6 break-even) plays
    its role instead."""
    conds = []
    mods = {m["id"]: m for m in modules or []}
    for mid in ("M7", "M8", "M9"):
        med = (mods.get(mid) or {}).get("median", (mods.get(mid) or {}).get("score"))
        if med is not None and med <= COND_GO_MODULE_FLOOR:
            conds.append({"rule": "a", "module": mid, "detail": f"{mid} mediana {med} <= 2"})
    t = tornado or {}
    if stage != "pre_launch" and (t.get("assumption_swing_share") or 0) > COND_GO_ASSUMPTION_SWING:
        conds.append({"rule": "b", "detail": f"{t['assumption_swing_share']:.0%} del swing procede de supuestos"})
    dominant = set(t.get("dominant_drivers") or [])
    for a in critical_assumptions or []:
        if not a.get("tested") and a.get("driver") in dominant:
            what = a.get("hypothesis") or a.get("test") or a.get("id")
            conds.append({"rule": "c", "assumption": a.get("id"), "driver": a.get("driver"),
                          "detail": f"Probar el supuesto {a.get('id')} ({what}) sobre el driver {a.get('driver')}, "
                                    "que esta entre los que suman el 80 % de la sensibilidad",
                          "hypothesis": a.get("hypothesis"), "threshold": a.get("threshold"), "by": a.get("by_date")})
    return conds


def dimension_bands(modules):
    """Banded dimensions (no decimals): mean of module medians; debil < 2.5, intermedia 2.5-3.5,
    fuerte > 3.5. Dimensions never override gates (RF-GATE-16)."""
    mods = {m["id"]: m for m in modules or []}
    out = []
    for dim, ids in DIMENSIONS.items():
        meds = [(mods.get(i) or {}).get("median", (mods.get(i) or {}).get("score")) for i in ids]
        known = [v for v in meds if v is not None]
        mean = sum(known) / len(known) if known else None
        band = None if mean is None else ("debil" if mean < 2.5 else "intermedia" if mean <= 3.5 else "fuerte")
        out.append({"dimension": dim, "band": band, "modules": ids,
                    "unknown_modules": [i for i, v in zip(ids, meds) if v is None]})
    return out


# ---------------------------------------------------------------- evaluate (6b.2 mapping)

def evaluate(inp=None, **kw):
    """Gates -> verdict. Returns gates, verdict, forced_verdict, reversal_conditions, p0 list, conditions."""
    inp = dict(inp or {}, **kw)
    warnings = []
    lines_out = []
    for ln in inp.get("lines", []):
        c = classify_line(ln)
        lines_out.append({"id": ln.get("id"), "archetype": c["value"], "modifiers": c.get("modifiers", []),
                          "revenue_share": ln.get("revenue_share"), "warnings": c["warnings"],
                          **{k: c[k] for k in ("boundary_case", "subtype", "routing") if k in c}})
        if ln.get("declared_archetype") and c["value"] and ln["declared_archetype"] != c["value"]:
            warnings.append(f"Linea {ln.get('id')}: etiqueta declarada {ln['declared_archetype']} pero el mecanismo "
                            f"de ingreso la clasifica como {c['value']}")
    hyb = hybrid_check(inp.get("lines", []))
    stage = stage_of(inp)
    if inp.get("stage") not in (None, *STAGES):
        warnings.append(f"stage {inp.get('stage')!r} no valido: se usa {DEFAULT_STAGE}")
    intake = None
    if isinstance(inp.get("intake"), dict):   # v0.7.3: copied from check_intake.py into gate_input.json
        intake = {k: inp["intake"].get(k) for k in ("mode", "mode_reason", "unconfirmed_assumptions")
                  if inp["intake"].get(k) is not None}
    elif stage == "pre_launch":
        warnings.append("Falta 'intake' en gate_input.json: ejecuta check_intake.py y copia mode, mode_reason y "
                        "unconfirmed_assumptions (references/intake.md)")
    gates = compute_gates(inp)
    g6, invertible = _g6(inp, gates)
    gates.append(g6)
    v = _verdict_from_gates(gates, invertible)
    reversal = [{"gate": g["id"], "condition": g.get("reversal_condition")} for g in gates if g["status"] == "fail"]
    p0_list = [d for d in g6["details"] if d.get("invertible")]
    for g in gates:
        if g["status"] == "unknown" and g["id"] != "G6" and not any(d.get("gate") == g["id"] for d in p0_list):
            p0_list.append({"gate": g["id"], "p0": g.get("questions") or g["reason"], "invertible": True,
                            "cheapest_test": g.get("reversal_condition")})
    conditions = []
    if v == "DECLINED":
        verdict = None
        warnings.append("Propuesta fuera de dominio: se declina sin veredicto")
    elif v == "NO_GO":
        verdict = "NO_GO"
    elif v == "INSUFFICIENT_EVIDENCE":
        verdict = "INSUFFICIENT_EVIDENCE"
    else:
        conditions = gate_conditions(gates) + conditional_rules(
            inp.get("modules"), inp.get("tornado"), inp.get("critical_assumptions"), stage=stage)
        verdict = "CONDITIONAL_GO" if conditions else "GO"
    # forced verdict (hidden, for the prospective log only): unknowns read at their conservative bound
    if verdict == "INSUFFICIENT_EVIDENCE":
        alt = copy.deepcopy(inp)
        for p in alt.pop("p0_unknowns", []):
            if p.get("path") and p.get("low") is not None:
                _set_path(alt, p["path"], p["low"])
        alt_gates = compute_gates(alt)
        if any(g["status"] == "fail" for g in alt_gates):
            forced = "NO_GO"
        else:
            c2 = conditional_rules(alt.get("modules"), alt.get("tornado"), alt.get("critical_assumptions"),
                                   stage=stage)
            forced = "CONDITIONAL_GO" if (c2 or any(g["status"] in ("unknown", "conditional")
                                                    for g in alt_gates)) else "GO"
    else:
        forced = verdict
    if verdict == "NO_GO" and not all(r["condition"] for r in reversal):
        warnings.append("Falta condicion de reversion en alguna compuerta fallida (RF-GATE-15)")
    alerts = [a for g in gates for a in g.get("alerts", [])]
    return res(verdict, "veredicto", warnings, sorted({i for g in gates for i in g.get("inputs", [])}),
               forced_verdict=forced, gates=gates, lines=lines_out, hybrid=hyb["value"],
               hybrid_segments=hyb["segments"], thesis_line=hyb["thesis_line"], reversal_conditions=reversal,
               p0_list=p0_list, conditions=conditions, alerts=alerts, stage=stage,
               plain_answer=plain_answer(verdict, gates, conditions, p0_list, stage), intake=intake,
               dimensions=dimension_bands(inp.get("modules")))


def gate_conditions(gates):
    """Conditions carried by 'conditional' gates, in gate order, as falsifiable hypotheses for the report."""
    out = []
    for g in gates:
        if g["status"] != "conditional":
            continue
        for c in g.get("conditions") or [{"condition": g.get("reversal_condition") or g["reason"]}]:
            out.append({"rule": "gate", "gate": g["id"], "detail": c["condition"],
                        **{k: c[k] for k in ("threshold", "direction", "field", "cheapest_test") if c.get(k) is not None}})
    return out


def plain_answer(verdict, gates, conditions, p0_list, stage=DEFAULT_STAGE):
    """One plain sentence that opens the report (v0.7.0): is it worth opening, under which conditions, and
    what to do first. Built from the verdict and the gates only, so every run says the same thing."""
    pre = stage == "pre_launch"
    if verdict is None:
        return "Fuera de dominio: no es un negocio tecnologico, asi que no se emite veredicto."
    tail = _likelihood_sentence(gates) if pre else ""
    if verdict == "GO":
        return ("Vale la pena abrirlo: los numeros salen incluso en el extremo pesimista y es probable conseguir "
                "los clientes que hacen falta." + tail if pre else
                "Vale la pena seguir: ninguna compuerta falla y no queda ninguna condicion abierta.")
    if verdict == "CONDITIONAL_GO":
        n = len(conditions)
        first = conditions[0]["detail"] if conditions else ""
        return (f"Vale la pena probarlo en pequeno antes de abrirlo del todo: hay {n} condicion"
                f"{'es' if n != 1 else ''} que comprobar, empezando por: {first}." + tail if pre else
                f"Vale la pena seguir con {n} condicion{'es' if n != 1 else ''}, empezando por: {first}.")
    if verdict == "NO_GO":
        g = next((g for g in gates if g["status"] == "fail"), {})
        return (f"Asi no vale la pena {'abrirlo' if pre else 'seguir'}: {g.get('id')} falla ({g.get('reason')}). "
                f"Lo cambiaria: {g.get('reversal_condition')}." + tail)
    missing = sorted({str(d.get("gate")) for d in p0_list})
    first = next((d.get("cheapest_test") for d in p0_list if d.get("cheapest_test")), None)
    return (f"Todavia no se puede responder: faltan datos basicos para {', '.join(missing)}"
            + (f". Lo primero: {first}." if first else "."))


def _likelihood_sentence(gates):
    """v0.7.3: the plain answer always says how likely winning the needed customers is, with the numbers."""
    g1 = next((g for g in gates if g["id"] == "G1"), {})
    lk = g1.get("likelihood")
    if not lk:
        return ""
    if lk["level"] == "sin estimar":
        return " Probabilidad de conseguir los clientes necesarios: sin estimar (falta " + ", ".join(lk["missing"]) + ")."
    exp = lk.get("expected_clients_per_year") or {}
    nums = (f" (hacen falta {lk['clients_needed_per_year']} al ano y se esperan entre {exp['low']:g} y {exp['high']:g})"
            if exp and lk.get("clients_needed_per_year") is not None else "")
    return f" Probabilidad de conseguir los clientes necesarios: {lk['level']}{nums}."


PUBLIC = ["evaluate", "demand_likelihood", "classify_line", "hybrid_check", "benchmark", "downtime_min_month", "fte_per_seat",
          "conditional_rules", "dimension_bands"]

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "evaluate" and len(sys.argv) >= 4 and sys.argv[2] == "--file":
        import json
        from _common import load_json
        print(json.dumps(evaluate(load_json(sys.argv[3])), ensure_ascii=False, indent=2, default=str))
    else:
        cli(globals(), PUBLIC)
