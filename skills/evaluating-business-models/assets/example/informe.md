# Evaluacion: Consultora de datos (ejemplo sintetico)

**Asi no vale la pena seguir: G2 falla (Tarifa efectiva 63.00 < coste por hora facturable 122,22). Lo cambiaria: Tarifa efectiva >= 122,22 o coste/hora facturable <= 63.00 (subir utilizacion o tarifa).**

**Resumen en cinco lineas.** Veredicto: **NO_GO**. La tarifa efectiva (63 USD/h, L5) no cubre el coste por hora facturable (122,22 USD/h, L6). Cada FTE facturable pierde 47.970 USD al anio (L7). Lo cambiaria: tarifa efectiva de al menos 122,22 USD/h o mas utilizacion. Siguiente paso: test de 90 dias para subir la utilizacion.

## Compuertas

| Compuerta | Estado |
|---|---|
| G0 | pass |
| G1 | pass |
| G2 | fail |
| G2b | not_applicable |
| G3 | pass |
| G4 | pass |
| G5 | pass |
| G7 | pass |
| G6 | pass |

## Condiciones de reversion

- **G2**: tarifa efectiva de al menos 122,22 USD/h, o coste por hora facturable de como mucho 63 USD/h.

*Analisis, no asesoramiento de inversion, legal ni fiscal.*
