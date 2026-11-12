# Evaluar un negocio que todavía no vende (etapa `pre_launch`)

Desde la versión 0.7.0 la pregunta principal de la Skill es si vale la pena **abrir** el negocio. Esta referencia explica qué preguntar antes de evaluar, cómo se registran las respuestas y qué significa cada veredicto en esta etapa. Las reglas por compuerta están en `references/gates.md`, sección 6b.1b.

## Contenido

- Cuándo usar `pre_launch` u `operating`
- Preguntas previas
- Probabilidad de conseguir clientes (G1)
- Cómo entran las respuestas al ledger
- Qué significa cada veredicto
- Qué no cambia

## Cuándo usar `pre_launch` u `operating`

`gate_input.json` lleva `"stage"`. Usa `pre_launch` (el valor por defecto) si el negocio todavía no tiene ventas recurrentes, aunque haya un proyecto suelto, pilotos o clientes interesados. Usa `operating` si ya factura con regularidad y hay historia de clientes, ingresos por cliente o churn. En caso de duda, `pre_launch`.

## Preguntas previas

Antes de construir el ledger, entrevista a los fundadores por rondas según `references/intake.md`, hasta que `check_intake.py` devuelva `can_evaluate: true`. Si no tienen la cifra exacta, pide un mínimo y un máximo. Antes de abrir, los datos que más pesan son:

1. Precio de cada servicio o plan, y qué incluye.
2. Horas estimadas por proyecto o por cliente al mes, o las reales de un proyecto ya hecho.
3. Horas por semana de cada socio y su nivel de experiencia, que fija el salario de mercado de sus horas.
4. Costes fijos mensuales: herramientas, alojamiento, contador, oficina.
5. A quién han contactado, qué respondió y si hay algo firmado o pagado, con el documento si existe.
6. Qué obligaciones legales conocen y si hay un plan escrito con responsable y fecha.
7. Horizonte para que el negocio se pague solo e intención de buscar capital riesgo.

Si no puedes preguntar, sigue el modo no interactivo de `references/intake.md`: lo que solo saben los socios entra como rango de referencia y lo básico que falte (qué se vende, a quién, a qué precio) lleva a INSUFFICIENT_EVIDENCE con la pregunta.

## Probabilidad de conseguir clientes (G1)

Antes de abrir, "todavía no hay clientes" es el punto de partida, no un hallazgo. Desde la versión 0.7.3, G1 responde si es **probable** conseguir los clientes que el negocio necesita (decisión del usuario, 2026-11-12). Rellena `demand.reachability` en `gate_input.json` con cinco datos, cada uno con su id del ledger:

| Campo | Qué es | De dónde sale |
|---|---|---|
| `clients_needed_per_year` | Clientes o proyectos al año para cubrir costes con el salario de mercado de los socios. Alternativa: `fixed_costs_per_year` y `contribution_per_client`, y el script lo calcula | `breakeven_runway.py`, con las cifras de la entrevista |
| `reachable_accounts` | Cuentas del segmento a las que el canal puede llegar | Recuento en un registro oficial (M2; en Colombia, registro mercantil o RUES), nunca "X % de un mercado" |
| `market_pays` | `true` si otros ya cobran por esto: competidores con precio publicado y clientes, o datos públicos de gasto del segmento | M5 y fuentes de `references/data-sources.md` |
| `contacts_per_month` | Contactos comerciales al mes que puede hacer el equipo, en rango | Entrevista (`sales_capacity`) |
| `conversion` | Fracción de contactos que acaban comprando, en rango (`low`, `high`) | Fuente publicada del canal (puerta fría, referidos, eventos); sin fuente, supuesto con rango amplio, nunca un valor puntual |

El script calcula los clientes esperados al año (contactos × 12 × conversión, en los extremos pesimista y optimista), la penetración (clientes necesarios / cuentas alcanzables) y la conversión mínima que hace falta:

| Probabilidad | Estado | Cuándo |
|---|---|---|
| Alta | `pass` | Incluso con el embudo pesimista se alcanzan los clientes necesarios, la penetración es ≤ 10 % [P] y el mercado ya paga por esto |
| Media | `conditional` | Solo se alcanzan con la conversión optimista: condición "viable si la conversión es ≥ X", que se mide en los primeros contactos. O los números alcanzan, pero falta prueba de que el mercado paga |
| Baja | `fail` | Ni con el embudo optimista se llega, o harían falta más del 10 % de las cuentas alcanzables cada año |
| Sin estimar | `conditional` | Falta alguno de los cinco datos. Es un fallo de la evaluación: búscalos antes de entregar |

Un compromiso firmado o un pago adelantado documentado (nivel ≥ 4) sigue haciendo pasar G1 directamente, y la evidencia negativa sigue fallando. Conseguir ese primer compromiso deja de ser obligatorio para GO, pero sigue siendo el primer paso recomendado en los próximos pasos. `plain_answer` termina siempre con la probabilidad y sus cifras. En el modo consorcio, el compilador descarta los números de la entrada base, así que `reachability` aún no llega a G1 y la compuerta queda sin estimar.

## Cómo entran las respuestas al ledger

- Cada respuesta es una entrada `user_statement` con `self_declared: true`.
- Un rango es un `assumption` con mínimo y máximo, y su P0 va a `p0_unknowns` con `low` y `high`. El script busca el punto de equilibrio dentro del rango y lo convierte en una condición del tipo "viable si las horas por proyecto son ≤ 117".
- En proyectos a precio fijo, declara `price_per_project` y `hours_per_project` en `economics`; la tarifa efectiva es precio / horas.
- El coste de las horas de los socios se calcula siempre a salario de mercado (R4), con una fuente local de la ocupación (en Colombia, GEIH o Fedesoft). Un portal de empleo solo sirve como contexto.
- Una cuenta que el proponente declara en nivel ≥ 4 sin documento (contrato, factura o extracto de nivel 1) se lee como nivel 3.
- Una obligación legal solo tiene plan si está escrito con responsable y fecha: `plan: {"owner": ..., "by_date": ...}`.

## Qué significa cada veredicto

`gates_and_score.py evaluate` devuelve `plain_answer`, una frase llana que el informe copia tal cual como primera línea.

| Veredicto | Respuesta | Cuándo |
|---|---|---|
| GO | Vale la pena abrirlo | Los números salen incluso en el extremo pesimista de cada rango y es probable conseguir los clientes necesarios (G1 con probabilidad alta o un compromiso documentado) |
| CONDITIONAL_GO | Vale la pena probarlo en pequeño | Nada falla, pero quedan condiciones con umbral o fecha: conversión mínima por confirmar, punto de equilibrio dentro del rango, plan de diversificación, obligaciones por cumplir |
| NO_GO | Así no vale la pena | Algo falla incluso en el escenario favorable: el precio no cubre el coste ni en el mejor extremo, los clientes necesarios no se alcanzan ni con el embudo optimista, evidencia negativa de demanda o un KO de due diligence |
| INSUFFICIENT_EVIDENCE | Todavía no se puede responder | Faltan datos básicos que ni los fundadores pueden dar |

Lo que solo se mide después de abrir (clientes que ya pagan, concentración real, churn, disponibilidad medida, guardia 24×7) se convierte en condición, nunca en bloqueo. La regla (b) de CONDITIONAL_GO (más del 50 % del swing por supuestos) no se aplica: antes de abrir casi todo es supuesto, y el extremo pesimista de cada rango cumple esa función.

## Qué no cambia

- La evidencia negativa de demanda y los KO de due diligence siguen dando NO_GO.
- Un margen negativo en el extremo favorable del rango sigue dando NO_GO.
- Ninguna cifra entra sin fuente o sin etiqueta de supuesto.
- Las condiciones son hipótesis falsables: cada una dice qué medir, el umbral y el plazo.
