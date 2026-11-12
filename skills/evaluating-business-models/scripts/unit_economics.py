"""Unit economics catalogue UE-01 ... UE-29 plus hybrid helpers H1, H3, H4 (stdlib only).

One formula = one function (RT-FIN-02). Every function returns {value, unit, warnings,
inputs_ledger_ids}; `value` is None when a P0 input is missing or the function refuses.
Rates are fractions; money is in the case currency; the period is in the name (_m, _a).
No benchmark is embedded here: thresholds and benchmarks arrive as inputs with ledger ids.

Usage: python unit_economics.py <function> '<json kwargs>'   (see _common.cli)
"""
from __future__ import annotations

import math
from typing import Sequence

from _common import check_domain, cli, isnum, missing, need, res

# ---------------------------------------------------------------- helpers

LOW_CHURN_FLOOR_M = 0.01      # RT-FIN-08: churn floor with < 12 months of history [P]
MIN_CUSTOMER_PERIODS = 30     # RF-ARQ-10 / RT-FIN-07: below this churn is "no estimable" [P]
MIN_CHURN_EVENTS = 3


def _monthly_rate(annual_rate: float) -> float:
    """Compound conversion of an annual discount rate to monthly (RT-FIN-09)."""
    return (1.0 + annual_rate) ** (1.0 / 12.0) - 1.0


def wilson_interval(events: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 1.0)
    p = events / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _binom_cdf(k: int, n: int, p: float) -> float:
    if p <= 0:
        return 1.0
    if p >= 1:
        return 0.0 if k < n else 1.0
    total, term = 0.0, (1 - p) ** n
    for i in range(0, k + 1):
        if i > 0:
            term *= (n - i + 1) / i * p / (1 - p)
        total += term
    return min(1.0, total)


def exact_interval(events: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Clopper-Pearson interval by bisection on the binomial CDF."""
    def solve(target, k, upper):
        lo, hi = 0.0, 1.0
        for _ in range(200):
            mid = (lo + hi) / 2
            val = _binom_cdf(k, n, mid)
            if (val > target) if upper else (val < target):
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    lower = 0.0 if events == 0 else solve(1 - alpha / 2, events - 1, upper=True)
    upper = 1.0 if events == n else solve(alpha / 2, events, upper=True)
    return (lower, upper)


# ---------------------------------------------------------------- UE-01 .. UE-05

def cac_blended(sm_spend=None, new_customers=None, ledger_ids=None):
    """UE-01: total S&M spend of the period / new customers of the period."""
    m = need("moneda/cliente", ledger_ids, sm_spend=sm_spend, new_customers=new_customers)
    if m:
        return m
    if new_customers <= 0:
        return res(None, "moneda/cliente", ["Sin clientes nuevos: CAC no definido (pre-revenue)"], ledger_ids)
    return res(sm_spend / new_customers, "moneda/cliente", [], ledger_ids)


def cac_paid(paid_spend=None, paid_customers=None, ledger_ids=None):
    """UE-02: paid-channel spend / customers attributed to paid channels."""
    m = need("moneda/cliente", ledger_ids, paid_spend=paid_spend, paid_customers=paid_customers)
    if m:
        return m
    if paid_customers <= 0:
        return res(None, "moneda/cliente", ["Sin clientes atribuidos a canales pagados"], ledger_ids)
    return res(paid_spend / paid_customers, "moneda/cliente",
               ["CAC pagado infravalora el coste real si hay referidos o venta del fundador: usar UE-03"],
               ledger_ids)


def cac_fully_loaded(new_customers=None, programs=0.0, sm_salaries_loaded=0.0, tools=0.0,
                     commissions=0.0, referral_fees=0.0, acquisition_credits=0.0,
                     founder_sales_hours=0.0, founder_market_rate_h=None, ledger_ids=None):
    """UE-03: all acquisition costs incl. founder selling time at market cost / new customers."""
    m = need("moneda/cliente", ledger_ids, new_customers=new_customers)
    if m:
        return m
    warnings = []
    founder_cost = 0.0
    if founder_sales_hours:
        if founder_market_rate_h is None:
            return missing("moneda/cliente", ["founder_market_rate_h"], ledger_ids)
        founder_cost = founder_sales_hours * founder_market_rate_h
    elif founder_market_rate_h is None:
        warnings.append("Horas comerciales del fundador no declaradas: si vende el fundador, el CAC esta infravalorado")
    if new_customers <= 0:
        return res(None, "moneda/cliente", ["Sin clientes nuevos"], ledger_ids)
    total = (programs + sm_salaries_loaded + tools + commissions + referral_fees
             + acquisition_credits + founder_cost)
    return res(total / new_customers, "moneda/cliente", warnings, ledger_ids,
               components={"founder_time_cost": founder_cost, "total_acquisition_cost": total})


def gross_margin_pct(revenue=None, cogs=None, pass_through_cost=None, principal=True,
                     support_or_delivery_in_opex=False, ledger_ids=None):
    """UE-04 with H1/RF-ARQ-06: reports gross (accounting) and net-of-pass-through margins.

    cogs must include hosting, inference, support, delivery labour, payment fees and per-customer
    licences. If support or delivery labour sits in opex (H2), a warning forces R4 recalculation.
    """
    m = need("fraccion", ledger_ids, revenue=revenue, cogs=cogs)
    if m:
        return m
    if revenue <= 0:
        return res(None, "fraccion", ["Ingresos <= 0: margen no definido"], ledger_ids)
    warnings = []
    if support_or_delivery_in_opex:
        warnings.append("H2/R4: soporte o entrega fuera del COGS; el margen bruto esta inflado. Recalcular con R4")
    gm = (revenue - cogs) / revenue
    extra = {}
    if pass_through_cost:
        net_rev = revenue - pass_through_cost
        own_cost = cogs - pass_through_cost
        extra["net_revenue"] = net_rev
        extra["gross_margin_net_of_pass_through"] = (net_rev - own_cost) / net_rev if net_rev > 0 else None
        extra["pass_through_share"] = pass_through_cost / revenue
        if pass_through_cost / revenue > 0.30:
            warnings.append("Pass-through > 30 % del ingreso: subtipo pass_through; comparar el margen neto (RF-ARQ-06)")
        if not principal:
            warnings.append("Agente (no controla el bien): contablemente el ingreso es neto (ASC 606-10-55-36..40)")
    return res(gm, "fraccion", warnings, ledger_ids, **extra)


def contribution_margin(revenue=None, cogs=None, variable_costs=0.0, ledger_ids=None):
    """UE-05: revenue - COGS - variable selling/servicing costs (also returned as % of revenue)."""
    m = need("moneda", ledger_ids, revenue=revenue, cogs=cogs)
    if m:
        return m
    cm = revenue - cogs - variable_costs
    pct = cm / revenue if revenue else None
    return res(cm, "moneda", [], ledger_ids, pct=pct)


# ---------------------------------------------------------------- UE-06 .. UE-11

def arpa_m(mrr=None, avg_active_accounts=None, ledger_ids=None):
    """UE-06: MRR / average active accounts."""
    m = need("moneda/cuenta/mes", ledger_ids, mrr=mrr, avg_active_accounts=avg_active_accounts)
    if m:
        return m
    if avg_active_accounts <= 0:
        return res(None, "moneda/cuenta/mes", ["Sin cuentas activas"], ledger_ids)
    return res(mrr / avg_active_accounts, "moneda/cuenta/mes", [], ledger_ids)


def churn_logo(churned=None, customers_start=None, periods=1, method="wilson", ledger_ids=None):
    """UE-07: logo churn per period with a 95 % interval (Wilson by default, 'exact' optional).

    'No estimable' (value None) with < 30 customer-periods or < 3 churn events (RT-FIN-07);
    the interval is still returned so G2b can test both bounds.
    """
    m = need("fraccion/periodo", ledger_ids, churned=churned, customers_start=customers_start) or \
        check_domain("fraccion/periodo", ledger_ids, churned=(churned, "nonneg"),
                     customers_start=(customers_start, "nonneg"), periods=(periods, "pos"))
    if m:
        return m
    exposure = int(customers_start * periods)
    if churned > exposure:
        return res(None, "fraccion/periodo", ["Mas bajas que cliente-periodos expuestos: dato incoherente"], ledger_ids)
    if exposure <= 0:
        return res(None, "fraccion/periodo", ["Sin exposicion"], ledger_ids)
    interval = (exact_interval if method == "exact" else wilson_interval)(int(churned), exposure)
    point = churned / exposure
    if exposure < MIN_CUSTOMER_PERIODS or churned < MIN_CHURN_EVENTS:
        return res(None, "fraccion/periodo",
                   [f"Churn no estimable: {exposure} cliente-periodos y {churned} bajas "
                    f"(minimo {MIN_CUSTOMER_PERIODS} y {MIN_CHURN_EVENTS}); usar el intervalo"],
                   ledger_ids, point_estimate=point, interval=list(interval), method=method,
                   estimable=False)
    return res(point, "fraccion/periodo", [], ledger_ids, interval=list(interval), method=method,
               estimable=True)


def churn_revenue_gross(mrr_lost_churn=None, mrr_contraction=0.0, mrr_start=None, ledger_ids=None):
    """UE-08: (MRR lost to churn + contraction) / starting MRR."""
    m = need("fraccion/periodo", ledger_ids, mrr_lost_churn=mrr_lost_churn, mrr_start=mrr_start)
    if m:
        return m
    return res((mrr_lost_churn + mrr_contraction) / mrr_start, "fraccion/periodo", [], ledger_ids)


def churn_m_to_a(churn_m=None, ledger_ids=None):
    """UE-09: annual = 1 - (1 - m)^12 (compound, never linear)."""
    m = need("fraccion/anio", ledger_ids, churn_m=churn_m) or \
        check_domain("fraccion/anio", ledger_ids, churn_m=(churn_m, "rate"))
    return m or res(1 - (1 - churn_m) ** 12, "fraccion/anio", [], ledger_ids)


def churn_a_to_m(churn_a=None, ledger_ids=None):
    """UE-09: monthly = 1 - (1 - a)^(1/12)."""
    m = need("fraccion/mes", ledger_ids, churn_a=churn_a) or \
        check_domain("fraccion/mes", ledger_ids, churn_a=(churn_a, "rate"))
    return m or res(1 - (1 - churn_a) ** (1 / 12), "fraccion/mes", [], ledger_ids)


def nrr(arr_start=None, expansion=0.0, contraction=0.0, churn=0.0, months_history=None,
        archetype=None, ledger_ids=None):
    """UE-10: starting-cohort NRR."""
    m = need("fraccion", ledger_ids, arr_start=arr_start)
    if m:
        return m
    warnings = _recurring_domain_warnings(months_history, archetype)
    return res((arr_start + expansion - contraction - churn) / arr_start, "fraccion", warnings, ledger_ids)


def grr(arr_start=None, contraction=0.0, churn=0.0, months_history=None, archetype=None, ledger_ids=None):
    """UE-11: GRR, capped at 1."""
    m = need("fraccion", ledger_ids, arr_start=arr_start)
    if m:
        return m
    warnings = _recurring_domain_warnings(months_history, archetype)
    return res(min(1.0, (arr_start - contraction - churn) / arr_start), "fraccion", warnings, ledger_ids)


def _recurring_domain_warnings(months_history, archetype):
    w = []
    if months_history is not None and months_history < 12:
        w.append("NRR/GRR con < 12 meses de historia: no comparable con benchmarks anuales")
    if archetype in ("S1", "S2", "S3"):
        w.append("NRR/GRR fuera de dominio en servicios por proyecto u horas (RF-ARQ-10)")
    return w


# ---------------------------------------------------------------- LTV family UE-12 .. UE-17

def ltv_simple(arpa_m=None, margin=None, churn_m=None, months_history=None, ledger_ids=None):
    """UE-12: m / c. Screening only: explodes with low churn and short history."""
    m = need("moneda/cliente", ledger_ids, arpa_m=arpa_m, margin=margin, churn_m=churn_m) or \
        check_domain("moneda/cliente", ledger_ids, arpa_m=(arpa_m, "nonneg"), margin=(margin, "num"),
                     churn_m=(churn_m, "rate"))
    if m:
        return m
    if churn_m <= 0:
        return res(None, "moneda/cliente", ["Churn 0: LTV simple infinito; usar ltv_capped"], ledger_ids)
    w = ["Solo cribado: usar ltv_capped (UE-14) como valor por defecto"]
    if churn_m < 0.01:
        w.append("Churn < 1 %/mes sin cota: LTV simple sobreestimado")
    if months_history is not None and months_history < 12:
        w.append("< 12 meses de historia: churn poco fiable")
    return res(arpa_m * margin / churn_m, "moneda/cliente", w, ledger_ids)


def ltv_discounted(m=None, churn_m=None, annual_rate=None, ledger_ids=None):
    """UE-13: m*r / (1 + i - r) with r = 1 - c and i the monthly rate (Gupta et al. form)."""
    mi = need("moneda/cliente", ledger_ids, m=m, churn_m=churn_m, annual_rate=annual_rate) or \
        check_domain("moneda/cliente", ledger_ids, m=(m, "num"), churn_m=(churn_m, "rate"),
                     annual_rate=(annual_rate, "nonneg"))
    if mi:
        return mi
    i = _monthly_rate(annual_rate)
    r = 1 - churn_m
    if 1 + i - r <= 0:
        return res(None, "moneda/cliente", ["Churn 0 y descuento 0: LTV infinito; usar ltv_capped con horizonte"],
                   ledger_ids)
    return res(m * r / (1 + i - r), "moneda/cliente",
               ["Supone retencion constante e infinita; preferir ltv_capped"], ledger_ids, monthly_rate=i)


def ltv_capped(m=None, churn_m=None, horizon_m=60, annual_rate=0.0, months_history=None,
               margin_basis="contribution", ledger_ids=None):
    """UE-14 (default LTV): sum_{t=1..H} m*r^(t-1)/(1+i)^t, m on contribution margin.

    RT-FIN-08: with < 12 months of history the churn is floored at 1 %/month.
    """
    mi = need("moneda/cliente", ledger_ids, m=m, churn_m=churn_m) or \
        check_domain("moneda/cliente", ledger_ids, m=(m, "num"), churn_m=(churn_m, "rate"),
                     horizon_m=(horizon_m, "pos"), annual_rate=(annual_rate, "nonneg"))
    if mi:
        return mi
    warnings = []
    c = churn_m
    if months_history is not None and months_history < 12 and c < LOW_CHURN_FLOOR_M:
        warnings.append(f"Churn {c} con < 12 meses de historia: se usa el suelo {LOW_CHURN_FLOOR_M} (RT-FIN-08)")
        c = LOW_CHURN_FLOOR_M
    if margin_basis != "contribution":
        warnings.append("Variante etiquetada: LTV sobre margen bruto (no es el valor por defecto)")
    i = _monthly_rate(annual_rate) if annual_rate else 0.0
    r = 1 - c
    total = sum(m * r ** (t - 1) / (1 + i) ** t for t in range(1, int(horizon_m) + 1))
    return res(total, "moneda/cliente", warnings, ledger_ids, churn_used=c, horizon_m=horizon_m,
               margin_basis=margin_basis)


def ltv_cohort_empirical(cohort_margin_by_period: Sequence[float] | None = None,
                         customers_acquired=None, annual_rate=0.0, ledger_ids=None):
    """UE-15: discounted observed cohort margin per acquired customer (monthly periods)."""
    m = need("moneda/cliente", ledger_ids, cohort_margin_by_period=cohort_margin_by_period,
             customers_acquired=customers_acquired)
    if m:
        return m
    w = []
    if customers_acquired < 30:
        w.append("Cohorte < 30 clientes: LTV empirico inestable")
    i = _monthly_rate(annual_rate) if annual_rate else 0.0
    total = sum(v / customers_acquired / (1 + i) ** t for t, v in enumerate(cohort_margin_by_period, start=1))
    return res(total, "moneda/cliente", w, ledger_ids)


def sbg_survival(alpha=None, beta=None, periods=12, ledger_ids=None):
    """UE-16: shifted-beta-geometric survival S(1..t) (Fader & Hardie)."""
    m = need("fraccion", ledger_ids, alpha=alpha, beta=beta)
    if m:
        return m
    s, out = 1.0, []
    for t in range(1, int(periods) + 1):
        s *= (beta + t - 1) / (alpha + beta + t - 1)
        out.append(s)
    return res(out, "fraccion", [], ledger_ids, p_churn_t1=alpha / (alpha + beta))


def sbg_retention(alpha=None, beta=None, periods=12, ledger_ids=None):
    """UE-16: period retention r_t = (beta + t - 1) / (alpha + beta + t - 1)."""
    m = need("fraccion", ledger_ids, alpha=alpha, beta=beta)
    if m:
        return m
    return res([(beta + t - 1) / (alpha + beta + t - 1) for t in range(1, int(periods) + 1)],
               "fraccion", [], ledger_ids)


def _sbg_loglik(a, b, alive):
    n0 = alive[0]
    ll, p_t, s_t = 0.0, a / (a + b), 1.0
    for t in range(1, len(alive)):
        if t > 1:
            p_t *= (b + t - 2) / (a + b + t - 1)
        lost = alive[t - 1] - alive[t]
        if lost > 0:
            ll += lost * math.log(max(p_t, 1e-300))
        s_t -= p_t
    ll += alive[-1] * math.log(max(s_t, 1e-300))
    return ll if n0 > 0 else -math.inf


def sbg_fit(alive: Sequence[int] | None = None, ledger_ids=None):
    """UE-16: maximum-likelihood alpha, beta from a survivor curve [n0, n1, ..., nT].

    Nelder-Mead on (log alpha, log beta). Warns when the cohort is small.
    """
    m = need("parametros", ledger_ids, alive=alive)
    if m:
        return m
    alive = [int(x) for x in alive]
    if len(alive) < 3 or alive[0] <= 0:
        return res(None, "parametros", ["Se necesitan >= 3 puntos de supervivencia"], ledger_ids)
    f = lambda v: -_sbg_loglik(math.exp(v[0]), math.exp(v[1]), alive)  # noqa: E731
    simplex = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
    vals = [f(p) for p in simplex]
    for _ in range(800):
        order = sorted(range(3), key=lambda k: vals[k])
        simplex = [simplex[k] for k in order]
        vals = [vals[k] for k in order]
        centroid = [(simplex[0][j] + simplex[1][j]) / 2 for j in range(2)]
        refl = [centroid[j] + (centroid[j] - simplex[2][j]) for j in range(2)]
        fr = f(refl)
        if fr < vals[0]:
            exp_ = [centroid[j] + 2 * (centroid[j] - simplex[2][j]) for j in range(2)]
            fe = f(exp_)
            simplex[2], vals[2] = (exp_, fe) if fe < fr else (refl, fr)
        elif fr < vals[1]:
            simplex[2], vals[2] = refl, fr
        else:
            con = [centroid[j] + 0.5 * (simplex[2][j] - centroid[j]) for j in range(2)]
            fc = f(con)
            if fc < vals[2]:
                simplex[2], vals[2] = con, fc
            else:
                for k in (1, 2):
                    simplex[k] = [simplex[0][j] + 0.5 * (simplex[k][j] - simplex[0][j]) for j in range(2)]
                    vals[k] = f(simplex[k])
        if abs(vals[2] - vals[0]) < 1e-10:
            break
    a, b = math.exp(simplex[0][0]), math.exp(simplex[0][1])
    w = [] if alive[0] >= 100 else ["Cohorte < 100 clientes: parametros sBG poco precisos"]
    return res({"alpha": a, "beta": b}, "parametros", w, ledger_ids, loglik=-vals[0])


def ltv_to_cac(ltv=None, cac=None, margin_basis="contribution", ledger_ids=None):
    """UE-17: secondary signal, NEVER a gate. Skok's 3x assumes GM-free LTV with GM >= 80 %."""
    m = need("ratio", ledger_ids, ltv=ltv, cac=cac)
    if m:
        return m
    if cac <= 0:
        return res(None, "ratio", ["CAC <= 0"], ledger_ids)
    w = ["Convencion, no compuerta: el 3x de Skok supone LTV sin ajustar por margen y GM >= 80 % (correccion 7)"]
    if margin_basis != "contribution":
        w.append("LTV y CAC deben usar la misma definicion de margen")
    return res(ltv / cac, "ratio", w, ledger_ids)


# ---------------------------------------------------------------- payback, burn, productivity

def cac_payback_gm(cac=None, arpa_m_new=None, margin=None, ledger_ids=None):
    """UE-18: CAC / (new-customer ARPA_m x margin), months."""
    m = need("meses", ledger_ids, cac=cac, arpa_m_new=arpa_m_new, margin=margin) or \
        check_domain("meses", ledger_ids, cac=(cac, "nonneg"), arpa_m_new=(arpa_m_new, "nonneg"), margin=(margin, "num"))
    if m:
        return m
    monthly = arpa_m_new * margin
    if monthly <= 0:
        return res(None, "meses", ["Margen mensual <= 0: el CAC nunca se recupera"], ledger_ids, never=True)
    return res(cac / monthly, "meses", [], ledger_ids)


def cac_payback_churn_adj(cac=None, m=None, churn_m=None, ledger_ids=None):
    """UE-19: n = ceil(ln(1 - CAC*c/m) / ln(1 - c)); 'never' (value None) if CAC*c/m >= 1."""
    mi = need("meses", ledger_ids, cac=cac, m=m, churn_m=churn_m) or \
        check_domain("meses", ledger_ids, cac=(cac, "nonneg"), m=(m, "num"), churn_m=(churn_m, "rate_lt1"))
    if mi:
        return mi
    if m <= 0:
        return res(None, "meses", ["Margen mensual <= 0: nunca"], ledger_ids, never=True)
    if churn_m <= 0:
        exact = cac / m
        return res(math.ceil(exact - 1e-12), "meses", [], ledger_ids, exact=exact, never=False)
    x = cac * churn_m / m
    if x >= 1:
        return res(None, "meses",
                   [f"CAC*c/m = {x:.3f} >= 1: el margen acumulado esperado nunca cubre el CAC ('nunca')"],
                   ledger_ids, never=True, ratio=x)
    exact = math.log(1 - x) / math.log(1 - churn_m)
    return res(math.ceil(exact - 1e-12), "meses", [], ledger_ids, exact=exact, never=False)


def burn_multiple(net_burn=None, net_new_arr=None, arr_start=None, arr_end=None, ledger_ids=None):
    """UE-20: net burn / net new ARR. 'N/A' if burn <= 0 or net new ARR <= 0 (RF-ARQ-10).

    Sacks: ~2x reasonable early, >= 3x needs extraordinary investment, ~5x terrible (FIN-003).
    """
    if net_new_arr is None and arr_start is not None and arr_end is not None:
        net_new_arr = arr_end - arr_start
    m = need("ratio", ledger_ids, net_burn=net_burn, net_new_arr=net_new_arr)
    if m:
        return m
    if net_burn <= 0 or net_new_arr <= 0:
        return res("N/A", "ratio", ["Burn <= 0 o ARR neto nuevo <= 0: burn multiple no aplica"], ledger_ids)
    return res(net_burn / net_new_arr, "ratio",
               ["Lente de capital riesgo; irrelevante para servicios o bootstrapped rentables"], ledger_ids)


def revenue_per_fte(revenue=None, avg_fte=None, ledger_ids=None):
    """UE-21: revenue / average FTE incl. owner and contractor equivalents."""
    m = need("moneda/FTE", ledger_ids, revenue=revenue, avg_fte=avg_fte)
    if m:
        return m
    return res(revenue / avg_fte, "moneda/FTE",
               ["Incluir dueno y contratistas como FTE equivalentes; no comparable entre paises sin ajuste salarial"],
               ledger_ids)


def arr_per_fte(arr=None, avg_fte=None, ledger_ids=None):
    """UE-21 variant for recurring businesses."""
    out = revenue_per_fte(arr, avg_fte, ledger_ids)
    out["unit"] = "ARR/FTE"
    return out


def utilisation(billable_hours=None, contract_hours=None, vacation_hours=0.0, holiday_hours=0.0,
                archetype=None, ledger_ids=None):
    """UE-22: billable / available hours (contract - vacation - holidays)."""
    m = need("fraccion", ledger_ids, billable_hours=billable_hours, contract_hours=contract_hours) or \
        check_domain("fraccion", ledger_ids, billable_hours=(billable_hours, "nonneg"),
                     contract_hours=(contract_hours, "pos"))
    if m:
        return m
    available = contract_hours - vacation_hours - holiday_hours
    if billable_hours > available > 0:
        return res(None, "fraccion", ["Horas facturables > horas disponibles: dato incoherente"], ledger_ids)
    if available <= 0:
        return res(None, "fraccion", ["Horas disponibles <= 0"], ledger_ids)
    w = []
    if archetype in ("S4", "P-SAAS-SS", "P-SAAS-SL", "P-USAGE", "P-INFRA"):
        w.append("Utilizacion fuera de su dominio principal en este arquetipo (RF-ARQ-10)")
    u = billable_hours / available
    if u > 0.85:
        w.append("Utilizacion > 85 %: sin holgura para crecer ni formar (regla R1)")
    return res(u, "fraccion", w, ledger_ids, available_hours=available)


def realisation(billed_collected=None, billable_hours=None, standard_rate=None, ledger_ids=None):
    """UE-23: billed and collected / (billable hours x standard rate)."""
    m = need("fraccion", ledger_ids, billed_collected=billed_collected, billable_hours=billable_hours,
             standard_rate=standard_rate)
    if m:
        return m
    return res(billed_collected / (billable_hours * standard_rate), "fraccion", [], ledger_ids)


def services_revenue(available_hours=None, utilisation=None, standard_rate=None, realisation=None,
                     ledger_ids=None):
    """UE-24: available hours x utilisation x standard rate x realisation (per FTE or team)."""
    m = need("moneda", ledger_ids, available_hours=available_hours, utilisation=utilisation,
             standard_rate=standard_rate, realisation=realisation) or \
        check_domain("moneda", ledger_ids, available_hours=(available_hours, "nonneg"),
                     utilisation=(utilisation, "rate"), standard_rate=(standard_rate, "nonneg"),
                     realisation=(realisation, "nonneg"))
    if m:
        return m
    return res(available_hours * utilisation * standard_rate * realisation, "moneda", [], ledger_ids)


def loaded_cost_per_hour(salary=None, expected_billable_hours=None, burden=0.0, benefits=0.0,
                         tools=0.0, overhead_share=0.0, ledger_ids=None):
    """UE-25: (salary + burden + benefits + tools + overhead share) / expected BILLABLE hours."""
    m = need("moneda/hora", ledger_ids, salary=salary, expected_billable_hours=expected_billable_hours)
    if m:
        return m
    if expected_billable_hours <= 0:
        return res(None, "moneda/hora", ["Horas facturables <= 0"], ledger_ids)
    total = salary + burden + benefits + tools + overhead_share
    return res(total / expected_billable_hours, "moneda/hora",
               ["Denominador = horas FACTURABLES, no horas pagadas"], ledger_ids, annual_loaded_cost=total)


def project_margin(revenue=None, actual_hours=None, loaded_cost_h=None, subcontract=0.0,
                   direct_infra_inference=0.0, ledger_ids=None):
    """UE-26: (revenue - hours x loaded cost - subcontract - direct infra/inference) / revenue."""
    m = need("fraccion", ledger_ids, revenue=revenue, actual_hours=actual_hours, loaded_cost_h=loaded_cost_h)
    if m:
        return m
    cost = actual_hours * loaded_cost_h + subcontract + direct_infra_inference
    return res((revenue - cost) / revenue, "fraccion", [], ledger_ids, total_cost=cost)


def cost_to_serve(customers=None, delivery_support=0.0, tools=0.0, infra=0.0, inference=0.0,
                  ledger_ids=None):
    """UE-27: (delivery and support + tools + infra + inference) / customers."""
    m = need("moneda/cliente", ledger_ids, customers=customers)
    if m:
        return m
    return res((delivery_support + tools + infra + inference) / customers, "moneda/cliente", [], ledger_ids)


def contract_npv(monthly_fee=None, cost_to_serve_m=None, months=None, annual_rate=0.0, onboarding=0.0,
                 cac=0.0, expected_sla_penalty_m=0.0, ledger_ids=None):
    """UE-28: -onboarding - CAC + sum_t (fee - cost_to_serve - expected SLA penalties)/(1+i)^t."""
    m = need("moneda", ledger_ids, monthly_fee=monthly_fee, cost_to_serve_m=cost_to_serve_m, months=months)
    if m:
        return m
    i = _monthly_rate(annual_rate) if annual_rate else 0.0
    pv = sum((monthly_fee - cost_to_serve_m - expected_sla_penalty_m) / (1 + i) ** t
             for t in range(1, int(months) + 1))
    return res(pv - onboarding - cac, "moneda", [], ledger_ids)


def cost_per_successful_outcome(total_cost=None, successful_runs=None, ledger_ids=None):
    """UE-29: total cost (inference + infra + supervision) / runs meeting the quality bar.

    For p50/p90 use ai_native_model.simulate_tasks (averages hide the right tail).
    """
    m = need("moneda/resultado", ledger_ids, total_cost=total_cost, successful_runs=successful_runs)
    if m:
        return m
    if successful_runs <= 0:
        return res(None, "moneda/resultado", ["Sin ejecuciones exitosas"], ledger_ids)
    return res(total_cost / successful_runs, "moneda/resultado",
               ["Media: reportar tambien p90 con ai_native_model (red flag 1)"], ledger_ids)


# ---------------------------------------------------------------- hybrid helpers (H1, H3, H4)

ARR_TYPES = {"subscription", "licence_access"}
MANAGED_TYPES = {"managed_service"}
BACKLOG_TYPES = {"hours_retainer", "dedicated_team"}


def resale_margin(gross_revenue=None, cost_of_resale=None, principal=True, ledger_ids=None):
    """H1: always compute net-of-pass-through revenue and show both margins."""
    m = need("moneda", ledger_ids, gross_revenue=gross_revenue, cost_of_resale=cost_of_resale)
    if m:
        return m
    net = gross_revenue - cost_of_resale
    accounting_revenue = gross_revenue if principal else net
    return res(net, "moneda", [] if principal else ["Agente: el ingreso contable es el neto"], ledger_ids,
               accounting_revenue=accounting_revenue,
               gross_margin_on_gross=net / gross_revenue if gross_revenue else None,
               economic_margin_on_net=1.0 if net > 0 and principal else None)


def split_recurring_revenue(items: Sequence[dict] | None = None, ledger_ids=None):
    """H3: ARR = only subscriptions / right-of-access licences with contractual renewal.

    items: [{"type": ..., "amount_annual": ..., "flagged_as_arr": bool}]
    Types: subscription, licence_access, managed_service, hours_retainer, dedicated_team,
    resale_recurring, project, usage. A retainer or managed MRR flagged as ARR is an error.
    """
    m = need("moneda/anio", ledger_ids, items=items)
    if m:
        return m
    arr = managed = backlog = resale = other = 0.0
    errors = []
    for it in items:
        t, amt = it.get("type"), float(it.get("amount_annual", 0))
        if t in ARR_TYPES:
            arr += amt
        elif t in MANAGED_TYPES:
            managed += amt
        elif t in BACKLOG_TYPES:
            backlog += amt
        elif t == "resale_recurring":
            resale += amt
        else:
            other += amt
        if it.get("flagged_as_arr") and t not in ARR_TYPES:
            errors.append(f"Error de clasificacion (H3/M6): '{t}' presentado como ARR")
    return res(arr, "moneda/anio", errors, ledger_ids, managed_recurring=managed,
               services_backlog=backlog, resale_recurring=resale, other=other,
               classification_errors=len(errors))


def consolidate_segments(segments: Sequence[dict] | None = None,
                         internal_transfers: Sequence[dict] | None = None, ledger_ids=None):
    """H4: eliminate internal transfers; revenue recognised once, in the segment billing the third party.

    segments: [{"id", "revenue", "costs"}]; internal_transfers: [{"from", "to", "amount"}]
    (amount booked as revenue in `from` and as cost in `to`).
    """
    m = need("moneda", ledger_ids, segments=segments)
    if m:
        return m
    internal = sum(float(t["amount"]) for t in (internal_transfers or []))
    rev = sum(float(s["revenue"]) for s in segments) - internal
    cost = sum(float(s["costs"]) for s in segments) - internal
    return res(rev, "moneda", [] if not internal else [f"Eliminadas transferencias internas: {internal}"],
               ledger_ids, consolidated_costs=cost, consolidated_profit=rev - cost)


PUBLIC = [
    "cac_blended", "cac_paid", "cac_fully_loaded", "gross_margin_pct", "contribution_margin", "arpa_m",
    "churn_logo", "churn_revenue_gross", "churn_m_to_a", "churn_a_to_m", "nrr", "grr", "ltv_simple",
    "ltv_discounted", "ltv_capped", "ltv_cohort_empirical", "sbg_survival", "sbg_retention", "sbg_fit",
    "ltv_to_cac", "cac_payback_gm", "cac_payback_churn_adj", "burn_multiple", "revenue_per_fte",
    "arr_per_fte", "utilisation", "realisation", "services_revenue", "loaded_cost_per_hour",
    "project_margin", "cost_to_serve", "contract_npv", "cost_per_successful_outcome", "resale_margin",
    "split_recurring_revenue", "consolidate_segments", "wilson_interval", "exact_interval",
]

if __name__ == "__main__":
    cli(globals(), PUBLIC)
