# M6–M7: modelo de ingresos y pricing

> Leer en M6 y M7: clase de recurrencia (H3), viabilidad del meter y outcome pricing.
>
> Generado desde: secciones 6d (M6–M7) y 6f.4 del informe «Evaluación negocios tecnológicos ampliada» (texto propio con citas). No editar a mano: editar el informe y ejecutar `evals/harness/build_references.py`. Etiquetas: [D] documentado, [S] secundario, [M] marco/libro o conocimiento no verificado, [I] inferencia, [P] propuesta metodológica.

### Especificación de módulos (6d)

| Módulo | Entradas (P0 en cursiva) | Cálculo y procedimiento | Umbrales y anclas específicas | Salida al ledger |
|---|---|---|---|---|
| **M6 Modelo de ingresos** | Líneas, contratos (plazo, terminación por conveniencia), meters | Profit formula; H3 (ARR frente a servicios); contratos cancelables con < 30 días sin penalización no son recurrencia (N08) | 1 = ingreso mal clasificado o recurrencia inflada; 4–5 = recurrencia contractual verificada [P] | `revenue_lines[]` con clase de recurrencia |
| **M7 Pricing** | *Meter*, *precio*, texto de la definición de outcome, precios públicos de alternativas | Matriz de viabilidad del meter (6f): seat (coste p95 por seat < 0,5 × precio), consumo (margen ≥ objetivo en p50 y > 0 en p95), créditos (coste p90 por crédito < precio), tarea (precio ≥ C_task p90), outcome (precio ≥ CPST_total p90 / (1 − margen objetivo) y definición escrita y auditable), híbrido (fee fijo ≥ C_fix) | La WTP declarada (Van Westendorp, Gabor-Granger, conjoint) solo orienta el rango, nunca sube la evidencia por encima del nivel 1; deflación de 3–5 % anual en servicios por horas como escenario (fase 1) | `meter_viability`, `price_tests[]` |


## 6f.4 Escalabilidad, márgenes y viabilidad del meter

Un negocio AI-native escala si su coste marginal por tarea exitosa baja o se mantiene con el volumen. La inferencia es casi lineal; las economías vienen de la fiabilidad (menos escalados y errores silenciosos), de amortizar evals y mantenimiento y de mejorar prompts y routing con datos de uso. **Si la fiabilidad no mejora con el volumen, el negocio escala como servicio, no como software** [I]. Los márgenes observados siguen por debajo del SaaS clásico (25–60 % según arquetipo en Bessemer, PRD-021; 45 % en ICONIQ para 2025, PRD-019; 31 % GAAP en C3.ai, AI-040). Los moats de datos se tratan como no probados hasta que el proponente demuestre una mejora medible de ACR, SER o coste frente a un modelo frontera sin esos datos ([a16z](https://a16z.com/2019/05/09/data-network-effects-moats/), [S]). El mercado converge en híbridos y el outcome solo funciona con un resultado observable, atribuible y contratable ([Bain](https://www.bain.com/insights/ai-pricing-a-reality-check-on-effort-usage-and-outcomes/), AI-043). Matriz de viabilidad [P]:

| Meter | Viable si | Riesgo principal | Test numérico de la Skill |
|---|---|---|---|
| Seat | Uso por usuario acotado y estable | Usuarios intensivos | Coste p95 por seat/mes < 0,5 × precio |
| Consumo (tokens, acciones) | El cliente tolera la variabilidad | Sesgo hacia la tarifa plana (AI-044) | Margen por unidad ≥ objetivo en p50 y > 0 en p95 |
| Créditos o capacidad | Mix de acciones estable | Breakage y cambios de mix | Coste p90 por crédito < precio por crédito |
| Por tarea | Tarea discreta y contable | Cola de coste | Precio ≥ C_task p90 (G2) |
| Por outcome | Resultado observable, atribuible, verificable y contratable | Pagar los fallos y disputas de definición | Precio ≥ CPST_total p90 / (1 − margen objetivo) y definición escrita y auditable |
| Suscripción plana | Uso muy predecible | Usuarios intensivos destruyen el margen | Simular la cola de clientes (p95/p99) |
| Híbrido (plataforma + consumo u outcome) | Atribución confundida o coste incierto | Complejidad | Fee fijo ≥ C_fix; componente variable ≥ coste p90 |

Con outcome pricing, el ingreso por tarea es precio × P(éxito facturable), y el margen se calcula sobre ese ingreso, incluidas las tareas fallidas no facturadas. En el ejemplo ilustrativo, ni 2 $ por resolución cubren el coste total medio (2,88 $): la economía solo cierra con escalado < ~5 % y QA ligera, o con un fee de plataforma [I].
