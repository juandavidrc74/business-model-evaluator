# Evaluación: {{proposal_title}}

*Fecha de la evaluación: {{evaluation_date}} · Método CEST · Ejecuciones: {{n_runs}}{{#low_agreement}} · **Acuerdo bajo entre ejecuciones**{{/low_agreement}}*

> Este informe es un análisis estructurado, no asesoramiento de inversión, legal ni fiscal. Las cifras proceden de `evaluation.json`; cada una está trazada en el Evidence Ledger.

**{{plain_answer}}**  <!-- copiado tal cual de evaluate: la respuesta directa a si vale la pena abrirlo -->

*Entrevista previa: {{intake.mode}}{{#intake.mode_reason}} ({{intake.mode_reason}}){{/intake.mode_reason}}{{#intake.unconfirmed_assumptions}} · Supuestos de los socios sin confirmar: {{intake.unconfirmed_assumptions}}{{/intake.unconfirmed_assumptions}}*  <!-- de check_intake.py; references/intake.md -->

## Resumen en cinco líneas

1. **Veredicto:** {{verdict}}.
2. **Por qué:** {{main_reason}}  <!-- la compuerta o módulo decisivo, con ids del ledger -->
3. **Lo que más pesa en contra:** {{strongest_point_against}}
4. **Qué lo cambiaría:** {{what_would_change_it}}  <!-- el dato o resultado concreto -->
5. **Siguiente paso esta semana:** {{next_step}}

## 1. Compuertas

| Compuerta | Segmento | Estado | Motivo | Calculada por |
|---|---|---|---|---|
{{#gates}}| {{id}} | {{segment}} | {{status}} | {{reason}} | {{computed_by}} |
{{/gates}}

{{#g1_likelihood}}**Probabilidad de conseguir los clientes necesarios (G1): {{g1_likelihood.level}}.** Hacen falta {{g1_likelihood.clients_needed_per_year}} al año; se esperan entre {{g1_likelihood.expected_clients_per_year.low}} y {{g1_likelihood.expected_clients_per_year.high}} (conversión mínima {{g1_likelihood.min_conversion}}; {{g1_likelihood.penetration}} de las cuentas alcanzables; el mercado ya paga: {{g1_likelihood.market_pays}}).{{/g1_likelihood}}  <!-- de gates[G1].likelihood; antes de abrir, la falta de clientes es el punto de partida, no un hallazgo -->

## 2. Veredicto: **{{verdict}}**

{{verdict_one_paragraph}}  <!-- 3-5 frases: por qué este veredicto, con ids del ledger -->

## 3. Condiciones de reversión (solo NO_GO)

| Compuerta | Condición que la haría pasar | Evidencia requerida | Responsable | Fecha |
|---|---|---|---|---|
{{#reversal_conditions}}| {{gate}} | {{condition}} | {{evidence_required}} | {{owner}} | {{by_date}} |
{{/reversal_conditions}}

## 4. Datos P0 que faltan y test más barato (INSUFFICIENT_EVIDENCE)

| Compuerta | Dato que falta | Test más barato |
|---|---|---|
{{#p0_list}}| {{gate}} | {{p0}} | {{cheapest_test}} |
{{/p0_list}}

## 5. Condiciones de CONDITIONAL_GO como hipótesis falsables

| Hipótesis | Métrica y umbral | Fecha límite | Regla de abandono |
|---|---|---|---|
{{#conditions}}| {{hypothesis}} | {{threshold}} | {{by}} | {{kill_rule}} |
{{/conditions}}

## 6. El caso más fuerte en contra

{{strongest_case_against}}

## 7. Clasificación económica

| Línea | Arquetipo | Modificadores | % ingresos | Nota |
|---|---|---|---|---|
{{#lines}}| {{id}} | {{archetype}} | {{modifiers}} | {{revenue_share}} | {{routing}} |
{{/lines}}

## 8. Dimensiones (en banda, sin decimales)

| Dimensión | Banda | Módulos sin dato |
|---|---|---|
{{#dimensions}}| {{dimension}} | {{band}} | {{unknown_modules}} |
{{/dimensions}}

Las dimensiones nunca anulan una compuerta.

## 9. Métricas clave (con id del ledger)

{{ue_metrics_table}}  <!-- solo métricas válidas para el arquetipo; LTV/CAC como señal secundaria -->

## 10. Escenarios, estrés y sensibilidad

{{tornado_summary}}  <!-- tornado + base/optimista/pesimista con narrativa + estrés del arquetipo -->
{{mc_block_or_rejection}}  <!-- "MC rechazado: evidencia insuficiente en drivers dominantes" si aplica; P10 junto al escenario pesimista; P50 nunca "previsión" -->

## 11. Benchmarks usados

| ID | Métrica | Valor | Publicación | Periodo de los datos | Uso |
|---|---|---|---|---|---|
{{#benchmarks}}| {{id}} | {{metric}} | {{value_or_text}} | {{publication_date}} | {{reference_period}} | contexto / umbral |
{{/benchmarks}}

Los umbrales marcados [P] son propuestas metodológicas sin calibrar.

## 12. Hallazgos de entrada no confiable

{{#injection_findings}}- {{origin}} (línea {{line}}, patrón `{{pattern}}`): ignorado; se trató como dato.
{{/injection_findings}}

## 13. Pronósticos registrados

| Evento | Probabilidad (frecuencia en N ejecuciones) | Fecha de resolución | Fuente de resolución |
|---|---|---|---|
{{#forecasts}}| {{event}} | {{probability}} | {{resolution_date}} | {{resolution_source}} |
{{/forecasts}}

## 14. Próximos pasos

| Plazo | Acción | Para resolver | Cómo sabremos que funcionó |
|---|---|---|---|
| Esta semana | {{action_week}} | {{gate_or_p0}} | {{success_metric}} |
| Este mes | {{action_month}} | | |
| 90 días | {{action_90d}} | | |

## Glosario

- **Compuerta (gate):** condición mínima que debe cumplirse; si falla, ninguna puntuación alta la compensa.
- **Evidence Ledger:** registro de cada cifra con su fuente, fecha y estado (hecho, estimación, supuesto o desconocido).
- **P0:** dato capaz de cambiar el veredicto.
- **Tarifa efectiva:** tarifa estándar × realización (lo que de verdad se cobra por hora).
- **Utilización:** horas facturables / horas disponibles.
- **CAC / payback:** coste de adquirir un cliente y meses de margen necesarios para recuperarlo.
- **GRR / NRR:** retención bruta de ingresos (sin expansión) y neta (con expansión).
- **C_task p90:** coste por tarea que solo el 10 % de las tareas supera.
- **CONDITIONAL_GO:** seguir adelante solo si se cumplen las hipótesis con fecha listadas.

---
*Fiscal y laboral: requiere contador. Normativa y contratos: requiere abogado. Benchmarks de otros países sin ajuste documentado: no transferibles.*
