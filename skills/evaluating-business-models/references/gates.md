# Compuertas G0–G7 y G2b, veredicto y agregación

> Leer antes de calcular compuertas y siempre que se redacte un veredicto. Las compuertas aritméticas las calcula `gates_and_score.py`; no se votan.
>
> Generado desde: sección 6b del informe «Evaluación negocios tecnológicos ampliada» (texto propio con citas). No editar a mano: editar el informe y ejecutar `evals/harness/build_references.py`. Etiquetas: [D] documentado, [S] secundario, [M] marco/libro o conocimiento no verificado, [I] inferencia, [P] propuesta metodológica.

## Contenido

- 6b. Compuertas antes de puntuar
  - 6b.1 Especificación operativa de las compuertas (fase 2)
  - 6b.2 Del estado de las compuertas al veredicto [P]
  - 6b.3 Agregación de varias ejecuciones [P]
- Formato de entrada de `gates_and_score.py evaluate` [PROPUESTA]

## 6b. Compuertas antes de puntuar

Las compuertas se evalúan primero y se muestran por separado. Si una falla, el veredicto es "no avanzar hasta resolver X", sea cual sea la puntuación. El fundamento es la regla no compensatoria de Åstebro & Elhedhli y la lógica de la compensación aditiva; los ejemplos concretos son inferencia del equipo [I]. **Corrección fase 2:** "no avanzar" no era ninguno de los cuatro veredictos; ahora cada compuerta tiene tres estados (`pass`, `fail`, `unknown`) y una correspondencia explícita con el veredicto (6b.2). La tabla siguiente es la de la fase 1; la especificación operativa que la sustituye está en 6b.1.

| Compuerta | Falla si… | Fuente del criterio |
|---|---|---|
| G0 Alcance | No están claros arquetipo, país/mercado, moneda u horizonte (se pregunta, no se asume) | Nota de arquitectura [PROPUESTA] |
| G1 Cliente pagador | No hay comprador económico identificable con razón de compra | Evidencia académica §8 [I]; Moore y Aulet [M] |
| G2 Margen de contribución | Negativo a tarifa realista (servicios: tarifa efectiva < coste cargado; IA: coste p90 por tarea > precio) | Maister; FinOps for AI (distribuciones) |
| G3 Concentración y dependencia | Dependencia total de un cliente, partner o proveedor de modelo sin mitigación | Evidencia académica §8 [I] |
| G4 Legal, regulatorio y compliance | Vende a mid/enterprise sin plan ni presupuesto de SOC 2/ISO 27001, o incumple regulación | Nota de operación (umbral orientativo ~30 k$ en primer año, fuentes de proveedor) [S] |
| G5 Testabilidad | Supuestos críticos sin forma de testearse en ≤ 90 días | Evidencia académica §8 [I]; Camuffo |
| G6 Cobertura de evidencia | Un dato P0 desconocido podría invertir el veredicto → INSUFFICIENT_EVIDENCE | Patrón de ledger de la comunidad ([skills.cat](https://skills.cat/skills/pirotequeen/ai-startup-due-diligence-skill)) |
| G7 Capacidad de entrega | El SLA prometido no es alcanzable con la operación descrita (p. ej., 99,99 % sin guardia 24×7) | SRE [M]; aritmética de disponibilidad |

### 6b.1 Especificación operativa de las compuertas (fase 2)

Las compuertas marcadas "script" las calcula `gates_and_score.py` a partir del Evidence Ledger y son deterministas: no se votan entre ejecuciones. Las marcadas "juicio" se extraen en cada ejecución y se agregan por moda. Toda compuerta en una línea de negocio con ≥ 20 % de los ingresos se evalúa por segmento (H8).

| Compuerta | Entradas del ledger (P0 en cursiva) | Cálculo (IDs) | `fail` si… | `unknown` si… | Cálculo por | Fuente y tag |
|---|---|---|---|---|---|---|
| **G0 Alcance** | *Arquetipo por línea, país del cliente y de la entrega, moneda, horizonte, intención de buscar capital riesgo* | Clasificación de 6a.3 | No tiene estado `fail`: una propuesta fuera del dominio (no es un negocio de servicios o producto tecnológico) se declina sin veredicto | Falta cualquiera de los cinco campos; en modo interactivo se pregunta, en `claude -p` produce INSUFFICIENT_EVIDENCE con preguntas (caso D.8) | Juicio + validación de esquema | Nota de arquitectura [P] |
| **G1 Cliente pagador** | *Cuentas del segmento con comprador económico identificado y su nivel de demanda (0–6, 6g)* | Recuento por cuenta del nivel máximo | Hay evidencia negativa documentada: con ≥ 5 compradores económicos contactados, al menos dos tercios rechazaron pagar o los pilotos pagados no convirtieron [P] | No hay cuentas del segmento con comprador económico identificado, o todas están en nivel ≤ 2 sin evidencia negativa | Juicio sobre el ledger | Nota de mercado [P]; Moore y Aulet [M] |
| | | | `pass`: ≥ 1 cuenta en nivel ≥ 4 con comprador económico, o ≥ 3 cuentas del mismo segmento en nivel 3 | | | |
| **G2 Margen de contribución** | *Precio o tarifa, realización, coste cargado, COGS completo por arquetipo, distribución de coste por tarea si hay AIX* | Servicios: tarifa × realización frente a UE-25; FM-03 con denominador ≤ 0. Producto: UE-05 por cliente. AIX/P-AI-APP: T1 (precio < C_task p90). Siempre sobre el margen recalculado de R4 | Margen de contribución < 0 a tarifa realista; FM-03 sin equilibrio; precio por tarea u outcome < coste p90 por tarea; R4 recalculado lo vuelve negativo | Falta un input P0; en AIX, falta pass^1 o el coste humano ("no evaluable"); si falta la tasa de error silencioso se usa 5 % con penalización de confianza | Script | Maister [M]; FinOps for AI [D]; aritmética |
| **G2b CAC recuperable** (nueva) | *CAC completo (UE-03), ARPA, margen de contribución, churn con intervalo de Wilson* | UE-18 frente a vida esperada 1/c; UE-19 | Payback simple > 1/c, o UE-19 = "nunca" (CAC·c/m ≥ 1) | El churn no es estimable (< 30 cliente-periodos o < 3 eventos) y el resultado cambia entre la cota baja y la alta del intervalo | Script; solo en líneas recurrentes con CAC | Aritmética [A]; corrección 3 del registro |
| **G3 Concentración y dependencia** | *Ingresos por cliente 12–24 meses, contratos y terminación por conveniencia, proveedores críticos, cuota de tokens por proveedor de modelo* | % top-1 y top-3; prueba de estrés de precio ×2,0 (6f) | Un cliente ≥ 50 % de los ingresos sin contrato plurianual sin terminación por conveniencia ni plan de diversificación **verificable** (objetivo < 50 %, fecha ≤ 12 meses y evidencia en el ledger; un plan solo declarado no mitiga, corrección tras la auditoría de noviembre de 2026) [P]; proveedor único de un insumo crítico sin alternativa probada; un solo proveedor de modelo sin fallback probado **y** margen de contribución < 0 con precio ×2,0 [P] | Faltan los ingresos por cliente | Script (cifras) + juicio (contratos) | ASC 280/IFRS 8 como ancla de divulgación (DD-001/002); Irvine et al.; [P] |
| | | | Alertas sin `fail`: cliente ≥ 25 % o top-3 ≥ 50 %; ≥ 10 % (paridad con divulgación); concentración alta con relaciones de < 2 años; créditos o subsidios ≥ 20 % de los costes (R5) | | | |
| **G4 Legal, regulatorio y compliance** (reformulada) | *País y tipo de datos de los titulares, sector del cliente, segmento objetivo declarado, cesiones de PI, SBOM* | Tabla de compliance (6h.2); filas KO de la matriz de DD | Aplica una fila "Legal" sin cumplimiento ni plan; el segmento objetivo declarado exige una fila "Contractual" (SOC 2, ISO 27001, BAA, PCI, DORA) sin plan ni presupuesto; KO de N11, N12, N13, T07, T14, C06, IA05, IA08 o IA09 | No se conoce dónde residen los titulares de datos o qué exige el segmento; sector regulado (modificador V) sin `sector_compliance_proven: true` con evidencia de nivel 1 (P0-MOD-V1) | Juicio + tabla | Nota de due diligence [P]; corrección 5 |
| **G5 Testabilidad** | *Supuestos críticos (drivers del 80 % del swing del tornado y P0 con estado `assumption`)* | Diseño de test de M15 | Algún supuesto crítico no admite un test que lo resuelva en ≤ 90 días | — | Juicio | Camuffo [D]; 90 días arbitrarios [P] |
| **G6 Cobertura de evidencia** | *Lista de P0 de todos los módulos* | Se recalculan las compuertas con cada P0 desconocido en sus dos extremos plausibles | — (G6 no falla: abstiene) | Algún P0 `unknown` cambia el veredicto entre extremos; o falta *eval set* propio en un dominio de alto impacto (IA03) | Script | Reject option [C] |
| **G7 Capacidad de entrega** | *SLA prometido, disponibilidad histórica, guardias, dotación 24×7, RTO, permisos de agentes* | Tabla de disponibilidad (99,9 % ≈ 43,8 min/mes; 99,99 % ≈ 4,4 min); 4,6–5,2 FTE por puesto 24×7 | SLA más exigente que lo medido o que lo que soporta la operación; penalizaciones sin tope; servicio con SLA sin monitorización (T10); RTO contractual sin prueba de restauración (T11); acciones irreversibles de agentes sin humano en el bucle (IA02); entrega dependiente de una persona sin documentación (N02) | Falta la disponibilidad histórica o la dotación; operación 24×7 sin `oncall_fte` ni `shift_schedule_proven: true` (la omisión no cuenta como prueba) | Script (aritmética) + juicio | SRE [M]; OWASP LLM06 [D]; [P] |

### 6b.1b Etapa `pre_launch`: negocios que todavía no venden (v0.7.0, decisión del usuario 2026-11-11)

La pregunta principal de la Skill es si vale la pena **abrir** el negocio. Por eso la etapa predeterminada de `gate_input.json` es `"stage": "pre_launch"`; `"operating"` conserva las reglas de la tabla anterior para negocios que ya facturan. En `pre_launch` aparece un quinto estado de compuerta, `conditional`: no se puede probar antes de abrir, así que se convierte en una condición falsable con umbral o fecha. Lo que se puede saber antes de abrir sigue fallando igual.

| Compuerta | `pre_launch`: pasa a `conditional` cuando… (condición generada) | Sigue en `fail` | Sigue en `unknown` |
|---|---|---|---|
| G1 (v0.7.3) | Estima la **probabilidad de conseguir los clientes necesarios** con `demand.reachability` (`references/pre-launch.md`). `pass` (alta): el embudo pesimista alcanza los clientes necesarios y el mercado ya paga por esto. `conditional` (media): solo alcanza con la conversión optimista → "viable si la conversión es ≥ X"; o falta prueba de que el mercado paga. Sin `reachability`, `conditional` (sin estimar) con el test de conseguir un compromiso en ≤ 60 días. Un compromiso firmado o pago adelantado (nivel ≥ 4) pasa directamente | Evidencia negativa (rechazos ≥ 2/3 de ≥ 5 contactados; pilotos pagados sin conversión); ni con la conversión optimista se llega; harían falta más del 10 % [P] de las cuentas alcanzables cada año | — |
| G2 | El margen pasa en un extremo del rango estimado y no en el otro → "Viable si horas por proyecto ≤ X" (punto de equilibrio por bisección) | Pierde dinero incluso en el extremo favorable | Falta el dato y no hay rango (pregunta básica) |
| G2b | El payback cambia dentro del intervalo de churn → "Viable si el churn mensual ≤ margen mensual / CAC"; un CAC con rango usa el mismo mecanismo | Payback > vida en ambos extremos | Sin estimación de CAC o de churn |
| G3 | Sin ingresos todavía, o cliente principal ≥ 50 % sin plan verificable → plan de diversificación con fecha; proveedor crítico o modelo sin alternativa probada → probarla antes del primer contrato | KO de due diligence (N04, N06, IA06) | — |
| G4 | Obligación legal sin plan **escrito con responsable y fecha** (`plan: {"owner", "by_date"}`); exigencia contractual del segmento sin plan y presupuesto; sector regulado sin prueba de nivel 1 | KO de due diligence | No se sabe dónde residen los titulares o qué exige el segmento |
| G7 | 24×7 sin cuadrante; SLA sin disponibilidad medida → no firmar el SLA hasta medirla en un piloto | Aritmética del SLA, penalizaciones sin tope, KO (N02, T10, T11, IA02) | Sin datos de operación |

Reglas comunes a las dos etapas desde v0.7.0:

- **Demanda sin documento.** Una cuenta en nivel ≥ 4 cuya única evidencia es la palabra del proponente (entradas `self_declared: true` sin documento de nivel 1) se lee como nivel 3, con una alerta. En la prueba de campo del 2026-11-11 el mismo proyecto autodeclarado salió en nivel 5 en dos pasadas y `unknown` en la tercera.
- **Plan de cumplimiento.** En `pre_launch` solo cuenta un plan escrito con responsable y fecha; una intención ("hay que revisar las obligaciones") es una condición, no un plan. Así las dos lecturas que dieron veredictos distintos en la prueba de campo dan el mismo resultado.
- **G7 y los KO.** Los códigos KO se revisan antes del `pass` por "sin SLA ni 24×7"; antes, un KO de persona clave (N02) nunca hacía fallar G7.

### 6b.2 Del estado de las compuertas al veredicto [P]

El procedimiento es determinista y se ejecuta en este orden. **Uno:** si alguna compuerta está en `fail`, el veredicto es **NO_GO**, con una condición de reversión por compuerta fallida (el dato concreto que la haría pasar). **Dos:** si ninguna falla pero alguna está en `unknown` con un dato P0 capaz de invertir el resultado (prueba de G6), el veredicto es **INSUFFICIENT_EVIDENCE**, con la lista de datos P0 y el test más barato para cada uno. **Dos bis (v0.7.0):** si alguna está en `conditional`, el veredicto es **CONDITIONAL_GO** y sus condiciones encabezan la lista. **Tres:** con todas en `pass`, se puntúan los módulos (6d). El veredicto es **CONDITIONAL_GO** si se cumple cualquiera de estas condiciones: algún módulo del núcleo económico (M7, M8, M9) tiene mediana ≤ 2; más del 50 % del swing del tornado procede de inputs con estado `assumption` (solo en `operating`: antes de abrir casi todo es supuesto y el extremo pesimista de cada rango cumple esa función); o queda por testear un supuesto crítico que afecta a un driver incluido en el 80 % del swing del tornado (decisión del usuario, 2026-11-10: la versión sin acotar enviaba casi toda idea temprana a CONDITIONAL_GO). En ese caso cada condición se escribe como hipótesis falsable con umbral y fecha. **Cuatro:** en otro caso, **GO**. Las condiciones de GO frente a CONDITIONAL_GO son nuevas (la fase 1 no las definía) y son [P].

### 6b.3 Agregación de varias ejecuciones [P]

Por defecto la Skill hace **N = 3** ejecuciones independientes, y **N = 5** en decisiones de alto impacto y en la calibración. Las cifras extraídas del input deben coincidir en todas (objetivo del 100 %, 6j); las compuertas de script se recalculan por ejecución sobre su ledger. El veredicto agregado es la **moda**. En caso de empate gana el más conservador según el orden NO_GO > INSUFFICIENT_EVIDENCE > CONDITIONAL_GO > GO, se marca `low_agreement` y se listan las compuertas o módulos que difirieron; el orden refleja que un GO falso cuesta más que un NO_GO falso a un fundador que solo puede arriesgar una pérdida asumible (Sarasvathy) [I]. También se marca `low_agreement` si el veredicto modal tiene menos de 4 de 5 (o 2 de 3) ejecuciones. Las puntuaciones 1–5 se agregan por **mediana** con rango intercuartílico; una desviación típica > 0,5 en un módulo se reporta como incertidumbre. La dispersión, no la confianza verbalizada, es la señal de incertidumbre ([Xiong et al. 2024](https://arxiv.org/abs/2306.13063)).



## Formato de entrada de `gates_and_score.py evaluate` [PROPUESTA]

`gate_input.json` se construye **desde el Evidence Ledger**: cada bloque lleva `ledger_ids` y ningún número entra sin id. Los campos ausentes se omiten (nunca se rellenan con cifras inventadas); la función los trata como `unknown`.

```json
{
  "evaluation_date": "2026-11-10",
  "stage": "pre_launch",
  "scope": {"archetype_per_line": ["S1"], "country_customer": "CO", "country_delivery": "CO",
            "currency": "COP", "horizon_m": 24, "seeks_vc": false, "ledger_ids": ["L1"]},
  "lines": [{
    "id": "servicios", "revenue_share": 1.0, "declared_archetype": "S1",
    "mechanisms": {"tm": 0.8, "fixed": 0.2, "managed": 0, "subscription": 0, "usage": 0, "resale": 0},
    "sells_expertise": false, "acv_median": null, "self_serve_majority": null,
    "inference_cost_share": null, "price_tied_to_model_usage": false, "owns_capacity": false,
    "agents": false, "human_share_cogs": null, "recurring_or_sla": false, "ip_assigned_to_client": false,
    "economics": {"kind": "services", "rate": 70, "realisation": 0.9,
                  "loaded_cost_per_paid_hour": 55, "utilisation": 0.45, "ledger_ids": ["L5", "L6"]}
  }],
  "intake": {"mode": "interactive", "unconfirmed_assumptions": []},
  "demand": {"accounts": [{"id": "acme", "segment": "pymes-retail", "level": 4, "economic_buyer": true}],
             "contacted_buyers": 6, "rejections": 1, "paid_pilots": 1, "paid_pilots_converted": 1,
             "reachability": {"clients_needed_per_year": 6, "reachable_accounts": 18000, "market_pays": true,
                              "contacts_per_month": {"low": 20, "high": 40},
                              "conversion": {"low": 0.01, "high": 0.05}, "ledger_ids": ["L30", "L31", "L32"]},
             "ledger_ids": ["L7"]},
  "concentration": {"top1_share": 0.30, "top3_share": 0.55,
                    "top1_contract": {"multi_year": false, "termination_for_convenience": true,
                                      "diversification_plan": {"target_top1_share": 0.35, "by_date": "2027-06-30",
                                                               "ledger_ids": ["L12"], "evidence_status": "fact"}},
                    "relationship_years": 3, "critical_suppliers": [{"name": "X", "alternative_tested": true}],
                    "model_provider": {"token_share": 0.9, "fallback_tested": false, "cm_at_x2": 0.1},
                    "credits_share": 0.0, "ko_codes": [], "ledger_ids": ["L8"]},
  "compliance": {"data_residence_known": true, "segment_requirements_known": true,
                 "rows": [{"row": "Ley 1581 de 2012", "type": "Legal", "applies": true, "compliant": false,
                           "plan": {"owner": "socio A", "by_date": "2027-01-15", "ledger_ids": ["L13"]},
                           "budget": true, "demanded_by_segment": false}],
                 "ko_codes": [], "ledger_ids": ["L9"]},
  "critical_assumptions": [{"id": "A1", "driver": "utilisation", "test": "dos clientes piloto pagados",
                            "days": 60, "tested": false, "hypothesis": "utilizacion >= 0,65",
                            "threshold": 0.65, "by_date": "2027-01-31", "ledger_id": "L10"}],
  "delivery": {"sla_promised": 0.999, "availability_measured": 0.9995, "needs_24x7": false,
               "penalties_capped": true, "ko_codes": [], "ledger_ids": ["L11"]},
  "p0_unknowns": [{"gate": "G2", "field": "realisation", "path": "lines.0.economics.realisation",
                   "low": 0.8, "high": 0.95, "cheapest_test": "facturas de los ultimos 6 meses"}],
  "modules": [{"id": "M7", "median": 3}, {"id": "M8", "median": 2}, {"id": "M9", "median": 3}],
  "tornado": {"assumption_swing_share": 0.35, "dominant_drivers": ["utilisation", "rate"]},
  "ledger": []
}
```

Claves por tipo de línea en `economics`:

| `kind` | Claves | Compuertas |
|---|---|---|
| `services` | `rate`, `realisation`, `loaded_cost_per_billable_hour` o (`loaded_cost_per_paid_hour` + `utilisation`); en proyectos a precio fijo, `price_per_project` + `hours_per_project` en lugar de `rate` (realización 1 por defecto) | G2 (tarifa efectiva frente a coste por hora facturable) |
| `product` | `arpa_m`, `margin` o `margin_recalculated` (R4), `variable_cost_m`, `recurring`, `cac`, `churn_m` o `churn_interval` | G2 (margen de contribución por cliente) y G2b (payback frente a 1/c) |
| `aix` | `price_per_task`, `pass1`, `c_task_p90` o (`inference_p90` + `other_cost_per_task` + `human_cost_per_task`) | G2 (T1: precio frente a C_task p90) |

`p0_unknowns[].path` usa puntos e índices (`lines.0.economics.realisation`). Con `low` y `high` documentados, G6 recalcula la compuerta en ambos extremos: si el estado coincide, la compuerta queda `resolved_by_bounds`; si no, en `operating` el veredicto es INSUFFICIENT_EVIDENCE con el test más barato, y en `pre_launch` el script busca por bisección el valor de equilibrio y la compuerta queda `conditional` con la condición "viable si `field` ≤ (o ≥) umbral" (`conditions[].threshold` y `direction`). Sin rango, el P0 se supone capaz de invertir el resultado (A5).

**Salida (v0.7.0).** `evaluate` devuelve además `stage` y `plain_answer`, una frase llana generada por el script a partir del veredicto y las compuertas ("Vale la pena probarlo en pequeño antes de abrirlo del todo: hay 3 condiciones…"). El informe la copia tal cual como primera línea.

**Plan de diversificación (G3, tras la auditoría REV-004).** Un plan solo evita el `fail` de G3 si es verificable: objeto con `target_top1_share` < 0,50, `by_date` como máximo a 12 meses de la evaluación, `ledger_ids` y `evidence_status` igual a `fact` o `estimate` (por ejemplo, LOI o contratos con clientes nuevos). Un `true` o un texto libre es una declaración: G3 falla igual y el motivo lo explica. Con un plan verificable, G3 pasa con una alerta que debe convertirse en condición con fecha.

**Validación de entradas.** Los mecanismos son fracciones en [0, 1] que suman como máximo 1 (`0.8`, no `"80%"`). Las tasas (churn, utilización, probabilidades) también van en [0, 1]. Un valor fuera de dominio devuelve `value: null` con `invalid_inputs: true` y un aviso, nunca un número complejo ni una excepción.

Decisiones confirmadas por el usuario (2026-11-10), codificadas como constantes del script: G1 sin evidencia por encima del nivel 2 → `unknown`; N = 3 ejecuciones (5 con `high_impact`) y desempate NO_GO > INSUFFICIENT_EVIDENCE > CONDITIONAL_GO > GO; regla (c) de CONDITIONAL_GO acotada a drivers del 80 % del swing; G3 falla con un cliente ≥ 50 % sin contrato plurianual protegido y avisa desde el 25 %.
