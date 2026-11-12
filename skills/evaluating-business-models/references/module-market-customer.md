# M2–M4: mercado, investigación de cliente y propuesta de valor

> Leer en M2, M3 y M4 y para G1: dimensionamiento bottom-up limitado por capacidad y escala de evidencia de demanda contada por cuenta.
>
> Generado desde: secciones 6d (M2–M4), 6g.1 y 6g.3 del informe «Evaluación negocios tecnológicos ampliada» (texto propio con citas). No editar a mano: editar el informe y ejecutar `evals/harness/build_references.py`. Etiquetas: [D] documentado, [S] secundario, [M] marco/libro o conocimiento no verificado, [I] inferencia, [P] propuesta metodológica.

### Especificación de módulos (6d)

| Módulo | Entradas (P0 en cursiva) | Cálculo y procedimiento | Umbrales y anclas específicas | Salida al ledger |
|---|---|---|---|---|
| **M2 Mercado** | *n_accounts* (registro oficial con año), p_problem, *acv_low/mid/high*, frecuencia, capacidad de venta | M2.1–M2.10 (6g): TAM = n × p × ACV × frecuencia; SOM = min(SAM × captura con evidencia, capacidad); outside view; tornado de factores | Techo 2 si el SOM no está limitado por capacidad o si el ACV solo procede de cifras de analistas de calidad C [P] | `tam`, `sam`, `som`, `capacity_constraint`, `outside_view_check`, `top_uncertainty` |
| **M3 Investigación de cliente** | *Cuentas por nivel 0–6 con subnivel*, documentos, entrevistas | Auditoría tipo Mom Test; nivel máximo por cuenta, no por contacto; la evidencia negativa no se borra | Nivel máximo repetido en el beachhead: 1–2 → 1; 3 → 2; 4 → 3; 5 → 4; 6 → 5 [P]. Reconciliación de notas: la nota de mercado proponía fallar G1 con todo en ≤ 2; se adopta `unknown` salvo evidencia negativa, para no confundir ausencia de evidencia con evidencia de ausencia (caso D.6) | `demand_evidence[]`, `max_level`, entrada de G1 |
| **M4 Propuesta de valor** | Trabajo del cliente (verbo + objeto + contexto), DMU, whole product | Perfil por decisor; lista de whole product (integración, soporte, seguridad, compliance, partners); qué aporta el proveedor del modelo y qué el servicio | 1 = trabajo no enunciado; 3 = trabajo y DMU con hechos de nivel ≥ 2; 5 = whole product completo y evidencia de nivel ≥ 4 de que el comprador lo valora [P] | `job_statement`, `dmu`, `whole_product_gaps[]` |


## 6g.1 Dimensionamiento reproducible (M2.1–M2.10) [P]

El TAM útil es un producto de factores, cada uno con su entrada en el ledger, y el SOM se limita por la **capacidad de venta**, no por un "% del mercado". Dos hallazgos empíricos lo justifican: preparar estados financieros proyectados **aumenta** el optimismo de los emprendedores sobre sus ventas, que solo las ventas reales corrigen ([Cassar 2010](https://econpapers.repec.org/RePEc:bla:stratm:v:31:y:2010:i:8:p:822-840)); y el exceso de confianza colectivo en un "gran mercado" lleva a sobrevalorar al conjunto de entrantes, porque un gran mercado no basta si la cuota es difícil de capturar ([Cornell & Damodaran 2020](https://ideas.repec.org/a/taf/ufajxx/v76y2020i2p15-25.html)). El debate Damodaran–Gurley sobre Uber da el contraejemplo: el TAM "del mercado existente" también subestima cuando el producto crea uso nuevo ([Gurley](https://abovethecrowd.com/2014/07/11/how-to-miss-by-a-mile-an-alternative-look-at-ubers-potential-market-size/), MKT-017).

| Paso | Qué hace | Fuentes | Salida al ledger |
|---|---|---|---|
| M2.1 Unidad de compra | Cuenta = entidad que firma y paga; fijar la DMU (comprador económico, usuario, compras) | Propuesta, entrevistas; Aulet [M] | `buyer_unit`, `dmu` |
| M2.2 Beachhead | Código sectorial (NAICS, NACE o CIIU) + tamaño + geografía; un solo segmento por cálculo | Propuesta | `segment_id` |
| M2.3 Contar cuentas | Tabla oficial con año de referencia y exclusiones registradas | Census SUSB (filas con < 3 empresas suprimidas desde 2017) y CBP (excluye empresas sin empleados) ([Census](https://census.gov/data/tables/2022/econ/susb/2022-susb-annual.html)); Eurostat `sbs_sc_ovw` ([DBnomics](https://db.nomics.world/Eurostat/sbs_sc_ovw)); RUES, DANE y Supersociedades en Colombia (6i) | `n_accounts` [D, A] |
| M2.4 Proporción con el problema | Solo desde evidencia de clientes de nivel ≥ 2 o encuesta pública con definición; si no, rango amplio como `assumption` | Entrevistas, encuestas | `p_problem` |
| M2.5 Presupuesto realista | Triangular precio de alternativas públicas, coste del problema (horas × coste/hora) y % de gasto de TI si hay fuente abierta; usar el **mínimo** plausible | Precios de competidores; resumen gratuito de Avasant (rangos p25–p75 de 4,4–11,4 % en servicios financieros y 1,4–3,2 % en manufactura discreta, sin muestra ni periodo, [Avasant](https://avasant.com/it-spending-as-a-percentage-of-revenue-by-industry-company-size-and-region/), MKT-008/009, C) | `acv_low/mid/high` |
| M2.6 Frecuencia | Recurrente frente a proyecto cada N años, anualizado | Contratos y casos | `purchases_per_year` |
| M2.7 TAM y SAM | TAM = n × p × ACV × frecuencia; SAM = TAM restringido por canal, idioma, regulación e integración | `market_sizing.py` | `tam`, `sam` con `derived_from` |
| M2.8 SOM por capacidad | SOM = min(SAM × captura con evidencia, capacidad); capacidad = Σ reps × meses productivos tras la rampa × cierres/mes, o en founder-led, horas de venta semanales / horas por cierre | Bridge Group 2026 como techo: 48 % de AEs a cuota, cuota mediana 960 k$, rampa 6,2 meses ([Bridge Group](https://www.bridgegroupinc.com/research/2026-ae-models-motions-metrics), MKT-010 a 012, [S]) | `som`, `capacity_constraint` |
| M2.9 Outside view | SOM a 3 años frente a tasas de supervivencia del país (6i) y sesgo de Cassar; si el SOM depende de proyecciones del fundador sin ventas, `optimism_risk: high` | Tasas base | `outside_view_check` |
| M2.10 Sensibilidad | Tornado sobre n, p, ACV y captura; el factor más incierto define la siguiente pregunta | `sensitivity.py` | `top_uncertainty` |

Reglas anti-error [P/I]: (1) prohibido "X % de un mercado de Y mil millones" sin el producto de factores; (2) no contar dos veces (segmentos solapados, establecimientos de CBP y empresas de SUSB a la vez, gasto de TI total más gasto de la categoría); (3) el gasto de TI del cliente no es el TAM de la categoría, solo la fracción que hoy paga por ese trabajo, incluidas horas internas; (4) una cifra de analista sin definición entra como `estimate` de calidad C y no sostiene una puntuación ≥ 3 en M2; (5) si la propuesta crea uso nuevo, el escenario de expansión va aparte del TAM base; (6) el SOM sale del cálculo, nunca del plan del fundador. Parada: cada factor con fuente o marcado `assumption` con rango, y el factor dominante identificado; presupuesto por defecto de ~30 llamadas web por evaluación, con lo no investigado registrado como `unknown` [P].


## 6g.3 Escala de evidencia de demanda B2B (amplía la escala 0–6 de la fase 1)

La intención declarada predice compras de forma imperfecta ([Morwitz 2014](https://nowpublishers.com/article/Details/MKT-036)) y la disposición a pagar hipotética está sesgada al alza (MKT-001, MKT-002). Ninguna fuente abierta da una tasa fiable de conversión LOI → contrato en B2B tecnológico, así que la Skill no convierte "interés" en ingresos con un factor fijo: cuenta cuentas por nivel. Los números enteros no cambian respecto a la fase 1; los subniveles son [P].

| Nivel | Definición (fase 1) | Subniveles [P] | Qué NO cuenta |
|---|---|---|---|
| 0 | Opinión del fundador | — | — |
| 1 | Interés verbal | 1a cumplido; 1b encuesta de intención o Van Westendorp | Likes, encuestas de WTP como prueba de compra |
| 2 | Problema descrito con hechos pasados | 2a último episodio con coste; 2b ya gasta en un workaround | Problemas hipotéticos ("sería útil si…") |
| 3 | Compromiso no monetario | 3a segunda reunión con el comprador económico; 3b acceso a datos o sistemas reales; 3c tiempo de su equipo en un piloto gratuito **con criterio de éxito escrito**; 3d presentación a otra cuenta | Piloto gratis sin criterio ni sponsor (pilot purgatory) |
| 4 | LOI o piloto con presupuesto | 4a LOI con importe, alcance y fecha; 4b piloto o discovery pagado; 4c presupuesto aprobado | LOI sin importe ni fecha; "lo meteremos en el presupuesto del año que viene" |
| 5 | Pago o contrato | 5a contrato o PO firmado; 5b prepago o anticipo cobrado; 5c entregado, aceptado y pagado | Contrato con salida gratuita antes del primer pago (cuenta como 4) |
| 6 | Pago repetido en el mismo segmento | 6a renovación o expansión; 6b ≥ 3 clientes pagadores del mismo segmento con el mismo servicio; 6c referencia que trae otro pagador | Pagadores de segmentos distintos |

Reglas de uso [P]: se cuenta por cuenta, con fecha y fuente documental o declaración marcada como autodeclarada; un prototipo hecho con IA no sube de nivel; los niveles 1–2 solo alimentan `p_problem`, y la captura se estima con la conversión observada en la propia cartera (p. ej., 2 de 5 pilotos pagados convertidos) registrada con su n; ningún método de WTP declarado produce evidencia > 1, aunque oriente el precio en M7; la evidencia negativa pesa igual y nunca se borra. Conexión con compuertas: G1 según 6b.1; P0 de este bloque para G6: `n_accounts`, `acv_low`, nivel máximo de demanda y presencia de un vendor C5 con la función incluida.
