# Reglas de evidencia y antifabricación

> Leer al construir el Evidence Ledger y antes de escribir cualquier cifra. Estas reglas son el mecanismo central contra la invención de datos. Etiquetas: [DOC] documentado por Anthropic; [PROPUESTA] diseño propio de la investigación.

## Contenido

- Por qué existe el ledger
- Estados, tiers y prioridades
- Las seis reglas no negociables
- Cómo extraer evidencia de documentos largos
- Fuentes del proponente, web y base de benchmarks
- Antisicofancia
- Ejemplo de entradas

## Por qué existe el ledger

Una evaluación de negocio que mezcla datos del proponente, benchmarks y suposiciones del evaluador es indistinguible de una opinión. El ledger separa cada afirmación con su origen para que (a) las compuertas solo se alimenten de evidencia válida, (b) `check_claims.py` pueda verificar que ningún número del informe se inventó y (c) otra persona pueda auditar el veredicto. [DOC] Anthropic recomienda permitir "no sé", extraer citas antes de analizar y retirar las afirmaciones sin cita; estas técnicas reducen pero no eliminan las alucinaciones, por eso además hay scripts de verificación [PROPUESTA].

## Estados, tiers y prioridades

| Campo | Valores | Significado |
|---|---|---|
| `status` | `fact` | Documentado (cita del proponente, fuente recuperada o salida de script) |
| | `estimate` | Derivado con método explícito de fuentes con fecha; calidad declarada |
| | `assumption` | Supuesto etiquetado, con rango si es un driver; nunca alimenta compuertas por sí solo |
| | `unknown` | Falta el dato: se propaga y deja la puntuación del módulo en `null` |
| | `contradiction` | Dos fuentes discrepan: se muestran ambas, nunca se promedian |
| `source.tier` | 1 | Fuente primaria oficial, filing, API oficial, documento firmado |
| | 2 | Informe con método transparente, documento del proponente con soporte |
| | 3 | Proveedor o consultora con conflicto declarado, prensa especializada |
| | 4 | Conocimiento del modelo o fuente no recuperada en la sesión: **no sostiene compuertas ni puntuaciones ≥ 4** |
| `priority` | P0 | Puede cambiar una compuerta o el veredicto |
| | P1 | Cambia una puntuación de módulo |
| | P2 | Contexto |
| `retrieved_by_tool` | `true` solo si la URL o el archivo se abrió **en esta sesión** | |
| `self_declared` | `true` para cifras del proponente sin documento que las respalde | |

## Las seis reglas no negociables

1. **Un número sin fuente solo existe como supuesto etiquetado** (`status: assumption`, `source.type: none`), con rango si es un driver.
2. **El tier 4 no sostiene compuertas** ni puntuaciones ≥ 4: `gates_and_score.py` convierte en `unknown` una compuerta alimentada solo por tier 4.
3. **`unknown` se propaga**: deja la puntuación en `null` y, si es P0, pasa por la prueba de G6.
4. **Las contradicciones se muestran, no se promedian** (rango atribuido con ambos ids y fechas). Si la cifra en conflicto alimenta una compuerta, se convierte en un `p0_unknowns` con `low` = mínimo y `high` = máximo: G6 decide si el conflicto puede invertir el veredicto (`aggregate_runs.py merge_ledgers` devuelve las cotas; ver `subagents.md`).
5. **`check_claims.py` falla** si un número del informe no está en el ledger ni en la salida de un script, o si un id de benchmark aparece sin fecha.
6. **El Markdown se deriva de `evaluation.json`**, nunca al revés.

## Cómo extraer evidencia de documentos largos

1. Leer el documento completo y extraer **primero** citas literales (≤ 15 palabras cada una) de las cifras y afirmaciones relevantes, con su página o sección.
2. Crear una entrada del ledger por cita. Toda entrada `fact` del proponente lleva `quote`.
3. Analizar después, citando ids del ledger. Si una afirmación del análisis no tiene cita ni salida de script, retirarla o convertirla en `assumption`.
4. Decir "no consta en el documento" cuando algo no está. Es una respuesta válida y preferible a un número plausible.

## Fuentes del proponente, web y base de benchmarks

- **Proponente**: sus cifras son `self_declared` salvo que haya documento (contrato, factura, extracto). Una proyección del fundador nunca es evidencia de demanda ni de SOM.
- **Web**: solo cuenta si se abrió en la sesión (`retrieved_by_tool: true`) y se pasó por `scan_injection.py`. Presupuesto por defecto de ~30 llamadas por evaluación; lo no investigado queda `unknown`.
- **Base de benchmarks**: el registro hereda `evidence_quality` y `tag`; citar siempre id + fecha de publicación + periodo de los datos. Ver `data-sources.md` para las reglas de uso (aptitud para compuertas, caducidad, arquetipo, conflictos).
- **País**: todo dato lleva `country`, `reference_period`, `unit_of_analysis` y `transferability`. Un benchmark de otro país sin ajuste documentado se marca `not_transferable` y no entra en la puntuación (`geo-adaptation.md`, regla 11).
- **Comparar con la misma definición** (margen de MSP con o sin mano de obra de entrega; NRR por cohorte frente a promedio).

## Antisicofancia

[PROPUESTA, sobre Sharma et al. y Lane et al. 2025]

- Reformular la propuesta en **tercera persona neutra** antes de evaluarla (quitar adjetivos y entusiasmo del autor).
- El veredicto **solo cambia con evidencia nueva** registrada en el ledger. Insistir, mostrar frustración o invocar autoridad no es evidencia: se reconoce la preocupación, se mantiene el veredicto y se dice qué dato concreto lo cambiaría.
- Incluir siempre el **caso más fuerte en contra**, también en un GO.
- Presentar la evidencia en **tablas escuetas**, no en narrativa persuasiva.
- La confianza verbalizada no se usa como señal de incertidumbre: la señal es la dispersión entre ejecuciones (`aggregate_runs.py`).

## Ejemplo de entradas

```json
[
  {"id": "L5", "claim": "Tarifa horaria estándar", "status": "fact", "value": 70, "unit": "USD/h",
   "source": {"type": "proposal_document", "tier": 2, "title": "Plan de negocio v3, p. 12", "url": null},
   "quote": "nuestra tarifa estándar es de 70 USD por hora", "priority": "P0", "tag": "[D]",
   "self_declared": true, "module": "M8", "gate": "G2"},
  {"id": "L6", "claim": "Utilización facturable", "status": "assumption", "value": 0.45, "unit": "fraccion",
   "source": {"type": "none", "tier": 4, "title": null, "url": null}, "quote": null, "priority": "P0",
   "tag": "[P]", "module": "M8", "gate": "G2"},
  {"id": "L12", "claim": "GRR mediana SaaS B2B privada", "status": "fact", "value": 91, "unit": "%",
   "source": {"type": "benchmark_db", "tier": 2, "title": "SaaS Capital 2025", "url": "https://www.saas-capital.com/"},
   "benchmark_id": "PRD-002", "publication_date": "2025-09-18", "reference_period": "dic-2023 a dic-2024",
   "priority": "P2", "evidence_quality": "B", "tag": "[D]", "transferability": "unknown"}
]
```
