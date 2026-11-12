# M12–M15: adquisición y retención, riesgos, escalabilidad y experimentos

> Leer en M12–M15 y para G5.
>
> Generado desde: sección 6d (M12–M16) del informe «Evaluación negocios tecnológicos ampliada» (texto propio con citas). No editar a mano: editar el informe y ejecutar `evals/harness/build_references.py`. Etiquetas: [D] documentado, [S] secundario, [M] marco/libro o conocimiento no verificado, [I] inferencia, [P] propuesta metodológica.

### Especificación de módulos (6d)

| Módulo | Entradas (P0 en cursiva) | Cálculo y procedimiento | Umbrales y anclas específicas | Salida al ledger |
|---|---|---|---|---|
| **M12 Adquisición y retención** | CAC completo, canales, NRR/GRR con panel, SLA | UE-01 a UE-03; capacidad de venta con Bridge Group como techo (6g); repetibilidad en servicios | Payback y retención contra el rango del arquetipo con su ID; nunca un único número de GRR sin panel y año | `acquisition{}`, `retention{}` |
| **M13 Riesgos** | Filas N01–N17 y C01–C06 de la matriz de DD; R5; tasas base | Kaplan & Strömberg (internos, externos, complejidad); riesgo de pilot purgatory (4 de 33 pruebas de concepto llegaron a producción según IDC, MKT-013, [S]) | KO de la matriz a G3, G4 o G7; alertas sin KO puntúan aquí | `risks[]` con compuerta vinculada |
| **M14 Escalabilidad** | Coste unitario por volumen, ER/SER por volumen, ARR/FTE, ventas/capital | Pendiente del coste por tarea exitosa frente al volumen; T5; R1; FM-12 | Si la fiabilidad no mejora con el volumen, la línea escala como servicio y no puede puntuar > 3 [P]; ARR/FTE frente a PRD-011 | `scaling{}` |
| **M15 Validación por experimentos** | Supuestos críticos de G5 | Hipótesis falsable, test más barato, métrica, umbral y fecha definidos antes; regla de abandono; tamaño muestral (323 tareas para ±5 % en una tasa de autonomía de ~70 %) | G5; la evidencia de un test no puede reinterpretarse cambiando el umbral a posteriori | `tests[]`, `forecasts[]` |
| **M16 Síntesis** | Salidas de M1–M15 | Compuertas primero (6b); medianas por módulo; dimensiones; moda del veredicto; reformulación neutra en tercera persona; versiones con orden de secciones intercambiado | Bandas sin decimales; condiciones de reversión obligatorias; caso más fuerte en contra | `evaluation.json` completo |
