"""AI-native economics (6f): cost per successful task (CPST) with tail percentiles, heterogeneous
reliability (Beta / pass^k), human supervision cost, fixed-cost allocation, meter viability,
thresholds AI_T1..AI_T9, the 16 red flags, provider-price stress and self-hosting break-even.

All thresholds are methodological proposals [P] unless a benchmark id is cited. Prices are never
hard-coded: they come from assets/price_cards.json (with access_date / next_review) or as inputs.
Stdlib only. Usage: python ai_native_model.py <function> '<json kwargs>'
"""
from __future__ import annotations

import datetime as dt
import math
import random
import statistics
from typing import Sequence

from _common import asset, check_domain, cli, need, res

SEED = 20261109
S_DEFAULT = 1.37           # Beta concentration fitted to tau-bench retail (AI-027) when pass^k is missing (T7)
SER_DEFAULT = 0.05         # silent error rate imputed with a confidence penalty when absent (RF-GATE-04)
SIGMA_NO_LOGS = 1.0        # lognormal sigma for input tokens without logs; sensitivity at 0.8 and 1.2 (A12)
MIGRATIONS_PER_YEAR_DEFAULT = 1

AI_T1 = "price_below_p90_cost"            # price per task/outcome < C_task p90 -> G2 fail
AI_T2 = 0.50                              # mean margin incl. humans < 50 % in an 'AI product' -> evaluate as service
AI_T3 = 2.0                               # margin < 0 with provider price x2.0 -> high risk (G3 KO without fallback)
AI_T4 = 0.80                              # main provider > 80 % of tokens without tested fallback
AI_T5 = 0.40                              # humans > 40 % of COGS per task -> route to S2/S4
AI_T6 = 323                               # ACR measured with n < 323 or without blind QA -> low confidence
AI_T7 = 3                                 # pass^k (k >= 3) not reported -> use s = 1.37
AI_T8 = 0.50                              # top 10 % of tasks > 50 % of AI cost -> require cost caps
AI_T9 = 0.50                              # seat with p95 cost per customer > 50 % of price -> repricing/limits


# ---------------------------------------------------------------- price cards

def price_card(provider_model=None, evaluation_date=None, ledger_ids=None):
    """Look up a price card; an expired card (next_review <= evaluation date) cannot feed T1/T3."""
    m = need("USD/MTok", ledger_ids, provider_model=provider_model)
    if m:
        return m
    cards = asset("price_cards.json")["cards"]
    card = next((c for c in cards if c["id"] == provider_model), None)
    if not card:
        return res(None, "USD/MTok", [f"Sin ficha de precios para {provider_model}"], ledger_ids)
    w = []
    today = dt.date.fromisoformat(evaluation_date) if evaluation_date else dt.date.today()
    card = dict(card)
    # REV-007: apply announced price changes in force on the evaluation date (latest 'from' <= date).
    applied = None
    for step in sorted(card.get("price_schedule", []), key=lambda s: s["from"]):
        if dt.date.fromisoformat(step["from"]) <= today:
            applied = step
    card["base_p_in_usd_mtok"], card["base_p_out_usd_mtok"] = card["p_in_usd_mtok"], card["p_out_usd_mtok"]
    if applied:
        card["p_in_usd_mtok"], card["p_out_usd_mtok"] = applied["p_in"], applied["p_out"]
        w.append(f"Precio programado aplicado desde {applied['from']}: {applied['p_in']}/{applied['p_out']} USD/MTok "
                 f"(antes {card['base_p_in_usd_mtok']}/{card['base_p_out_usd_mtok']})")
    pending = [s for s in card.get("price_schedule", []) if dt.date.fromisoformat(s["from"]) > today]
    if pending:
        w.append("Cambio de precio anunciado a partir de " + ", ".join(s["from"] for s in pending) +
                 ": incluirlo en el estres de precio (T3)")
    expired = dt.date.fromisoformat(card["next_review"]) <= today
    if expired:
        w.append(f"Ficha vencida desde {card['next_review']}: refrescar antes de usar en T1/T3 (RT-BMK-06)")
    return res(card, "USD/MTok", w, [card["benchmark_id"]], expired=expired, schedule_applied=applied)


# ---------------------------------------------------------------- RT-AI-02 cost of one attempt

def attempt_cost(t_in=None, t_out=None, p_in=None, p_out=None, cache_read_share=0.0, cache_write_share=0.0,
                 p_cache_read=None, p_cache_write=None, tools_cost=0.0, runtime_h=0.0, p_runtime_h=0.0,
                 ledger_ids=None):
    """C_att = [T_in(1-h-w)P_in + T_in w P_cw + T_in h P_cr + T_out P_out]/1e6 + tools + runtime."""
    m = need("USD/intento", ledger_ids, t_in=t_in, t_out=t_out, p_in=p_in, p_out=p_out)
    if m:
        return m
    h, w = cache_read_share, cache_write_share
    if (h or w) and (p_cache_read is None or p_cache_write is None):
        return res(None, "USD/intento", ["Cuotas de cache sin precio de lectura/escritura"], ledger_ids)
    tokens = (t_in * (1 - h - w) * p_in + t_in * w * (p_cache_write or 0) + t_in * h * (p_cache_read or 0)
              + t_out * p_out) / 1e6
    return res(tokens + tools_cost + runtime_h * p_runtime_h, "USD/intento", [], ledger_ids,
               token_cost=tokens)


# ---------------------------------------------------------------- RT-AI-03 heterogeneous reliability

def pass_k(alpha=None, beta=None, k=None, ledger_ids=None):
    """pass^k = prod_{i<k} (alpha+i)/(alpha+beta+i): probability that k independent runs ALL succeed."""
    m = need("probabilidad", ledger_ids, alpha=alpha, beta=beta, k=k) or \
        check_domain("probabilidad", ledger_ids, alpha=(alpha, "pos"), beta=(beta, "pos"), k=(k, "pos"))
    if m:
        return m
    v = 1.0
    for i in range(int(k)):
        v *= (alpha + i) / (alpha + beta + i)
    return res(v, "probabilidad", [], ledger_ids)


def success_within(alpha=None, beta=None, attempts=None, ledger_ids=None):
    """P(success in <= K attempts) = 1 - prod_{i<K} (beta+i)/(alpha+beta+i) (correlated difficulty)."""
    m = need("probabilidad", ledger_ids, alpha=alpha, beta=beta, attempts=attempts) or \
        check_domain("probabilidad", ledger_ids, alpha=(alpha, "pos"), beta=(beta, "pos"), attempts=(attempts, "pos"))
    if m:
        return m
    fail = 1.0
    for i in range(int(attempts)):
        fail *= (beta + i) / (alpha + beta + i)
    p1 = alpha / (alpha + beta)
    independent = 1 - (1 - p1) ** int(attempts)
    return res(1 - fail, "probabilidad",
               [] if abs(independent - (1 - fail)) < 0.01 else
               [f"Suponer reintentos independientes daria {independent:.2f}: sobreestima la autonomia (red flag 4)"],
               ledger_ids, independent_assumption=independent)


def beta_from_pass(pass1=None, passk=None, k=None, ledger_ids=None):
    """Fit alpha/(alpha+beta) = pass^1 and s = alpha+beta to a measured pass^k (bisection).

    Without pass^k (k >= 3) the concentration defaults to s = 1.37 (AI_T7) with a warning."""
    m = need("parametros", ledger_ids, pass1=pass1) or \
        check_domain("parametros", ledger_ids, pass1=(pass1, "prob"), passk=(passk, "prob"))
    if m:
        return m
    if not 0 < pass1 < 1:
        return res(None, "parametros", ["pass^1 debe estar en (0, 1): con 0 o 1 la fiabilidad no es heterogenea "
                                        "(revisar la muestra)"], ledger_ids)
    w = []
    if passk is None or k is None or k < AI_T7:
        s = S_DEFAULT
        w.append(f"pass^k (k >= {AI_T7}) no reportado: supuestos de fiabilidad no aceptados; s = {S_DEFAULT} (T7)")
    else:
        def f(s):
            a = pass1 * s
            v = 1.0
            for i in range(int(k)):
                v *= (a + i) / (s + i)
            return v - passk
        lo, hi = 1e-4, 1e4
        if f(lo) * f(hi) > 0:
            return res(None, "parametros", ["pass^k incompatible con pass^1"], ledger_ids)
        for _ in range(200):
            mid = math.sqrt(lo * hi)
            if f(lo) * f(mid) <= 0:
                hi = mid
            else:
                lo = mid
        s = math.sqrt(lo * hi)
    return res({"alpha": pass1 * s, "beta": (1 - pass1) * s, "s": s}, "parametros", w, ledger_ids)


# ---------------------------------------------------------------- RT-AI-04/05 human & fixed cost

def human_cost(wage_h=None, q_sampled=None, t_qa_min=None, ser=None, t_fix_min=None, t_late_min=None,
               escalation_rate=None, t_esc_min=None, autonomous_rate=None, external_damage=0.0,
               t_esc_is_median=False, t_esc_sigma=None, ledger_ids=None):
    """Expected human cost per task:
    C_h = ACR * (q t_qa w + SER (q t_fix + (1-q)(t_late + damage)) w) + ER * t_esc w.
    All times are MEANS (expected value). If the escalation time is a lognormal MEDIAN (as in
    simulate_tasks), pass t_esc_is_median=True and t_esc_sigma: mean = median x exp(sigma^2 / 2) (REV-008).
    Missing SER -> 5 % with confidence penalty; other missing P0 -> unknown (G2 'no evaluable')."""
    warnings = []
    if t_esc_is_median and t_esc_min is not None:
        if t_esc_sigma is None:
            return res(None, "USD/tarea", ["t_esc_min es mediana pero falta t_esc_sigma para convertirla a media"],
                       ledger_ids)
        t_esc_min = t_esc_min * math.exp(t_esc_sigma ** 2 / 2)
        warnings.append(f"Tiempo de escalado convertido de mediana a media: {t_esc_min:.2f} min")
    dom = check_domain("USD/tarea", ledger_ids, wage_h=(wage_h, "nonneg"), q_sampled=(q_sampled, "prob"),
                       ser=(ser, "prob"), escalation_rate=(escalation_rate, "prob"),
                       autonomous_rate=(autonomous_rate, "prob"))
    if dom:
        return dom
    if ser is None:
        ser = SER_DEFAULT
        warnings.append("Tasa de error silencioso ausente: se usa 5 % con penalizacion de confianza")
    m = need("USD/tarea", ledger_ids, wage_h=wage_h, q_sampled=q_sampled, t_qa_min=t_qa_min, t_fix_min=t_fix_min,
             t_late_min=t_late_min, escalation_rate=escalation_rate, t_esc_min=t_esc_min,
             autonomous_rate=autonomous_rate)
    if m:
        m["warnings"] += warnings
        return m
    w = wage_h / 60.0
    qa = q_sampled * t_qa_min * w
    err = ser * (q_sampled * t_fix_min * w + (1 - q_sampled) * (t_late_min * w + external_damage))
    esc = escalation_rate * t_esc_min * w
    total = autonomous_rate * (qa + err) + esc
    return res(total, "USD/tarea", warnings, ledger_ids,
               components={"qa": autonomous_rate * qa, "errors": autonomous_rate * err, "escalation": esc})


def fixed_cost_per_task(volume=None, evals=0.0, prompt_maintenance=0.0, migrations_per_year=None,
                        migration_cost=0.0, infra=0.0, observability=0.0, period_years=1.0, ledger_ids=None):
    """C_fix = (evals + prompt maintenance + migrations + infra + observability) / volume (RT-AI-05)."""
    m = need("USD/tarea", ledger_ids, volume=volume)
    if m:
        return m
    w = []
    if migrations_per_year is None:
        migrations_per_year = MIGRATIONS_PER_YEAR_DEFAULT
        w.append("Sin dato de migraciones de modelo: se imputa 1 al anio (RT-AI-05)")
        if not migration_cost:
            w.append("Coste de migracion no declarado: C_fix infravalorado")
    total = evals + prompt_maintenance + migrations_per_year * period_years * migration_cost + infra + observability
    return res(total / volume, "USD/tarea", w, ledger_ids)


# ---------------------------------------------------------------- RT-AI-06/07 simulation

def _poisson(lam, rng):
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p < L:
            return k
        k += 1


def _pct(sorted_vals, q):
    return sorted_vals[int(q / 100 * (len(sorted_vals) - 1))]


def simulate_tasks(p_in=None, p_out=None, p_cache_read=None, p_cache_write=None, median_t_in=None,
                   sigma_t_in=None, out_ratio_median=0.04, out_ratio_sigma=0.4, cache_read_share=0.0,
                   cache_write_share=0.0, tool_calls_mean=0.0, tool_price=0.0, pass1=None, passk=None, k=None,
                   attempts=3, q_sampled=None, t_qa_min=None, ser=None, t_fix_min=None, t_late_min=None,
                   t_esc_median_min=None, t_esc_sigma=0.5, wage_h=None, fixed_cost=0.0, price=None,
                   price_multiplier=1.0, n=100_000, seed=SEED, has_logs=False, ledger_ids=None):
    """Monte Carlo of cost per task: p50/p90/p95/p99 of C_att and C_task, mean, top-10 % share,
    human share of COGS, autonomy/escalation/late-error rates and P(C_task > price).

    Without logs (has_logs=False) the output is flagged 'uncalibrated' and the sigma sensitivity
    (0.8 / 1.0 / 1.2) is attached (RT-AI-07)."""
    warnings = []
    if ser is None:
        ser = SER_DEFAULT
        warnings.append("SER ausente: 5 % con penalizacion de confianza")
    m = need("USD/tarea", ledger_ids, p_in=p_in, p_out=p_out, median_t_in=median_t_in, pass1=pass1,
             q_sampled=q_sampled, t_qa_min=t_qa_min, t_fix_min=t_fix_min, t_late_min=t_late_min,
             t_esc_median_min=t_esc_median_min, wage_h=wage_h)
    if m:
        m["warnings"].append("G2 'no evaluable' para AIX/P-AI-APP hasta tener estos datos (RF-GATE-04)")
        return m
    if (cache_read_share or cache_write_share) and (p_cache_read is None or p_cache_write is None):
        return res(None, "USD/tarea", ["Cuotas de cache sin precios de cache"], ledger_ids)
    bp = beta_from_pass(pass1, passk, k)
    warnings += bp["warnings"]
    a, b = bp["value"]["alpha"], bp["value"]["beta"]
    sigma = sigma_t_in if sigma_t_in is not None else SIGMA_NO_LOGS
    rng = random.Random(seed)
    pin, pout = p_in * price_multiplier, p_out * price_multiplier
    pcr, pcw = (p_cache_read or 0) * price_multiplier, (p_cache_write or 0) * price_multiplier
    hshare, wshare = cache_read_share, cache_write_share
    W = wage_h
    ai, hum, tot = [], [], []
    auto = esc = late = 0
    for _ in range(int(n)):
        p = rng.betavariate(a, b)
        c, ok = 0.0, False
        for _k in range(int(attempts)):
            tin = rng.lognormvariate(math.log(median_t_in), sigma)
            tout = tin * rng.lognormvariate(math.log(out_ratio_median), out_ratio_sigma)
            c += (tin * (1 - hshare - wshare) * pin + tin * wshare * pcw + tin * hshare * pcr + tout * pout) / 1e6
            if tool_calls_mean:
                c += _poisson(tool_calls_mean, rng) * tool_price
            if rng.random() < p:
                ok = True
                break
        h = 0.0
        if ok:
            auto += 1
            sampled = rng.random() < q_sampled
            wrong = rng.random() < ser
            if sampled:
                h += t_qa_min / 60 * W
            if wrong:
                if sampled:
                    h += t_fix_min / 60 * W
                else:
                    h += t_late_min / 60 * W
                    late += 1
        else:
            esc += 1
            h += rng.lognormvariate(math.log(t_esc_median_min), t_esc_sigma) / 60 * W
        ai.append(c)
        hum.append(h)
        tot.append(c + h + fixed_cost)
    sa, st = sorted(ai), sorted(tot)
    N = len(ai)
    out = {
        "inference_tools": {f"p{q}": _pct(sa, q) for q in (50, 90, 95, 99)} | {"mean": statistics.fmean(ai)},
        "total": {f"p{q}": _pct(st, q) for q in (50, 90, 95, 99)} | {"mean": statistics.fmean(tot)},
        "autonomous_completion_rate": auto / N, "escalation_rate": esc / N, "late_error_rate": late / N,
        "human_share_of_cost": sum(hum) / sum(tot) if sum(tot) else None,
        "top10_share_of_ai_cost": sum(sa[-N // 10:]) / sum(sa) if sum(sa) else None,
        "cpst_auto": sum(ai) / auto if auto else None,
        "cpst_total": sum(tot) / max(1, auto - late),
    }
    if price is not None:
        out["prob_cost_above_price"] = sum(1 for t in tot if t > price) / N
        out["margin_on_mean_inference"] = 1 - out["inference_tools"]["mean"] / price
        out["margin_on_total_mean"] = 1 - out["total"]["mean"] / price
    extra = {"seed": seed, "n": n, "uncalibrated": not has_logs}
    if not has_logs:
        warnings.append("Sin logs: distribucion de tokens no calibrada (confianza baja, RT-AI-07)")
        sens = {}
        for sg in (0.8, 1.2):
            if abs(sg - sigma) < 1e-9:
                continue
            sub = simulate_tasks(p_in, p_out, p_cache_read, p_cache_write, median_t_in, sg, out_ratio_median,
                                 out_ratio_sigma, cache_read_share, cache_write_share, tool_calls_mean,
                                 tool_price, pass1, passk, k, attempts, q_sampled, t_qa_min, ser, t_fix_min,
                                 t_late_min, t_esc_median_min, t_esc_sigma, wage_h, fixed_cost, price,
                                 price_multiplier, min(int(n), 20_000), seed, has_logs=True)
            sens[f"sigma={sg}"] = {"total": sub["value"]["total"], "inference_tools": sub["value"]["inference_tools"]}
        extra["sigma_sensitivity"] = sens
    return res(out, "USD/tarea", warnings, ledger_ids, **extra)


# ---------------------------------------------------------------- RT-AI-08 sample size

def min_sample_size(p=None, margin_error=None, z=1.959964, ledger_ids=None):
    """n = ceil(z^2 p (1-p) / e^2): 323 tasks for ~70 % autonomy at +/-5 % (T6)."""
    m = need("tareas", ledger_ids, p=p, margin_error=margin_error)
    return m or res(math.ceil(z * z * p * (1 - p) / margin_error ** 2 - 1e-9), "tareas", [], ledger_ids)


# ---------------------------------------------------------------- RT-AI-10/11 meters & outcome pricing

def meter_viability(meter=None, price=None, cost_p50=None, cost_p90=None, cost_p95=None, target_margin=None,
                    fixed_fee=None, c_fix=None, variable_price=None, outcome_definition_auditable=None,
                    tail_simulated=False, ledger_ids=None):
    """Numeric viability test per meter (6f.4 matrix) [P]."""
    m = need("booleano", ledger_ids, meter=meter)
    if m:
        return m
    checks, w = {}, []
    if meter == "seat":
        checks["p95_cost_below_half_price"] = cost_p95 is not None and price and cost_p95 < 0.5 * price
    elif meter == "consumption":
        checks["p50_margin_meets_target"] = (price and cost_p50 is not None and target_margin is not None
                                             and 1 - cost_p50 / price >= target_margin)
        checks["p95_margin_positive"] = price and cost_p95 is not None and price - cost_p95 > 0
    elif meter == "credits":
        checks["p90_cost_below_credit_price"] = cost_p90 is not None and price and cost_p90 < price
    elif meter == "task":
        checks["price_ge_p90_cost"] = cost_p90 is not None and price is not None and price >= cost_p90
    elif meter == "outcome":
        checks["price_ge_cpst_p90_over_margin"] = (cost_p90 is not None and target_margin is not None and price
                                                   is not None and price >= cost_p90 / (1 - target_margin))
        checks["outcome_definition_written_and_auditable"] = bool(outcome_definition_auditable)
    elif meter == "flat_subscription":
        checks["customer_tail_simulated_p95_p99"] = bool(tail_simulated)
    elif meter == "hybrid":
        checks["fixed_fee_covers_c_fix"] = fixed_fee is not None and c_fix is not None and fixed_fee >= c_fix
        checks["variable_ge_p90"] = variable_price is not None and cost_p90 is not None and variable_price >= cost_p90
    else:
        return res(None, "booleano", [f"meter desconocido: {meter}"], ledger_ids)
    unknown = [k for k, v in checks.items() if v is None]
    if unknown:
        w.append("Datos insuficientes para: " + ", ".join(unknown))
    return res(all(bool(v) for v in checks.values()), "booleano", w, ledger_ids, checks=checks)


def outcome_revenue(price=None, p_billable_success=None, cost_per_task=None, ledger_ids=None):
    """RT-AI-11: revenue per task = price x P(billable success); margin over that revenue incl. failures."""
    m = need("USD/tarea", ledger_ids, price=price, p_billable_success=p_billable_success, cost_per_task=cost_per_task)
    if m:
        return m
    rev = price * p_billable_success
    return res(rev, "USD/tarea", [], ledger_ids, margin=(rev - cost_per_task) / rev if rev else None)


# ---------------------------------------------------------------- RT-AI-12/14 thresholds & stress

def route_archetype(human_share_of_cogs=None, human_cost_decreasing_with_volume=None, recurring_or_sla=False,
                    ledger_ids=None):
    """T5 routing for AIX lines: humans > 40 % of COGS per task (or human cost not falling with volume)
    -> S4 if recurring/per-task with SLA, else S2; otherwise P-AI-APP."""
    m = need("arquetipo", ledger_ids, human_share_of_cogs=human_share_of_cogs)
    if m:
        return m
    service = human_share_of_cogs > AI_T5 or human_cost_decreasing_with_volume is False
    code = ("S4" if recurring_or_sla else "S2") if service else "P-AI-APP"
    why = (f"humanos {human_share_of_cogs:.0%} del COGS por tarea" +
           (" > 40 % (T5)" if human_share_of_cogs > AI_T5 else "") +
           ("; coste humano no baja con el volumen" if human_cost_decreasing_with_volume is False else ""))
    return res(code, "arquetipo", [], ledger_ids, modifier="AIX", reason=why,
               compare_with="S4 (no SaaS)" if service else "P-AI-APP")


def stress_table(price=None, inference_cost=None, other_cost=None, multipliers=(0.5, 1.5, 2.0), ledger_ids=None):
    """RT-AI-14: margin per task with the provider price at x0.5, x1.5 and x2.0."""
    m = need("tabla", ledger_ids, price=price, inference_cost=inference_cost, other_cost=other_cost)
    if m:
        return m
    rows = {f"x{mu}": {"cost": inference_cost * mu + other_cost,
                       "margin": (price - inference_cost * mu - other_cost) / price} for mu in multipliers}
    t3 = rows.get(f"x{AI_T3}", {}).get("margin")
    w = [f"Margen < 0 con precio del proveedor x{AI_T3}: riesgo alto; KO de G3 si no hay fallback probado (T3)"] \
        if t3 is not None and t3 < 0 else []
    return res(rows, "tabla", w, ledger_ids, t3_triggered=bool(w))


def evaluate_thresholds(price=None, c_task_p90=None, mean_margin_with_humans=None, is_ai_product=False,
                        margin_at_x2=None, has_tested_fallback=None, main_provider_token_share=None,
                        human_share_of_cogs=None, acr_sample_n=None, blind_qa=None, passk_reported_k=None,
                        top10_share_ai_cost=None, seat_p95_cost=None, seat_price=None, ledger_ids=None):
    """AI_T1..AI_T9 with their CEST connections. Unknown inputs leave the threshold 'unknown'."""
    out = {}

    def put(tid, status, link, detail=""):
        out[tid] = {"status": status, "link": link, "detail": detail}

    put("T1", "unknown" if price is None or c_task_p90 is None else ("fail" if price < c_task_p90 else "pass"),
        "G2", f"precio {price} vs C_task p90 {c_task_p90}")
    put("T2", "unknown" if mean_margin_with_humans is None else
        ("alert" if is_ai_product and mean_margin_with_humans < AI_T2 else "pass"), "M11, M14 (PRD-019, PRD-021)")
    if margin_at_x2 is None:
        put("T3", "unknown", "M11, G3 (AI-012)")
    else:
        status = "pass" if margin_at_x2 >= 0 else ("fail" if has_tested_fallback is False else "alert")
        put("T3", status, "M11, G3 (AI-012)", "fail = KO de G3 (sin fallback probado)")
    put("T4", "unknown" if main_provider_token_share is None else
        ("alert" if main_provider_token_share > AI_T4 and not has_tested_fallback else "pass"), "M10")
    put("T5", "unknown" if human_share_of_cogs is None else ("route_service" if human_share_of_cogs > AI_T5 else "pass"),
        "M1, M14")
    put("T6", "unknown" if acr_sample_n is None else
        ("low_confidence" if acr_sample_n < AI_T6 or not blind_qa else "pass"), "Ledger")
    put("T7", "low_confidence" if passk_reported_k is None or passk_reported_k < AI_T7 else "pass", "M10",
        "usar s = 1,37")
    put("T8", "unknown" if top10_share_ai_cost is None else
        ("alert" if top10_share_ai_cost > AI_T8 else "pass"), "M11", "exigir topes de coste")
    put("T9", "unknown" if seat_p95_cost is None or not seat_price else
        ("alert" if seat_p95_cost > AI_T9 * seat_price else "pass"), "M7", "repricing o limites")
    return res(out, "umbrales", [], ledger_ids)


# ---------------------------------------------------------------- RT-AI-13 red flags

RED_FLAGS = {
    1: ("Margen calculado con inferencia media o p50, sin p90/p95", "AI-022"),
    2: ("Precio por tarea u outcome bajo el coste p90", "T1"),
    3: ("Revision humana no presupuestada o estimada por intuicion", "AI-029"),
    4: ("Reintentos supuestos independientes", "AI-027"),
    5: ("Un solo proveedor sin fallback o margen que no resiste x2", "AI-012, AI-015"),
    6: ("'El coste de inferencia caera 10x al anio' en el plan de margenes", "AI-019..AI-021"),
    7: ("Autonomia o resolucion de un vendor usada como propia", "AI-032..AI-034"),
    8: ("Definicion de outcome ambigua o no auditable", "AI-043"),
    9: ("Sin presupuesto de evals, prompts ni migraciones", "AI-015"),
    10: ("Tarifa plana o seat sin limites ni simulacion de clientes intensivos", "6f.4"),
    11: ("Coste de herramientas ignorado (10-14 USD por 1.000 busquedas)", "AI-007, AI-011, AI-014"),
    12: ("Moat de datos sin demostracion", "6f.4"),
    13: ("Self-hosting justificado al 100 % de utilizacion o sin personal", "AI-045"),
    14: ("Comparacion de coste sin linea base simple", "AI-023"),
    15: ("Recargos de residencia o region ignorados en clientes regulados", "AI-006, AI-009"),
    16: ("Productividad de copiloto (+14 %) presentada como sustitucion autonoma", "AI-028"),
}


def red_flags(facts: dict | None = None, ledger_ids=None):
    """Detect the 16 red flags from structured facts extracted to the ledger (booleans / numbers).

    Keys: margin_basis ('mean'|'p50'|'p90'...), price, c_task_p90, human_review_budgeted, review_time_source
    ('measured'|'intuition'), retries_assumed_independent, single_provider, has_fallback, margin_at_x2,
    plan_assumes_inference_deflation, uses_vendor_autonomy_figures, outcome_definition_auditable,
    evals_budget, flat_or_seat_without_limits, tool_costs_included, data_moat_claimed, data_moat_demonstrated,
    self_hosting_utilisation, self_hosting_staff_included, has_simple_baseline, regulated_customers,
    residency_surcharge_included, copilot_gain_as_autonomy."""
    m = need("lista", ledger_ids, facts=facts)
    if m:
        return m
    f, hit = facts, []
    if f.get("margin_basis") in ("mean", "p50", "average"):
        hit.append(1)
    if f.get("price") is not None and f.get("c_task_p90") is not None and f["price"] < f["c_task_p90"]:
        hit.append(2)
    if f.get("human_review_budgeted") is False or f.get("review_time_source") == "intuition":
        hit.append(3)
    if f.get("retries_assumed_independent"):
        hit.append(4)
    if (f.get("single_provider") and not f.get("has_fallback")) or (f.get("margin_at_x2") is not None and f["margin_at_x2"] < 0):
        hit.append(5)
    if f.get("plan_assumes_inference_deflation"):
        hit.append(6)
    if f.get("uses_vendor_autonomy_figures"):
        hit.append(7)
    if f.get("outcome_pricing") and not f.get("outcome_definition_auditable"):
        hit.append(8)
    if f.get("evals_budget") is False:
        hit.append(9)
    if f.get("flat_or_seat_without_limits"):
        hit.append(10)
    if f.get("tool_costs_included") is False:
        hit.append(11)
    if f.get("data_moat_claimed") and not f.get("data_moat_demonstrated"):
        hit.append(12)
    if f.get("self_hosting_utilisation") is not None and (f["self_hosting_utilisation"] >= 0.999
                                                          or f.get("self_hosting_staff_included") is False):
        hit.append(13)
    if f.get("has_simple_baseline") is False:
        hit.append(14)
    if f.get("regulated_customers") and f.get("residency_surcharge_included") is False:
        hit.append(15)
    if f.get("copilot_gain_as_autonomy"):
        hit.append(16)
    flags = [{"id": i, "flag": RED_FLAGS[i][0], "evidence": RED_FLAGS[i][1]} for i in hit]
    return res(flags, "lista", [], ledger_ids, flag_ids=hit)


# ---------------------------------------------------------------- RT-AI-15 self-hosting

def self_hosting_breakeven(gpu_cost_h=None, tokens_per_s=None, utilisation=None, staff_cost_m=0.0,
                           gpus=1, api_price_per_mtok=None, ledger_ids=None):
    """Effective self-hosted cost per MTok = (GPU cost / U + staff) / tokens served; never at U = 1 without staff."""
    m = need("USD/MTok", ledger_ids, gpu_cost_h=gpu_cost_h, tokens_per_s=tokens_per_s, utilisation=utilisation)
    if m:
        return m
    w = []
    if utilisation >= 0.999 or not staff_cost_m:
        w.append("Red flag 13: self-hosting calculado al 100 % de utilizacion o sin personal")
    hours_m = 730.0
    tokens_m = tokens_per_s * 3600 * hours_m * utilisation * gpus
    cost_m = gpu_cost_h * hours_m * gpus + staff_cost_m
    per_mtok = cost_m / (tokens_m / 1e6) if tokens_m else None
    extra = {}
    if api_price_per_mtok and per_mtok:
        extra["cheaper_than_api"] = per_mtok < api_price_per_mtok
        extra["breakeven_tokens_per_s_at_full_util"] = gpu_cost_h / (api_price_per_mtok / 1e6) / 3600
    return res(per_mtok, "USD/MTok", w, ledger_ids, **extra)


PUBLIC = ["price_card", "attempt_cost", "pass_k", "success_within", "beta_from_pass", "human_cost",
          "fixed_cost_per_task", "simulate_tasks", "min_sample_size", "meter_viability", "outcome_revenue",
          "route_archetype", "stress_table", "evaluate_thresholds", "red_flags", "self_hosting_breakeven"]

if __name__ == "__main__":
    cli(globals(), PUBLIC)
