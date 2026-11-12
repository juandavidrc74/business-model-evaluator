# Entrevista previa por rondas (Paso 0)

Desde la versión 0.7.1, antes de construir el ledger la Skill entrevista a los fundadores hasta que cada dato que necesita la evaluación tiene un tratamiento decidido: una cifra con fuente, un rango o un "no lo sabemos" dicho por ellos. Motivo: en la prueba de campo de la versión 0.7.0 el veredicto dependió de supuestos que nadie preguntó (nivel de experiencia de los socios, horizonte, capital riesgo). El método está adaptado, no copiado, de la skill `grilling` de Matt Pocock (repositorio `mattpocock/skills`, licencia MIT).

## Contenido

- Principios
- Cómo es una ronda
- Árbol de preguntas
- Registro en `intake.json`
- Comprobación con `check_intake.py`
- Cierre
- Modo no interactivo

## Principios

1. **Primero busca, después pregunta.** Lo que dice la propuesta o una fuente de las referencias no se pregunta: se registra con su cita. Si es ambiguo o contradictorio, se confirma.
2. **Solo la frontera.** En cada ronda pregunta todo lo que ya se puede responder, es decir, cada dato cuyos requisitos ya están respondidos. Lo que depende de otra respuesta espera a la ronda siguiente.
3. **Una decisión por pregunta, con respuesta recomendada.** Cada pregunta lleva tu recomendación y de dónde sale. Así los socios pueden contestar "sí" y avanzar rápido.
4. **Una recomendación no es evidencia.** Si los socios aceptan una recomendación que sale de una referencia, el dato entra al ledger como `assumption` con su fuente y su rango. Si sale de ellos, entra como `user_statement` con `self_declared: true`. Aceptarla nunca la convierte en `fact`.
5. **"No lo sabemos" es una respuesta.** Pide entonces un mínimo y un máximo. Si tampoco hay rango, el dato queda `unknown`.
6. **No pares hasta vaciar la frontera,** y cierra con un resumen que los socios confirman antes de calcular.

## Cómo es una ronda

- Numera las preguntas de la ronda (P1, P2…). Con la herramienta de preguntas (AskUserQuestion), cada llamada admite como máximo 4 preguntas: reparte la ronda en varias llamadas seguidas, y pon tu recomendación como primera opción, marcada "(Recomendado)".
- **Sin herramienta de preguntas, pregunta en el chat:** escribe la ronda como lista numerada con la recomendación de cada pregunta y **termina tu turno**. No sigas hasta que el usuario responda. No tener la herramienta nunca es motivo para pasar al modo no interactivo.
- Para cada pregunta, di en una línea por qué importa: qué compuerta o qué cifra mueve.
- No inventes la recomendación. Si no hay dato en la propuesta ni en las referencias, recomienda un rango de una referencia con su fuente, o di que no tienes recomendación.
- Tras cada ronda, actualiza `intake.json` y ejecuta `check_intake.py`: su campo `next_round` es la frontera de la ronda siguiente.

## Árbol de preguntas

El catálogo exacto está en `scripts/check_intake.py`. Los campos marcados como "solo socios" no se pueden suponer en modo interactivo sin que los socios confirmen el valor.

| Ronda típica | Campo | Requisito | Solo socios | Para qué |
|---|---|---|---|---|
| 1 | `offer`, `customer_segment` | — | no (básico) | M1, G0 |
| 1 | `countries`, `currency` | — | no | G0, geo-adaptation |
| 1 | `stage`, `horizon_months`, `seeks_vc` | — | sí | G0, etapa, caja |
| 1 | `partners` | — | sí | capacidad |
| 2 | `price` (básico), `price_includes` | `offer` | no | G2, M7 |
| 2 | `partner_hours_per_week`, `partner_seniority` | `partners` | sí | capacidad; coste de mercado de sus horas (R4) |
| 2 | `fixed_costs_monthly` | `offer` | sí | caja, punto de equilibrio |
| 2 | `hours_per_project` (S1–S4) | arquetipo | sí | G2, G6 |
| 2 | `churn_expected` (P-*) | arquetipo | no | G2b |
| 2 | `acquisition` | arquetipo | sí | G2b, M12, G1 |
| 2 | `sales_capacity` | `partners` | sí | G1: contactos al mes del embudo |
| 2 | `ai_cost_per_task` (AIX, P-AI-APP) | arquetipo | no | T1–T9 |
| 3 | `demand_evidence` | `customer_segment` | sí | G1 |
| 3 | `legal_obligations` | `offer`, `countries` | sí | G4 |
| 3 | `critical_suppliers` | `offer` | no | G3 |
| 3 | `service_commitments` | `offer` | sí | G7 |

Las preguntas que dependen del arquetipo se abren cuando clasificas las líneas (Paso 1) y anotas `archetypes` en `intake.json`. Sobre `partner_seniority`: el coste de las horas de los socios es siempre el salario de mercado de su perfil (R4), no lo que se pagan. Si son estudiantes o junior, ese perfil baja el coste; si no se sabe, va como rango del perfil más bajo al más alto, y G6 calcula el umbral.

## Registro en `intake.json`

Escríbelo en el directorio de trabajo, junto a `gate_input.json`. `mode` es obligatorio: `interactive` siempre que haya una persona que pueda responder.

```json
{"mode": "interactive", "stage": "pre_launch", "archetypes": ["S2"], "modifiers": [],
 "summary_confirmed": false,
 "fields": {
  "offer": {"answered_by": "proposal", "value": "Automatizacion de procesos para pymes", "quote": "Automatizamos procesos administrativos de pymes"},
  "horizon_months": {"answered_by": "user", "value": 24, "round": 1},
  "partner_seniority": {"answered_by": "reference", "low": "junior", "high": "senior", "ledger_id": "L14", "confirmed": true},
  "legal_obligations": {"answered_by": "unknown", "accepted_unknown": true}}}
```

- `answered_by`: `proposal` (lleva `quote`), `user` (lleva `round`), `reference` (lleva `ledger_id`; si es un dato que solo saben los socios, `confirmed: true` cuando ellos lo aceptan) o `unknown` (con `accepted_unknown: true` cuando los socios dicen que no lo saben).
- Cada dato con valor lleva `value` o un rango `low` y `high`. Un rango pasa después a `p0_unknowns` de `gate_input.json`.
- Copia `mode`, `mode_reason` y `unconfirmed_assumptions` de `check_intake.py` en `gate_input.json` → `intake`; `evaluate` los devuelve en `intake` y `validate_output.py` exige que lleguen a `evaluation.json` en `pre_launch`. El informe los muestra justo debajo de la respuesta directa, para que se vea si hubo entrevista.

## Comprobación con `check_intake.py`

`python "${CLAUDE_SKILL_DIR}/scripts/check_intake.py" intake.json` devuelve:

- `value`: `complete` (se puede evaluar), `insufficient` (se puede evaluar, pero falta un dato básico y el veredicto será INSUFFICIENT_EVIDENCE con `questions_for_report`) o `incomplete` (no se evalúa todavía).
- `next_round`: las preguntas de la frontera, con dónde buscar antes de preguntar.
- `problems`: datos registrados que no cuentan (sin cita, supuestos sin confirmar, `unknown` que nadie dijo).
- `blocked`: preguntas que esperan otra respuesta o la clasificación.

No ejecutes `gates_and_score.py evaluate` mientras `can_evaluate` sea `false`.

## Cierre

Cuando la frontera esté vacía, muestra una tabla corta: cada dato, el valor o rango que vas a usar y de dónde sale. Pregunta si es correcto. Corrige lo que señalen y marca `summary_confirmed: true` solo cuando lo confirmen. Esta confirmación no convierte nada en evidencia: solo comprueba que entendéis lo mismo.

## Modo no interactivo

Úsalo **solo** en dos casos, y decláralo en `mode_reason`:

- `user_asked_no_questions`: el usuario pidió expresamente que no preguntes ("trabaja con lo que hay").
- `no_human`: no hay nadie que pueda responder, como en una evaluación automática.

No tener herramienta de preguntas no es uno de ellos. `check_intake.py` trata un `non_interactive` sin motivo válido como interactivo y pide las preguntas. En este modo:


- Lo que dice la propuesta entra con su cita.
- Lo que solo saben los socios entra como rango de una referencia (`answered_by: reference`, con `low` y `high` distintos y su `ledger_id`) o como `unknown`. Nunca como un valor puntual supuesto.
- Lo demás entra con su fuente o queda `unknown`.
- Si falta un dato básico (qué se vende, a quién o a qué precio), `check_intake.py` devuelve `insufficient` y el informe lista sus preguntas.
- El informe dice qué datos de los socios se supusieron con rango (`unconfirmed_assumptions`).
