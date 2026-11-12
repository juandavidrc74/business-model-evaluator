"""Intake coverage check (v0.7.1): every datum the evaluation needs has a decided treatment before `evaluate`.

The 2026-11-12 field test of v0.7.0 reached a verdict on assumptions nobody asked the founders about
(partner seniority, horizon, venture capital). This script makes the interview deterministic: it lists the
"frontier" of questions whose prerequisites are already answered (interview method adapted from the
`grilling` skill by Matt Pocock, mattpocock/skills, MIT licence) and refuses to let the evaluation start
while a field is missing, a founder-only datum was assumed without the user's confirmation, or the closing
summary was not confirmed.

    python check_intake.py intake.json

intake.json:
    {"mode": "interactive" | "non_interactive",
     "mode_reason": "user_asked_no_questions" | "no_human"   (only with non_interactive),
     "stage": "pre_launch" | "operating",
     "archetypes": ["S2"], "modifiers": ["AIX"], "founders_deliver": true,
     "summary_confirmed": true,
     "fields": {"<field id>": {"answered_by": "proposal" | "user" | "reference" | "unknown",
                               "value": ..., "low": ..., "high": ...,
                               "quote": "...", "round": 1, "ledger_id": "L3",
                               "confirmed": true, "accepted_unknown": true}}}

Output: {"value": "complete" | "incomplete" | "insufficient", "can_evaluate": bool, "next_round": [...],
         "problems": [...], "unconfirmed_assumptions": [...], ...}. Exit code 0 when can_evaluate, 1 otherwise,
2 on a malformed file.
"""
from __future__ import annotations

import json
import sys

from _common import res

SERVICES = {"S1", "S2", "S3", "S4"}
PRODUCTS = {"P-SAAS-SS", "P-SAAS-SL", "P-USAGE", "P-AI-APP", "P-INFRA", "P-MKT"}
SOURCES = ("proposal", "user", "reference", "unknown")
MODES = ("interactive", "non_interactive")
# The only two reasons not to interview: the user said not to ask, or nobody can answer (automated eval).
# Lacking a question tool is NOT a reason: ask in the chat and stop until the answer arrives.
NON_INTERACTIVE_REASONS = ("user_asked_no_questions", "no_human")

# id, prerequisites, question, founder_only, basic, applies(ctx), where to look before asking
FIELDS = [
    ("offer", [], "Que venden exactamente: cada servicio o producto y en que consiste", False, True, None,
     "la propuesta"),
    ("customer_segment", [], "A quien le venden: tipo y tamano de cliente y quien decide y paga", False, True,
     None, "la propuesta"),
    ("countries", [], "En que pais estan los clientes y desde que pais se entrega", False, False, None,
     "la propuesta"),
    ("currency", [], "En que moneda cobran y en cual quieren ver las cifras", False, False, None,
     "la propuesta; si no, la del pais del cliente"),
    ("stage", [], "Ya facturan con regularidad o todavia no han vendido", True, False, None,
     "la propuesta; en duda, pre_launch"),
    ("horizon_months", [], "En cuantos meses necesitan que el negocio se pague solo", True, False, None,
     "la propuesta; recomendacion por defecto 24 meses"),
    ("seeks_vc", [], "Piensan buscar capital riesgo o financiarse con las ventas", True, False, None,
     "la propuesta"),
    ("price", ["offer"], "Precio de cada servicio o plan (si no es fijo, minimo y maximo)", False, True, None,
     "la propuesta; si no, precios publicados de competidores (M5) como rango"),
    ("price_includes", ["price"], "Que incluye cada precio: entregables, horas, soporte, revisiones", False,
     False, None, "la propuesta"),
    ("partners", [], "Cuantos socios son y quienes trabajan en la entrega", True, False, None, "la propuesta"),
    ("partner_hours_per_week", ["partners"], "Cuantas horas por semana puede dedicar cada socio", True, False,
     None, "la propuesta"),
    ("partner_seniority", ["partners"],
     "Que experiencia tiene cada socio (estudiante, junior, semi-senior, senior); fija el salario de mercado "
     "con el que se costean sus horas (R4)", True, False, None,
     "la propuesta; si no, rango de salario de geo-adaptation.md del perfil mas bajo al mas alto"),
    ("fixed_costs_monthly", ["offer"], "Costes fijos al mes: herramientas, alojamiento, contador, oficina",
     True, False, None, "la propuesta"),
    ("hours_per_project", ["offer", "archetypes"],
     "Horas estimadas por proyecto o por cliente al mes (o las reales de un proyecto ya hecho)", True, False,
     lambda c: bool(c["archetypes"] & SERVICES), "la propuesta; si no, rango de referencias del sector"),
    ("churn_expected", ["offer", "archetypes"], "Cuantos clientes esperan perder al mes o al ano", False,
     False, lambda c: bool(c["archetypes"] & PRODUCTS), "benchmarks del arquetipo, como rango"),
    ("acquisition", ["customer_segment", "archetypes"],
     "Como van a conseguir clientes y cuanto les cuesta cada uno (tiempo o dinero)", True, False,
     lambda c: bool(c["archetypes"]), "la propuesta"),
    ("sales_capacity", ["partners"],
     "Cuantos contactos comerciales (reuniones, llamadas o mensajes con respuesta) pueden hacer al mes entre "
     "todos; con la conversion, estima cuantos clientes es probable conseguir (G1)", True, False, None,
     "la propuesta; si no, horas de los socios dedicadas a vender"),
    ("ai_cost_per_task", ["offer", "archetypes"],
     "Que modelo de IA usan, cuantas llamadas por tarea y cuanta revision humana", False, False,
     lambda c: "AIX" in c["modifiers"] or "P-AI-APP" in c["archetypes"],
     "price_cards.json y la propuesta"),
    ("demand_evidence", ["customer_segment"],
     "A quien han contactado, que respondio y si hay algo firmado o pagado (con el documento)", True, False,
     None, "la propuesta y sus anexos"),
    ("legal_obligations", ["offer", "countries"],
     "Que obligaciones legales conocen y si hay un plan escrito con responsable y fecha", True, False, None,
     "due-diligence.md para la lista; el plan solo lo saben los socios"),
    ("critical_suppliers", ["offer"],
     "De que proveedor dependen (API, nube, plataforma) y si hay una alternativa probada", False, False, None,
     "la propuesta"),
    ("service_commitments", ["offer"],
     "Prometen disponibilidad, tiempos de respuesta o soporte 24x7; quien cubre las guardias", True, False,
     None, "la propuesta"),
]
FIELD_IDS = {f[0] for f in FIELDS}


def _has_value(entry: dict) -> bool:
    if entry.get("value") not in (None, ""):
        return True
    return entry.get("low") is not None and entry.get("high") is not None


def _is_range(entry: dict) -> bool:
    return entry.get("low") is not None and entry.get("high") is not None and entry.get("low") != entry.get("high")


def _entry_problems(fid: str, e: dict, founder_only: bool, mode: str) -> list[str]:
    """Problems that keep a present field from counting as answered."""
    src = e.get("answered_by")
    if src not in SOURCES:
        return [f"{fid}: answered_by debe ser uno de {list(SOURCES)}"]
    if src == "unknown":
        if mode == "interactive" and not e.get("accepted_unknown"):
            return [f"{fid}: unknown sin que los socios digan que no lo saben (accepted_unknown); pregunta"]
        return []
    if not _has_value(e):
        return [f"{fid}: answered_by={src} sin value ni rango low/high"]
    if src == "proposal" and not str(e.get("quote") or "").strip():
        return [f"{fid}: dato de la propuesta sin cita (quote)"]
    if src == "user":
        if mode == "non_interactive":
            return [f"{fid}: answered_by=user en modo non_interactive; nadie pudo responder"]
        if not isinstance(e.get("round"), int) or e["round"] < 1:
            return [f"{fid}: respuesta del usuario sin numero de ronda (round)"]
    if src == "reference":
        if not e.get("ledger_id"):
            return [f"{fid}: dato de referencia sin ledger_id"]
        if founder_only and mode == "interactive" and not e.get("confirmed"):
            return [f"{fid}: supuesto de referencia sobre algo que solo saben los socios, sin confirmar; "
                    "pregunta con ese valor como recomendacion"]
        if founder_only and mode == "non_interactive" and not _is_range(e):
            return [f"{fid}: supuesto de referencia sin rango; antes de abrir, lo que solo saben los socios "
                    "entra como rango (low/high) para que G6 calcule el umbral"]
    return []


def check(intake: dict) -> dict:
    if not isinstance(intake, dict) or not isinstance(intake.get("fields", {}), dict):
        return res(None, "intake", ["intake.json debe ser un objeto con 'fields'"], [], can_evaluate=False,
                   problems=["formato"], next_round=[])
    warnings: list[str] = []
    mode_problems: list[str] = []
    mode, reason = intake.get("mode"), intake.get("mode_reason")
    if mode not in MODES:
        mode_problems.append(f"mode {mode!r} ausente o no valido: declara 'interactive' (por defecto: hay una "
                             "persona que puede responder) o 'non_interactive' con mode_reason")
        mode = "interactive"
    elif mode == "non_interactive" and reason not in NON_INTERACTIVE_REASONS:
        # v0.7.2: a model without a question tool used to conclude it "could not ask". Without a tool you
        # ask in the chat and wait; non_interactive is only for no human at all or an explicit request.
        mode_problems.append(f"non_interactive sin mode_reason valido {list(NON_INTERACTIVE_REASONS)}: si hay "
                             "una persona al otro lado, pregunta en el chat y espera la respuesta")
        mode = "interactive"
    fields = intake.get("fields") or {}
    ctx = {"archetypes": set(intake.get("archetypes") or []), "modifiers": set(intake.get("modifiers") or [])}
    extra = sorted(set(fields) - FIELD_IDS)
    if extra:
        warnings.append(f"campos no reconocidos (se ignoran): {extra}")

    answered, missing, unconfirmed, basics_unknown, ids = set(), [], [], [], []
    problems = list(mode_problems)
    for fid, _needs, _q, founder_only, basic, applies, _look in FIELDS:
        if applies is not None and ctx["archetypes"] and not applies(ctx):
            continue
        e = fields.get(fid)
        if not isinstance(e, dict):
            missing.append(fid)
            continue
        errs = _entry_problems(fid, e, founder_only, mode)
        if errs:
            problems += errs
            continue
        answered.add(fid)
        if e.get("ledger_id"):
            ids.append(e["ledger_id"])
        if e.get("answered_by") == "reference" and founder_only and not e.get("confirmed"):
            unconfirmed.append(fid)
        if e.get("answered_by") == "unknown" and basic:
            basics_unknown.append(fid)

    def ready(needs):
        return all((n == "archetypes" and ctx["archetypes"]) or n in answered for n in needs)

    next_round, blocked = [], []
    for fid, needs, question, founder_only, basic, applies, look in FIELDS:
        if fid in answered:
            continue
        if applies is not None and ctx["archetypes"] and not applies(ctx):
            continue
        if applies is not None and not ctx["archetypes"]:
            blocked.append(fid)          # depends on the classification of Paso 1
            continue
        if ready(needs):                 # the frontier: every prerequisite already answered
            next_round.append({"field": fid, "question": question, "founder_only": founder_only,
                               "basic": basic, "look_first_in": look})
        else:
            blocked.append(fid)

    pending = bool(missing or problems or blocked)
    if mode == "interactive":
        if not pending and not intake.get("summary_confirmed"):
            problems.append("falta el cierre: muestra el resumen de lo que vas a usar y que los socios lo "
                            "confirmen (summary_confirmed: true)")
        status = "incomplete" if (pending or not intake.get("summary_confirmed")) else "complete"
        if status == "complete" and basics_unknown:
            status = "insufficient"
    else:
        # Nobody can answer: every field still needs a decided treatment (a sourced value, a reference range
        # or unknown); a missing basic datum leads to INSUFFICIENT_EVIDENCE with the questions.
        status = "incomplete" if pending else ("insufficient" if basics_unknown else "complete")
    can_evaluate = status in ("complete", "insufficient")
    if basics_unknown:
        warnings.append(f"datos basicos desconocidos {basics_unknown}: el veredicto sera "
                        "INSUFFICIENT_EVIDENCE con estas preguntas")
    if blocked and not ctx["archetypes"]:
        warnings.append("clasifica las lineas (Paso 1) y anota 'archetypes' para abrir las preguntas que "
                        "dependen del arquetipo")
    question_of = {f[0]: f[2] for f in FIELDS}
    report_questions = ([q["question"] for q in next_round] if not can_evaluate
                        else [question_of[b] for b in basics_unknown])
    return res(status, "intake", warnings, ids, can_evaluate=can_evaluate, mode=mode,
               mode_reason=reason if mode == "non_interactive" else None,
               next_round=next_round, blocked=sorted(set(blocked)), problems=problems,
               unconfirmed_assumptions=unconfirmed, basics_unknown=basics_unknown,
               questions_for_report=report_questions)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print("uso: python check_intake.py intake.json")
        return 2
    try:
        with open(argv[1], encoding="utf-8") as fh:
            intake = json.load(fh)
    except (OSError, ValueError) as exc:
        print(json.dumps({"value": None, "can_evaluate": False, "warnings": [f"no se pudo leer: {exc}"]},
                         ensure_ascii=False))
        return 2
    out = check(intake)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["can_evaluate"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
