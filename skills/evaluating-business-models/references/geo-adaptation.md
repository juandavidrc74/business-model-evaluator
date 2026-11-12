# Adaptación por país (Colombia e internacional)

> Leer siempre que el país del negocio no sea EE. UU. o que se use un benchmark de otro país.
>
> Generado desde: secciones 6i, 6i.1, 6i.3 y 6i.4 del informe «Evaluación negocios tecnológicos ampliada» (texto propio con citas). No editar a mano: editar el informe y ejecutar `evals/harness/build_references.py`. Etiquetas: [D] documentado, [S] secundario, [M] marco/libro o conocimiento no verificado, [I] inferencia, [P] propuesta metodológica.

## 6i. Adaptación geográfica: Colombia tiene datos gratuitos y nada se transfiere entre países sin ajuste documentado


## 6i.1 Cifras clave de Colombia (fechas y advertencias)

| Variable | Valor | Fecha del dato / publicación | ID | Advertencia |
|---|---|---|---|---|
| Tasa de política monetaria | 12,25 % | Vigente desde el 1-oct-2026; decisión del 30-oct-2026 (votación 4–3) ([BanRep](https://www.banrep.gov.co/es/noticias/junta-directiva/junta-directiva-octubre-2026)) | GEO-007 | Próxima decisión 30-nov-2026 |
| Inflación anual | 6,3 % | Septiembre de 2026; expectativas a dic-2026 6,9 % | GEO-008 | El dato de octubre (9-nov-2026) no se capturó |
| Inflación proyectada (FMI WEO) | 6,0 % (2026); 5,7 % (2027) | Edición no confirmada en la respuesta ([FMI](https://www.imf.org/external/datamapper/api/v1/PCPIPCH/COL)) | GEO-009 | — |
| TRM | 3.269,88 COP/USD | Vigente el 10-nov-2026 ([datos.gov.co](https://www.datos.gov.co/resource/32sa-8pi3.json)) | GEO-010 | Usar promedio del periodo en proyecciones |
| Usura (consumo y ordinario) | 28,34 % E.A. | Noviembre de 2026 (vía prensa) | GEO-011 | Techo legal, nunca tasa base |
| Crédito comercial ordinario, ponderado por monto | 16,66 % E.A. (todas las actividades); 25,44 % (deudores CIIU 6201/6202/6209/6311/6312) | Cortes semanales de octubre de 2026 (cálculo propio con la API) | GEO-023 | Mezcla de productos y plazos; "crédito productivo" a 37,2 % es la modalidad relevante para micro |
| SMMLV | 1.750.905 COP/mes + auxilio de transporte 249.095 | 2026, por **decreto transitorio** 0159 del 19-feb-2026 tras la suspensión del original ([La República](https://www.larepublica.co/economia/mintrabajo-publico-decreto-transitorio-que-mantiene-minimo-de-1-75-millones-en-2026-4331878)) | GEO-001, GEO-002 | Nulidad pendiente; usar el valor en pesos, no el % de prensa |
| Multiplicador de coste laboral | Legal teórico 1,38 (exonerada, art. 114-1 ET) a 1,52 (no exonerada); observado 1,46 en TI grande | Cálculo propio 2026; EAS 2024 | GEO-003, GEO-004 | Tasas legales no verificadas en norma primaria; **contador** |
| Recargos laborales | Dominical y festivo 90 % desde el 1-jul-2026 (100 % desde jul-2027); nocturno desde las 19:00; jornada de 42 h desde el 15-jul-2026 ([Deloitte](https://www.deloitte.com/latam/es/services/legal/perspectives/co-1julio2026-flash-extraordinario-legal-laboral.html)) | 2026 | — | Solo si el modelo opera fuera de horario; **abogado laboralista** |
| Renta de personas jurídicas | 35 % | Tabla de Damodaran de ene-2026 (dato KPMG) | GEO-005 | Proyecto de ley de rescate económico radicado el 29-oct-2026; **contador** |
| UVT | 52.374 COP | 2026 (Resolución DIAN 000238) | GEO-006 | Resolución no leída directamente |
| IVA | 19 % general; excluidos hosting, nube y mantenimiento a distancia (art. 476 ET, num. 24) ([MinTIC](https://www.mintic.gov.co/portal/715/w3-article-63377.html)) | Vigente | — | Desarrollo a la medida sin confirmar; régimen Simple con tope en conflicto (80.000 frente a 100.000 UVT); ICA y retenciones sin verificar; **contador** |
| Prima de riesgo país | CRP 2,85 %; ERP total 7,08 % (Baa3) | Tabla del 5-ene-2026; hay actualizaciones de abr y jul-2026 no leídas | GEO-012 | Descargar el archivo vigente antes de usar |
| Supervivencia a 5 años (todas las actividades) | 33,5 % (micro 33,4 %; pequeña 60,9 %; mediana 73,7 %; grande 85,7 %) | Cohorte 2017 → 2022 (Confecámaras, may-2023, vía [INCP](https://incp.org.co/publicaciones/infoincp-publicaciones/informacion-para-empresas/actualidad/2023/05/confecamaras-revelo-la-tasa-de-supervivencia-de-las-empresas-del-pais/)) | GEO-013 | Informe primario no leído; sin desglose TI; sociedades 44,5 % frente a 30,2 % según la fuente |
| Subsector TI grande (EAS 2024) | 457 empresas; ingresos 30.119 mm COP; 115.206 personas; gasto de personal 44,1 % de ingresos; ingresos por persona ≈ 261 M COP; excedente aproximado 15,9 % de ingresos | 2024 provisional, publicado el 12-dic-2025 | GEO-015 a GEO-017 | Solo empresas con ≥ 75 personas o ≥ 3.000 M COP; el excedente no es EBITDA |
| Márgenes de empresas TI grandes (Supersociedades) | Operativo mediano 7,5 % (p25 2,7; p75 13,2); neto 3,4 %; 18,6 % con pérdidas; n = 237 | Ejercicio 2025 (dataset actualizado en jul-2026) | GEO-018, GEO-019 | Sesgo de tamaño y supervivencia; no representan a una microagencia |
| Plazo legal de pago a mipymes | 45 días calendario desde 2022 (Ley 2024 de 2020) ([Garrigues](https://www.garrigues.com/es_ES/noticia/colombia-fija-nuevos-plazos-maximos-obligatorios-pago-facturas-ambito-mercantil)) | Vigente | GEO-022 | Excluye operaciones entre grandes; cumplimiento real cuestionado |
| Industria de software y TI (Fedesoft) | Ventas 44,2 billones COP; 6.805 empresas; exportaciones 1.758 M US$ | 2024, publicado el 6-oct-2025 | GEO-020 | Metodología no publicada; universo distinto de la EAS |


## 6i.3 Matriz variable × país

D = disponible gratis y verificado; P = parcial o no verificado en detalle; N = no disponible en lo encontrado; ? = no investigado.

| Variable | Colombia | EE. UU. | UE (ES/DE) | México | Brasil |
|---|---|---|---|---|---|
| Inflación actual y proyectada | D | D | D | D | D |
| Tasa de política | D | D | D | D | D |
| Tasas de crédito a pymes por tipo | D (SFC semanal con CIIU) | P | P | ? | ? |
| Salario mínimo | D (transitorio) | D [M] | D [M] | P | P |
| Salarios por ocupación TI | P (GEIH, Fedesoft) | D (OEWS) | P | P | P |
| Multiplicador de coste laboral | P (legal [M] + EAS 1,46) | D (ECEC 1,43, GEO-021) | P | ? | ? |
| Impuesto de sociedades | D (35 %) | D | D | D (30 %) | D (34 %) |
| Regímenes simplificados e IVA de servicios | P | P | P | ? | ? |
| Supervivencia total | D (Confecámaras) | D (BED) | D (Eurostat) | P | P |
| Supervivencia del sector TI | **N** | D (NAICS 51/54) | P (J62 vacío) | ? | ? |
| Márgenes de empresas TI locales | D (Supersociedades, grandes) / P (EAS) | D (EDGAR, cotizadas) | P | ? | ? |
| CRP y ERP | D | D | D | D | D |
| Plazos legales de pago | D (Ley 2024) | N [M] | D (Directiva 2011/7/UE) [M] | ? | ? |


## 6i.4 Reglas de adaptación por país [P]

| # | Regla |
|---|---|
| 1 | Todo benchmark lleva `country`, `reference_period`, `unit_of_analysis` (empresa, establecimiento o cotizada) y `transferability` ∈ {local, ajustable-documentado, proxy-con-advertencia, no-transferible} |
| 2 | Salarios: fuente local de la ocupación (GEIH o Fedesoft en Colombia, OEWS en EE. UU., ILOSTAT como respaldo); prohibido convertir salarios de EE. UU. a COP por tipo de cambio; sin dato local, SMMLV × múltiplo declarado por el usuario, calidad C |
| 3 | Coste laboral total con multiplicador por país y fuente: Colombia 1,38–1,52 legal o 1,46 observado en TI grande; EE. UU. 1,43; salario integral con base de aportes del 70 % y sin prima ni cesantías [M, contador]; recargos solo si se opera fuera de horario |
| 4 | Impuestos: tarifa nominal local con "verificar con contador"; para microempresas, el régimen Simple solo como escenario; el IVA es ingreso de terceros, no margen; ICA y retenciones como efecto de caja (anticipos), salvo indicación del contador |
| 5 | Proyecciones en moneda local nominal con inflación de BanRep o FMI, reportadas también en términos reales; si se mezclan precios en USD con costes en COP, paridad de inflación o supuesto cambiario declarado |
| 6 | Financiación: tasa SFC del tipo de crédito y tamaño correspondientes; la usura es solo el techo legal |
| 7 | Coste de capital: WACC_USD = rf USD + β × (ERP maduro + CRP del país) + ajustes; a COP con el diferencial de inflación (1 + r_USD) × (1 + π_local) / (1 + π_USD) − 1 [M]; prima por tamaño o iliquidez declarada como supuesto; beta total si el dueño no está diversificado; nunca el WACC de EE. UU. sin CRP |
| 8 | Tasas base: Colombia 33,5 % a 5 años o por tamaño; para TI no hay dato local y se usa BLS BED NAICS 51 (41–47 % a 5 años, GEO-014) marcado "proxy EE. UU., establecimientos, no transferible sin advertencia", siempre como rango |
| 9 | Márgenes: Supersociedades 2025 para TI grandes con advertencia de sesgo; Damodaran y EDGAR solo como "cotizadas", nunca como objetivo de una microagencia |
| 10 | DSO en Colombia: plazo pactado con tope legal de 45 días para acreedores mipyme frente a grandes deudores; estrés a 60–90 días; con concentración en grandes clientes, escenario de factoring |
| 11 | No extrapolación: si el país del benchmark ≠ país del negocio y no hay ajuste documentado (los admitidos son CRP, inflación, cargas laborales legales y tipo de cambio de flujos en moneda extranjera), el dato se muestra con bandera "no transferible", baja un nivel de calidad y no entra en la puntuación |
| 12 | Caducidad según la fuente: tasa de política e IPC mensual; SMMLV en enero; UVT en diciembre; Damodaran en enero y julio; EAS en diciembre; Supersociedades en julio |

La supervivencia a 5 años del sector Information en EE. UU. (41–47 %) es mayor que la de todas las empresas colombianas (33,5 %), pero no son comparables: establecimiento frente a unidad registrada, distinta definición de "muerte" (fin del empleo frente a no renovar la matrícula) y distinto sector [I]. La regla 11 corrige el sesgo hacia EE. UU. y cotizadas de la fase 1 sin bloquear el análisis cuando falta un dato local.
