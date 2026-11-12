# Arquetipos económicos, métricas y reglas de híbridos

> Leer en M1 (clasificación) y siempre que se elija una métrica o un benchmark: el mecanismo de ingreso, no la etiqueta, define el arquetipo.
>
> Generado desde: secciones 6a y 6d (M1) del informe «Evaluación negocios tecnológicos ampliada» (texto propio con citas). No editar a mano: editar el informe y ejecutar `evals/harness/build_references.py`. Etiquetas: [D] documentado, [S] secundario, [M] marco/libro o conocimiento no verificado, [I] inferencia, [P] propuesta metodológica.

## Contenido

- 6a. Paso cero: clasificar el modelo económico
  - 6a.1 Decisión fase 2: el mecanismo de ingreso, no la etiqueta, define el arquetipo
  - 6a.2 Correspondencia entre la fase 1 y la fase 2
  - 6a.3 Reglas de clasificación y frontera [P]
  - 6a.4 Matriz de arquetipos (para `references/archetypes.md`)
  - 6a.5 Catálogo de métricas con su dominio de validez
  - 6a.6 Reglas de híbridos H0–H8 [P]
  - Especificación de módulos (6d)

## 6a. Paso cero: clasificar el modelo económico

La clasificación decide qué métricas, benchmarks y compuertas se aplican. Una propuesta puede ser híbrida; en ese caso se evalúa cada línea de ingreso con su arquetipo.

**Tabla original de fase 1.** Se conserva para trazabilidad. **Corrección fase 2:** sus filas quedan reasignadas en la tabla de correspondencia de 6a.2 y sustituidas, a efectos de implementación, por la matriz de 6a.4; los valores que siguen vigentes reaparecen allí con su identificador.

| Arquetipo | Motor económico | Métricas núcleo | Referencias con fecha | No aplicar |
|---|---|---|---|---|
| Software factory / outsourcing TI | Horas × tarifa, utilización, pirámide, offshore | Utilización, tarifa efectiva, realización, margen de proyecto, DSO | SPI 2026: utilización 66,4 % (2025); EPAM utilización 75,4 % en Q4 2025 ([AOL transcript](https://www.aol.com/finance/epam-epam-q4-2025-earnings-144801914.html)) [S] | ARR, NRR, LTV/CAC |
| Consultoría tecnológica / datos-BI | Tarifa, realización, leverage | Igual + concentración de clientes, dependencia de partners | SPI: margen de proyecto T&M 36,4 % (2025) ([Rocketlane](https://rocketlane.com/blogs/professional-services-maturity-index-2026)) [S]; EBITDA PS 9,9 % (2025) [S] | Métricas SaaS |
| Agencia web/app | Proyecto fijo, scope creep, utilización | Margen por proyecto, riesgo de precio fijo | Sin benchmark público fiable (hueco) | Métricas SaaS |
| MSP / cloud gestionado | MRR por endpoint/usuario, coste de entrega lineal | % recurrente, EBITDA ajustado por modelo, margen bruto **con mano de obra de entrega en COGS** | Best-in-class EBITDA ajustado ≥ 19 % (datos 2025, pub. 23-jun-2026) [D]; media 11,1 % (Q4 2024) ([GlobeNewswire](https://globenewswire.com/news-release/2025/02/13/3025918/27043/en/Service-Leadership-Index-Q4-Data-Reveals-MSP-Profitability-Remains-Near-Historic-Highs-While-Managed-Service-Revenue-Growth-Continues-to-Slowdown.html)); margen bruto 40–50 % mid-market (entrevista a experto) [S] | Benchmarks de IT services genéricos |
| Ciberseguridad | Consultoría + MSSP recurrente | Mezcla de ambos; certificaciones | Coste SOC 2 primer año 30–150 k$ (proveedores, 2026) [S] | — |
| B2B SaaS | ARR, retención, margen bruto alto | NRR, GRR, CAC payback, burn multiple, Rule of 40 | SaaS Capital 2025: NRR 101 %, GRR 91 % [D]; Benchmarkit: GRR 84 %, NRR 102 % [S] | Utilización |
| IA de producto | Margen deprimido por inferencia; consumo/outcome | Margen bruto con inferencia, coste por unidad de valor | Bessemer (n = 20, 2025): ~25 % Supernovas, ~60 % Shooting Stars [D]; ICONIQ 45 % (2025) [S] | Supuesto de ~80 % de margen SaaS |
| Agencia de automatización / agentes | Híbrido proyecto + retainer + outcome | Coste por tarea (inferencia + supervisión humana), margen por cliente | Sin benchmark público (hueco); tesis de VC ([BVP AI-Native Services](https://www.bvp.com/atlas/owning-the-outcome-bessemer-s-ai-native-services-evaluation-framework)) | Benchmarks de SaaS o de consultoría puros |
| Cloud / infraestructura | Capex, utilización de capacidad | ROIC, ventas/capital, cobertura de compromisos | Damodaran por sector (ene-2026) [D] | Métricas de agencia |

### 6a.1 Decisión fase 2: el mecanismo de ingreso, no la etiqueta, define el arquetipo

**Decisión.** La taxonomía final tiene **cuatro arquetipos de servicios** (S1 capacidad T&M, S2 proyecto a precio fijo, S3 asesoría apalancada, S4 servicio gestionado recurrente), **cinco de producto** (P-SAAS-SS, P-SAAS-SL, P-USAGE con subtipo pass-through, P-AI-APP, P-INFRA), un **marketplace opcional** (P-MKT, sin benchmarks) y **dos modificadores**: V (SaaS vertical) y AIX (ejecución con agentes de IA). Las etiquetas comerciales de la fase 1 ("factoría", "agencia", "ciberseguridad", "nearshore", "datos/BI") pasan a ser alias que el clasificador traduce.

**Evidencia en servicios.** Lo que separa la economía es el mecanismo contractual, porque cambia quién asume el riesgo, el capital circulante y la estructura de coste. EPAM, con etiqueta de factoría, obtuvo en 2025 el 80,0 % de sus ingresos por T&M y el 19,5 % a precio fijo ([EPAM](https://s202.q4cdn.com/436759741/files/doc_financials/2025/q4/EPAM-Fact-Sheet-Q4-2025.pdf), SVC-005). NCC Group reconoce el pentesting y la consultoría por grado de avance y divide los servicios gestionados en obligaciones de desempeño separadas, con contratos de hasta cinco años; persigue utilización en una línea y proporción de managed services en la otra ([NCC AR FY2025](https://www.nccgroupplc.com/media/aebnh13z/ncc-group-plc-annual-report-and-accounts-for-the-year-ended-30-september-2025.pdf)). Por eso la ciberseguridad se parte en S3 y S4. Accenture separa Consulting y Managed Services con book-to-bill de 1,1 y 1,2 ([Accenture FY26](https://newsroom.accenture.com/content/4q-full-fy26-earnings/accenture-reports-fourth-quarter-and-full-year-fiscal-2026-results.pdf), SVC-015). Datos/BI no muestra economía distinta de la consultoría; solo añade dependencia de partner y reventa de licencias, que se tratan con H1 y H6.

**Evidencia en producto.** SaaS Capital no ve diferencias de GRR entre ACV de < 12 k$ y 250 k$ (90–91 %), pero Benchmarkit encuentra 88 % en sales-led frente a 79 % en PLG y 80 % por debajo de 5 k$ de ACV ([SaaS Capital](https://www.saas-capital.com/wp-content/uploads/2025/09/RB32WS1-2025-B2B-SaaS-Retention-Benchmarks.pdf); [Aleph](https://www.getaleph.com/answers/gross-revenue-retention-saas-2026)): la caída se concentra en el self-serve de ticket bajo, y eso justifica la escisión SS/SL [I]. El consumo tiene otra lógica de retención (NRR 108 % por uso frente a 98 % por seat, PRD-014) y de COGS: Twilio prevé que las tasas de operadores repercutidas le resten ~170 pb de margen en 2026 ([Twilio](https://www.businesswire.com/news/home/20260212472439/en/Twilio-Announces-Fourth-Quarter-and-Full-Year-2025-Results/), PRD-025). El SaaS vertical no justifica arquetipo propio: SaaS Capital solo ve "minor differences" de retención frente al horizontal. Un revendedor de hosting sin capacidad propia no soporta riesgo de utilización y se evalúa como S4; las plataformas alojadas en hiperescaladores (Snowflake) son P-USAGE, no P-INFRA.

**Decisión sobre la automatización con agentes (AIX).** La fase 1 tenía una fila "agencia de automatización / agentes". La fase 2 la convierte en **modificador obligatorio** y no en arquetipo, por tres razones. Primero, su coste es la suma de dos mecanismos ya conocidos: inferencia variable (como P-AI-APP) y supervisión humana semifija (como S4); en el ejemplo ilustrativo de 6f, el coste medio por tarea pasa de 0,45 $ solo con inferencia a 2,88 $ con humanos, que son el 79 % del total [I]. Segundo, la misma etiqueta puede tener cualquiera de las dos economías: con tasa de escalado inferior al ~5 % y QA ligera se acerca a producto; con escalado del 30 % es un servicio (caso D.5 de 6j.4; véase también el ejemplo B.2 de `economia_ai_native.md`, resumido en 6f.2). Tercero, no existe benchmark público de márgenes de agencias de agentes; los AI Pods de Globant, el único caso documentado, son menos del 1 % de sus ingresos ([Globant](https://investors.globant.com/2026-02-26-Globant-Reports-2025-Fourth-Quarter-Financial-Results)). Un arquetipo propio tendría la columna de benchmarks vacía y clasificaría por tecnología, el error que la fase 1 señaló como más grave. **Regla [P]:** toda línea en la que agentes ejecuten tareas lleva el modificador AIX, se modela con `ai_native_model.py` (6f) y se enruta así: si los humanos superan el 40 % del COGS por tarea (umbral T5) o el coste humano por tarea no baja con el volumen, se evalúa como **S2** (si se cobra por proyecto) o **S4** (si se cobra recurrente o por tarea con SLA) con benchmarks de servicios; si no, como **P-AI-APP**. **Alternativas rechazadas:** arquetipo propio "agencia de agentes" (sin benchmarks y clasificado por etiqueta) y fusión directa con P-AI-APP (aplicaría márgenes de producto de IA, 25–60 %, a un negocio intensivo en personas).

### 6a.2 Correspondencia entre la fase 1 y la fase 2

| Fila de fase 1 | Arquetipo fase 2 | Qué cambia |
|---|---|---|
| Software factory / outsourcing TI | S1 si ≥ 50 % T&M; S2 si ≥ 50 % precio fijo | Decide el contrato, no el nombre; la utilización de EPAM se conserva como SVC-001 (76,8 % en FY2025; 75,4 % en Q4) |
| Consultoría tecnológica / datos-BI | S3; datos/BI como alias | Reventa de licencias (Snowflake, Fabric) con H1/H6 |
| Agencia web/app | S2 (S1 o S3 si cobra retainers de horas) | Ancla nueva de margen neto: SVC-025/026 (calidad C) |
| MSP / cloud gestionado | S4 | Absorbe a los revendedores de hosting sin capacidad propia |
| Ciberseguridad | S3 (pentesting, consultoría, DFIR) y S4 (MSSP/MDR/SOC) | **Corrección fase 2:** deja de ser arquetipo |
| B2B SaaS | P-SAAS-SS o P-SAAS-SL; modificador V si es vertical | Escisión por motion de venta y ACV |
| IA de producto | P-AI-APP | Acotada a aplicaciones sobre modelos de terceros |
| Agencia de automatización / agentes | Modificador AIX sobre S2, S4 o P-AI-APP | Decisión de 6a.1 |
| Cloud / infraestructura | P-INFRA solo con capacidad propia; plataformas sobre hiperescaladores → P-USAGE; revendedores → S4 | Acotada por riesgo de utilización |
| (nuevo) | P-USAGE, con subtipo pass-through | Consumo medido y commits |
| (nuevo, opcional) | P-MKT | Take rate sobre GMV; sin benchmarks |

### 6a.3 Reglas de clasificación y frontera [P]

| Regla | Criterio | Base |
|---|---|---|
| Atributos obligatorios por línea | % de ingresos T&M, precio fijo, recurrente gestionado, suscripción, uso medido y reventa; país de entrega y de facturación; dependencia de partner; vertical regulado; cobertura 24×7; motion de venta; ACV mediano; capacidad propia; % humanos en el COGS por tarea si hay agentes | Notas de arquetipos [P] |
| S1 | ≥ 50 % de los ingresos facturados por hora, día o FTE-mes | [P] |
| S2 | ≥ 50 % de los ingresos de precio fijo o hitos | [P] |
| S3 | Se vende experiencia (diagnóstico, diseño, auditoría) con tarifa ligada al seniority | [P] |
| S4 | ≥ 50 % de los ingresos en contratos recurrentes con SLA, por usuario, dispositivo o tramo | [P] |
| P-SAAS-SS frente a SL | SS si la mayoría del ARR nuevo se cierra sin intervención comercial o el ACV mediano es < 12 k$ (primer corte de SaaS Capital); SL en otro caso | [P], sin evidencia de que el corte sea óptimo |
| P-AI-APP frente a SaaS | Coste de inferencia o API de modelos > 10–15 % de los ingresos, o precio ligado al consumo de modelo | [P]; el hosting mediano de SaaS es 5 % del ARR (PRD-008) |
| P-USAGE | > 50 % de los ingresos variable con el uso medido; si los costes repercutidos superan el 30 % del ingreso, el margen se calcula neto de pass-through | [P] |
| P-INFRA | Posee o arrienda capacidad (servidores, GPU, colocation) con riesgo de utilización; si no, S4 | [I] |
| Modificador AIX | Agentes ejecutan tareas; enrutamiento por T5 (humanos > 40 % del COGS por tarea) | [P] (6a.1) |
| Modificador V | Exigir margen solo de software frente a combinado si hay pagos o servicios financieros embebidos, y TAM bottom-up del nicho | [P] |
| Híbrido (H0) | Dos o más mecanismos con ≥ 20 % de los ingresos o ≥ 20 % del margen bruto cada uno, o una línea pequeña presentada como la tesis de valor | [P] |

### 6a.4 Matriz de arquetipos (para `references/archetypes.md`)

Los rangos son observaciones de las fuentes citadas, no umbrales validados; los benchmarks de una sola empresa cotizada describen escala grande y no son objetivo para una pyme. Los red flags con [P] deben calibrarse.

| Arquetipo | Modelo de ingresos | Comportamiento de costes | Capital | Capital circulante | Métricas clave | Rangos de referencia (IDs) | Killers y red flags |
|---|---|---|---|---|---|---|---|
| **S1 Capacidad de ingeniería T&M** (factoría T&M, outsourcing, staff augmentation, nearshore) | FTE facturables × tarifa × utilización; T&M mensual o managed capacity | Nómina de entrega en COGS, semifija (bench); arbitraje salarial; riesgo de divisa | Bajo (capex < 1 % de ingresos en EPAM) | DSO de 47–86 días frente a nómina mensual (SVC-006, 010, 014) | Utilización, tarifa efectiva, ingreso/FTE, coste de bench, rotación, concentración, DSO | Utilización 75–78 % (SVC-001); 66,4 % en todas las PS (SVC-022); margen bruto GAAP 28,8–35,0 % (SVC-002, 008, 011); operativo GAAP 7,0–15,4 % y ajustado 15,2–15,8 % (SVC-003, 008, 013); ingreso/FTE 82–98 k$ (SVC-007, 010, 016); top-10 22–59 % (SVC-004, 009, 012); estrés: bruto ≈ 20 % (SVC-017); Colombia, TI grandes: operativo mediano 7,5 % (GEO-018) | Tarifa efectiva < coste cargado (G2); concentración según G3; utilización sostenida < 65 % [P]; ingresos en una moneda y costes en otra sin cobertura (EPAM: 67 % de ingresos en USD frente a 37 % del opex); un solo país de entrega |
| **S2 Proyecto a precio fijo** (agencia web/app, llave en mano, MVP) | Precio por entregable o hitos; reconocimiento por avance | Como S1 más sobrecoste por estimación y preventa cara | Bajo | Contract assets y WIP; anticipos como palanca (sin benchmark) | Margen de proyecto, desviación EAC, realización, días de WIP, % con anticipo, concentración | Margen neto de agencias 13 % (SVC-025, C); desarrollo 11 %, < 10 personas 19 % (SVC-026, C); margen de proyecto ~35–36 % (SVC-024, 026) | Sobrecostes > 20 % recurrentes [P]; WIP que crece más rápido que los ingresos [P]; venta dependiente del fundador; precio fijo sin control de cambios; precio fijo calculado desde horas (hora disfrazada) |
| **S3 Asesoría apalancada** (consultoría tecnológica, datos/BI, consultoría de ciberseguridad, pentesting) | T&M por seniority, retainers, diagnósticos cortos | Senior caros más pirámide; coste comercial vía socios | Bajo | Como S1 | Realización, tarifa efectiva, leverage, utilización por nivel, margen por cuenta, book-to-bill, dependencia de partner | Utilización cyber 70,4 % (SVC-020); bruto cyber 36,6 % (SVC-019); EBITDA PS 9,9 % (SVC-023); margen T&M 36,4 % (SVC-024); book-to-bill 1,1 (SVC-015) | Ingreso concentrado en 1–2 socios (persona clave) [P]; pirámide junior-dependiente bajo presión de la IA (supuesto de riesgo, fase 1); un vendor partner > 50 % del pipeline [P] |
| **S4 Servicio gestionado recurrente** (MSP, cloud gestionado, MSSP/MDR/SOC, AMS, revendedor de hosting) | MRR por usuario, dispositivo o tramo + set-up + proyectos + reventa | Técnicos y analistas en COGS (semifijos, turnos 24×7); herramientas por endpoint (variables); licencias revendidas | Bajo o medio | Favorable con facturación anticipada; negativo si la reventa se paga antes de cobrar | % recurrente, margen de acuerdo con mano de obra, Service Multiple of Labor, densidad por técnico, MRR/cliente, churn, reventa, créditos de SLA | Margen bruto de servicios BIC 48,7 % (SVC-027); multiple of labor BIC 2,8× (SVC-028); EBITDA ajustado BIC ≥ 19 % y media 11,1 % (SVC-029); ~10 % de MSP no rentables (SVC-030); margen de acuerdo ~65 % solo como regla práctica (SVC-031); 200–400+ endpoints por técnico sin método (SVC-032) | Margen bruto sin mano de obra de entrega (R4); reventa bruta sin análisis principal-agente (H1); "todo incluido" sin límites ni escalador; SOC 24×7 con < ~5 FTE por puesto (8.760 h / 1.700–1.900 h productivas ≈ 4,6–5,2 FTE) [I]; subidas de herramientas no trasladables |
| **P-SAAS-SS** (SMB, self-serve, PLG) | Suscripción mensual o anual por plan o seat | Hosting ~5 % del ARR, DevOps ~4 %, soporte, pasarela (PRD-008) | Bajo o medio; marketing continuo | Cobro con tarjeta: DSO ~0, poco diferido | Churn de logos mensual, GRR, NRR, CAC payback, ARPA | GRR 79–90 % (PRD-003, 013); NRR ~98 % con ACV < 12 k$ (PRD-003); payback 6–18 meses como heurística (PRD-028) | Churn que obliga a reponer > 30–40 % de la base al año [I]; GRR < 80 % (R3); CAC payback > vida del cliente (G2b) |
| **P-SAAS-SL** (mid-market y enterprise, sales-led) | Contrato anual o multianual + implantación | Hosting, soporte dedicado, CS técnico, servicios profesionales (~5 % del ARR) | Medio o alto; equipo comercial, SOC 2/ISO si el segmento lo exige | Prepago anual: el diferido financia el crecimiento; DSO de facturas enterprise | GRR, NRR, ACV, CAC payback, magic number (solo con VC), RPO | GRR 88–95 % (PRD-003, 013); NRR 102–106 % (PRD-003); bootstrapped NRR 104 % y GRR 92 % (PRD-004); payback 24–36 meses como heurística (PRD-028), mediana 16 meses en Benchmarkit (PRD-015, C); ARR/FTE mediano 141 k$ (PRD-011); margen bruto privado 75–80 % [S/I] (PRD-015, 027) | Servicios > 20–25 % de los ingresos sin margen [P]; ciclo de venta > runway; GRR < 90 %; implantación cargada a I+D (H2) |
| **P-USAGE** (developer tools, API, consumo; subtipo pass-through) | Pago por uso + commits anuales con descuento por volumen | Cómputo y almacenamiento de terceros o propios; en el subtipo, tasas repercutidas que inflan ingresos y COGS | Medio; adopción bottom-up | Commits prepagados (RPO) o pago por uso a mes vencido (cuentas por cobrar) | NRR de consumo o DBNE, margen bruto neto de pass-through, cohortes de uso | NRR por uso 108 % frente a 98 % por seat (PRD-014); Snowflake NRR 125 % y margen de producto non-GAAP 75,8 % (PRD-022); Datadog ~120 % y ~80 % (PRD-023); Twilio DBNE 108 % y bruto 49,9 % (PRD-025) | Optimización de consumo del cliente; ingresos inflados por pass-through; dependencia de un hiperescalador |
| **P-AI-APP** (aplicación sobre modelos de terceros) | Suscripción + créditos o consumo + outcome (1,7 modelos de precio por empresa, PRD-020) | Inferencia variable fijada por el proveedor, hosting, vector DB, evals | Medio | Créditos prepagados; compromisos de capacidad con el proveedor | Margen bruto con inferencia, coste por unidad de valor, NRR, GRR, ARR/FTE | Margen bruto 25–60 % (PRD-021); ~45 % en 2025 y 53 % proyectado en 2026 (PRD-019); C3.ai 31 % GAAP (AI-040); Anthropic ~40 % previsto para 2025 [S] (AI-039) | Seat con uso ilimitado; margen negativo en clientes intensivos (T9); función replicable por el proveedor del modelo; margen < 0 con precio ×2,0 (T3) |
| **P-INFRA** (cloud con capacidad propia) | Consumo de cómputo, almacenamiento y red; GPU-hora | Depreciación, energía, colocation, red, operaciones | Alto (capex) | Capex adelantado a la demanda | Utilización de capacidad, ROIC, ventas/capital, NDR, margen FCF | DigitalOcean: bruto 60 %, NDR 101 %, FCF ajustado 19 % (PRD-024); Damodaran por sector | Utilización baja; competir en precio con hiperescaladores; capex financiado a corto plazo; break-even de self-hosting calculado al 100 % de utilización (AI-045) |
| **P-MKT** (marketplace de servicios tech, opcional) | Take rate sobre GMV | Confianza, pagos, soporte | Medio (liquidez) | Float de pagos | GMV, take rate, liquidez, repetición | Sin benchmarks recogidos (laguna) | Desintermediación cliente-proveedor |
| **Modificador V** (SaaS vertical) | Igual que SS/SL + pagos embebidos | Los pagos diluyen el margen combinado | Igual | Float de pagos | Margen de software frente a combinado; TAM del nicho | Sin diferencia de retención relevante frente a horizontal (SaaS Capital) | TAM de nicho insuficiente; dependencia de un canal o regulador |
| **Modificador AIX** (ejecución con agentes) | Proyecto, retainer, por tarea, por outcome o híbrido | Inferencia variable de cola pesada + supervisión humana + costes fijos de evals y migraciones | Bajo o medio | Según el meter | CPST p50/p90/p95 con humanos, ACR, ER, SER, pass^k, cuota humana del COGS | Sin benchmark de margen; precios públicos de 0,99–2 $ por resolución como techo (AI-033, 035, 036); ACR declarado por vendors no auditado (AI-034) | Los 16 red flags de 6f; en particular precio < C_task p90 (G2) y autonomía de vendor usada como propia |
| **Híbridos** | Suma de líneas | Personal compartido | Según líneas | Según líneas | Métricas por segmento + ingreso neto de pass-through | Ninguno combinado; siempre por segmento | Margen SaaS inflado con soporte en opex; ARR que incluye retainers o reventa; múltiplo de ARR aplicado a servicios |

### 6a.5 Catálogo de métricas con su dominio de validez

| Métrica (ID de fórmula) | Usar en | No usar en o cuando |
|---|---|---|
| Utilización (UE-22) | S1, S2, S3, AIX con horas | S4 (el ingreso no depende de horas); denominador no homogéneo entre fuentes (EPAM y NCC no publican el suyo) |
| Realización (UE-23) y tarifa efectiva | S2, S3; tarifa efectiva en S1–S3 | S4; S1 con tarifa fija por FTE-mes (≈ 100 % por construcción) |
| Leverage (Maister) | S3, S1 | S4; microempresas sin estructura |
| Margen de proyecto o cuenta (UE-26) | S1–S3, AIX por proyecto | Como sustituto del EBITDA |
| Service Multiple of Labor | S1–S4 | Si el ingreso incluye reventa sin netear |
| Ingreso por FTE (UE-21) | Todos | Entre países con costes laborales muy distintos sin ajustar (6i) |
| Coste de bench, días de WIP, desviación EAC [P] | S1 (bench), S2 (WIP, EAC) | S4; sin registro horario o de proyectos |
| DSO con contract assets (FM-04) | Todos | Comparar fuentes sin homogeneizar la fórmula (Accenture netea partidas, EPAM no) |
| Concentración top-1/5/10 | Todos | — |
| Book-to-bill | S3, S4, S1 grandes | Pymes sin registro de backlog |
| % recurrente | S4 e híbridos | S2 puro; los retainers de horas no son recurrencia gestionada |
| Margen de acuerdo, endpoints por técnico, MRR/cliente | S4 (MSP) | MSSP/SOC (usar alertas por analista); S1–S3 |
| % y margen de reventa | S4, S3 de datos, híbridos | — |
| ARR/MRR | P-SAAS, P-AI-APP con suscripción, línea S4 aparte como "MRR gestionado" | Consumo puro (usar run-rate y llamarlo así); servicios (H3) |
| NRR (UE-10) y GRR (UE-11) | Recurrentes, siempre juntos | < 12 meses de historia; S1–S3 (la "expansión" son más horas); P-USAGE sin contrato (usar caída de uso) |
| Churn de logos (UE-07) | P-SAAS-SS, S4 | Enterprise con pocos clientes (ruido); < 30 cliente-periodos o < 3 eventos |
| CAC payback (UE-18, UE-19) | P-SAAS, P-AI-APP, S4, AIX recurrente | Sin S&M separado; servicios por proyecto |
| LTV y LTV/CAC (UE-12 a UE-17) | Recurrentes, como señal secundaria | Como compuerta; churn < 1 %/mes sin cota; proyectos sin recurrencia |
| Magic number | SaaS sales-led con VC [M] | Pymes con venta del fundador |
| Burn multiple (UE-20) | SaaS e IA de producto con VC y ARR | Bootstrapped rentable ("N/A"); servicios; pre-revenue |
| Rule of 40 (FM-11) | SaaS con escala (> ~10 M$ de ARR) [I] | < 3 M$ de ARR (efecto denominador, PRD-007); micro y servicios |
| Margen bruto (UE-04) | Todos, con desglose de COGS | Sin desglose; con pass-through sin netear |
| Coste de cómputo por $ de ingreso [P] | P-AI-APP, P-USAGE, P-INFRA | — |
| CPST (UE-29 y 6f) | AIX, P-AI-APP | Con umbral de calidad definido a posteriori |

### 6a.6 Reglas de híbridos H0–H8 [P]

| ID | Regla | Base |
|---|---|---|
| H0 | Es híbrido si dos o más mecanismos tienen ≥ 20 % de los ingresos o del margen bruto cada uno, o si una línea pequeña es la tesis de valor ("somos una SaaS" con 5 % de ingresos SaaS) | [P] |
| H1 | Para cada reventa (licencias, nube, hardware, subcontratas, medios), registrar quién controla el bien antes de transferirlo; calcular siempre el ingreso neto de pass-through y mostrar margen sobre bruto (contable) y sobre neto (económico) | ASC 606-10-55-36 a 55-40, vía [PwC Viewpoint](https://viewpoint.pwc.com/dt/us/en/pwc/accounting_guides/revenue_from_contrac/revenue_from_contrac_US/chapter_10_principa_US/10_2_principal_versus.html) [D]; NCC contabiliza el mismo MDR como principal o como agente según el modelo [D] |
| H2 | El personal compartido se asigna por horas registradas a coste cargado; prohibido llevar soporte e implantación de la línea SaaS a I+D u opex; los ingenieros que construyen producto propio salen de la capacidad facturable | Definición de costes directos de Service Leadership [D]; [P] |
| H3 | ARR = solo suscripciones o licencias de derecho de acceso con renovación contractual; el MRR gestionado (S4) se reporta aparte; retainers de horas y equipos dedicados son backlog de servicios; la reventa recurrente no es ARR propio | [P] |
| H4 | Las transferencias internas (horas de S1 para construir el producto) se eliminan; el ingreso se reconoce una sola vez en el segmento que factura al tercero | Consolidación intragrupo [M]; [P] |
| H5 | Implementación, licencia y mantenimiento se separan si son obligaciones distintas; si no lo son, todo se difiere y se trata como riesgo de capital circulante; el desarrollo a medida con cesión de PI al cliente es S2 | ASC 606-10-25-19 a 25-22 [D vía PwC]; ASU 2025-06 sobre software de uso interno ([Crowe](https://www.crowe.com/insights/take-into-account/fasb-revises-internal-use-software-cost-guidance)) [S] |
| H6 | Servicios gestionados con reventa de infraestructura: aplicar H1; la reventa se evalúa contra su propio rango (no hay benchmark público) y la dependencia de un hiperescalador entra en G3 | Rackspace reduce a propósito la reventa de bajo margen ([Rackspace](https://ir.rackspace.com/news-releases/news-release-details/rackspace-technology-reports-fourth-quarter-and-full-year-2025)) [S] |
| H7 | Agentes de IA con supervisión humana: modificador AIX con enrutamiento por T5 (6a.1); coste por tarea = inferencia p50/p90 + minutos humanos × coste cargado; el margen se compara con S4, no con SaaS, si la línea queda como servicio | [P] |
| H8 | Valoración por suma de partes con el método de cada segmento; nunca un múltiplo de ARR sobre servicios ni un margen combinado frente a un benchmark de un solo arquetipo; G2 y G3 se evalúan por segmento y basta que falle uno con ≥ 20 % de los ingresos | Damodaran [M]; [P] |


### Especificación de módulos (6d)

| Módulo | Entradas (P0 en cursiva) | Cálculo y procedimiento | Umbrales y anclas específicas | Salida al ledger |
|---|---|---|---|---|
| **M1 Clasificación** | *% de ingresos por mecanismo*, *% humanos en el COGS por tarea si hay agentes*, país de entrega y facturación, motion, ACV, capacidad propia | Reglas de 6a.3; H0 para detectar híbridos; H1 para netear pass-through | Umbrales de 6a.3 [P]; no puntúa | `lines[]` con `archetype`, `modifiers`, `revenue_share`, `net_revenue` |
