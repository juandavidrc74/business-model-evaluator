"""Deterministic Gate Input Compiler (v0.4.9).

Validates specialist responses against schemas, maps atomic observations to canonical gate inputs,
verifies referential closure and P0 sufficiency fail-closed, and seals reproducibility manifest.
"""
from __future__ import annotations

import decimal
import hashlib
import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from _common import ASSETS_DIR, SKILL_DIR, load_json, res
from consortium import adverse_polarity, validate_specialist_response

SCHEMAS_DIR = os.path.join(ASSETS_DIR, "schemas")


def compute_sha256_file(filepath: str | Path) -> str:
    """Calcula hash SHA-256 de un archivo en disco."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_sha256_bytes(data: bytes) -> str:
    """Calcula hash SHA-256 de una secuencia de bytes."""
    return hashlib.sha256(data).hexdigest()


def load_p0_matrix() -> dict:
    """Carga la matriz canonica p0_requirements.json."""
    p0_path = os.path.join(ASSETS_DIR, "p0_requirements.json")
    with open(p0_path, "r", encoding="utf-8") as f:
        return json.load(f)


def allowed_tiers(p0_matrix: dict, key: str) -> Set[int]:
    """Strictest evidence tiers the P0 contract allows for a predicate or metric: the intersection over every
    archetype/modifier that requires it (default {1, 2}, the predicate_claim_entry enum)."""
    sets = []
    groups = list(p0_matrix.get("archetypes", {}).values()) + list(p0_matrix.get("modifiers", {}).values())
    cross = p0_matrix.get("cross_cutting_p0")
    reqs = [r for g in groups for r in g.get("required_p0", [])]
    if isinstance(cross, list):
        reqs += cross
    elif isinstance(cross, dict):
        for v in cross.values():
            reqs += v if isinstance(v, list) else (v or {}).get("required_p0", [])
    for r in reqs:
        if key in (r.get("predicate"), r.get("metric")) and r.get("allowed_tiers"):
            sets.append(set(r["allowed_tiers"]))
    return set.intersection(*sets) if sets else {1, 2}


PLUGIN_DIR = os.path.abspath(os.path.join(SKILL_DIR, "..", ".."))
VALID_STATUSES = {"SUCCESS", "FAILED", "DEGRADED"}
VALID_CLAIM_STATUSES = {"true", "false", "unknown"}
# Base-input economics may only carry structure, never numbers: every number must come from an atomic
# measurement tied to the ledger (final audit F5: LLM-drafted values used to survive compilation).
BASE_DEMAND_KEYS_ALLOWED = {"contacted_buyers", "rejections", "paid_pilots", "paid_pilots_converted"}
# Predicate -> demand level it proves (G1 scale: 4 = LOI with budget / paid pilot / paying customer, 5 = contract).
# PRED_ECONOMIC_BUYER_CONFIRMED alone is level 3 (identified buyer without commitment): never enough on its own.
PER_SUBJECT_PREDICATES = {"PRED_CRITICAL_SUPPLIER_ALTERNATIVE_TESTED"}   # one claim per supplier subject_id (sup_NN)
DEMAND_PREDICATES = {"PRED_CONTRACT_SIGNED": 5, "PRED_PAYING_CUSTOMER_OR_CONVERSION_PROVEN": 4,
                     "PRED_ECONOMIC_BUYER_CONFIRMED": 3}
BASE_ECONOMICS_KEYS_ALLOWED = {"ledger_ids"}


def plugin_version() -> str:
    try:
        return load_json(os.path.join(PLUGIN_DIR, ".claude-plugin", "plugin.json")).get("version", "unknown")
    except (OSError, ValueError):
        return "unknown"


def _schema_catalogues() -> Tuple[Set[str], Set[str], Set[str]]:
    schema = load_json(os.path.join(SCHEMAS_DIR, "specialist_response.schema.json"))
    defs = schema.get("$defs", {})
    preds = set(defs.get("allowed_predicates", {}).get("enum", []))
    meas = set(defs.get("allowed_measurements", {}).get("enum", []))
    agents = set()
    for k, v in defs.items():
        if "agent" in k.lower() and isinstance(v, dict) and "enum" in v:
            agents |= set(v["enum"])
    return preds, meas, agents


def build_reproducibility_manifest(
    ledger_data: bytes,
    p0_reqs_data: bytes,
    computed_metrics_data: bytes,
    plugin_version: str | None = None,
) -> dict:
    """Seal every file that can change a verdict (final audit F8): all scripts, all assets that feed gates
    (benchmarks, price cards, country params, DD matrix, P0 matrix, schemas) and the agent prompts.
    A self-contained hash is tamper-EVIDENT only when the manifest itself is anchored outside the run
    (log_evaluation.py freeze, a signed commit or an external timestamp)."""
    def tree(root: str, patterns: Tuple[str, ...]) -> Dict[str, str]:
        out = {}
        for base, _dirs, files in os.walk(root):
            if "__pycache__" in base or os.sep + "example" in base:
                continue
            for fn in sorted(files):
                if fn.endswith(patterns):
                    p = os.path.join(base, fn)
                    out[os.path.relpath(p, PLUGIN_DIR).replace(os.sep, "/")] = compute_sha256_file(p)
        return dict(sorted(out.items()))

    return {
        "ledger_sha256": compute_sha256_bytes(ledger_data),
        "p0_requirements_sha256": compute_sha256_bytes(p0_reqs_data),
        "computed_metrics_sha256": compute_sha256_bytes(computed_metrics_data),
        "scripts_manifest": tree(os.path.join(SKILL_DIR, "scripts"), (".py",)),
        "schemas_manifest": tree(ASSETS_DIR, (".json",)),
        "agents_manifest": tree(os.path.join(PLUGIN_DIR, "agents"), (".md",)),
        "skill_md_sha256": compute_sha256_file(os.path.join(SKILL_DIR, "SKILL.md")),
        "git_commit_or_plugin_version": plugin_version or globals()["plugin_version"](),
        "anchoring_note": "Anclar este manifiesto fuera de la ejecucion (log_evaluation.py freeze o commit firmado)",
    }


def compile_specialist_observations(
    specialist_outputs: List[dict],
    ledger_entries: Optional[List[dict]] = None,
    validate: bool = True,
) -> Tuple[Dict[str, Any], Dict[str, Any], List[str]]:
    """Extrae y valida observaciones atomicas y claims cualitativos emitidos por especialistas.

    Devuelve:
      - measurements: dict[metric_type -> valor float/decimal parseado con su ledger_id]
      - claims: dict[predicate -> status ('true', 'false', 'unknown') con su ledger_id]
      - missing_or_corrupt_logs: lista de advertencias o errores
    """
    """Fail-closed rules added by the final audit:
      F1 no ledger -> nothing is accepted (the ledger_id check used to be skipped when the ledger was empty);
      F2 evidence tier comes from the ledger entry (source.tier), never from the agent's self-declaration;
      F3 a measurement or claim reported with different values by two specialists becomes a conflict and is
         dropped to unknown (it used to be silently overwritten by the last specialist);
      F4 enum closure: unknown statuses, measurement types, predicates and claim statuses are rejected.
    """
    measurements: Dict[str, Any] = {}
    claims: Dict[str, Any] = {}
    logs: List[str] = []
    conflicts: Dict[str, List[dict]] = {}

    ledger_by_id = {e["id"]: e for e in (ledger_entries or []) if isinstance(e, dict) and "id" in e}
    if not ledger_by_id:
        logs.append("Ledger vacio: ninguna medicion ni claim puede aceptarse (fail-closed)")
    allowed_preds, allowed_meas, _agents = _schema_catalogues()

    def ledger_tier(lid):
        src = (ledger_by_id.get(lid) or {}).get("source") or {}
        tier = src.get("tier")
        return tier if isinstance(tier, int) and 1 <= tier <= 4 else 4

    def same(a, b, field):
        if field == "value_decimal":   # numeric equality: "1000" and "1000.00" are the same measurement
            return Decimal(a[field]) == Decimal(b[field])
        return a[field] == b[field]

    def record(store, key, item, compare_field):
        prev = store.get(key)
        if key in conflicts:
            conflicts[key].append(item)
        elif prev is not None and not same(prev, item, compare_field):
            conflicts[key] = [prev, item]
            del store[key]
        elif prev is None:
            store[key] = item

    for output in specialist_outputs:
        status = output.get("status") if isinstance(output, dict) else None
        agent_id = output.get("agent_id") if isinstance(output, dict) else None
        if status not in VALID_STATUSES:
            logs.append(f"Respuesta de {agent_id} con status invalido {status!r}: descartada")
            continue
        violations = validate_specialist_response(output) if validate else []
        if violations:
            # Blocker 1: a response that violates the schema (branch, jurisdiction, required fields) is
            # discarded whole - partial acceptance would let a malformed agent shape the gates.
            logs.append(f"Respuesta de {agent_id} descartada por el esquema: {violations[:5]}")
            continue
        if status in ("FAILED", "DEGRADED"):
            logs.append(
                f"Especialista {agent_id} reporto {status}: {output.get('error_message') or output.get('degraded_reason')}"
            )
            continue

        for m in output.get("atomic_measurements", []):
            m_type = m.get("measurement_type")
            val_str = m.get("value_decimal")
            lid = m.get("ledger_id")
            if allowed_meas and m_type not in allowed_meas:
                logs.append(f"Medicion {m_type!r} fuera del catalogo cerrado: descartada")
                continue
            if lid not in ledger_by_id:
                logs.append(f"Medicion {m_type} cita ledger_id {lid} inexistente en el Ledger: descartada")
                continue
            try:
                dec_val = Decimal(str(val_str))
                if not dec_val.is_finite():
                    raise decimal.InvalidOperation("no finito")
            except (ValueError, decimal.InvalidOperation, TypeError) as err:
                logs.append(f"Medicion {m_type} con valor decimal invalido '{val_str}': {err}")
                continue
            tier = ledger_tier(lid)
            if m.get("evidence_tier") not in (None, tier):
                logs.append(f"Medicion {m_type}: tier declarado {m.get('evidence_tier')} ignorado; tier del ledger {tier}")
            record(measurements, m_type, {"value_decimal": str(dec_val), "value": float(dec_val), "ledger_id": lid,
                                          "evidence_tier": tier, "unit": m.get("unit"), "agent_id": agent_id},
                   "value_decimal")

        for c in output.get("predicate_claims", []):
            pred = c.get("predicate")
            c_status = c.get("claimed_status", "unknown")
            lid = c.get("ledger_id")
            if allowed_preds and pred not in allowed_preds:
                logs.append(f"Claim {pred!r} fuera del catalogo cerrado: descartado")
                continue
            if c_status not in VALID_CLAIM_STATUSES:
                logs.append(f"Claim {pred} con estado invalido {c_status!r}: tratado como unknown")
                c_status = "unknown"
            if lid not in ledger_by_id:
                logs.append(f"Claim {pred} cita ledger_id {lid} inexistente en el Ledger: descartado")
                continue
            adverse = adverse_polarity(ledger_by_id[lid]) if c_status == "true" else []
            if adverse:
                # Blocker 3: the cited evidence says the opposite ("sin presupuesto", "not signed"...).
                logs.append(f"Claim {pred}=true contradicho por el texto de {lid} {adverse}: degradado a unknown")
                c_status = "unknown"
            key = f"{pred}#{c.get('subject_id')}" if pred in PER_SUBJECT_PREDICATES else pred
            record(claims, key, {"status": c_status, "ledger_id": lid, "evidence_tier": ledger_tier(lid),
                                  "agent_id": agent_id}, "status")

    for key, items in conflicts.items():
        vals = sorted({i.get("value_decimal") or i.get("status") for i in items})
        logs.append(f"CONFLICTO en {key}: valores {vals} de {[i.get('agent_id') for i in items]} -> unknown (no se promedia)")
    measurements["__conflicts__"] = {k: [{x: i.get(x) for x in ("value_decimal", "status", "ledger_id", "agent_id")}
                                         for i in v] for k, v in conflicts.items()}
    return measurements, claims, logs


def compile_gate_input(
    specialist_outputs: List[dict],
    base_input: dict,
    ledger_entries: Optional[List[dict]] = None,
    validate: bool = True,
) -> dict:
    """Compila deterministicamente el gate_input.json consumible por gates_and_score.py.

    Aplica la logica fail-closed y mapea los P0 de los arquetipos declarados.
    """
    p0_matrix = load_p0_matrix()
    ledger_entries = ledger_entries if ledger_entries is not None else base_input.get("ledger", [])
    measurements, claims, logs = compile_specialist_observations(specialist_outputs, ledger_entries, validate)
    conflicts = measurements.pop("__conflicts__", {})

    compiled = dict(base_input)
    compiled["ledger"] = ledger_entries
    compiled_lines = []

    for line in base_input.get("lines", []):
        arch = line.get("archetype")
        seg_id = line.get("id")
        base_econ = line.get("economics") or {}
        dropped = sorted(k for k in base_econ if k not in BASE_ECONOMICS_KEYS_ALLOWED)
        if dropped:
            logs.append(f"Linea {seg_id}: valores de la entrada base descartados {dropped} (solo mediciones atomicas)")
        econ: Dict[str, Any] = {k: v for k, v in base_econ.items() if k in BASE_ECONOMICS_KEYS_ALLOWED}
        ledger_ids: List[str] = list(econ.get("ledger_ids", []))

        # Servicios (S1, S2, S3, S4)
        if arch in ("S1", "S2", "S3", "S4"):
            econ["kind"] = "services"

            if arch == "S2":
                # S2: Determinista precio fijo / horas
                fp = measurements.get("MEAS_PROJECT_FIXED_PRICE")
                hrs = measurements.get("MEAS_ESTIMATED_PROJECT_HOURS")
                if fp and hrs and hrs["value"] > 0:
                    econ["rate"] = fp["value"] / hrs["value"]
                    econ["realisation"] = 1.0
                    ledger_ids.extend([fp["ledger_id"], hrs["ledger_id"]])
                else:
                    econ["rate"] = None
                    econ["realisation"] = None
            else:
                rate_m = measurements.get("MEAS_HOURLY_BILLING_RATE")
                if rate_m:
                    econ["rate"] = rate_m["value"]
                    ledger_ids.append(rate_m["ledger_id"])
                real_m = measurements.get("MEAS_REALIZATION_RATE")
                if real_m:
                    econ["realisation"] = real_m["value"]
                    ledger_ids.append(real_m["ledger_id"])

            cost_m = measurements.get("MEAS_LOADED_LABOR_COST_PER_HOUR")
            if cost_m:
                econ["loaded_cost_per_billable_hour"] = cost_m["value"]
                ledger_ids.append(cost_m["ledger_id"])

            util_m = measurements.get("MEAS_BILLABLE_UTILIZATION")
            if util_m:
                econ["utilisation"] = util_m["value"]
                ledger_ids.append(util_m["ledger_id"])

            # S4: Servicios gestionados recurrentes con G2b
            if arch == "S4":
                econ["recurring"] = True
                cac_exempt_claim = claims.get("PRED_CAC_NOT_APPLICABLE_PROVEN")
                if cac_exempt_claim and cac_exempt_claim["status"] == "true" and cac_exempt_claim["evidence_tier"] == 1:
                    econ["cac_not_applicable"] = True
                    ledger_ids.append(cac_exempt_claim["ledger_id"])
                else:
                    cac_m = measurements.get("MEAS_CAC")
                    if cac_m:
                        econ["cac"] = cac_m["value"]
                        ledger_ids.append(cac_m["ledger_id"])
                    else:
                        econ["cac"] = None  # Fail-closed: causara unknown en gate_g2b

                arpa_m = measurements.get("MEAS_ARPA_MONTHLY")
                if arpa_m:
                    econ["arpa_m"] = arpa_m["value"]
                    ledger_ids.append(arpa_m["ledger_id"])

                churn_m = measurements.get("MEAS_CHURN_MONTHLY")
                if churn_m:
                    econ["churn_m"] = churn_m["value"]
                    ledger_ids.append(churn_m["ledger_id"])

                margin_m = measurements.get("MEAS_GROSS_MARGIN_DIRECT")
                if margin_m:
                    econ["margin"] = margin_m["value"]
                    ledger_ids.append(margin_m["ledger_id"])

        # Productos Software / Infra / Marketplaces
        elif arch in ("P-SAAS-SS", "P-SAAS-SL", "P-USAGE", "P-INFRA", "P-MKT"):
            econ["kind"] = "product"
            arpa_m = measurements.get("MEAS_ARPA_MONTHLY")
            if arpa_m:
                econ["arpa_m"] = arpa_m["value"]
                ledger_ids.append(arpa_m["ledger_id"])

            margin_m = measurements.get("MEAS_GROSS_MARGIN_DIRECT")
            if margin_m:
                econ["margin"] = margin_m["value"]
                ledger_ids.append(margin_m["ledger_id"])

            if arch in ("P-SAAS-SS", "P-SAAS-SL"):
                econ["recurring"] = True
                cac_m = measurements.get("MEAS_CAC")
                if cac_m:
                    econ["cac"] = cac_m["value"]
                    ledger_ids.append(cac_m["ledger_id"])
                churn_m = measurements.get("MEAS_CHURN_MONTHLY")
                if churn_m:
                    econ["churn_m"] = churn_m["value"]
                    ledger_ids.append(churn_m["ledger_id"])

            if arch == "P-USAGE":
                econ["recurring"] = True
                pt_m = measurements.get("MEAS_PASS_THROUGH_COST_RATIO")
                if pt_m:
                    econ["pass_through_cost_ratio"] = pt_m["value"]
                    ledger_ids.append(pt_m["ledger_id"])

            if arch == "P-INFRA":
                pwr_m = measurements.get("MEAS_FACILITY_POWER_COST")
                if pwr_m:
                    econ["facility_power_cost"] = pwr_m["value"]
                    ledger_ids.append(pwr_m["ledger_id"])
                cap_m = measurements.get("MEAS_CAPEX_ANNUAL")
                if cap_m:
                    econ["capex_annual"] = cap_m["value"]
                    ledger_ids.append(cap_m["ledger_id"])

            if arch == "P-MKT":
                tr_m = measurements.get("MEAS_TAKE_RATE")
                if tr_m:
                    econ["take_rate"] = tr_m["value"]
                    ledger_ids.append(tr_m["ledger_id"])

        # AI-Apps (AIX). Final audit F6: keys aligned with gate_g2 ('human_cost_per_task', 'c_task_p90');
        # the old 'human_cost' key was never read, so every compiled AI line ended in INSUFFICIENT_EVIDENCE.
        # F7: AI apps sold by subscription or usage are recurring, so G2b (CAC recovery) applies to them too.
        elif arch == "P-AI-APP":
            econ["kind"] = "aix"
            task_p = measurements.get("MEAS_TASK_PRICE")
            if task_p:
                econ["price_per_task"] = task_p["value"]
                ledger_ids.append(task_p["ledger_id"])
            p1 = measurements.get("MEAS_PASS1_ACCURACY")
            if p1:
                econ["pass1"] = p1["value"]
                ledger_ids.append(p1["ledger_id"])
            inf_c = measurements.get("MEAS_INFERENCE_COGS_PER_TASK")
            if inf_c:
                econ["inference_p90"] = inf_c["value"]
                ledger_ids.append(inf_c["ledger_id"])
            hum_c = measurements.get("MEAS_HUMAN_SUPERVISION_COGS_PER_TASK")
            if hum_c:
                econ["human_cost_per_task"] = hum_c["value"]
                ledger_ids.append(hum_c["ledger_id"])
            tot_c = measurements.get("MEAS_TOTAL_COGS_PER_TASK")
            parts = [x["value"] for x in (inf_c, hum_c) if x]
            if tot_c:
                # Conservative: the larger of the reported total and the sum of its reported parts.
                econ["c_task_p90"] = max([tot_c["value"], sum(parts)]) if parts else tot_c["value"]
                ledger_ids.append(tot_c["ledger_id"])
            mech = line.get("mechanisms") or {}
            non_recurring_only = mech and (mech.get("subscription", 0) + mech.get("usage", 0) + mech.get("managed", 0)) == 0
            econ["recurring"] = not non_recurring_only
            for meas_key, econ_key in (("MEAS_CAC", "cac"), ("MEAS_ARPA_MONTHLY", "arpa_m"),
                                       ("MEAS_CHURN_MONTHLY", "churn_m"), ("MEAS_GROSS_MARGIN_DIRECT", "margin")):
                mm = measurements.get(meas_key)
                if mm:
                    econ[econ_key] = mm["value"]
                    ledger_ids.append(mm["ledger_id"])
            if econ["recurring"] and "cac" not in econ:
                econ["cac"] = None
        else:
            # R2: a typo ("P-SAAS") must not compile silently into an empty line whose G2b reads not_applicable.
            logs.append(f"Arquetipo desconocido o no soportado {arch!r} en linea {seg_id!r}: G2/G2b quedan unknown")
            econ["recurring"] = True
            econ["cac"] = None

        econ["ledger_ids"] = list(dict.fromkeys(ledger_ids))
        new_line = dict(line)
        new_line["economics"] = econ
        compiled_lines.append(new_line)

    compiled["lines"] = compiled_lines

    def _tri(pred):
        """True only with a tier the P0 contract allows for this predicate; False (adverse) from any tier."""
        c = claims.get(pred)
        if not c or c["status"] not in ("true", "false"):
            return None, None
        tiers = allowed_tiers(p0_matrix, pred.split("#")[0])
        if c["status"] == "true" and c["evidence_tier"] not in tiers:
            logs.append(f"{pred}=true con evidencia de nivel {c['evidence_tier']} (el contrato P0 exige {sorted(tiers)}): "
                        "no se usa")
            return None, None
        return c["status"] == "true", c["ledger_id"]

    def _merge_ids(block, *ids):
        block["ledger_ids"] = list(dict.fromkeys(list(block.get("ledger_ids") or []) + [i for i in ids if i]))

    # Demanda (G1) - C1: accounts, levels and economic buyers come ONLY from specialist claims.
    base_demand = base_input.get("demand")
    if base_demand is not None or any(p in claims for p in DEMAND_PREDICATES):
        demand: Dict[str, Any] = {k: v for k, v in (base_demand or {}).items() if k in BASE_DEMAND_KEYS_ALLOWED}
        dropped = sorted(k for k in (base_demand or {}) if k not in BASE_DEMAND_KEYS_ALLOWED)
        if dropped:
            logs.append(f"Demanda: campos de la entrada base descartados {dropped} (solo predicados de especialistas)")
        accounts = []
        for pred, level in DEMAND_PREDICATES.items():
            value, lid = _tri(pred)
            if value:
                accounts.append({"level": level, "economic_buyer": True, "ledger_id": lid, "from_predicate": pred})
                _merge_ids(demand, lid)
        demand["accounts"] = accounts
        compiled["demand"] = demand

    # Concentracion universal (G3) - C1: shares and contract protection come ONLY from specialists.
    base_conc = dict(base_input.get("concentration") or {})
    dropped = [k for k in ("top1_share", "top3_share") if base_conc.pop(k, None) is not None]
    contract = dict(base_conc.get("top1_contract") or {})
    dropped += [f"top1_contract.{k}" for k in ("multi_year", "termination_for_convenience") if contract.pop(k, None) is not None]
    if contract or "top1_contract" in base_conc:
        base_conc["top1_contract"] = contract
    # Critical suppliers: the base input names them (structure, with subject_id sup_NN); whether an alternative
    # was tested comes only from PRED_CRITICAL_SUPPLIER_ALTERNATIVE_TESTED for that subject_id.
    suppliers = []
    for sup in base_conc.get("critical_suppliers") or []:
        sup = dict(sup)
        if sup.pop("alternative_tested", None) is not None:
            dropped.append(f"critical_suppliers[{sup.get('subject_id') or sup.get('name')}].alternative_tested")
        value, lid = _tri(f"PRED_CRITICAL_SUPPLIER_ALTERNATIVE_TESTED#{sup.get('subject_id')}") if sup.get("subject_id") else (None, None)
        if not sup.get("subject_id"):
            logs.append(f"Proveedor critico {sup.get('name')!r} sin subject_id (sup_NN): su alternativa no puede probarse")
        sup["alternative_tested"] = bool(value)
        if lid:
            sup["ledger_ids"] = [lid]
        suppliers.append(sup)
    if "critical_suppliers" in base_conc:
        base_conc["critical_suppliers"] = suppliers
    known = {s.get("subject_id") for s in suppliers}
    for k in claims:
        if k.startswith("PRED_CRITICAL_SUPPLIER_ALTERNATIVE_TESTED#") and k.split("#", 1)[1] not in known:
            logs.append(f"{k}: el proveedor no figura en critical_suppliers de la entrada base; no se usa")
    # Diversification plan: kept only if a specialist proves it (PRED_DIVERSIFICATION_PLAN_VERIFIABLE);
    # its evidence status and ledger ids are never taken from the base input.
    plan = contract.pop("diversification_plan", None)
    if plan is not None:
        proven_plan, lid = _tri("PRED_DIVERSIFICATION_PLAN_VERIFIABLE")
        if proven_plan and isinstance(plan, dict):
            contract["diversification_plan"] = dict(plan, evidence_status="fact", ledger_ids=[lid])
        else:
            dropped.append("top1_contract.diversification_plan (sin PRED_DIVERSIFICATION_PLAN_VERIFIABLE probado)")
        base_conc["top1_contract"] = contract
    if isinstance(base_conc.get("model_provider"), dict) and "fallback_tested" in base_conc["model_provider"]:
        base_conc["model_provider"] = {k: v for k, v in base_conc["model_provider"].items() if k != "fallback_tested"}
        dropped.append("model_provider.fallback_tested")
    if dropped:
        logs.append(f"Concentracion: valores de la entrada base descartados {dropped} (solo especialistas)")
    conc: Dict[str, Any] = base_conc
    conc_ledger_ids = list(conc.get("ledger_ids", []))
    top1_m = measurements.get("MEAS_TOP1_CLIENT_REVENUE_SHARE")
    if top1_m:
        conc["top1_share"] = top1_m["value"]
        conc_ledger_ids.append(top1_m["ledger_id"])
    top3_m = measurements.get("MEAS_TOP3_CLIENT_REVENUE_SHARE")
    if top3_m:
        conc["top3_share"] = top3_m["value"]
        conc_ledger_ids.append(top3_m["ledger_id"])

    # Verificacion de contrato plurianual protegido
    protected, lid = _tri("PRED_MULTIYEAR_NO_CONVENIENCE_TERMINATION")
    if protected:
        top1_contract = dict(conc.get("top1_contract") or {})
        top1_contract["multi_year"] = True
        top1_contract["termination_for_convenience"] = False
        conc["top1_contract"] = top1_contract
        conc_ledger_ids.append(lid)
    fallback, lid = _tri("PRED_MODEL_PROVIDER_FALLBACK_TESTED")
    if fallback is not None and isinstance(conc.get("model_provider"), dict):
        conc["model_provider"] = dict(conc["model_provider"], fallback_tested=fallback)
        conc_ledger_ids.append(lid)

    conc["ledger_ids"] = list(dict.fromkeys(conc_ledger_ids))
    compiled["concentration"] = conc

    # Compliance (G4)
    comp: Dict[str, Any] = dict(base_input.get("compliance") or {})
    residence, lid = _tri("PRED_DATA_RESIDENCE_DOCUMENTED")      # C3: tier-checked, and False propagates
    if residence is not None:
        comp["data_residence_known"] = residence
        _merge_ids(comp, lid)
    if any("V" in (ln.get("modifiers") or []) for ln in base_input.get("lines", [])):
        comp["regulated_sector"] = True                               # C4: modifier V -> P0-MOD-V1 required
    proven, lid = _tri("PRED_SECTOR_REGULATORY_COMPLIANCE_PROVEN")
    if proven is not None:
        comp["sector_compliance_proven"] = proven
        _merge_ids(comp, lid)
    compiled["compliance"] = comp

    # Delivery y SLA (G7)
    g7_claims = {k: _tri(p) for k, p in (("sla_architecture_supported", "PRED_SLA_BACKED_BY_ARCHITECTURE"),
                                         ("shift_schedule_proven", "PRED_24X7_SHIFT_SCHEDULE_PROVEN"))}
    if "delivery" in base_input:
        deliv: Dict[str, Any] = dict(base_input.get("delivery") or {})
        for key, (value, lid) in g7_claims.items():
            if value is not None:
                deliv[key] = value
                _merge_ids(deliv, lid)
        compiled["delivery"] = deliv
    elif any(v is not None for v, _ in g7_claims.values()):
        logs.append("Predicados de SLA/turnos sin bloque 'delivery' en la entrada base: G7 queda unknown")

    # Sellado del Manifest de Reproducibilidad
    ledger_bytes = json.dumps(compiled.get("ledger", []), sort_keys=True).encode("utf-8")
    p0_bytes = json.dumps(p0_matrix, sort_keys=True).encode("utf-8")
    metrics_bytes = json.dumps({"measurements": measurements, "claims": claims}, sort_keys=True).encode("utf-8")

    compiled["reproducibility_manifest"] = build_reproducibility_manifest(
        ledger_data=ledger_bytes,
        p0_reqs_data=p0_bytes,
        computed_metrics_data=metrics_bytes,
    )
    compiled["measurement_conflicts"] = conflicts
    compiled["compiler_log"] = logs
    return compiled
