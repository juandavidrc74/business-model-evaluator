# Economía AI-native: coste por tarea exitosa, supervisión, meters y umbrales

> Leer siempre que una línea lleve el modificador AIX o sea P-AI-APP: el precio del token no es el coste de la tarea.
>
> Generado desde: sección 6f del informe «Evaluación negocios tecnológicos ampliada» (texto propio con citas). No editar a mano: editar el informe y ejecutar `evals/harness/build_references.py`. Etiquetas: [D] documentado, [S] secundario, [M] marco/libro o conocimiento no verificado, [I] inferencia, [P] propuesta metodológica.

## 6f. Economía AI-native: el precio del token no es el coste de la tarea

### 6f.1 Precios de inferencia con fecha de acceso (9-nov-2026)

A 9-nov-2026 los precios de lista abarcan unas 500 veces entre modelos, y caché y batch son las palancas mejor documentadas. Estos valores caducan en semanas: `assets/price_cards.yaml` los guarda con `access_date` y `next_review` de un mes.

| Proveedor y modelo | Entrada / salida (USD por MTok) | Modificadores documentados | ID |
|---|---|---|---|
| Anthropic Opus 5.5 | 4 / 20 | Lectura de caché 0,05× en Opus y Sonnet 5.5; escritura 1,25× (5 min) o 2× (1 h); batch −50 %; inferencia solo en EE. UU. ×1,1; fast mode 2× | AI-001, AI-005, AI-006 |
| Anthropic Sonnet 5.5 | 2 / 10 | Batch 1 / 5; la subida prevista de Sonnet 5 a 3/15 se canceló | AI-002 |
| Anthropic Haiku 5.5 | 0,10 / 0,50 hasta 100k tokens de prompt; 0,50 / 2,50 por encima | El umbral cambia la economía de agentes con contexto largo | AI-003 |
| Anthropic Fable/Mythos 5.2 | 8 / 40 | Lectura de caché 0,025×; Mythos de disponibilidad limitada | AI-004 |
| Herramientas Anthropic | Web search 10 $ por 1.000; code execution con 1.550 h/mes gratis y luego 0,05 $/h; Managed Agents 0,08 $ por sesión-hora | Los resultados de búsqueda cuentan como entrada en turnos siguientes | AI-007 |
| OpenAI gpt-6-astra / gpt-6.1-sol / gpt-6.1-terra / gpt-6-luna / gpt-5-nano | 10/50; 2/10; 1/5; 0,10/0,50; 0,05/0,40 | Batch/Flex 0,5×; Fast ≈ 2–2,5×; regional +10 %; promociones con fecha de fin (GPT-5.6 Sol hasta el 30-nov-2026) | AI-009, AI-010 |
| Google Gemini 4 Argon | 2 / 10, **sube a 4 / 20 desde el 1-dic-2026** | Batch/Flex ≈ 0,5×; Priority ≈ 1,8×; grounding 5.000/mes gratis y luego 14 $ por 1.000 | AI-012 a AI-014 |
| Google Gemini 3.8 Flash | 0,75 / 3,75, **sube a 1,50 / 7,50 desde el 1-ene-2027** | 2.5 Pro y 2.5 Flash se redirigen el 1-dic-2026 | AI-012, AI-015 |
| Together AI (open-weight serverless) | gpt-oss-120B 0,15/0,60; DeepSeek V4.1 Flash 0,30/1,20; Qwen3.8 Flash 0,15/0,47; Kimi K3 3/15 | H100 3,99 $/GPU-h bajo demanda, 1,99 preemptible, 3,19 con reserva; inferencia dedicada H100 5,49 | AI-016, AI-017 |

Fuentes: [Anthropic](https://platform.claude.com/docs/en/about-claude/pricing), [OpenAI](https://developers.openai.com/api/docs/pricing), [Google AI Studio](https://aistudio.google.com/docs/pricing) (leída a través de un resumidor sin los últimos 3,5k caracteres: **reverificar las subidas antes del 1-dic-2026**) y [Together AI](https://www.together.ai/pricing). La trayectoria dentro de Anthropic es descendente (Opus 15/75 → 5/25 → 4/20, AI-008), pero el riesgo de precio es **bidireccional**: hay subidas de 2× publicadas, retiradas forzosas de modelos (AI-015) y subidas de GPU en 2026 (AI-018, [S]). Las tendencias de caída (Epoch AI: 9× a 900× al año a rendimiento constante, con caídas recientes que "podrían no persistir", [Epoch](https://epoch.ai/data-insights/llm-inference-price-trends), AI-019) miden precio por token a capacidad fija, no coste por tarea. El self-hosting solo compite con utilización alta: ignorar la utilización U infravalora el coste en un factor 1/U ([preprint](https://www.alphaxiv.org/abs/2606.11690), AI-045); en el ejemplo de la nota, una H100 a 3,99 $/h iguala a la API de gpt-oss-120B al procesar ≈ 4.220 tokens/s sostenidos al 100 % de utilización, sin contar personal [I]. El routing ahorra mucho en benchmarks de chat (RouteLLM, > 85 % en MT Bench, [arXiv](https://arxiv.org/pdf/2406.18665), AI-024), pero en agentes la misma precisión puede costar 3,7 veces más según la arquitectura (HAL, [Princeton](https://hal.cs.princeton.edu/), AI-023).

### 6f.2 Coste por tarea exitosa (CPST) con p50/p90/p95 [P]

Bai et al. muestran, en ocho modelos frontera sobre SWE-bench Verified, que el coste por instancia tiene cola derecha pesada, que los tokens de entrada dominan incluso con caché porque el agente reprocesa el historial, que más tokens no dan más éxito y que los modelos predicen mal su propio consumo (correlación ≤ 0,39) ([arXiv 2604.22750](https://arxiv.org/pdf/2604.22750), AI-022). τ-bench muestra que la fiabilidad cae con la repetición: GPT-4o pasa de pass^1 ≈ 0,61 a pass^8 ≈ 0,25 en retail ([arXiv 2406.12045](https://export.arxiv.org/pdf/2406.12045), AI-027). Con esas dos piezas, la especificación de `ai_native_model.py` es:

| Paso | Fórmula |
|---|---|
| Coste de un intento | C_att = [T_in·(1 − h − w)·P_in + T_in·w·P_cw + T_in·h·P_cr + T_out·P_out] / 1e6 + Σ herramientas + t_runtime·P_runtime, con h = cuota de lectura de caché y w = cuota de escritura |
| Fiabilidad heterogénea | p_j ~ Beta(α, β); pass^k = Π_{i=0}^{k−1} (α + i)/(α + β + i); P(éxito en ≤ K intentos) = 1 − Π_{i=0}^{K−1} (β + i)/(α + β + i); α/(α + β) = pass^1 medido y s = α + β ajustado a un pass^k medido |
| Coste humano | C_h = 1[autónoma]·(q·t_qa·w_h + SER·(q·t_fix + (1 − q)·t_late)·w_h) + 1[escalada]·t_esc·w_h (+ daño externo si el error lo causa) |
| Coste fijo asignado | C_fix = (evals + mantenimiento de prompts + migraciones de modelo + infraestructura + observabilidad) / volumen; ≥ 1 migración al año por defecto |
| Totales | C_task = Σ C_att + C_h + C_fix; CPST_auto = Σ C_att / tareas autónomas correctas; CPST_total = Σ C_task / tareas entregadas correctas |
| Salidas | p50, p90, p95 y p99 de C_task y C_att; media; cuota del top 10 % de tareas; cuota humana del COGS; P(C_task > precio) |
| Sin logs | T_in ~ lognormal(ln mediana, σ ∈ [0,8; 1,2]) marcado "no calibrado"; s = 1,37 si no hay pass^k |
| Muestra mínima | n = z²·p(1 − p)/e²: 323 tareas para estimar una autonomía de ~70 % con ±5 % al 95 % |

Con los datos de τ-retail, s ≈ 1,37 y la probabilidad de éxito con 2, 3 y 5 intentos es 0,75, 0,81 y 0,87; suponiendo intentos independientes saldría 0,85, 0,94 y 0,99. **Suponer reintentos independientes sobreestima la autonomía en 9–13 puntos** [I].

**Ejemplo ILUSTRATIVO, no benchmark** (Sonnet 5.5; entrada lognormal con mediana de 150k tokens; caché h = 0,70; autonomía media 0,70 con K = 3; QA del 20 % de 3 min; error silencioso del 3 %; escalado con mediana de 15 min; 40 $/h; 0,15 $ de coste fijo; 100.000 tareas simuladas):

| Métrica (USD por tarea) | p50 | p90 | p95 | p99 | Media |
|---|---|---|---|---|---|
| Inferencia + herramientas | 0,28 | 1,01 | 1,38 | 2,47 | 0,45 |
| Coste total | 0,61 | 10,23 | 15,74 | 21,73 | 2,88 |

El completado autónomo fue del 87,3 %, el 12,7 % se escaló, el 2,1 % de las tareas llegó al cliente con error y los humanos fueron el 79 % del coste. A 1,50 $ por tarea, el "margen con inferencia media" sería del 70 %; con el coste total, −92 %. La palanca dominante es la tasa de escalado, no el precio del token [I].

### 6f.3 Supervisión humana: lo que dice la evidencia independiente

Las ganancias documentadas son reales pero modestas y de **aumento**, no de sustitución: un asistente de IA subió un 14 % las resoluciones por hora en soporte, ≈ 34 % en novatos y casi nada en expertos ([NBER w31161](https://nber.org/papers/w31161), AI-028). En el RCT de METR, desarrolladores expertos tardaron un 19 % **más** con IA aunque creían haber ganado un 20 % ([arXiv](https://arxiv.org/pdf/2507.09089), AI-029); su actualización de febrero de 2026 declara sus nuevas estimaciones no fiables por sesgo de selección ([METR](https://metr.org/blog/2026-02-24-uplift-update/)). Las cifras de autonomía de proveedores no están auditadas: Klarna anunció el trabajo de 700 FTE y en 2025 su CEO admitió menor calidad y volvió a contratar ([Tech.co](https://tech.co/news/klarna-reverses-ai-overhaul), AI-032, [S]); Intercom cobra 0,99 $ por outcome y cuenta como tal que el cliente deje de pedir ayuda, incluidos traspasos ([Intercom](https://www.intercom.com/pricing), AI-033). Por eso la Skill exige estas métricas medidas por el proponente [P]:

| Métrica | Fórmula | Fuente del dato |
|---|---|---|
| Tasa de completado autónomo (ACR) | Tareas cerradas sin intervención **y** correctas / tareas | Logs + QA por muestreo |
| Tasa de intervención (IR) y de escalado (ER) | Tareas con ≥ 1 intervención / tareas; traspasadas / tareas | Logs |
| Tasa de error silencioso (SER) | Errores hallados en QA ciego / tareas autónomas muestreadas | QA ciego |
| Tiempo de revisión | Media, p50 y p90 de minutos por revisión | Registro de tiempos |
| Coste de revisión y de corrección | q·t_qa·w; SER·[q·t_fix + (1 − q)·(t_late + daño)]·w | Cálculo |
| Fiabilidad | pass^k con k = 3–8 en un *eval set* fijo | Evals |
| Ratio de supervisión | Horas humanas por 100 tareas | Cálculo |

### 6f.4 Escalabilidad, márgenes y viabilidad del meter

Un negocio AI-native escala si su coste marginal por tarea exitosa baja o se mantiene con el volumen. La inferencia es casi lineal; las economías vienen de la fiabilidad (menos escalados y errores silenciosos), de amortizar evals y mantenimiento y de mejorar prompts y routing con datos de uso. **Si la fiabilidad no mejora con el volumen, el negocio escala como servicio, no como software** [I]. Los márgenes observados siguen por debajo del SaaS clásico (25–60 % según arquetipo en Bessemer, PRD-021; 45 % en ICONIQ para 2025, PRD-019; 31 % GAAP en C3.ai, AI-040). Los moats de datos se tratan como no probados hasta que el proponente demuestre una mejora medible de ACR, SER o coste frente a un modelo frontera sin esos datos ([a16z](https://a16z.com/2019/05/09/data-network-effects-moats/), [S]). El mercado converge en híbridos y el outcome solo funciona con un resultado observable, atribuible y contratable ([Bain](https://www.bain.com/insights/ai-pricing-a-reality-check-on-effort-usage-and-outcomes/), AI-043). Matriz de viabilidad [P]:

| Meter | Viable si | Riesgo principal | Test numérico de la Skill |
|---|---|---|---|
| Seat | Uso por usuario acotado y estable | Usuarios intensivos | Coste p95 por seat/mes < 0,5 × precio |
| Consumo (tokens, acciones) | El cliente tolera la variabilidad | Sesgo hacia la tarifa plana (AI-044) | Margen por unidad ≥ objetivo en p50 y > 0 en p95 |
| Créditos o capacidad | Mix de acciones estable | Breakage y cambios de mix | Coste p90 por crédito < precio por crédito |
| Por tarea | Tarea discreta y contable | Cola de coste | Precio ≥ C_task p90 (G2) |
| Por outcome | Resultado observable, atribuible, verificable y contratable | Pagar los fallos y disputas de definición | Precio ≥ CPST_total p90 / (1 − margen objetivo) y definición escrita y auditable |
| Suscripción plana | Uso muy predecible | Usuarios intensivos destruyen el margen | Simular la cola de clientes (p95/p99) |
| Híbrido (plataforma + consumo u outcome) | Atribución confundida o coste incierto | Complejidad | Fee fijo ≥ C_fix; componente variable ≥ coste p90 |

Con outcome pricing, el ingreso por tarea es precio × P(éxito facturable), y el margen se calcula sobre ese ingreso, incluidas las tareas fallidas no facturadas. En el ejemplo ilustrativo, ni 2 $ por resolución cubren el coste total medio (2,88 $): la economía solo cierra con escalado < ~5 % y QA ligera, o con un fee de plataforma [I].

### 6f.5 Umbrales T1–T9 y red flags [P]

| Umbral | Regla | Conexión con CEST |
|---|---|---|
| T1 | Precio por tarea u outcome < C_task p90 → **falla G2** | G2 |
| T2 | Margen medio con humanos < 50 % en un "producto de IA" → evaluar como servicio | M11, M14 (PRD-019, PRD-021) |
| T3 | Margen < 0 con precio del proveedor ×2,0 → riesgo alto (y KO de G3 si además no hay fallback probado) | M11, G3 (AI-012) |
| T4 | Proveedor principal > 80 % de los tokens sin fallback probado → riesgo de dependencia | M10 |
| T5 | Humanos > 40 % del COGS por tarea → enrutar a S2/S4 con benchmarks de servicios | M1, M14 |
| T6 | ACR medido con n < 323 o sin QA ciego → confianza baja | Ledger |
| T7 | pass^k (k ≥ 3) no reportado → supuestos de fiabilidad no aceptados; usar s = 1,37 | M10 |
| T8 | Top 10 % de tareas > 50 % del coste de IA → exigir topes de coste | M11 |
| T9 | Seat con coste p95 por cliente > 50 % del precio → repricing o límites | M7 |

**Red flags** (cada uno con su evidencia): (1) margen calculado con inferencia media o p50, sin p90/p95 (AI-022); (2) precio por tarea u outcome bajo el coste p90 (T1); (3) revisión humana no presupuestada o estimada por intuición (METR, AI-029); (4) reintentos supuestos independientes (AI-027); (5) un solo proveedor sin fallback o margen que no resiste ×2 (AI-012, AI-015); (6) "el coste de inferencia caerá 10× al año" en el plan de márgenes (AI-019 a AI-021); (7) autonomía o resolución de un vendor usada como propia (AI-032 a AI-034); (8) definición de outcome ambigua o no auditable (AI-043); (9) sin presupuesto de evals, prompts ni migraciones (AI-015); (10) tarifa plana o seat sin límites ni simulación de clientes intensivos; (11) coste de herramientas ignorado (10–14 $ por 1.000 búsquedas, AI-007, AI-011, AI-014); (12) moat de datos sin demostración; (13) self-hosting justificado al 100 % de utilización o sin personal (AI-045); (14) comparación de coste sin línea base simple (AI-023); (15) recargos de residencia o región ignorados en clientes regulados (AI-006, AI-009); (16) productividad de copiloto (+14 %) presentada como sustitución autónoma (AI-028).
