# M10–M11: viabilidad técnica y costes operativos

> Leer en M10 y M11 junto con `due-diligence.md` (filas T e IA).
>
> Generado desde: sección 6d (M10–M11) del informe «Evaluación negocios tecnológicos ampliada» (texto propio con citas). No editar a mano: editar el informe y ejecutar `evals/harness/build_references.py`. Etiquetas: [D] documentado, [S] secundario, [M] marco/libro o conocimiento no verificado, [I] inferencia, [P] propuesta metodológica.

### Especificación de módulos (6d)

| Módulo | Entradas (P0 en cursiva) | Cálculo y procedimiento | Umbrales y anclas específicas | Salida al ledger |
|---|---|---|---|---|
| **M10 Viabilidad técnica** | Arquitectura, CI, SBOM, SLO, evals, pass^k | Filas T01–T16 e IA01–IA09 de la matriz de DD (6h); DORA con tendencia; agente frente a línea base simple en la frontera coste-precisión | Techo 2 sin *eval set* propio o sin pass^k (k ≥ 3) reportado (T7); KO de la matriz a G4, G6 o G7 | `tech_findings[]` con Pub/Emp |
| **M11 Costes operativos** | Coste de servir, compliance, inferencia, multiplicador laboral del país | UE-27; estrés del precio del modelo a ×0,5, ×1,5 y ×2,0 (T3); límites de coste (T8); break-even de self-hosting; multiplicadores de 6i | T3: margen < 0 con ×2,0 → riesgo alto; T8: top 10 % de tareas > 50 % del coste de IA → exigir topes [P] | `cost_to_serve`, `stress_table`, `compliance_cost` |
