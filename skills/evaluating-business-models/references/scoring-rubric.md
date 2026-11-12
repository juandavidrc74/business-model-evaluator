# Rúbrica de puntuación de módulos y dimensiones

> Leer al puntuar M2–M15: anclas 1–5 verificables, regla de techo, null con unknown y bandas sin decimales.
>
> Generado desde: sección 6d del informe «Evaluación negocios tecnológicos ampliada» (texto propio con citas). No editar a mano: editar el informe y ejecutar `evals/harness/build_references.py`. Etiquetas: [D] documentado, [S] secundario, [M] marco/libro o conocimiento no verificado, [I] inferencia, [P] propuesta metodológica.

## Anclas, techo y dimensiones (6d)

**Anclas comunes de puntuación [P].** Todo módulo puntúa de 1 a 5 con anclas verificables contra el ledger, no con impresiones: **1** = evidencia en contra o fallo de una regla del módulo; **2** = solo supuestos o evidencia de nivel ≤ 1; **3** = estimaciones con fuente de calidad C o evidencia de nivel 2–3; **4** = hechos de fuente A o B, o evidencia de nivel 4–5; **5** = hechos verificados y repetidos (nivel 6) sin contradicciones abiertas. **Regla de techo [P]:** un módulo no puede puntuar por encima del nivel que su mejor evidencia permite; se prefiere el techo a multiplicar la nota por un "factor de calidad", porque el multiplicador reintroduce la compensación (mucha evidencia débil igualaría a poca fuerte) y no tiene evidencia empírica (6j). Un dato `unknown` deja la puntuación en `null`. La justificación de anclar no es una mejora de fiabilidad demostrada (la evidencia sobre escalas BARS es mixta, [DTIC](https://apps.dtic.mil/sti/pdfs/ADA142009.pdf)), sino que cada nivel sea comprobable por un grader determinista.



## Cómo aplicar la rúbrica en cada ejecución

1. Puntuar cada módulo M2–M15 **por separado** antes de formarse una opinión global (protocolo tipo MAP; el juicio global va al final, en M16).
2. Para cada puntuación, citar las entradas del ledger que la sostienen. Si el módulo depende de un P0 `unknown`, `score = null`.
3. Aplicar la **regla de techo**: la puntuación no puede superar el nivel de su mejor evidencia; el tier 4 (conocimiento del modelo) nunca sostiene una puntuación ≥ 4.
4. Escala entera 1–5, sin decimales. Las medianas y el rango intercuartílico entre ejecuciones los calcula `aggregate_runs.py`.
5. Las dimensiones (viabilidad, rentabilidad, competitividad, escalabilidad) se reportan en banda (débil, intermedia, fuerte) y **nunca** anulan una compuerta.
6. El caso más fuerte en contra se redacta siempre, aunque el veredicto sea GO.
