# M5: competencia, defensibilidad e inteligencia competitiva

> Leer en M5: siete cubos de competidores, ficha por competidor, reglas de información ausente y límites éticos.
>
> Generado desde: secciones 6d (M5) y 6g.2 del informe «Evaluación negocios tecnológicos ampliada» (texto propio con citas). No editar a mano: editar el informe y ejecutar `evals/harness/build_references.py`. Etiquetas: [D] documentado, [S] secundario, [M] marco/libro o conocimiento no verificado, [I] inferencia, [P] propuesta metodológica.

### Especificación de módulos (6d)

| Módulo | Entradas (P0 en cursiva) | Cálculo y procedimiento | Umbrales y anclas específicas | Salida al ledger |
|---|---|---|---|---|
| **M5 Competencia y defensibilidad** | Siete cubos C1–C7, fichas M5.2 | M5.1 y M5.2 (6g); prueba de Helmer frente al cubo más fuerte; cinco fuerzas con IA como sustituto; kernel de Rumelt | Techo 2 si un vendor de plataforma (C5) ya incluye la función en una licencia que el cliente paga y no hay beneficio + barrera demostrados; 5 exige un poder con ambos elementos evidenciados [P] | `competitors[]`, `saturation_reached`, `power_test`, riesgo P0 de bundling |


## 6g.2 Competencia por web (M5.1–M5.2) [P]

La lista de competidores sale del **trabajo del cliente** (una línea: verbo + objeto + contexto), no de la categoría del fundador, y siempre incluye dos competidores que el fundador omite: hacerlo internamente o no hacer nada, y que una plataforma lo incluya en su paquete. El caso Teams lo documenta: la Comisión Europea aceptó el 12-sep-2025 compromisos de Microsoft para vender suites sin Teams, y los analistas no esperaban un éxodo pese al desagregado ([The Register](https://www.theregister.com/2025/09/12/eu_regulators_let_microsoft_off/), [S]).

**M5.1, siete cubos obligatorios**, cada uno con al menos una búsqueda registrada aunque dé cero: C1 directos; C2 indirectos (consultoras, agencias, BPO, freelancers); C3 sustitutos y no consumo (Excel, proceso manual, no hacer nada, con su coste en horas); C4 build interno (incluidas ofertas de empleo del cliente objetivo pidiendo ese perfil); C5 plataformas que pueden empaquetar la función (hiperescalares, suites, laboratorios de modelos con agentes); C6 entrantes potenciales recién financiados; C7 open source o herramientas gratuitas que hacen el 80 %. Cada candidato se clasifica por cubo, segmento, precio público o `unknown`, solapamiento y fecha. **Parada:** dos familias de consulta consecutivas sin competidores nuevos de solapamiento alto, o 25 candidatos (`saturation_reached`). La prueba de Helmer se aplica al diferencial frente al **cubo más fuerte**. **Knock-out:** si un vendor de C5 ya ofrece la función dentro de una licencia que el cliente paga y no hay beneficio + barrera demostrables, M5 no puede pasar de 2 y el riesgo es P0.

**M5.2, ficha por competidor** (máximo 8, priorizando C1, C2 y C5 de solapamiento alto):

| Campo | Dónde mirar | Regla de evidencia |
|---|---|---|
| Precio y planes | /pricing, documentación, marketplaces cloud, licitaciones públicas | Publicado = `fact` con fecha; "Contact sales" = `unknown` (**nunca inferir precio del silencio**); de un tercero = `estimate` |
| Posicionamiento | Home, páginas de soluciones, comparativas "vs" | Cita ≤ 15 palabras; trabajo y segmento declarados |
| Clientes | Casos de estudio, logos, notas de prensa | Logo sin caso = señal débil; caso con nombre, cifra y fecha = hecho autodeclarado |
| Barreras | Docs técnicas, integraciones, certificaciones, patentes | Certificación verificable en el auditor o trust center |
| Reputación | G2, Capterra, Clutch, Trustpilot; Glassdoor (empleados) | n y fecha; n < 10 no concluyente; nunca promediar plataformas. La regla de la FTC de 2024 prohíbe incentivos condicionados al sentimiento ([FTC](https://www.ftc.gov/news-events/news/press-releases/2024/08/federal-trade-commission-announces-final-rule-banning-fake-reviews-testimonials)), pero las campañas las disparan los vendedores [I] |
| Tracción | Ofertas de empleo, plantilla pública, apps, tráfico estimado | Tráfico solo como orden de magnitud ±50 %: Similarweb dio un 19,4 % menos de visitas y un 38,7 % menos de usuarios únicos que Google Analytics en 86 sitios ([PLOS ONE](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9140287/), MKT-005/006) |
| Stack | Detectores públicos sin cuenta | Solo front-end; ausencia ≠ no uso |
| Financiación | Notas de prensa, SEC Form D, páginas públicas sin sesión | Ronda con fuente primaria = `fact`; agregador = `estimate`. El plan gratuito de Crunchbase exige registro (la Skill no crea cuentas, MKT-015) |

Información ausente: `unknown` se propaga; ≥ 2 fuentes independientes para pasar de `estimate` a `fact`; si discrepan, `contradiction` sin promediar; prohibido inferir precio de "contact sales", clientes de logos o ingresos de plantilla sin ratio documentado. **Límites éticos:** solo páginas públicas sin login, sin crear cuentas, sin formularios de demo con identidad falsa, sin hacerse pasar por cliente, sin scraping que viole robots.txt o términos de uso y sin documentos filtrados; basado en el código de SCIP vía fuentes secundarias ([Crayon](https://www.crayon.co/blog/how-to-practice-ethical-competitive-intelligence)) y en las restricciones del proyecto.
