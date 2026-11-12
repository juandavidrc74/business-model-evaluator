# Due diligence empresarial y técnica, y tabla de compliance

> Leer en M10, M13 y para G3, G4 y G7. Sin escaneo activo de terceros; los marcos no son universales.
>
> Generado desde: sección 6h del informe «Evaluación negocios tecnológicos ampliada» (texto propio con citas). No editar a mano: editar el informe y ejecutar `evals/harness/build_references.py`. Etiquetas: [D] documentado, [S] secundario, [M] marco/libro o conocimiento no verificado, [I] inferencia, [P] propuesta metodológica.

## 6h. Due diligence: no hay estándar técnico, pero sí piezas normalizadas que se pueden componer

La búsqueda de la fase 2 confirma que **no existe un estándar de Technical Due Diligence**; las guías son de practicantes y una de ellas admite que no hay checklist industrial ([Redwerk](https://redwerk.com/blog/ma-technical-due-diligence-checklist/)). Sí existen estándares parciales: ISO/IEC 25010:2023 como taxonomía de calidad con nueve características ([arc42](https://quality.arc42.org/standards/iso-25010)); ISO/IEC 5055 para calidad estructural medida con CWE ([CISQ](https://www.it-cisq.org/webinars/iso-5055-automated-source-code-quality-measures)); OpenChain ISO/IEC 5230 y 18974 para licencias y seguridad del open source ([OpenChain](https://openchainproject.org/security-assurance)); SPDX y CycloneDX para el SBOM; OWASP SAMM y ASVS como preguntas de madurez; Well-Architected, SRE, DORA e ISO 22301 para operación y continuidad. La evidencia de riesgo más útil viene de un proveedor de auditorías de M&A: el 56 % de 965 bases de código tenía conflictos de licencia y el 86 % componentes vulnerables ([Black Duck](https://blackduck.com/blog/ossra-addresses-common-open-source-questions.html), DD-003, DD-005, [S]). En negocio, el 10 % de ingresos por cliente de ASC 280 e IFRS 8 es un umbral de **divulgación** (DD-001, DD-002); los cortes de riesgo son [P]. Esta sección es metodología de evaluación, **no asesoramiento legal**: donde la tabla dice "abogado", hay que consultar a uno.

### 6h.1 Matriz de due diligence (para `references/due-diligence.md`)

Pub = verificable con información pública; Emp = solo con datos de la empresa. "KO → Gx" indica la compuerta que activa el fallo; un dato P0 no verificable activa G6. Las filas tienen fuente, pero su selección, sus cortes y sus vínculos con las compuertas son [P]. El evaluador **no escanea activamente** sistemas ajenos sin autorización escrita: solo observación pasiva de información pública.

| ID | Riesgo | Condición de fallo o alerta | Evidencia | Arquetipos | Fuente |
|---|---|---|---|---|---|
| N01 | Equipo fundador | Ningún fundador con experiencia en venta B2B ni en entrega del servicio, sin plan de contratación (alerta) | Pub/Emp | Todos | Sahlman; Gompers et al. 2020 |
| N02 | Persona clave | Una persona controla código, cliente principal y credenciales sin documentación; KO → G7 si la entrega depende de ella | Emp | Todos, sobre todo S3, S2 y AIX | Fase 1 [P] |
| N03 | Gobierno corporativo | Cap table que no cuadra o socios inactivos con mucho capital sin pacto (alerta) | Emp | Todos | Kaplan & Strömberg |
| N04 | Concentración de clientes | Un cliente ≥ 50 % sin contrato plurianual o con terminación por conveniencia: KO → G3 [P] | Emp (Pub si cotiza) | S1–S4, AIX | ASC 280; IFRS 8; Patatoukas; Irvine et al. |
| N05 | Relaciones jóvenes | Concentración alta con relaciones de < 2 años (alerta) [P] | Emp | Todos B2B | Irvine et al. 2016 |
| N06 | Proveedor crítico único | Insumo crítico sin alternativa probada: KO → G3 | Emp | Producto, AIX, S4 | Fase 1 G3 |
| N07 | Partner o marketplace | Gran parte de los ingresos vía un partner con terminación unilateral (alerta, sin umbral documentado) | Pub/Emp | S3, S4, SaaS | [I] |
| N08 | Terminación por conveniencia | Contratos cancelables con < 30 días sin penalización usados como "ARR": se reclasifican | Emp | SaaS, S4, AIX | [I] |
| N09 | Límite de responsabilidad | Responsabilidad ilimitada por datos o PI sin seguro cyber (alerta; abogado) | Emp | Todos | [I] |
| N10 | SLA y penalizaciones | SLA más exigente que lo medido o penalizaciones sin tope: KO → G7 | Pub/Emp | SaaS, S4, P-INFRA, AIX | SRE |
| N11 | Código de empleados | Sin cesión documentada donde no se presume: KO → G4 | Emp | Todos los que venden software | 17 U.S.C. §101 [M]; Ley 23/1982 art. 20 mod. Ley 1450 art. 28 |
| N12 | Código de contratistas | Núcleo del producto escrito por freelancers sin cesión escrita: KO → G4; abogado | Emp | SaaS, P-AI-APP, AIX, S2 | Ídem; conflicto en fuentes colombianas |
| N13 | PI cedida a clientes | "Producto" construido con código cedido a clientes en SOW: KO → G4 | Emp | S1, S2, AIX | [I] |
| N14 | GenAI en el código | Sin política ni registro donde la PI es el activo (alerta) | Emp | SaaS, P-AI-APP | NVCA SPA [S] |
| N15 | Riesgo financiero | Runway < plazo al siguiente hito sin financiación comprometida (alerta) | Emp | Todos | M9 |
| N16 | Litigios y sanciones | Litigio o sanción material no divulgado: KO → G6 o G4 | Pub/Emp | Todos | [I] |
| N17 | Profundidad de la DD | Informativo: no saltar la DD en operaciones "calientes" | — | — | Wangerin 2019; Fu & Taylor 2024 [S] |
| T01 | Arquitectura | Escalado prometido (10×) sin pruebas de carga ni diseño que lo soporte (alerta M14) | Emp | Producto, AIX | ISO 25010; Well-Architected |
| T02 | Calidad de código | Sin CI ni tests en el producto núcleo (alerta) | Pub/Emp | Producto, AIX, S1 | ISO 5055; ISO 25010 |
| T03 | Deuda técnica | Runtime o framework sin soporte en producción sin plan (alerta) | Emp | Quien opera software | Kruchten, Nord & Ozkaya [M] |
| T04 | Seguridad de aplicación | Sin pentest ni prueba de seguridad en una app con datos sensibles: KO → G4 si el cliente lo exige | Emp | SaaS, P-AI-APP, AIX, S4-MSSP | OWASP SAMM; ASVS 5.0 |
| T05 | Higiene de repositorios | Puntuación baja de OpenSSF Scorecard: pedir evidencia | Pub | OSS público | OpenSSF Scorecard [M] |
| T06 | Dependencias vulnerables | Vulnerabilidades críticas conocidas sin parchear (alerta) | Emp | Quien opera software | OSSRA 2025; ISO 18974 |
| T07 | Licencias OSS | Copyleft fuerte (GPL; AGPL en SaaS) sin cumplimiento: KO → G4; abogado | Emp | SaaS, P-AI-APP, S1, S2 | OpenChain 5230; OSSRA 2025 |
| T08 | Infraestructura | Credenciales en el repositorio o producción manual sin backup (alerta) | Emp | Producto, S4 | Well-Architected |
| T09 | Disponibilidad | Ver N10 → G7 | Pub/Emp | SaaS, S4, P-INFRA | SRE |
| T10 | Observabilidad | Servicio con SLA sin monitorización ni alertas: KO → G7 | Emp | SaaS, S4, P-INFRA, AIX | Google SRE |
| T11 | Backups y DR | Sin prueba de restauración en ≤ 12 meses (alerta); RTO contractual sin prueba: KO → G7 | Emp | Quien custodia datos | ISO 22301 [M]; [P] |
| T12 | Continuidad | Ver N02 y N06 | Emp | S4, P-INFRA | ISO 22301 |
| T13 | Lock-in cloud | Salida imposible en < 12 meses con cliente que exige portabilidad (alerta) | Emp | Producto | DORA UE art. 30 [S] |
| T14 | Gestión de datos | Sin inventario de datos personales donde se tratan: KO → G4 | Emp | Quien trata datos personales | GDPR art. 30 [M]; Ley 1581 |
| T15 | Mantenibilidad | Ver N02 | Emp | Todos | ISO 25010 |
| T16 | Entrega (DORA) | Sin medición: no es KO, se puntúa en M10 | Emp | Producto, S1 | dora.dev |
| C01 | Privacidad | Datos personales sin política ni base legal: KO → G4 | Pub/Emp | Todos | Ley 1581, GDPR, LGPD, leyes estatales de EE. UU. |
| C02 | RNBD Colombia | Obligado (activos > 100.000 UVT) y no registrado (alerta subsanable) | Pub/Emp | Empresas colombianas | Decreto 090 de 2018 |
| C03 | Certificación exigida por el cliente | El segmento objetivo exige SOC 2 o ISO 27001 sin plan ni presupuesto: KO → G4 | Pub/Emp | SaaS, S4, P-INFRA, P-AI-APP | Fase 1 G4 (reformulada) |
| C04 | Sector regulado | Vende a salud de EE. UU. sin BAA, procesa tarjetas sin PCI o sirve a finanzas de la UE sin cláusulas DORA: KO → G4 | Emp | Según cliente | HIPAA, PCI DSS, DORA |
| C05 | NIS2 | Entidad en alcance (MSP, MSSP o cloud ≥ mediana en la UE) sin medidas de gestión de riesgos: KO → G4 | Pub/Emp | S4, P-INFRA (UE) | NIS2 [S] |
| C06 | AI Act | Caso prohibido: KO → G4; caso del Anexo III sin plan antes del 2-dic-2027 (alerta) | Pub/Emp | P-AI-APP, AIX con UE | AI Act + Omnibus 2026 [S] |
| IA01 | Prompt injection | Agente con herramientas sobre contenido externo sin pruebas de inyección (alerta) | Emp | P-AI-APP, AIX | OWASP LLM01; AgentDojo |
| IA02 | Agencia excesiva | Acciones irreversibles con daño material sin humano en el bucle: KO → G7 [P] | Emp | AIX, P-AI-APP | OWASP LLM06 |
| IA03 | Alucinación y calidad | Sin *eval set* propio en un dominio de alto impacto (legal, salud, finanzas): KO → G6 | Emp | P-AI-APP, AIX | Magesh et al. 2025; OWASP LLM09 |
| IA04 | Fallo de agentes | Automatización "end-to-end" prometida sin medición frente a una línea base (alerta) | Emp | AIX | MAST; TheAgentCompany; Kapoor et al. |
| IA05 | Fuga de datos | Datos de clientes enviados a un proveedor que entrena con ellos sin consentimiento: KO → G4 | Pub/Emp | P-AI-APP, AIX | OWASP LLM02/07/08 |
| IA06 | Dependencia del proveedor de modelo | Un solo modelo, sin plan de migración probado y margen < 0 con precio ×2,0: KO → G3 [P]. **Corrección fase 2:** antes ±50 % | Pub/Emp | P-AI-APP, AIX | Páginas de deprecación de OpenAI y Anthropic; AI-012 |
| IA07 | Coste desbocado | Precio fijo con coste variable sin tope: KO → G2 si el p90 > precio | Emp | P-AI-APP, AIX | OWASP LLM10; FinOps for AI |
| IA08 | Reproducibilidad | Decisiones con efecto legal sin logs ni versionado: KO → G4 | Emp | P-AI-APP, AIX | AI Act (registros) |
| IA09 | Modelos de terceros | Modelo con licencia incompatible con el uso comercial: KO → G4 | Pub/Emp | P-AI-APP, AIX | OWASP LLM03/04; MITRE ATLAS |

Las frecuencias de riesgo AI-native son de **benchmark**, no de producción, y sirven como outside view: los sistemas multiagente fallan en el 41–86,7 % de las trazas según el marco ([Cemri et al.](https://arxiv.org/html/2503.13657v2), DD-009); el mejor agente completó el 30,3 % de tareas de oficina simuladas ([TheAgentCompany](https://arxiv.org/html/2412.14161v2), DD-010); la inyección tuvo éxito en menos del 25 % de los casos contra los mejores agentes y en el 8 % con un detector ([AgentDojo](https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract.html), DD-011); las herramientas legales con RAG alucinaron en al menos el 17 % de las consultas ([Magesh et al.](https://nlp.stanford.edu/~manning/papers/Magesh-Hallucination%E2%80%90Free-2025.pdf), DD-012). OpenAI publica aviso previo de deprecación, de unos 6 meses para modelos GA según fuentes secundarias (DD-017); Anthropic se comprometió a conservar los pesos de sus modelos públicos, pero no su disponibilidad por API ([Anthropic](https://www.anthropic.com/research/deprecation-commitments)).

### 6h.2 Tabla de decisión de compliance [P sobre fuentes D/S/M]

Ningún marco es universal. Regla de uso: G4 falla **solo** si aplica una fila "Legal" sin cumplimiento ni plan, o una fila "Contractual" del segmento **objetivo declarado** sin plan ni presupuesto; las filas "Voluntario" suman en M10 o M13 y nunca son KO.

| # | Si… | Marco | Tipo | Coste o plazo con evidencia | ¿Abogado? |
|---|---|---|---|---|---|
| 1 | Trata datos personales de residentes en Colombia | Ley 1581 de 2012; Circular SIC 002 de 2024 si usa IA ([SIC](https://sedeelectronica.sic.gov.co/sites/default/files/normativa/Circular%20Externa%20No.%20002%20del%2021%20de%20agosto%20de%202024.pdf)) | Legal | Sin coste documentado | Sí |
| 2 | Lo anterior y activos > 100.000 UVT | Registro Nacional de Bases de Datos ([Decreto 090](https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=85039), DD-013) | Legal | Sin coste documentado | Recomendable |
| 3 | Trata datos de residentes de la UE | GDPR (DPA art. 28, transferencias cap. V, registro art. 30) | Legal, multas hasta 4 % o 20 M€ [M] | Sin coste documentado para pymes | Sí |
| 4 | Trata datos de residentes en Brasil | LGPD | Legal, multas hasta 2 % con tope de 50 M R$ por infracción [M] | Sin coste documentado | Sí |
| 5 | Trata datos de consumidores de estados de EE. UU. con ley integral | Leyes estatales (unas 20; consultar el tracker de la [IAPP](https://iapp.org/resources/article/us-state-privacy-legislation-tracker)) | Legal | Sin coste documentado | Sí |
| 6 | Trata PHI para entidades sanitarias de EE. UU. | HIPAA (BAA) | Legal o contractual | Sin coste documentado | Sí |
| 7 | Almacena, procesa o transmite datos de tarjeta | PCI DSS v4.0.1 (alcance reducible con tokenización) | Contractual | Sin coste documentado | Recomendable |
| 8 | Proveedor TIC de entidades financieras de la UE | DORA art. 30; supervisión directa si es CTPP (19 designados el 18-nov-2025, [ESMA](https://www.esma.europa.eu/press-news/esma-news/european-supervisory-authorities-designate-critical-ict-third-party-providers), DD-016) | Contractual vía cliente (legal si es CTPP) | Sin coste documentado | Sí |
| 9 | MSP, MSSP, cloud o centro de datos en la UE con ≥ 50 empleados o > 10 M€ | NIS2 ([CCB](https://ccb.belgium.be/en/publication/nis2-directive-whom-why), DD-015, fuentes en conflicto) | Legal según transposición | Sin coste documentado | Sí |
| 10 | Proveedor de un MSP o cloud sujeto a NIS2 | NIS2 indirecta | Contractual | Sin coste documentado | Recomendable |
| 11 | Sistema de IA con usuarios en la UE que interactúa con personas o genera contenido sintético | AI Act art. 50, desde el 2-ago-2026 | Legal | Sin coste documentado | Sí |
| 12 | Caso de uso del Anexo III (empleo, crédito, educación…) en la UE | AI Act alto riesgo, desde el 2-dic-2027 tras el Omnibus (DD-018) | Legal | Sin coste documentado | Sí |
| 13 | Proveedor de un modelo GPAI en la UE | AI Act GPAI, desde el 2-ago-2025 | Legal | Sin coste documentado | Sí |
| 14 | Vende SaaS, MSP o MSSP a mid/enterprise de EE. UU. que lo pide en procurement | SOC 2 Type 2 | Contractual o comercial | Auditoría 12–50 kUSD; primer año 30–150 kUSD (proveedores, DD-019) | No |
| 15 | Vende a enterprise o sector público de la UE o LatAm, o a finanzas | ISO/IEC 27001:2022 | Contractual o comercial | 5.000–50.000 GBP + 3.000–10.000 GBP/año (proveedor, DD-020) | No |
| 16 | MSSP o empresa de ciberseguridad | NIST CSF 2.0 como marco de servicio + fila 14 o 15 | Voluntario o comercial | Gratuito | No |
| 17 | IA de producto o AIX que vende a enterprise, regulados o UE | NIST AI RMF o ISO/IEC 42001 | Voluntario o comercial | 42001 sin coste documentado | No |
| 18 | Distribuye software o vende a clientes que piden SBOM | OpenChain ISO/IEC 5230 + SBOM | Voluntario o contractual | Autocertificación gratuita [M] | Para copyleft, sí |
| 19 | Pyme B2B que vende a pymes de LatAm sin datos sensibles ni sector regulado | Ninguna certificación; buenas prácticas (NIST CSF como guía) | — | — | No |

Para una empresa colombiana pequeña, el disparador legal más probable es la Ley 1581 (siempre) más el RNBD si supera los 100.000 UVT; SOC 2 solo importa si vende a empresas de EE. UU. que lo piden, y la ISO 27001 si vende a clientes grandes de la UE o LatAm o al sector financiero [I]. DORA no aplica directamente a un proveedor no financiero, pero sí por contrato si sus clientes son entidades financieras de la UE [I]. La titularidad del código de contratistas en Colombia está **en conflicto**: el comunicado oficial sobre la Ley 1450 de 2011 habla de presunción de transferencia en contratos de prestación de servicios ([Ámbito Jurídico](https://ambitojuridico.com/sites/default/files/BancoMedios/Archivos/comunicado%20explican%20alcances%20de%20reforma%20al%20regimen%20-%2011.pdf)), mientras una fuente de plantillas exige cláusula expresa; la Skill pide siempre la cesión escrita y remite a un abogado.
