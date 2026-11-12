# M8–M9: unit economics, proyecciones, caja y escenarios

> Leer en M8 y M9: motor de caja, modelo por tipo de empresa, escenarios, puerta de Monte Carlo y reglas R1–R6.
>
> Generado desde: secciones 6d (M8–M9) y 6e.3–6e.6 del informe «Evaluación negocios tecnológicos ampliada» (texto propio con citas). No editar a mano: editar el informe y ejecutar `evals/harness/build_references.py`. Etiquetas: [D] documentado, [S] secundario, [M] marco/libro o conocimiento no verificado, [I] inferencia, [P] propuesta metodológica.

### Especificación de módulos (6d)

| Módulo | Entradas (P0 en cursiva) | Cálculo y procedimiento | Umbrales y anclas específicas | Salida al ledger |
|---|---|---|---|---|
| **M8 Unit economics** | Por arquetipo: utilización, tarifa, realización, coste cargado; o CAC, ARPA, margen, churn, NRR/GRR | Scripts UE-01 a UE-29 (6e); churn con intervalo de Wilson; GRR siempre junto a NRR; LTV por defecto UE-14 | G2 y G2b; R3: GRR < 80 %, NRR ≥ 100 % con GRR < 85 % o churn de logos > 3 %/mes en mid-market [P]; payback de BVP como rango de referencia (PRD-028) | `ue_metrics{}` con ids de ledger e intervalos |
| **M9 Proyecciones financieras** | Plan de drivers, caja inicial, plantilla, créditos, DSO/DPO/WIP, rondas | Modelo según tipo de empresa (6e.4); motor de caja; R1, R2, R5, R6; NPV con IRR solo si hay un cambio de signo; escenarios + estrés del arquetipo; puerta de MC | Más del 50 % del swing por inputs `assumption` → máximo CONDITIONAL_GO y marca en G6 [P]; burn multiple ~2× razonable en etapa temprana, ≥ 3× alarma (FIN-003) | `projection[]`, `runway_month`, `min_cash`, `funding_need`, `breakeven_month`, `flags[]` |


## 6e.3 Motor de caja y runway

El motor mensual (`breakeven_runway.py`) recibe todo input con id de ledger y estado, y recorre el horizonte (12–24 meses en micro, 24–36 en startup, 60 en establecida). En cada mes actualiza clientes por línea (bajas con churn constante o con la tabla sBG, altas del plan), ingresos recurrentes, por proyecto o por horas facturables, y COGS con el crecimiento del coste de infraestructura y un multiplicador de precio del modelo para escenarios. Aplica los créditos cloud o de IA vigentes antes de calcular el COGS en caja, suma la nómina con inflación salarial y el opex, y registra aparte la brecha entre el salario de mercado y el pagado del dueño, que no sale de caja pero sí del EBITDA ajustado. El capital circulante se aproxima en estado estacionario (AR = ingresos × DSO/30, WIP = ingresos × días WIP/30, AP con DPO), que **subestima el AR en meses de crecimiento fuerte** [I]; la alternativa exacta es un lag de cobro por cohorte de facturación [P]. Las salidas son el mes de runway (primer mes con caja < caja mínima, por defecto 3 meses de gastos fijos [P]), la caja mínima, la necesidad de financiación, el mes de equilibrio (EBITDA ajustado ≥ 0 sostenido 3 meses), la dependencia de créditos y los flags R1–R6. La comprobación de cierre es caja_t = caja_{t−1} + flujo_t con tolerancia 1e−6, y ninguna fila puede quedar sin ids de ledger. Para micro y startup se prefiere el flujo directo, auditable contra el banco; para la establecida, el indirecto conciliado con el balance [M].


## 6e.4 Qué modelo para qué empresa [P]

| Elemento | Micro o freelance que pasa a agencia | Startup (SaaS, IA, AIX con capital) | Empresa tecnológica establecida |
|---|---|---|---|
| Periodo y horizonte | Mensual, 12–24 meses | Mensual, 24–36 meses | Anual a 5 años + 12 meses de caja mensual |
| P&L | Con salario de mercado del dueño (R6), SDE y EBITDA ajustado | Por drivers | Completo |
| Caja | Directo simplificado con DSO, WIP y DPO | Motor completo con créditos y rondas | Indirecto anual + motor a 12 meses |
| Balance | Solo AR, AP, WIP y caja | Simplificado (caja, AR, AP, deuda, equity aportado) | Simplificado completo |
| Unit economics | UE-22 a UE-26, FM-03 | UE-01 a UE-20, UE-27 a UE-29 | Los del arquetipo de cada línea |
| Tasa de descuento | Rendimiento exigido por el dueño (beta total o supuesto declarado); **sin WACC** | Tasa objetivo VC solo si hay ronda; si no, beta total | WACC con Damodaran y CRP del país (6i) |
| Valor | Beneficio económico del dueño = SDE − salario de reposición − capital × rendimiento exigido; payback de su inversión | NPV por escenarios + supervivencia de referencia | ROIC − WACC, NPV, reinversión (FM-12) |
| Sensibilidad | Tornado + 3 escenarios, incluida la pérdida del mayor cliente | Tornado + escenarios + MC si pasa la puerta | Tornado + escenarios; MC opcional |
| Reglas prioritarias | R1, R4, R6 | R2, R3, R5 | R2, R3, R4 |

El WACC no tiene sentido en una microempresa sin deuda ni acceso a capital externo, en la que el dueño aporta trabajo y capital a la vez [I]. Damodaran justifica la beta total (beta de mercado / correlación con el mercado; ejemplo 1,18 / 0,5 = 2,36) porque el dueño no diversificado soporta todo el riesgo ([NYU](https://pages.stern.nyu.edu/~adamodar/pdfiles/valonlineslides/session19A.pdf), FIN-006). El NPV se prefiere a la IRR: en un reanálisis de McKinsey, proyectos con IRR de 800 %, 150 % y 130 % bajaron a 15 %, 23 % y 22 % con una tasa de reinversión realista ([McKinsey](https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/internal-rate-of-return-a-cautionary-tale), FIN-005, [S]).


## 6e.5 Escenarios y Monte Carlo sin falsa precisión

La secuencia es fija. **Uno**, tornado (SA-01) como cribado. **Dos**, tres escenarios coherentes (base, optimista y pesimista, en los que los drivers se mueven juntos según una narrativa declarada) más un estrés específico del arquetipo: deflación de 3–5 % anual en servicios por horas, precio del proveedor del modelo ×2,0 en IA, pérdida del mayor cliente en servicios y MSP, y fin de los créditos cloud o de IA. **Tres**, Monte Carlo solo si pasa la **puerta**: ≥ 3 drivers relevantes con rango documentado y todos los drivers que suman ≥ 80 % del swing del tornado con mínimo y máximo de estado `fact` o `estimate`, nunca un `assumption` del fundador [P]. Si la puerta falla se reportan tornado, escenarios y el motivo ("MC rechazado: evidencia insuficiente en drivers dominantes"). Las distribuciones se eligen por tipo: triangular o PERT solo con mínimo, moda y máximo documentados; uniforme con solo mínimo y máximo; lognormal o PERT para costes con cola derecha; Beta o PERT acotada para tasas; nunca normal para tasas cercanas a 0 o 1. Sin evidencia de correlación se ejecuta con ρ = 0 y con ρ = ±0,5 y se reporta la diferencia. Por defecto N = 10.000 con semilla fija (20261109): el error estándar de una probabilidad de 0,05 es 0,22 puntos.

Cinco reglas contra la falsa precisión [P]: rangos y percentiles con dos cifras significativas; cada input con id de ledger y estado; si más del 50 % del swing procede de `assumption`, el veredicto no pasa de CONDITIONAL_GO y se marca G6; el P50 nunca se presenta como "previsión"; y el escenario pesimista coherente se muestra siempre junto al P10.


## 6e.6 Reglas de patrones R1–R6

| ID | Patrón | Test operativo | Umbral y tag | Salida |
|---|---|---|---|---|
| R1 | Rentable pero sin capacidad de crecer | Servicios con utilización ≥ 85 % y sin FTE facturable adicional en el plan, o dueño > 40 % de las horas facturadas; caja libre anual tras salario de mercado < coste de contratar 1 FTE durante la rampa (3 meses de coste cargado); ingresos/FTE planos ±5 % tres periodos | [P] | Alerta M14; escenario "contratar 1 FTE" obligatorio |
| R2 | Crecimiento que destruye caja | Burn multiple > 2 tras la semilla; o payback ajustado por churn > 24 meses (SMB) o > 36 (enterprise); o cada 1 € de ingreso nuevo consume > 1 € de capital circulante | 2× de Sacks [D]; 24/36 del extremo de BVP [D]; resto [P] | Alerta M9; G6 si faltan datos |
| R3 | Recurrencia con retención pobre | GRR < 80 %; o NRR ≥ 100 % con GRR < 85 %; o churn de logos > 3 %/mes en B2B mid-market | Referencia SaaS Capital 91 % [D]; cortes [P] | Alerta M12; LTV con la cota alta de churn |
| R4 | Margen alto por costes omitidos | Recalcular con salario de mercado del dueño por sus horas de entrega, mano de obra de entrega y soporte en COGS, inferencia a precio de lista sin créditos, comisiones de pago, hosting por cliente y onboarding no facturado; diferencia > 10 pp | [P] | G2 se evalúa con el margen recalculado |
| R5 | Dependencia de subsidios, financiación o créditos | Créditos o subsidios ≥ 20 % de los costes en algún mes de los próximos 12; runway sin la próxima ronda < 12 meses; margen de contribución negativo al expirar los créditos | [P] | Escenario "créditos expiran"; alerta G3 (G2 si el margen se vuelve negativo) |
| R6 | Fundadores sin salario de mercado | Salario de reposición (rol × horas × tarifa local con id de ledger) − salario pagado > 0; beneficio ajustado < 0 → "rentable solo por autoexplotación"; SDE y EBITDA ajustado por separado, nunca el SDE como rentabilidad | Sin umbral [P]; concepto SDE [S] | M9; G2 si el margen de contribución pasa a negativo |
