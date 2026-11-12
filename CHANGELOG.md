# Changelog

## 0.7.3 — 2026-11-12 · G1 estima la probabilidad de conseguir clientes

En la prueba de campo del 2026-11-12 (con entrevista interactiva), el veredicto fue CONDITIONAL_GO. Aun así, el informe giraba en torno a "no tienen clientes", y la primera condición era firmar un compromiso en 60 días. El usuario señaló que, para un negocio por abrir, esa es la situación de partida, y que la pregunta es si es probable conseguir clientes. Decisión del usuario: G1 se rediseña en `pre_launch`.

- **G1 en `pre_launch`.** Usa `demand.reachability` (`references/pre-launch.md`), con cinco datos:
  - clientes necesarios al año, o costes fijos y aportación por cliente;
  - cuentas alcanzables contadas en un registro;
  - prueba de que el mercado ya paga;
  - contactos al mes;
  - conversión, en rango.

  `demand_likelihood` calcula los clientes esperados en los extremos pesimista y optimista, la penetración y la conversión mínima:
  - probabilidad **alta** (`pass`): el embudo pesimista alcanza y el mercado paga;
  - **media** (`conditional`): "viable si la conversión es ≥ X", que se mide en los primeros contactos;
  - **baja** (`fail`): ni con el embudo optimista se llega, o haría falta más del 10 % [P] de las cuentas alcanzables al año;
  - **sin estimar** (`conditional`): falta alguno de los cinco datos.

  Un compromiso documentado sigue pasando directamente y la evidencia negativa sigue fallando. **Ya se puede llegar a GO antes del primer cliente.**
- **Respuesta directa.** `plain_answer` termina con la probabilidad y sus cifras. El informe tiene una línea para la probabilidad debajo de las compuertas.
- **Entrevista.** Pregunta nueva `sales_capacity`: cuántos contactos comerciales al mes podéis hacer entre todos.
- **Modo de la entrevista en el resultado.** `gate_input.json` lleva `intake`; `evaluate` lo devuelve y `validate_output.py` lo exige en `pre_launch`. En la prueba, el modelo no lo había copiado.
- **Carpeta de salida.** Los archivos se escriben junto a la propuesta. En la prueba quedaron en la carpeta superior.
- **Casos.** D06 acepta GO o CONDITIONAL_GO y exige que el informe declare la probabilidad.
- **Límite conocido.** En el modo consorcio, `reachability` aún no llega a G1, porque el compilador descarta los números de la entrada base; G1 queda "sin estimar".
- **Pruebas.** 14 nuevas en `test_demand_likelihood.py`.

## 0.7.2 — 2026-11-12 · El modo interactivo es el predeterminado

Al probar la skill en otra IA, el modelo no hizo ninguna pregunta. La causa probable estaba en las instrucciones: decían que, si no podía preguntar, pasara al modo no interactivo, pero no decían cuándo se considera que no puede. Además, la referencia mencionaba la herramienta de preguntas de Claude Code, que otras IAs no tienen.

- **Sin herramienta de preguntas, se pregunta en el chat.** La skill escribe la ronda como lista numerada y termina su turno hasta recibir la respuesta. No tener la herramienta nunca justifica dejar de preguntar.
- **`non_interactive` solo tiene dos motivos,** que se declaran en `mode_reason`:
  - `user_asked_no_questions`: el usuario pidió que no se le pregunte;
  - `no_human`: nadie puede responder, como en una evaluación automática.
- **`check_intake.py`** exige el campo `mode`. Si el modo es `non_interactive` sin un motivo válido, lo trata como interactivo y pide las preguntas.
- **Informe y esquema.** `evaluation.json` gana el bloque opcional `intake` (modo, motivo y supuestos sin confirmar). El informe lo muestra justo debajo de la respuesta directa, así se ve enseguida si hubo entrevista.
- **Casos de evaluación.** Llevan una línea que dice que nadie puede responder, para que tomen el camino `no_human`.
- **Pruebas.** 3 nuevas; 16 en `test_intake.py`.

## 0.7.1 — 2026-11-12 · Entrevista previa por rondas

En la prueba de campo de la versión 0.7.0 el veredicto dependió de datos que nadie preguntó: el nivel de experiencia de los socios (se supuso senior, y con el perfil estándar el precio propuesto sí cubre costes), el horizonte y la intención de buscar capital riesgo. El usuario pidió apoyarse en la skill Grill me. No se puede llamar desde esta skill: solo la activa el usuario y no viene con el plugin. Por eso se adapta su método (skill `grilling` de Matt Pocock, `mattpocock/skills`, licencia MIT).

- **Entrevista por rondas** (`references/intake.md`). En cada ronda la skill hace todas las preguntas cuyos requisitos ya están respondidos, numeradas y con una respuesta recomendada y su fuente. Lo que dice la propuesta no se pregunta. Antes de calcular, cierra con un resumen que los socios confirman. Aceptar una recomendación no la convierte en evidencia.
- **`scripts/check_intake.py`.** Lee `intake.json` y devuelve la frontera de preguntas de la ronda siguiente (`next_round`). Impide evaluar (`can_evaluate: false`, código de salida 1) en cuatro casos:
  - falta un dato;
  - un dato que solo saben los socios se supuso sin que lo confirmaran;
  - hay un `unknown` que los socios no dijeron;
  - el resumen final no está confirmado.
  En modo no interactivo, esos datos entran como rango de referencia (nunca como valor puntual), y si falta un dato básico el resultado es `insufficient`, con las preguntas para el informe.
- **Preguntas nuevas.** El nivel de experiencia de los socios (que fija su salario de mercado, R4), el horizonte, el capital riesgo, cómo conseguirán clientes, los compromisos de servicio y, según el arquetipo, el churn esperado o el coste de IA por tarea.
- **SKILL.md.** El Paso 0 pasa a ser la entrevista. Los límites del modo consorcio pasan a `references/subagents.md` para respetar el tamaño máximo.
- **Pruebas.** 13 nuevas en `test_intake.py`.

## 0.7.0 — 2026-11-11 · Orientada a negocios que todavía no venden

Decisión del usuario tras la prueba de campo del 2026-11-11 (propuesta de automatización para pymes): la pregunta principal es si vale la pena **abrir** el negocio. En esa prueba el resultado fue INSUFFICIENT_EVIDENCE porque varias compuertas exigían datos que solo existen después de abrir.

- **Etapa.** `gate_input.json` lleva `stage`: `pre_launch` (por defecto) u `operating` (reglas anteriores). Nuevo estado de compuerta `conditional`: lo que solo se mide después de abrir se convierte en una condición con umbral o fecha.
  - G1: sin compromiso firmado o pago adelantado, la condición es conseguirlo en 60 días. Solo pasa con nivel ≥ 4. La evidencia negativa sigue fallando.
  - G2 y G2b: con un rango estimado en `p0_unknowns`, el script calcula el punto de equilibrio por bisección ("viable si horas por proyecto ≤ 117,4"). Nuevos campos `price_per_project` y `hours_per_project`.
  - G3: depender de 1 o 2 clientes al inicio, o no tener aún una alternativa probada a un proveedor, da una condición con fecha. Los KO siguen fallando.
  - G4: una obligación sin plan escrito con responsable y fecha es una condición.
  - G7: un SLA sin disponibilidad medida, o una guardia 24×7 sin cuadrante, es una condición.
  - Regla (b) de CONDITIONAL_GO: no se aplica antes de abrir.
- **Veredictos en `pre_launch`.** GO = abrirlo (números bien en el extremo pesimista y al menos un compromiso documentado); CONDITIONAL_GO = probarlo en pequeño; NO_GO = así no; INSUFFICIENT_EVIDENCE = faltan datos básicos.
- **Respuesta directa.** `evaluate` devuelve `plain_answer`, y el informe la copia como primera línea.
- **Preguntas previas.** La skill pregunta antes de evaluar precio, horas, costes fijos, compromisos y plan legal. Nueva referencia `references/pre-launch.md`.
- **Correcciones de la prueba de campo.**
  - G7 revisa los KO (N02, persona clave) antes del `pass` sin SLA.
  - Una cuenta en nivel ≥ 4 sin documento se lee como nivel 3.
  - Un plan de cumplimiento solo cuenta si está escrito con responsable y fecha. Con esto, las lecturas que dieron veredictos distintos entre pasadas dan el mismo resultado.
  - Las pasadas van en subagentes distintos cuando los hay; si no, se marcan como no independientes.
  - El verificador de evidencia se vuelve a pasar sobre la versión corregida.
- **Esquema.** `stage`, `plain_answer` y el estado `conditional` en `evaluation.schema.json`.
- **Casos.** D06 pasa de INSUFFICIENT_EVIDENCE a CONDITIONAL_GO y su propuesta describe ahora un negocio sin abrir. Los casos de negocios que ya facturan llevan `stage: operating`. El ejemplo resuelto documenta la cuenta de nivel 5 con un contrato y conserva su veredicto (NO_GO) y el estado de cada compuerta.
- **Pruebas.** 12 nuevas en `test_pre_launch.py`; 162 en total.

## 0.6.2 — 2026-11-11 · Proveedores críticos y plan de diversificación

- **Proveedores críticos.** Nuevo predicado `PRED_CRITICAL_SUPPLIER_ALTERNATIVE_TESTED` (P0-CC-08, G3, niveles 1–2), con una afirmación por proveedor (`sup_NN`). Está en los tres esquemas, en la matriz P0 y en el prompt de `risk-compliance-analyst`. El compilador descarta `alternative_tested` de la entrada base: la alternativa solo cuenta como probada si el especialista lo demuestra para ese proveedor.
- **Plan de diversificación.** Solo se conserva si `PRED_DIVERSIFICATION_PLAN_VERIFIABLE` está probado. Su estado de evidencia ya no sale de la entrada base.
- **Corrección.** `allowed_tiers` lee ahora los P0 transversales.
- **Pruebas.** T01 actualizada a 17 predicados. Tres pruebas nuevas; 150 en total.

## 0.6.1 — 2026-11-11 · Tercera auditoría (cuatro vías fail-open)

Ver la sección 5 de `AUDITORIA_FINAL.md`.

- **C1. G1 y G3 solo con evidencia de los especialistas.** La entrada base ya no aporta cuentas, niveles de demanda, cuotas de concentración ni protecciones contractuales. G1 se construye a partir de los predicados de demanda.
- **C2. Operación 24×7 sin dotación ni cuadrante probado:** G7 da `unknown`.
- **C3 y C4. Niveles de evidencia de cada predicado leídos de `p0_requirements.json`.**
  - Residencia de datos: un `false` se propaga.
  - Cumplimiento sectorial, contrato plurianual y contrato firmado: exigen nivel 1.
  - Con el modificador V, G4 exige cumplimiento sectorial probado.
- **R1 y R2.**
  - Mensaje claro al resolver una objeción no registrada.
  - Un arquetipo desconocido queda registrado en `compiler_log` y G2b da `unknown`.
- **R3.** La prueba de empaquetado cubre los archivos del consorcio.

Seis pruebas nuevas; 147 en total. El ejemplo completo no cambia.

## 0.6.0 — 2026-11-11 · Cierre de los cuatro bloqueantes del consorcio

Nuevo `scripts/consortium.py`, que solo usa la biblioteca estándar.

- **Validación de respuestas en tiempo de ejecución.** Comprueba la rama según `status`, la jurisdicción exacta de `module_scores` leída del esquema, los campos obligatorios y sobrantes, los enums, los patrones y los tipos. El compilador descarta entera cualquier respuesta inválida.
- **Bucle de objeciones de producción** (`RemandLoop` y la CLI `remand`):
  - deduplica por huella SHA-256;
  - admite 1 devolución, o 2 en operaciones críticas;
  - para refutar hace falta evidencia en el ledger;
  - una objeción confirmada da NO_GO y una abierta deja como mucho INSUFFICIENT_EVIDENCE;
  - el veredicto nunca sube.
- **Polaridad adversa.** Comprobación léxica: un predicado `true` que el texto de su entrada del ledger contradice baja a `unknown`.
- **G4 y G7** leen ya los predicados de cumplimiento sectorial, arquitectura del SLA y cuadrante de turnos 24×7. El valor `true` solo se acepta con evidencia de nivel 1–2.

T04, T07 y T08 dejan de ser tautológicas e importan el código de producción. SKILL.md cambia la lista de "no implementado" por los límites reales, y `AUDITORIA_FINAL.md` está actualizada. Pruebas: 141.

## 0.5.0 — 2026-11-11 · Auditoría final del arquitecto sobre las fases 1–4

Ver `AUDITORIA_FINAL.md`. Corregidas ocho vías fail-open del compilador y de G2b/G3, que se reproducían contra el código de producción: ledger vacío aceptado, nivel de evidencia autodeclarado, conflictos entre especialistas sobrescritos, catálogos abiertos, números de la entrada base conservados, claves de la rama de IA desalineadas con `gate_g2`, P-AI-APP no recurrente, churn 0 y CAC 0 aprobados, y contrato plurianual sin documento. El manifiesto sella ahora todos los scripts, activos, prompts y SKILL.md con la versión real del plugin. SKILL.md incorpora el "Modo consorcio" y declara lo que aún no está implementado (NLI, bucle de objeciones, aislamiento de carpetas, validación de esquemas en tiempo de ejecución). 11 pruebas nuevas contra código de producción; 138 en total.

## 0.2.1 — 2026-11-10 · Auditoría de Antigravity

Fuente: `Proyectos_Personales/revision plugin antigravity/` (16 hallazgos), restaurada tras comprobarse que la primera copia era la auditoría de Codex sobrescrita en una carpeta de trabajo compartida (ahora los hashes difieren de los de Codex). Cada hallazgo se reprodujo contra la versión 0.2.0.

| ID (Antigravity) | Sev. | Decisión | Motivo / qué se hizo |
|---|---|---|---|
| REV-001 `ltv_discounted` ÷ 0 | Crítica | Ya corregido en 0.2.0 | Devuelve `null` con aviso (REV-003 de Codex). |
| REV-002 churn complejo | Crítica | Ya corregido en 0.2.0 | Validación de dominio. |
| REV-003 años y "2,3 M" en `check_claims` | Alta | Ya corregido en 0.2.0 | Fechas escritas y sufijos normalizados. |
| REV-004 cifras en palabras | Alta | Ya corregido en 0.2.0 | Se marcan como no verificables. |
| REV-005 Base64, multilingüe, falso positivo | Alta | Ya corregido en 0.2.0 | |
| REV-006 casos anidados en `evals/cases/` "no descubribles" | Alta | **Rechazado** | La documentación oficial de `claude plugin eval` (leída el 2026-11-10) dice que un directorio es un caso si contiene `prompt.md` o `case.yaml` y permite anidarlos bajo una carpeta de agrupación. Mover los casos a la raíz de `evals/` mezclaría `unit/` y `harness/` con los casos sin ningún beneficio. La auditoría de Codex llegó a la misma conclusión. |
| REV-007 graders `llm` | Alta | Ya corregido en 0.2.0 | 155 de 191 graders son ahora deterministas. |
| REV-008 `price_schedule` | Alta | Ya corregido en 0.2.0 | |
| REV-009 pruebas de `market_sizing` y métricas | Media | Ya corregido en 0.2.0 | |
| REV-010 runway negativo | Media | Ya corregido en 0.2.0 | Devuelve 0 con aviso de caja agotada. |
| REV-011 mediana frente a media | Media | Ya corregido en 0.2.0 | Parámetro `t_esc_is_median`. |
| REV-012 descripción solo en español | Media | Ya corregido en 0.2.0 | |
| REV-013 validador sin `additionalProperties` | Media | **Aceptado** | El validador interno soporta `additionalProperties: false` y el esquema lo aplica en el nivel superior: una clave mal escrita (`verdit`) ahora falla. Se añadieron al esquema los campos legítimos que faltaban. |
| REV-014 plantilla sin resumen ni glosario | Media | Ya corregido en 0.2.0 | |
| REV-015 `${CLAUDE_SKILL_DIR}` en PowerShell | Baja | **Aceptado como documentación** | Dentro de Claude Code la variable se sustituye antes de ejecutar; el README explica cómo definirla para ejecuciones manuales en bash y PowerShell. |
| REV-016 Krippendorff O(N²) | Baja | Ya corregido en 0.2.0 | |
| Fusión de ledgers por cotas | — | **Aceptado** | `merge_ledgers` devuelve `bounds` y un `suggested_p0_unknown` para cada conflicto numérico; G6 recalcula la compuerta en ambas cotas. Documentado en `subagents.md` y `evidence-rules.md`. |
| Cobertura MUST: RF-FLOW-02 sin M16 | — | **Rechazado** | La tabla de SKILL.md cubre M16 ("síntesis (M16)") y `test_packaging` lo comprueba para M1–M16. |
| Cobertura MUST: RT-FIN-10, RT-CASH-07 sin prueba | — | **Aceptado** | Pruebas de coste del capital con la CRP de Colombia (GEO-012) y conversión a COP, y de SDE positivo con EBITDA ajustado negativo. |
| Cobertura MUST: RQ-EVAL-06 en CI | — | **No aplicable sin modelo** | D.09, D.11 y D.12 necesitan ejecuciones con el modelo; sus graders ya son deterministas, pero no pueden correr en CI sin consumir cuota. |
| Casos D.16–D.25 propuestos | — | **Aceptado en parte** | Ya existían D.16 (vertical), D.22 (inglés) y equivalentes de D.21/D.23. Se añadieron como casos: panadería fuera de dominio (G0 declina), margen del resumen desmentido por el anexo (R4 → G2b fail) y créditos cloud que expiran (R5 → G2 fail). Pass-through, transferencias internas y WACC con CRP se cubren con pruebas unitarias deterministas. No se añadieron "benchmark vencido" ni "informe de pago aportado" como casos: ya los cubren `check_staleness` y las reglas de fuentes opcionales. |
| R7 "prueba de uso real" | — | Nota | Fue un recorrido simulado a mano, no una ejecución con el modelo; la prueba de punta a punta sigue pendiente. |

Pruebas: 114 (antes 106).

## 0.2.0 — 2026-11-10 · Correcciones tras la auditoría independiente de Codex

Fuente: `Proyectos_Personales/revisión ChatGPT/Auditoría Codex/` (16 hallazgos REV-001…REV-016 y notas R4/R8). En ese momento la carpeta de Antigravity contenía una copia de esta misma auditoría (ver 0.2.1).

Cada hallazgo se reprodujo contra el código antes de decidir. Todos se reprodujeron.

| ID | Sev. | Decisión | Qué se hizo |
|---|---|---|---|
| REV-001 | Alta | **Aceptado y ampliado** | `check_claims.py` solo acepta como respaldo las secciones de evidencia de `evaluation.json` (nunca `injection_findings`, texto libre ni descripciones `claim`). Además se descubrió que aceptaba cifras del texto del atacante. Normaliza sufijos (`2,3 M`, `millones`, `k`, `bn`), ignora fechas escritas y marca cifras escritas en palabras. Se corrigió un falso "mes" (`Margen` se leía como `mar`). |
| REV-002 | Alta | **Aceptado** | `scan_injection.py`: patrones en francés, portugués, italiano y alemán, decodificación y nuevo escaneo de Base64, y `role_claim` restringido a órdenes dirigidas al asistente. Se documenta como ayuda heurística, no barrera; SKILL.md y la política lo dicen explícitamente. Precisión verificada con textos legítimos (0 falsos positivos en la batería). |
| REV-003 | Alta | **Aceptado** | Validación de dominio (`check_domain`) en churn, LTV, payback, utilización, runway, WACC, NPV, pass^k, Beta, mercado, Monte Carlo y clasificación. Devuelve `value: null` con `invalid_inputs`, nunca complejos ni excepciones; la CLI convierte cualquier error aritmético en error estructurado. |
| REV-004 | Alta | **Aceptado** | Un plan de diversificación solo mitiga G3 si es verificable (objetivo < 50 %, fecha ≤ 12 meses, evidencia `fact`/`estimate` en el ledger). Un `true` o texto libre ya no evita el `fail`. Se actualizaron el informe ampliado (6b.1), los requisitos (decisión 4) y `gates.md`. |
| REV-005 | Alta | **Aceptado** | Con el formato oficial de `claude plugin eval` (leído el 2026-11-10): 138 de 169 graders (155 de 191 en 0.2.1) pasan a deterministas (`regex` sobre `evaluation.json`, `file_exists`, `tool_used`, `tool_order`); `llm` solo para juicio semántico. CI en `.github/workflows/ci.yml` (Linux y Windows, Python 3.10 y 3.13). |
| REV-006 | Alta | **No aplicable al código** | La ejecución con el modelo falló por el sandbox del entorno del auditor (`EACCES`, AppContainer), no por la Skill. Sigue pendiente ejecutar D.01/D.05/D.08 con el modelo (consume cuota). |
| REV-007 | Media | **Aceptado** | `price_card` aplica `price_schedule` según la fecha y avisa de cambios anunciados. |
| REV-008 | Media | **Aceptado en parte** | No era un error: `human_cost` usa medias y `simulate_tasks` una lognormal con mediana. Se documenta y se añade `t_esc_is_median` + `t_esc_sigma` para convertir mediana a media. |
| REV-009 | Media | **Aceptado** | Pruebas de `market_sizing` y `consistency_metrics` (adaptadas de las del auditor, que afirmaban los defectos, invertidas para exigir el comportamiento correcto) con valores de referencia publicados. |
| REV-010 | Media | **Aceptado** | SKILL.md documenta H0 completo (ingresos o margen ≥ 20 %, o línea tesis) y su precedencia. |
| REV-011 | Media | **Aceptado en parte** | Descripción bilingüe (frase en inglés) y redactada en tercera persona. Se mantiene la tercera persona porque es la recomendación de las buenas prácticas de Skills, aunque el auditor no la encontró como obligatoria. |
| REV-012 | Media | **Aceptado** | `validate_benchmarks.py` usa por defecto `assets/benchmarks.json` relativo al script. |
| REV-013 | Media | **Pendiente, no es defecto** | Cotejo externo de una muestra de benchmarks y licencias: requiere visitar fuentes; queda como tarea de mantenimiento. |
| REV-014 | Media | **Aceptado en parte** | No se refrescan GEO-008/GEO-010 a mano (la TRM caduca a diario y el diseño ya obliga a reconsultarla). Se corrigió `check_staleness.py`: modo inventario (`ok_for_gates: null`) frente a modo evaluación, que solo bloquea lo que la evaluación usa; antes una ficha vencida no usada bloqueaba todo. |
| REV-015 | Baja | **Aceptado** | Alfa de Krippendorff calculado con matriz de coincidencias; reproduce 0,743 / 0,849 / 0,815 (nominal / intervalo / ordinal) del conjunto canónico. |
| REV-016 | Baja | **Aceptado** | Plantilla con resumen de cinco líneas, condiciones de reversión con evidencia/responsable/fecha, próximos pasos por plazo y glosario. |
| R4 (nota) | — | **Aceptado** | `fetch_open_data.py` bloquea redirecciones fuera de la lista blanca o sin HTTPS. |
| R8 (subagentes) | — | **Aceptado** | Arquitectura híbrida: coordinador único que calcula; `agents/domain-researcher.md` (web, devuelve candidatos al ledger), `agents/devils-advocate.md` (solo lectura); contratos en `references/subagents.md`; `merge_ledgers` (deduplica, agrupa conflictos sin promediar) y ejecuciones incompletas marcadas. |
| §7 casos | — | **Aceptado en parte** | Nuevos casos D.16–D.19: propuesta en inglés, fuera de dominio (acción cotizada), cifras contradictorias y SaaS vertical con pagos embebidos. Los demás casos sugeridos (pass-through, transferencias internas, créditos, WACC/CRP, benchmark vencido) ya tienen pruebas unitarias deterministas. |

Otros añadidos: ejemplo completo generado por los scripts (`assets/example/`, `references/worked-example.md`) y rutas de salida fijas (`evaluation.json`, `gate_input.json`, `informe.md`) para que los graders sean deterministas.

Pruebas: 106 (antes 79), todas en verde con `python -I -S -m unittest discover -s evals/unit -t evals/unit`.

## 0.1.0 — 2026-11-10

Primera versión: método CEST, 14 scripts, 18 referencias, base de 250 benchmarks, 15 casos de evaluación y 79 pruebas.
