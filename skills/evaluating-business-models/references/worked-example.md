# Ejemplo completo de principio a fin

> Leer la primera vez que se usa la Skill o cuando no esté claro qué archivo construir en cada paso. Los tres archivos del ejemplo están en `assets/example/` y se generaron ejecutando los scripts (`evals/harness/build_worked_example.py`), así que sus cifras son exactamente las que producen las funciones.

Caso sintético: una consultora de datos colombiana que factura por horas (mismas cifras que el caso de evaluación D.03).

## 1. Reformulación neutra y escaneo

"Consultora de datos que factura por horas a pymes colombianas." Se ejecuta `scan_injection.py proposal.md`: sin hallazgos.

## 2. Clasificación (M1)

100 % de los ingresos por horas → `mechanisms: {"tm": 1.0}` → **S1**. Sin agentes (no hay AIX), una sola línea (no es híbrido).

## 3. Evidence Ledger

Cada cifra del documento entra con su cita literal (≤ 15 palabras), estado `fact`, `self_declared: true` y tier 2 (`assets/example/evaluation.json → ledger`, L1–L4): tarifa 70 USD/h, realización 90 %, coste cargado 55 USD por hora pagada y utilización 45 %. Las cifras derivadas entran como `estimate` con `source.type: script_output` y `derived_from` (L5–L7).

## 4. `gate_input.json`

Se construye desde el ledger (`assets/example/gate_input.json`). En la línea, `economics.kind = "services"` con `rate`, `realisation`, `loaded_cost_per_paid_hour` y `utilisation`, cada bloque con sus `ledger_ids`. El formato completo está en `gates.md`.

## 5. Compuertas y veredicto

```bash
python "${CLAUDE_SKILL_DIR}/scripts/gates_and_score.py" evaluate --file gate_input.json
```

G2 falla: el coste por hora facturable es 55 / 0,45 = 122,22 USD, mayor que la tarifa efectiva de 70 × 0,9 = 63 USD. El mapeo es determinista: una compuerta en `fail` → **NO_GO**, con condición de reversión ("tarifa efectiva ≥ 122,22 o coste por hora facturable ≤ 63"). Con NO_GO no se puntúan los módulos para decidir: las dimensiones nunca anulan una compuerta.

Una cifra de contexto útil para el informe sale de `breakeven_runway.py breakeven_billable_fte`: cada FTE facturable pierde 47.970 USD al año, así que no hay plantilla que alcance el equilibrio.

## 6. `evaluation.json`, validación e informe

1. Escribir `evaluation.json` (fuente única de verdad) y ejecutar `validate_output.py evaluation.json`.
2. Derivar `informe.md` con `report_template.md`: resumen de cinco líneas, compuertas, reversión, caso en contra, próximos pasos, glosario.
3. Ejecutar `check_claims.py informe.md evaluation.json`: cada número del informe debe estar en las secciones de evidencia (ledger o salidas de scripts). En el ejemplo pasa.
4. Pasar ambos archivos al subagente `evidence-verifier` si está disponible y ofrecer `log_evaluation.py freeze evaluation.json`.

## Errores típicos que el ejemplo evita

- Calcular el margen con horas pagadas en lugar de horas facturables (el coste por hora facturable es el que decide G2).
- Usar NRR, LTV/CAC o burn multiple en una consultora por horas: no aplican a S1.
- Escribir en el informe una cifra que no está en el ledger ("margen del 87 %"): `check_claims.py` la rechaza.
