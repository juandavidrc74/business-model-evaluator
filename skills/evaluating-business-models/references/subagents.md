# Subagentes: roles, contratos y fusión

> Leer solo si el entorno ofrece la herramienta de subagentes. Sin ella, la Skill funciona igual en secuencia. Arquitectura [PROPUESTA] adoptada tras la auditoría independiente de noviembre de 2026 (sección R8): cómputo determinista central y agentes solo donde aportan juicio independiente o fuentes diversas.

## Contenido

- Principios
- Roles y contratos
- Fusión de ledgers
- Ejecuciones independientes
- Qué no delegar
- Límites del modo consorcio

## Principios

1. **Un solo coordinador** (la sesión que cargó la Skill) congela el ledger, construye `gate_input.json`, ejecuta todos los scripts, fusiona y firma el veredicto. Ningún subagente emite el veredicto final ni calcula compuertas aritméticas.
2. **Aislamiento cognitivo no es aislamiento de datos.** Un subagente recibe solo lo que su tarea necesita: a los investigadores web nunca se les pasa la propuesta completa ni datos privados del usuario, solo preguntas acotadas.
3. **Los candidatos no son hechos.** Lo que devuelve un investigador entra al ledger como candidato; el coordinador lo valida (fuente recuperada, fecha, cita ≤ 15 palabras, `scan_injection.py`) antes de usarlo.
4. **Coste.** Cada subagente consume cuota del plan. Por defecto: hasta 3 investigadores, N = 3 evaluadores (5 en alto impacto), 1 verificador y 1 abogado del diablo. Si el usuario pide ahorrar, haz el trabajo en secuencia.

## Roles y contratos

| Rol | Definición | Recibe | Devuelve (JSON) | Límites |
|---|---|---|---|---|
| Investigador de dominio | `agents/domain-researcher.md` | Lista de preguntas (p. ej. "número de empresas CIIU 6201 en Colombia con 10–49 empleados"), fuentes permitidas (`data-sources.md`), presupuesto de llamadas, plantilla de entrada del ledger | `{"candidates": [entradas de ledger con status, value, unit, source{type,tier,url,title}, quote, publication_date, access_date, retrieved_by_tool, country, definition, limitations]}`, `{"unanswered": [...]}`, `{"injection_findings": [...]}`, `{"web_calls": n}` | Sin veredicto; sin promediar; "contact sales" = `unknown`; sin cuentas ni formularios |
| Evaluador independiente | General (o el propio coordinador en secuencia) | La propuesta, el ledger **congelado** y estas instrucciones, idénticas para todos | `run_k.json`: `extracted_figures{}`, estados de las compuertas de juicio (G1, G4 filas, G5 tests), `modules[]` con puntuaciones 1–5 o null y sus ids del ledger | No ve otras ejecuciones; no recalcula aritmética; no añade cifras al ledger |
| Verificador de evidencia | `agents/evidence-verifier.md` (solo Read/Grep/Glob) | `evaluation.json`, `informe.md` | Lista de afirmaciones sin soporte, citas que no coinciden y severidad | Solo lectura; no completa cifras |
| Abogado del diablo | `agents/devils-advocate.md` (solo Read/Grep/Glob) | Tesis neutra, ledger fusionado, veredicto provisional | `{"strongest_case_against": "...", "evidence_ids": [...], "tests_that_would_resolve": [...]}` | No cambia el veredicto; solo argumentos con ids del ledger |

## Fusión de ledgers

`aggregate_runs.py merge_ledgers '{"ledgers": [[...], [...]]}'`:

- Clave de deduplicación: afirmación + URL de la fuente + fecha de publicación + país + unidad. Duplicados exactos se colapsan conservando los ids de origen (`merged_from`).
- Misma afirmación, país y unidad con valores distintos → `conflict_group` y estado `contradiction` en todos los miembros. **Nunca se promedian**: el informe muestra el rango atribuido con ambas fuentes y fechas.
- Si el conflicto es numérico, `merge_ledgers` devuelve `bounds` (mínimo y máximo) y un `suggested_p0_unknown`. Si la cifra alimenta una compuerta, añádelo a `gate_input.json → p0_unknowns` con su `path`: G6 recalcula la compuerta en ambas cotas. Si el estado coincide, el conflicto no cambia el veredicto (`resolved_by_bounds`); si no, el veredicto es INSUFFICIENT_EVIDENCE con el test que resuelve la discrepancia. Este es también el procedimiento para cifras contradictorias dentro de la propia propuesta (por ejemplo, un churn en el resumen y otro en un anexo).
- Tras fusionar, el coordinador renumera ids, vuelve a pasar `check_staleness.py` y reconstruye `gate_input.json`. Las compuertas se recalculan sobre el ledger fusionado.

## Ejecuciones independientes

1. Congela el ledger (sin más cambios durante las ejecuciones).
2. Lanza N evaluadores con instrucciones idénticas; si es posible, reordena las secciones de la propuesta entre ejecuciones para medir sensibilidad al orden.
3. Ejecuta `gates_and_score.py evaluate` una vez por ejecución con las compuertas de juicio de esa ejecución (las aritméticas salen iguales; si no, es un error del ledger).
4. `aggregate_runs.py aggregate --file runs.json`: moda del veredicto con desempate conservador, medianas e IQR de módulos, errores de extracción y compuertas de script inconsistentes. Una ejecución incompleta se marca y cuenta como `low_agreement`, nunca se borra en silencio.

## Qué no delegar

- Aritmética, compuertas, agregación y validaciones: siempre scripts del coordinador.
- La decisión de qué fuentes son aceptables y si un candidato entra al ledger.
- El texto final del informe (se deriva de `evaluation.json`).

## Límites del modo consorcio

Decláralos en el informe. La comprobación de afirmaciones contra el ledger es léxica, no un modelo NLI semántico (una negación indirecta puede escaparse); el aislamiento de carpetas por agente depende de las herramientas de solo lectura de cada agente, no de un aislamiento físico; la validación de esquemas es propia (stdlib) y cubre el subconjunto que usa `specialist_response.schema.json`, no todo Draft 2020-12.
