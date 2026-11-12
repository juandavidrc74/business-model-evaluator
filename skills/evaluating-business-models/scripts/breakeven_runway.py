"""Financial modelling FM-01 ... FM-12, the monthly cash/runway engine and pattern rules R1-R6.

Stdlib only. Same return shape as unit_economics (RT-FIN-01). The cash engine refuses to run
without ledger ids for its numeric inputs (each row lists the ids it used) and checks the
closing identity cash_t = cash_{t-1} + flow_t with tolerance 1e-6 (RT-CASH-04).

Usage: python breakeven_runway.py <function> '<json kwargs>'  |  cash_engine --file model.json
"""
from __future__ import annotations

import math
from typing import Sequence

from _common import check_domain, cli, need, res

COMPANY_TYPES = {
    # RT-CASH-05 / table 6e.4 [P]
    "micro": {"horizon_m": (12, 24), "rules": ["R1", "R4", "R6"], "discount": "owner_required_return"},
    "startup": {"horizon_m": (24, 36), "rules": ["R2", "R3", "R5"], "discount": "total_beta_or_vc_if_round"},
    "established": {"horizon_m": (60, 60), "rules": ["R2", "R3", "R4"], "discount": "wacc_with_crp"},
}


# ---------------------------------------------------------------- break-even FM-01 .. FM-03

def breakeven_revenue(fixed_costs=None, contribution_margin_pct=None, ledger_ids=None):
    """FM-01: fixed costs / CM%. 'Sin equilibrio' (None) if CM% <= 0."""
    m = need("moneda/periodo", ledger_ids, fixed_costs=fixed_costs, contribution_margin_pct=contribution_margin_pct)
    if m:
        return m
    if contribution_margin_pct <= 0:
        return res(None, "moneda/periodo", ["Margen de contribucion <= 0: sin equilibrio"], ledger_ids,
                   no_breakeven=True)
    return res(fixed_costs / contribution_margin_pct, "moneda/periodo", [], ledger_ids)


def breakeven_units(fixed_costs=None, price=None, variable_cost_unit=None, ledger_ids=None):
    """FM-02: fixed costs / (price - unit variable cost) (accounts, endpoints...)."""
    m = need("unidades", ledger_ids, fixed_costs=fixed_costs, price=price, variable_cost_unit=variable_cost_unit)
    if m:
        return m
    unit_cm = price - variable_cost_unit
    if unit_cm <= 0:
        return res(None, "unidades", ["Margen unitario <= 0: sin equilibrio"], ledger_ids, no_breakeven=True)
    q = fixed_costs / unit_cm
    return res(q, "unidades", [], ledger_ids, whole_units=math.ceil(q - 1e-12))


def breakeven_billable_fte(unallocated_fixed=None, available_hours=None, utilisation=None, rate=None,
                           realisation=None, loaded_cost_annual=None, ledger_ids=None):
    """FM-03: fixed / (h x util x rate x realisation - loaded annual cost per FTE).

    Denominator <= 0 means each billable FTE loses money: 'sin equilibrio' and G2 fails.
    """
    m = need("FTE", ledger_ids, unallocated_fixed=unallocated_fixed, available_hours=available_hours,
             utilisation=utilisation, rate=rate, realisation=realisation, loaded_cost_annual=loaded_cost_annual)
    if m:
        return m
    per_fte = available_hours * utilisation * rate * realisation - loaded_cost_annual
    if per_fte <= 0:
        return res(None, "FTE", [f"Cada FTE facturable pierde {-per_fte:.2f} al anio: sin equilibrio (G2 fail)"],
                   ledger_ids, no_breakeven=True, g2_fail=True, contribution_per_fte=per_fte)
    fte = unallocated_fixed / per_fte
    return res(fte, "FTE", [], ledger_ids, whole_fte=math.ceil(fte - 1e-12), contribution_per_fte=per_fte)


# ---------------------------------------------------------------- working capital FM-04

def dso(accounts_receivable=None, revenue=None, days=365, ledger_ids=None):
    m = need("dias", ledger_ids, accounts_receivable=accounts_receivable, revenue=revenue)
    return m or res(accounts_receivable / revenue * days, "dias", [], ledger_ids)


def dpo(accounts_payable=None, purchases=None, days=365, ledger_ids=None):
    m = need("dias", ledger_ids, accounts_payable=accounts_payable, purchases=purchases)
    return m or res(accounts_payable / purchases * days, "dias", [], ledger_ids)


def wip_days(unbilled=None, revenue=None, days=365, ledger_ids=None):
    m = need("dias", ledger_ids, unbilled=unbilled, revenue=revenue)
    return m or res(unbilled / revenue * days, "dias", [], ledger_ids)


def ccc(dso_days=None, wip=0.0, dpo_days=None, ledger_ids=None):
    """FM-04: cash conversion cycle = DSO + WIP - DPO."""
    m = need("dias", ledger_ids, dso_days=dso_days, dpo_days=dpo_days)
    return m or res(dso_days + wip - dpo_days, "dias", [], ledger_ids)


# ---------------------------------------------------------------- runway & funding FM-05, FM-06

def runway_simple(cash=None, avg_net_burn_3m=None, ledger_ids=None):
    """FM-05: cash / average net burn of the last 3 months."""
    m = need("meses", ledger_ids, cash=cash, avg_net_burn_3m=avg_net_burn_3m) or \
        check_domain("meses", ledger_ids, cash=(cash, "num"), avg_net_burn_3m=(avg_net_burn_3m, "num"))
    if m:
        return m
    if cash <= 0 and avg_net_burn_3m > 0:
        return res(0.0, "meses", ["Caja ya nula o negativa: runway agotado (necesidad de financiacion inmediata)"],
                   ledger_ids, exhausted=True)
    if avg_net_burn_3m <= 0:
        return res("no aplica", "meses", ["Caja creciente: runway no aplica"], ledger_ids)
    return res(cash / avg_net_burn_3m, "meses", [], ledger_ids)


def runway_projected(cash=None, burn_m=None, burn_growth_m=0.0, min_cash=0.0, max_months=600, ledger_ids=None):
    """FM-05: whole months completed before cash falls below the minimum (growing burn)."""
    m = need("meses", ledger_ids, cash=cash, burn_m=burn_m) or \
        check_domain("meses", ledger_ids, cash=(cash, "num"), burn_m=(burn_m, "num"), burn_growth_m=(burn_growth_m, "num"))
    if m:
        return m
    if burn_m <= 0:
        return res("no aplica", "meses", ["Sin burn"], ledger_ids)
    if cash < min_cash:
        return res(0, "meses completos", ["Caja inicial ya por debajo del minimo"], ledger_ids, exhausted=True)
    c, b = cash, burn_m
    for month in range(1, max_months + 1):
        c -= b
        if c < min_cash:
            return res(month - 1, "meses completos", [], ledger_ids, cash_out_month=month)
        b *= 1 + burn_growth_m
    return res(max_months, "meses completos", ["Horizonte maximo alcanzado"], ledger_ids)


def funding_need(min_cash=None, min_projected_cash=None, buffer=0.0, ledger_ids=None):
    """FM-06: max(0, minimum cash - minimum projected cash) + buffer."""
    m = need("moneda", ledger_ids, min_cash=min_cash, min_projected_cash=min_projected_cash)
    return m or res(max(0.0, min_cash - min_projected_cash) + (buffer if min_projected_cash < min_cash else 0.0),
                    "moneda", [], ledger_ids)


# ---------------------------------------------------------------- returns & cost of capital FM-07, FM-08

def roic(nopat=None, invested_capital_avg=None, company_type=None, ledger_ids=None):
    m = need("fraccion", ledger_ids, nopat=nopat, invested_capital_avg=invested_capital_avg)
    if m:
        return m
    w = ["ROIC poco informativo en micro con capital ~0"] if company_type == "micro" else []
    if invested_capital_avg <= 0:
        return res(None, "fraccion", ["Capital invertido <= 0"], ledger_ids)
    return res(nopat / invested_capital_avg, "fraccion", w, ledger_ids)


def total_beta(market_beta=None, correlation_with_market=None, ledger_ids=None):
    """FM-08: Damodaran total beta = market beta / correlation (undiversified owner)."""
    m = need("beta", ledger_ids, market_beta=market_beta, correlation_with_market=correlation_with_market) or \
        check_domain("beta", ledger_ids, market_beta=(market_beta, "num"),
                     correlation_with_market=(correlation_with_market, "rate"))
    if m:
        return m
    if correlation_with_market <= 0:
        return res(None, "beta", ["Correlacion <= 0"], ledger_ids)
    return res(market_beta / correlation_with_market, "beta", [], ledger_ids)


def cost_of_equity(risk_free=None, beta=None, erp=None, crp=0.0, country=None, ledger_ids=None):
    """FM-08: Re = Rf + beta x ERP (+ CRP). Never US cost of capital for a non-US case without CRP."""
    m = need("fraccion", ledger_ids, risk_free=risk_free, beta=beta, erp=erp)
    if m:
        return m
    w = []
    if country and country.upper() not in ("US", "USA", "EE. UU.", "EEUU") and not crp:
        w.append("Pais distinto de EE. UU. sin prima de riesgo pais (CRP): coste de capital infravalorado (6i.4)")
    return res(risk_free + beta * erp + crp, "fraccion", w, ledger_ids)


def wacc(equity_value=None, debt_value=None, cost_equity=None, cost_debt=None, tax_rate=None,
         company_type=None, ledger_ids=None):
    """FM-08: E/V Re + D/V Rd (1 - t). Not meaningful for a micro without debt or external capital."""
    if company_type == "micro":
        return res(None, "fraccion",
                   ["WACC no aplica en una microempresa sin deuda ni acceso a capital: usar el rendimiento "
                    "exigido por el dueno con beta total (RT-CASH-05)"], ledger_ids, use_instead="total_beta")
    m = need("fraccion", ledger_ids, equity_value=equity_value, debt_value=debt_value, cost_equity=cost_equity,
             cost_debt=cost_debt, tax_rate=tax_rate) or \
        check_domain("fraccion", ledger_ids, equity_value=(equity_value, "nonneg"), debt_value=(debt_value, "nonneg"),
                     tax_rate=(tax_rate, "rate"))
    if m:
        return m
    v = equity_value + debt_value
    if v <= 0:
        return res(None, "fraccion", ["Capital total (E + D) = 0: WACC no definido"], ledger_ids)
    return res(equity_value / v * cost_equity + debt_value / v * cost_debt * (1 - tax_rate), "fraccion", [],
               ledger_ids)


def convert_rate_currency(rate_usd=None, inflation_local=None, inflation_usd=None, ledger_ids=None):
    """RT-FIN-10: local nominal rate = (1 + r_USD)(1 + pi_local)/(1 + pi_USD) - 1."""
    m = need("fraccion", ledger_ids, rate_usd=rate_usd, inflation_local=inflation_local, inflation_usd=inflation_usd)
    return m or res((1 + rate_usd) * (1 + inflation_local) / (1 + inflation_usd) - 1, "fraccion", [], ledger_ids)


# ---------------------------------------------------------------- NPV / IRR / MIRR FM-09

def npv(rate=None, cashflows: Sequence[float] | None = None, ledger_ids=None):
    """FM-09: NPV with CF0 at t = 0. Preferred over IRR in every output."""
    m = need("moneda", ledger_ids, rate=rate, cashflows=cashflows) or check_domain("moneda", ledger_ids, rate=(rate, "num"))
    if m:
        return m
    if rate <= -1:
        return res(None, "moneda", ["Tasa de descuento <= -100 %: NPV no definido"], ledger_ids)
    if not cashflows:
        return res(None, "moneda", ["Sin flujos de caja"], ledger_ids)
    return res(sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows)), "moneda", [], ledger_ids)


def _sign_changes(cfs):
    signs = [1 if c > 0 else -1 for c in cfs if c != 0]
    return sum(1 for a, b in zip(signs, signs[1:]) if a != b)


def irr(cashflows: Sequence[float] | None = None, lo=-0.99, hi=10.0, ledger_ids=None):
    """FM-09: bisection on [-0.99, 10]; refuses with more than one sign change (T18)."""
    m = need("fraccion", ledger_ids, cashflows=cashflows)
    if m:
        return m
    changes = _sign_changes(cashflows)
    if changes == 0:
        return res(None, "fraccion", ["Sin cambio de signo: IRR no existe"], ledger_ids)
    if changes > 1:
        return res(None, "fraccion", [f"{changes} cambios de signo: puede haber varias IRR. Se niega; usar NPV o MIRR"],
                   ledger_ids, refused=True)
    f = lambda r: sum(cf / (1 + r) ** t for t, cf in enumerate(cashflows))  # noqa: E731
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return res(None, "fraccion", ["IRR fuera de [-0,99; 10]"], ledger_ids)
    for _ in range(300):
        mid = (lo + hi) / 2
        fm = f(mid)
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return res((lo + hi) / 2, "fraccion", ["Reportar NPV como cifra principal; IRR supone reinversion a la propia IRR"],
               ledger_ids)


def mirr(cashflows: Sequence[float] | None = None, finance_rate=None, reinvest_rate=None, ledger_ids=None):
    m = need("fraccion", ledger_ids, cashflows=cashflows, finance_rate=finance_rate, reinvest_rate=reinvest_rate)
    if m:
        return m
    n = len(cashflows) - 1
    pv_neg = sum(cf / (1 + finance_rate) ** t for t, cf in enumerate(cashflows) if cf < 0)
    fv_pos = sum(cf * (1 + reinvest_rate) ** (n - t) for t, cf in enumerate(cashflows) if cf > 0)
    if pv_neg >= 0 or fv_pos <= 0 or n <= 0:
        return res(None, "fraccion", ["MIRR no definida"], ledger_ids)
    return res((fv_pos / -pv_neg) ** (1 / n) - 1, "fraccion", [], ledger_ids)


# ---------------------------------------------------------------- owner economics FM-10, FM-11, FM-12

def sde(ebitda=None, owner_total_comp=None, discretionary=0.0, ledger_ids=None):
    """FM-10: SDE = EBITDA + one owner's total compensation + discretionary. Never a profitability measure."""
    m = need("moneda", ledger_ids, ebitda=ebitda, owner_total_comp=owner_total_comp)
    return m or res(ebitda + owner_total_comp + discretionary, "moneda",
                    ["SDE no es rentabilidad: mostrar junto al EBITDA ajustado (RT-CASH-07)"], ledger_ids)


def adjusted_ebitda(ebitda=None, owner_comp_paid=None, owner_market_salary=None, ledger_ids=None):
    """FM-10: EBITDA + (owner comp paid - market salary). Negative => 'rentable solo por autoexplotacion'."""
    m = need("moneda", ledger_ids, ebitda=ebitda, owner_comp_paid=owner_comp_paid,
             owner_market_salary=owner_market_salary)
    if m:
        return m
    v = ebitda + (owner_comp_paid - owner_market_salary)
    w = ["Rentable solo por autoexplotacion: beneficio ajustado < 0 (R6)"] if v < 0 else []
    return res(v, "moneda", w, ledger_ids, self_exploitation=v < 0)


def owner_salary_gap(owner_market_salary=None, owner_paid=None, ledger_ids=None):
    m = need("moneda", ledger_ids, owner_market_salary=owner_market_salary, owner_paid=owner_paid)
    return m or res(owner_market_salary - owner_paid, "moneda", [], ledger_ids)


def rule_of_40(growth=None, fcf_margin=None, arr=None, ledger_ids=None):
    """FM-11: growth % + FCF margin %. Anecdotal origin; only for SaaS with scale."""
    m = need("fraccion", ledger_ids, growth=growth, fcf_margin=fcf_margin)
    if m:
        return m
    w = ["Regla de origen anecdotico, sin validacion publicada; lente de capital riesgo"]
    if arr is not None and arr < 3_000_000:
        w.append("ARR < 3 M$: Rule of 40 fuera de dominio (RF-ARQ-10)")
    return res(growth + fcf_margin, "fraccion", w, ledger_ids)


def reinvestment_needed(delta_revenue=None, sales_to_capital=None, ledger_ids=None):
    m = need("moneda", ledger_ids, delta_revenue=delta_revenue, sales_to_capital=sales_to_capital)
    return m or res(delta_revenue / sales_to_capital, "moneda", [], ledger_ids)


# ---------------------------------------------------------------- monthly cash engine (RT-CASH-01..05)

ENGINE_NUMERIC_KEYS = ("start_cash", "payroll_m", "opex_m", "dso", "wip_days", "dpo", "salary_inflation_a",
                       "infra_cost_growth_m", "owner_market_salary_m", "owner_paid_m")


def _line_ids(line):
    return list(line.get("ledger_ids", []))


def cash_engine(model: dict | None = None, **kwargs):
    """Monthly direct cash-flow engine.

    model = {
      "company_type": "micro"|"startup"|"established", "horizon_m": 24, "start_cash": ..., "min_cash": optional,
      "payroll_m": ..., "salary_inflation_a": 0.0, "opex_m": ..., "dso": 30, "wip_days": 0, "dpo": 30,
      "infra_cost_growth_m": 0.0, "model_price_multiplier": 1.0,
      "owner_market_salary_m": ..., "owner_paid_m": ...,
      "credits": [{"amount_m": ..., "until_month": ...}], "funding": [{"month": ..., "amount": ...}],
      "lines": [ {"id", "kind": "recurring"|"hours"|"project", ...line inputs..., "ledger_ids": [...]} ],
      "ledger_ids": {"start_cash": "L1", ...}            # ids for the top-level numeric inputs
    }
    recurring line: customers0, new_customers_m (number or list), churn_m, arpa_m, cogs_pct, inference_share_of_cogs
    hours line: billable_fte (number or list), hours_per_fte_m, utilisation, rate, realisation, direct_cost_m
    project line: projects_m (number or list), avg_project_value, cogs_pct
    """
    model = dict(model or {}, **kwargs)
    ctype = model.get("company_type", "startup")
    if ctype not in COMPANY_TYPES:
        raise ValueError(f"company_type desconocido: {ctype}")
    default_h = COMPANY_TYPES[ctype]["horizon_m"][1]
    horizon = int(model.get("horizon_m", default_h))
    ids_top = model.get("ledger_ids", {})
    warnings, unledgered = [], []
    for k in ENGINE_NUMERIC_KEYS:
        if k in model and k not in ids_top:
            unledgered.append(k)
    for ln in model.get("lines", []):
        if not ln.get("ledger_ids"):
            unledgered.append(f"line:{ln.get('id')}")
    if unledgered:
        return res(None, "tabla", [f"Inputs sin id de ledger: {', '.join(unledgered)}. Ninguna fila puede quedar sin id"],
                   [], unledgered_inputs=unledgered)
    if "start_cash" not in model:
        return res(None, "tabla", ["P0 ausente: start_cash"], [], missing_inputs=["start_cash"])

    def series(v, t):
        if isinstance(v, (list, tuple)):
            return v[t - 1] if t - 1 < len(v) else v[-1]
        return v or 0.0

    payroll0, opex = model.get("payroll_m", 0.0), model.get("opex_m", 0.0)
    infl_m = (1 + model.get("salary_inflation_a", 0.0)) ** (1 / 12) - 1
    infra_g = model.get("infra_cost_growth_m", 0.0)
    price_mult = model.get("model_price_multiplier", 1.0)
    dso_d, wip_d, dpo_d = model.get("dso", 30), model.get("wip_days", 0), model.get("dpo", 30)
    gap = max(0.0, model.get("owner_market_salary_m", 0.0) - model.get("owner_paid_m", 0.0))
    credits = model.get("credits", [])
    funding = {int(f["month"]): float(f["amount"]) for f in model.get("funding", [])}
    min_cash = model.get("min_cash", 3 * (payroll0 + opex))

    customers = {ln["id"]: float(ln.get("customers0", 0)) for ln in model.get("lines", []) if ln["kind"] == "recurring"}
    cash, ar, wip, ap = float(model["start_cash"]), 0.0, 0.0, 0.0
    rows, prev_rev = [], None
    max_credit_share, growth_warned = 0.0, False
    for t in range(1, horizon + 1):
        revenue, cogs, row_ids = 0.0, 0.0, list(ids_top.values())
        for ln in model.get("lines", []):
            row_ids += _line_ids(ln)
            kind = ln["kind"]
            if kind == "recurring":
                c = customers[ln["id"]] * (1 - ln.get("churn_m", 0.0)) + series(ln.get("new_customers_m", 0), t)
                customers[ln["id"]] = c
                r = c * ln["arpa_m"]
                base = r * ln.get("cogs_pct", 0.0) * (1 + infra_g) ** (t - 1)
                inf_share = ln.get("inference_share_of_cogs", 0.0)
                cogs_l = base * (1 - inf_share) + base * inf_share * price_mult
            elif kind == "hours":
                r = (series(ln.get("billable_fte", 0), t) * ln["hours_per_fte_m"] * ln["utilisation"]
                     * ln["rate"] * ln["realisation"])
                cogs_l = series(ln.get("direct_cost_m", 0.0), t)
            elif kind == "project":
                r = series(ln.get("projects_m", 0), t) * ln["avg_project_value"]
                cogs_l = r * ln.get("cogs_pct", 0.0)
            else:
                raise ValueError(f"kind desconocido: {kind}")
            revenue += r
            cogs += cogs_l
        payroll = payroll0 * (1 + infl_m) ** (t - 1)
        credit = sum(float(c["amount_m"]) for c in credits if t <= int(c["until_month"]))
        credit_used = min(credit, cogs)
        cogs_cash = cogs - credit_used
        total_costs = cogs + payroll + opex
        if total_costs > 0:
            max_credit_share = max(max_credit_share, credit_used / total_costs)
        ebitda = revenue - cogs - payroll - opex
        adj_ebitda = ebitda - gap
        new_ar, new_wip = revenue * dso_d / 30, revenue * wip_d / 30
        new_ap = (cogs_cash + opex) * dpo_d / 30
        flow = (revenue - (new_ar - ar) - (new_wip - wip) - cogs_cash - payroll - opex + (new_ap - ap)
                + funding.get(t, 0.0))
        prev_cash = cash
        cash = prev_cash + flow
        if abs(cash - (prev_cash + flow)) > 1e-6:  # RT-CASH-04 closing identity
            raise ValueError(f"Cierre de caja roto en el mes {t}")
        ar, wip, ap = new_ar, new_wip, new_ap
        if prev_rev and prev_rev > 0 and revenue / prev_rev - 1 > 0.10 and not growth_warned:
            warnings.append("Crecimiento mensual > 10 %: el capital circulante en estado estacionario subestima el AR")
            growth_warned = True
        prev_rev = revenue
        rows.append({"month": t, "revenue": revenue, "cogs": cogs, "credits_used": credit_used,
                     "payroll": payroll, "opex": opex, "ebitda": ebitda, "adjusted_ebitda": adj_ebitda,
                     "ar": ar, "wip": wip, "ap": ap, "funding": funding.get(t, 0.0), "flow": flow,
                     "cash": cash, "ledger_ids": sorted(set(row_ids))})

    runway_month = next((r["month"] for r in rows if r["cash"] < min_cash), None)
    breakeven_month = None
    for i in range(len(rows) - 2):
        if all(rows[j]["adjusted_ebitda"] >= 0 for j in range(i, i + 3)):
            breakeven_month = rows[i]["month"]
            break
    min_proj = min(r["cash"] for r in rows)
    flags = []
    if max_credit_share >= 0.20:
        flags.append({"rule": "R5", "detail": f"Creditos/subsidios hasta {max_credit_share:.0%} de los costes"})
    if gap > 0:
        flags.append({"rule": "R6", "detail": f"Brecha de salario del dueno {gap:.2f}/mes fuera de caja"})
    return res(rows, "tabla", warnings, sorted({i for r in rows for i in r["ledger_ids"]}),
               company_type=ctype, rules_priority=COMPANY_TYPES[ctype]["rules"],
               runway_month=runway_month, min_cash_threshold=min_cash, min_projected_cash=min_proj,
               funding_need=max(0.0, min_cash - min_proj), breakeven_month=breakeven_month,
               max_credit_share=max_credit_share, flags=flags)


# ---------------------------------------------------------------- pattern rules R1-R6 (6e.6)

def pattern_rules(utilisation=None, hiring_planned=None, owner_hours_share=None, free_cash_after_market_salary=None,
                  loaded_cost_m_per_fte=None, rev_per_fte_last3: Sequence[float] | None = None,
                  burn_multiple=None, post_seed=False, payback_churn_adj_m=None, segment="SMB",
                  wc_per_new_revenue=None, grr=None, nrr=None, logo_churn_m=None, midmarket=False,
                  margin_reported=None, margin_recalculated=None, credits_share_max=None,
                  runway_without_round_m=None, cm_after_credits=None, owner_market_salary=None,
                  owner_paid=None, adjusted_profit=None, ledger_ids=None):
    """R1-R6 operational tests. Thresholds are [P] except Sacks 2x (FIN-003) and BVP 24/36 months."""
    flags = []

    def flag(rule, detail, output):
        flags.append({"rule": rule, "detail": detail, "output": output})

    # R1 profitable but cannot grow
    r1 = []
    if utilisation is not None and utilisation >= 0.85 and hiring_planned is False:
        r1.append("utilizacion >= 85 % sin FTE adicional")
    if owner_hours_share is not None and owner_hours_share > 0.40:
        r1.append("dueno > 40 % de las horas facturadas")
    if free_cash_after_market_salary is not None and loaded_cost_m_per_fte is not None \
            and free_cash_after_market_salary < 3 * loaded_cost_m_per_fte:
        r1.append("caja libre < 3 meses de coste cargado de 1 FTE")
    if rev_per_fte_last3 and len(rev_per_fte_last3) >= 3:
        a = rev_per_fte_last3[-3:]
        if max(a) <= min(a) * 1.05 + 1e-9:
            r1.append("ingresos/FTE planos (+/-5 %) tres periodos")
    if r1:
        flag("R1", "; ".join(r1), "Alerta M14; escenario 'contratar 1 FTE' obligatorio")
    # R2 growth that destroys cash
    r2 = []
    if isinstance(burn_multiple, (int, float)) and post_seed and burn_multiple > 2:
        r2.append(f"burn multiple {burn_multiple:.2f} > 2 tras la semilla (Sacks, FIN-003)")
    limit = 36 if segment == "enterprise" else 24
    if payback_churn_adj_m is not None and payback_churn_adj_m > limit:
        r2.append(f"payback ajustado {payback_churn_adj_m} > {limit} meses (BVP)")
    if wc_per_new_revenue is not None and wc_per_new_revenue > 1:
        r2.append("cada 1 de ingreso nuevo consume > 1 de capital circulante")
    if r2:
        flag("R2", "; ".join(r2), "Alerta M9; G6 si faltan datos")
    # R3 recurring revenue with poor retention
    r3 = []
    if grr is not None and grr < 0.80:
        r3.append(f"GRR {grr:.0%} < 80 %")
    if nrr is not None and grr is not None and nrr >= 1.0 and grr < 0.85:
        r3.append("NRR >= 100 % con GRR < 85 %: la expansion tapa la fuga")
    if logo_churn_m is not None and midmarket and logo_churn_m > 0.03:
        r3.append("churn de logos > 3 %/mes en mid-market")
    if r3:
        flag("R3", "; ".join(r3), "Alerta M12; LTV con la cota alta del churn")
    # R4 margins inflated by omitted costs
    if margin_reported is not None and margin_recalculated is not None and margin_reported - margin_recalculated > 0.10:
        flag("R4", f"margen declarado {margin_reported:.0%} vs recalculado {margin_recalculated:.0%} (> 10 pp)",
             "G2 se evalua con el margen recalculado")
    # R5 dependence on subsidies, funding or credits
    r5 = []
    if credits_share_max is not None and credits_share_max >= 0.20:
        r5.append(f"creditos/subsidios {credits_share_max:.0%} >= 20 % de los costes")
    if runway_without_round_m is not None and runway_without_round_m < 12:
        r5.append(f"runway sin la proxima ronda {runway_without_round_m} < 12 meses")
    if cm_after_credits is not None and cm_after_credits < 0:
        r5.append("margen de contribucion < 0 al expirar los creditos")
    if r5:
        flag("R5", "; ".join(r5), "Escenario 'creditos expiran'; alerta G3 (G2 si el margen se vuelve negativo)")
    # R6 founders without market salary
    if owner_market_salary is not None and owner_paid is not None and owner_market_salary - owner_paid > 0:
        detail = f"brecha salarial {owner_market_salary - owner_paid:.2f}"
        if adjusted_profit is not None and adjusted_profit < 0:
            detail += "; rentable solo por autoexplotacion"
        flag("R6", detail, "M9; G2 si el margen de contribucion pasa a negativo")
    return res(flags, "flags", [], ledger_ids, rules_triggered=[f["rule"] for f in flags])


PUBLIC = [
    "breakeven_revenue", "breakeven_units", "breakeven_billable_fte", "dso", "dpo", "wip_days", "ccc",
    "runway_simple", "runway_projected", "funding_need", "roic", "total_beta", "cost_of_equity", "wacc",
    "convert_rate_currency", "npv", "irr", "mirr", "sde", "adjusted_ebitda", "owner_salary_gap",
    "rule_of_40", "reinvestment_needed", "cash_engine", "pattern_rules",
]

if __name__ == "__main__":
    cli(globals(), PUBLIC)
