# Catálogo de fórmulas UE, FM y SA

> Leer para saber qué función de `scripts/` usar y dónde no aplica. Nunca calcular a mano lo que tiene función.
>
> Generado desde: secciones 6e.1, 6e.2 y 6e.7 del informe «Evaluación negocios tecnológicos ampliada» (texto propio con citas). No editar a mano: editar el informe y ejecutar `evals/harness/build_references.py`. Etiquetas: [D] documentado, [S] secundario, [M] marco/libro o conocimiento no verificado, [I] inferencia, [P] propuesta metodológica.

## 6e.1 Qué es convención y qué tiene base académica

Las métricas de unit economics de SaaS son **convenciones de practicantes**, no resultados empíricos. Lo único con base académica es el valor de cliente descontado con retención: Gupta, Lehmann & Stuart estiman que mejorar la retención un 1 % sube el valor del cliente un 3–7 %, frente a una elasticidad de ~1 al margen, aunque con solo cinco empresas de consumo e Internet y retención constante ([Columbia PDF](https://business.columbia.edu/sites/default/files-efs/pubfiles/534/Valuing_Customers--JMR_2003.pdf), FIN-004). El modelo **shifted-beta-geometric** de Fader & Hardie muestra por qué extrapolar el churn de los primeros meses infravalora la vida: con clientes heterogéneos, los más propensos a irse se van antes y la retención de la cohorte sube con su antigüedad ([Hardie](https://www.brucehardie.com/papers/021/)) [fórmulas M]. Skok advierte que en etapas tempranas el churn sale bajo porque los contratos aún no llegaron a renovación, y que la guía de payback < 12 meses es de 2011 y en enterprise lo normal son ~20 meses ([Skok](https://www.forentrepreneurs.com/saas-metrics-2-definitions-2/), FIN-002). a16z añade tres reglas que la Skill adopta como validaciones: bookings no son ingresos y las LOI no cuentan como ninguno; el ARR excluye setup y servicios; y el CAC incluye referral fees, créditos y descuentos ([a16z](https://a16z.com/16-startup-metrics/)).

De ahí salen seis reglas de implementación [P/I]. El **LTV con churn bajo explota** (con 0,5 % mensual la vida implícita es de 200 meses), así que se usa horizonte máximo, descuento y un churn mínimo igual al de la cohorte madura más antigua, o 1 %/mes si hay menos de 12 meses de historia. El **churn con muestra pequeña** se reporta con intervalo de Wilson: con 1 baja entre 20 clientes, el intervalo exacto va de ~0,1 % a ~25 %, y con menos de 30 cliente-periodos o menos de 3 eventos se marca "no estimable". La **mezcla de cohortes** sesga en direcciones opuestas según el crecimiento, así que se calcula por cohorte o se reporta el rango joven-madura. La **conversión mensual-anual es compuesta** (2 % mensual = 21,5 % anual, no 24 %). El **NRR nunca va sin GRR**. Y el **payback ajustado por churn puede no converger nunca** si m/c < CAC, lo que es una alarma de G2b.


## 6e.2 Catálogo de fórmulas (una fórmula = una función de `scripts/`)

Convenciones: tasas como fracción, dinero en la moneda del caso, periodo explícito en el nombre (`_m`, `_a`); cada función devuelve `value`, `unit`, `warnings` e `inputs_ledger_ids`, y `None` si falta un input P0. Abreviaturas de aplicación: SaaS (SaaS e IA de producto), SVC (S1 y S3), AGY (S2), MSP (S4), AIA (modificador AIX), INF (P-INFRA). El pseudocódigo completo está en `modelacion_financiera.md` (§E2 y §E3).

| ID | Función | Fórmula | Aplica / no aplica | Fuente y tag |
|---|---|---|---|---|
| UE-01 | `cac_blended` | Gasto S&M del periodo / clientes nuevos del periodo | Todos / pre-revenue | a16z [D] |
| UE-02 | `cac_paid` | Gasto en canales pagados / clientes atribuidos | SaaS, AIA / solo referidos | a16z [D] |
| UE-03 | `cac_fully_loaded` | (Programas + salarios S&M con cargas + herramientas + comisiones + referral fees + créditos de captación + tiempo comercial del fundador a coste de mercado) / clientes nuevos | Todos | a16z [D]; fundador [P] |
| UE-04 | `gross_margin_pct` | (Ingresos − COGS) / ingresos, con COGS = hosting + inferencia + soporte + entrega + comisiones de pago + licencias por cliente | Todos | a16z [D]; fase 1 |
| UE-05 | `contribution_margin` | Ingresos − COGS − costes variables de venta y servicio | Todos | a16z [D] |
| UE-06 | `arpa_m` | MRR / cuentas activas medias | SaaS, MSP, AIA con retainer / proyectos únicos | Skok [D] |
| UE-07 | `churn_logo` | Bajas del periodo / clientes al inicio, con intervalo de Wilson | Recurrentes / proyectos sin contrato | a16z [D]; intervalo [P] |
| UE-08 | `churn_revenue_gross` | (MRR perdido por bajas + contracción) / MRR inicial | SaaS, MSP | a16z, Skok [D] |
| UE-09 | `churn_m_to_a`, `churn_a_to_m` | a = 1 − (1 − m)^12; m = 1 − (1 − a)^(1/12) | Recurrentes | Aritmética [I] |
| UE-10 | `nrr` | (ARR_ini + expansión − contracción − churn) / ARR_ini, solo cohorte inicial | SaaS, MSP / proyectos | Fase 1 [S] |
| UE-11 | `grr` | (ARR_ini − contracción − churn) / ARR_ini, ≤ 1 | SaaS, MSP, AIA | Fase 1 [S] |
| UE-12 | `ltv_simple` | m / c (margen declarado: contribución o bruto) | Solo cribado / churn < 1 %/mes sin cota; < 12 meses de historia | Skok, a16z [D] |
| UE-13 | `ltv_discounted` | m·r / (1 + i − r), r = 1 − c | SaaS, MSP / retención creciente sin ajuste | Gupta et al. [D modelo; M forma] |
| UE-14 | `ltv_capped` (**por defecto**) | Σ_{t=1..H} m·r^(t−1) / (1+i)^t, m sobre margen de contribución | SaaS, MSP, AIA | [P] |
| UE-15 | `ltv_cohort_empirical` | Σ_{t=1..H} (margen observado de la cohorte en t / clientes adquiridos) / (1+i)^t | SaaS, MSP / cohortes < 30 clientes | a16z [D]/[P] |
| UE-16 | `sbg_survival`, `sbg_retention`, `sbg_fit` | P(T=1) = α/(α+β); S(t) = S(t−1)(β+t−1)/(α+β+t−1); r_t = (β+t−1)/(α+β+t−1); ajuste por máxima verosimilitud | SaaS, MSP con contrato periódico / uso no contractual | Fader & Hardie [M] |
| UE-17 | `ltv_to_cac` | UE-14 / UE-03, misma definición de margen | Recurrentes, señal secundaria / como compuerta | Skok (3× como convención) |
| UE-18 | `cac_payback_gm` | CAC / (ARPA_m nuevo × margen) | SaaS, MSP, AIA | Skok, BVP [D] |
| UE-19 | `cac_payback_churn_adj` | n = ⌈ln(1 − CAC·c/m) / ln(1 − c)⌉; si CAC·c/m ≥ 1 → "nunca" | Ídem | Aritmética [I] |
| UE-20 | `burn_multiple` | Burn neto / (ARR_fin − ARR_ini); "N/A" si burn ≤ 0 o ARR neto ≤ 0 | SaaS e IA de producto con VC / bootstrapped rentable, servicios | Sacks [D] |
| UE-21 | `revenue_per_fte`, `arr_per_fte` | Ingresos (o ARR) / FTE medios, incluidos dueño y contratistas equivalentes | Todos | Fase 1 [S] |
| UE-22 | `utilisation` | Horas facturables / horas disponibles (contrato − vacaciones − festivos) | SVC, AGY, AIA, MSP / SaaS puro | Maister [M]; SPI [S] |
| UE-23 | `realisation` | Facturado y cobrado / (horas facturables × tarifa estándar) | SVC, AGY | Maister [M] |
| UE-24 | `services_revenue` | Horas disponibles × utilización × tarifa estándar × realización | SVC, AGY, AIA | Maister [M] |
| UE-25 | `loaded_cost_per_hour` | (Salario + cargas + beneficios + herramientas + parte de overhead) / horas **facturables** esperadas | SVC, AGY, AIA, MSP | [I] |
| UE-26 | `project_margin` | (Ingresos − horas reales × coste cargado/h − subcontratas − inferencia e infra directa) / ingresos | SVC, AGY, AIA | Maister [M] |
| UE-27 | `cost_to_serve` | (Entrega y soporte + herramientas por endpoint o usuario + infra + inferencia) / clientes | MSP, AIA, SaaS | [P] |
| UE-28 | `contract_npv` | −onboarding − CAC + Σ (cuota_t − cost_to_serve_t − penalizaciones SLA esperadas_t)/(1+i)^t | MSP, AIA, SVC con retainer | [P] |
| UE-29 | `cost_per_successful_outcome` | Coste total (inferencia + infra + supervisión) / ejecuciones que cumplen el umbral de calidad; p50/p90 | AIA, IA de producto | FinOps for AI [D] |
| FM-01 | `breakeven_revenue` | Costes fijos / margen de contribución % | Todos / CM% ≤ 0 → "sin equilibrio" | Fase 1 [M] |
| FM-02 | `breakeven_units` | Costes fijos / (precio − coste variable unitario) | SaaS (cuentas), MSP (endpoints) | Estándar [M] |
| FM-03 | `breakeven_billable_fte` | Fijos no asignados / (h_disp × util × tarifa × realización − coste cargado anual por FTE) | SVC, AGY, AIA / denominador ≤ 0 → falla G2 | Maister [I] |
| FM-04 | `dso`, `dpo`, `wip_days`, `ccc` | DSO = AR / ingresos × días; DPO = AP / compras × días; WIP = no facturado / ingresos × días; CCC = DSO + WIP − DPO | Todos, crítico en SVC y AGY | Fase 1 [M] |
| FM-05 | `runway_simple`, `runway_projected` | Caja / burn neto medio de 3 meses; primer mes con caja < caja mínima (motor de caja) | Startup, micro con pérdidas / caja creciente → "no aplica" | a16z [D]; forma [P] |
| FM-06 | `funding_need` | max(0, caja mínima − mín_t caja proyectada) + colchón | Startup, micro | [P] |
| FM-07 | `roic` | NOPAT / capital invertido medio | Establecida, INF, MSP / micro con capital ~0 | Damodaran, McKinsey [M] |
| FM-08 | `cost_of_equity`, `total_beta`, `wacc` | Re = Rf + β·ERP (+ CRP); β_total = β_mercado / ρ; WACC = E/V·Re + D/V·Rd·(1 − t) | Establecida; privada con beta total / micro sin deuda ni acceso a capital | Damodaran [D]/[M] |
| FM-09 | `npv`, `irr`, `mirr` | NPV = Σ CF_t/(1+r)^t; IRR por bisección en [−0,99; 10] con conteo de cambios de signo y negativa si hay más de uno; MIRR con tasas de financiación y reinversión | Todos / IRR con varios cambios de signo | McKinsey 2004 [S]; estándar [M] |
| FM-10 | `sde`, `adjusted_ebitda`, `owner_salary_gap` | SDE = EBITDA + compensación total de un dueño + discrecionales; EBITDA ajustado = EBITDA + (compensación del dueño − salario de mercado); gap = salario de mercado − pagado | Micro, agencia, MSP pequeño / startup con VC | Brokers [S] |
| FM-11 | `rule_of_40` | Crecimiento % + margen FCF % | SaaS con escala / micro y servicios | Fase 1 [S] |
| FM-12 | `reinvestment_needed` | Δ ingresos / ratio ventas-capital del sector | Establecida, INF, IA intensiva / micro | Damodaran [M] |
| SA-01 | `tornado` | Salida con cada driver en su mínimo y máximo y el resto en base; swing ordenado y cuota acumulada | Siempre | [P] |
| SA-02 | `pert_params`, `sample_pert`, `sample_triangular` | Media PERT = (a + 4m + b)/6; α = 1 + 4(m − a)/(b − a); β = 1 + 4(b − m)/(b − a) | MC / sin ledger → rechazar | [M] |
| SA-03 | `correlated_uniforms` | Cópula gaussiana con Cholesky, o reordenación de rangos (Iman-Conover simplificado) | MC / matriz no definida positiva | [P] |
| SA-04 | `mc_summary` | P10/P50/P90, P(caja < 0), P(LTV/CAC < 1), error estándar √(p(1 − p)/N) | MC con N ≥ 10.000 | [P] |


## 6e.7 Casos de prueba de las fórmulas

Valores calculados a mano y verificados con Python en la sesión de investigación (`modelacion_financiera.md` §E4). Tolerancias: ±0,01 en dinero y ±1e−4 en ratios. T7b y T18 comprueban que la función se **niega** a dar un número.

| # | Función | Inputs | Esperado |
|---|---|---|---|
| T1 | `cac_blended` | S&M 60.000; 40 nuevos | 1.500 |
| T2 | `cac_paid` | 20.000; 10 pagados | 2.000 |
| T3 | `ltv_simple` | ARPA 500/mes; margen 0,80; c = 0,02 | 20.000 |
| T4 | `ltv_discounted` | m = 400; r = 0,98; i_a = 12 % (i_m = 0,0094888) | 13.293,19 |
| T5 / T5b | `ltv_capped` | m = 400; c = 0,02; H = 36; sin descuento / con 12 % anual | 10.335,74 / 8.899,09 |
| T6 | `cac_payback_gm` | CAC 6.000; ARPA 500; GM 0,75 | 16,0 meses |
| T7 / T7b | `cac_payback_churn_adj` | Ídem con c = 0,02 / CAC 20.000, m = 375 | 20 meses (19,09) / "nunca" |
| T8 | `churn_m_to_a` / `churn_a_to_m` | 0,02 mensual / 0,20 anual | 0,21528 / 0,018423 |
| T9 | `nrr` / `grr` | ARR 1.000.000; expansión 150.000; contracción 30.000; churn 70.000 | 1,05 / 0,90 |
| T10 | `burn_multiple` | Burn 2.400.000; ARR neto nuevo 1.600.000 | 1,5 |
| T11 | `services_revenue` | 1.800 h; util. 0,70; tarifa 100; realiz. 0,90 | 113.400 |
| T12 | `breakeven_revenue` | Fijos 120.000; CM 0,40 | 300.000 |
| T13 | `breakeven_billable_fte` | Fijos 60.000; 1.600 h; 0,75; 80; 0,9; coste 55.000 | 1,911 FTE (2 enteros) |
| T14 | `dso` / `dpo` / `ccc` | AR 90.000; ingresos 730.000; AP 20.000; COGS 365.000; WIP 10 días | 45 / 20 / 35 |
| T15 | `runway_simple` / proyectado | Caja 300.000; burn 25.000 creciendo 3 %/mes | 12,0 / 10 meses completos |
| T16 | `npv` | r = 10 %; [−1.000, 300, 400, 500] | −21,04 |
| T17 | `irr` | Ídem | 0,08896 |
| T18 | `irr` múltiple | [−100, 230, −132] | Dos IRR (10 % y 20 %): debe negarse |
| T19 | `total_beta` | β = 1,18; ρ = 0,5 | 2,36 |
| T20 | `sde` / `adjusted_ebitda` | EBITDA 100.000 tras pagar 300.000 al dueño; mercado 180.000 | 400.000 / 220.000 |
| T21 | `pert_params` | a = 0,01; m = 0,02; b = 0,05 | media 0,02333 |
| T22 | `mc_summary` | p = 0,05; N = 10.000 | EE 0,00218 |
