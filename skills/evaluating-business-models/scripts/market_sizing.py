"""Bottom-up market sizing M2.1-M2.10 (6g.1) and demand-evidence helpers (6g.3). Stdlib only.

TAM = n_accounts x p_problem x ACV_low x purchases_per_year  (each factor a ledger entry)
SAM = TAM restricted by channel, language, regulation and integration (share factors)
SOM = min(SAM x capture_rate_observed, sales_capacity); capacity from reps or founder hours.
Levels 1-2 of demand evidence only feed p_problem; capture comes from the portfolio's own observed
conversion (with its n). Top-down "X % of a Y-billion market" is refused.

Usage: python market_sizing.py size '<json kwargs>'  |  capacity '<json>'  |  demand_summary '<json>'
"""
from __future__ import annotations

from _common import check_domain, cli, need, res


def sales_capacity(reps=None, productive_months=None, closes_per_rep_month=None, ramp_months=0.0,
                   founder_sales_hours_week=None, hours_per_close=None, weeks=52, acv=None, ledger_ids=None):
    """Annual deals the team can close: reps x (months after ramp) x closes/month, or founder-led
    weekly sales hours / hours per close. Returned in deals and, with ACV, in money."""
    dom = check_domain("acuerdos/anio", ledger_ids, reps=(reps, "nonneg"), productive_months=(productive_months, "nonneg"),
                       closes_per_rep_month=(closes_per_rep_month, "nonneg"), ramp_months=(ramp_months, "nonneg"),
                       founder_sales_hours_week=(founder_sales_hours_week, "nonneg"), hours_per_close=(hours_per_close, "pos"))
    if dom:
        return dom
    if reps is not None:
        m = need("acuerdos/anio", ledger_ids, productive_months=productive_months,
                 closes_per_rep_month=closes_per_rep_month)
        if m:
            return m
        deals = reps * max(0.0, productive_months - ramp_months) * closes_per_rep_month
        mode = "reps"
    else:
        m = need("acuerdos/anio", ledger_ids, founder_sales_hours_week=founder_sales_hours_week,
                 hours_per_close=hours_per_close)
        if m:
            return m
        deals = founder_sales_hours_week * weeks / hours_per_close
        mode = "founder_led"
    return res(deals, "acuerdos/anio", [], ledger_ids, mode=mode,
               money=deals * acv if acv is not None else None)


def size(n_accounts=None, p_problem=None, acv_low=None, purchases_per_year=1.0, sam_share=None,
         capture_rate_observed=None, capture_n=None, capacity_deals=None, acv_for_som=None,
         top_down_share_of_market=None, analyst_headline=None, ledger_ids=None):
    """M2.7-M2.8. Refuses top-down shares (anti-error rule 1). SOM never comes from the founder plan."""
    if top_down_share_of_market is not None:
        return res(None, "moneda/anio", ["Prohibido 'X % de un mercado de Y': construir el producto de factores (regla 1)"],
                   ledger_ids, refused=True)
    m = need("moneda/anio", ledger_ids, n_accounts=n_accounts, p_problem=p_problem, acv_low=acv_low) or \
        check_domain("moneda/anio", ledger_ids, n_accounts=(n_accounts, "nonneg"), p_problem=(p_problem, "prob"),
                     acv_low=(acv_low, "nonneg"), purchases_per_year=(purchases_per_year, "nonneg"),
                     sam_share=(sam_share, "prob"), capture_rate_observed=(capture_rate_observed, "prob"),
                     capacity_deals=(capacity_deals, "nonneg"))
    if m:
        return m
    w = []
    tam = n_accounts * p_problem * acv_low * purchases_per_year
    sam = tam * sam_share if sam_share is not None else None
    if sam_share is None:
        w.append("SAM sin restricciones de canal/idioma/regulacion declaradas: SAM = unknown")
    som = None
    if sam is not None and capture_rate_observed is not None:
        som_demand = sam * capture_rate_observed
        cap_money = capacity_deals * (acv_for_som or acv_low) if capacity_deals is not None else None
        som = min(som_demand, cap_money) if cap_money is not None else None
        if cap_money is None:
            w.append("Sin capacidad de venta: el SOM no puede limitarse por capacidad (unknown)")
        if capture_n is not None and capture_n < 5:
            w.append(f"Tasa de captura con n = {capture_n}: muy incierta")
    elif capture_rate_observed is None:
        w.append("Sin conversion observada en la propia cartera: SOM unknown (los niveles 1-2 no alimentan la captura)")
    if analyst_headline is not None:
        w.append("Cifra de analista sin definicion: estimate de calidad C; no sostiene M2 >= 3 (regla 4)")
    return res(tam, "moneda/anio", w, ledger_ids, tam=tam, sam=sam, som=som,
               capacity_constraint=som is not None and capacity_deals is not None
               and som < (sam or 0) * (capture_rate_observed or 0))


def outside_view(som_year3=None, survival_rate_3y=None, based_on_founder_projection=False, ledger_ids=None):
    """M2.9: compare SOM to country survival base rates and Cassar's optimism bias."""
    m = need("texto", ledger_ids, som_year3=som_year3)
    if m:
        return m
    w = []
    risk = "high" if based_on_founder_projection else "normal"
    if survival_rate_3y is None:
        w.append("Sin tasa de supervivencia del pais/sector: outside view incompleta")
    return res(risk, "optimism_risk", w, ledger_ids, survival_rate_3y=survival_rate_3y,
               expected_som_survival_weighted=som_year3 * survival_rate_3y if survival_rate_3y else None)


DEMAND_LEVELS = {0: "Opinion del fundador", 1: "Interes verbal", 2: "Problema descrito con hechos pasados",
                 3: "Compromiso no monetario", 4: "LOI o piloto con presupuesto", 5: "Pago o contrato",
                 6: "Pago repetido en el mismo segmento"}


def demand_summary(accounts=None, ledger_ids=None):
    """Count accounts by max evidence level (per ACCOUNT, not per contact). An AI-built prototype never
    raises the level; a contract with free exit before first payment counts as 4; negative evidence kept."""
    m = need("tabla", ledger_ids, accounts=accounts)
    if m:
        return m
    by_level, w = {k: 0 for k in DEMAND_LEVELS}, []
    seen = {}
    for a in accounts:
        lvl = int(a.get("level", 0))
        if a.get("free_exit_before_first_payment") and lvl == 5:
            lvl = 4
            w.append(f"{a.get('id')}: contrato con salida gratuita antes del primer pago -> nivel 4")
        if a.get("based_on_ai_prototype_only") and lvl > 2:
            lvl = 2
            w.append(f"{a.get('id')}: un prototipo hecho con IA no sube de nivel")
        seen[a.get("id")] = max(seen.get(a.get("id"), 0), lvl)
    for lvl in seen.values():
        by_level[lvl] += 1
    negatives = sum(1 for a in accounts if a.get("negative"))
    return res(by_level, "cuentas por nivel", w, ledger_ids, max_level=max(seen.values()) if seen else 0,
               negative_evidence=negatives, feeds_p_problem_only=all(v <= 2 for v in seen.values()))


PUBLIC = ["size", "sales_capacity", "outside_view", "demand_summary"]

if __name__ == "__main__":
    cli(globals(), PUBLIC)
