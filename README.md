# Business Model Evaluator (plugin de Claude Code)

Evalúa propuestas de negocio de servicios tecnológicos con el método **CEST** (Compuertas → Evidencia → Supuestos → Tests): clasifica la economía real de cada línea (S1–S4, P-SAAS-SS/SL, P-USAGE, P-AI-APP, P-INFRA; modificadores V y AIX), aplica compuertas no compensatorias G0–G7 + G2b, puntúa módulos M2–M15 con techo por evidencia y emite **GO / CONDITIONAL_GO / NO_GO / INSUFFICIENT_EVIDENCE** con cada cifra trazada en un Evidence Ledger.

Antes de evaluar, entrevista a los socios por rondas. Si el negocio todavía no vende, responde si vale la pena **abrirlo** y qué tan probable es conseguir los clientes que necesita.

## Instalación (para los socios)

Requisitos: [Claude Code](https://claude.com/claude-code) con sesión iniciada y Python 3.10 o superior (los scripts solo usan la biblioteca estándar).

Dentro de Claude Code, escribe:

```
/plugin marketplace add juandavidrc74/business-model-evaluator
/plugin install business-model-evaluator@bme
```

O desde una terminal:

```bash
claude plugin marketplace add juandavidrc74/business-model-evaluator
claude plugin install business-model-evaluator@bme
```

Reinicia Claude Code después de instalar.

**Actualizar** a la última versión: `/plugin marketplace update bme`, y reinicia Claude Code.

## Cómo usarlo

1. Guarda la propuesta en una carpeta propia (por ejemplo `propuesta.md`) y abre Claude Code en esa carpeta.
2. Pide: *"Evalúa la propuesta de negocio de propuesta.md en modo interactivo: hazme todas las preguntas necesarias antes de evaluar."*
3. Responde las rondas de preguntas. Cada una trae una respuesta recomendada; puedes aceptarla o corregirla.
4. Al terminar, la carpeta tiene `informe.md` (el informe para leer), `evaluation.json`, `intake.json` y `gate_input.json`.

La primera línea del informe responde en lenguaje llano si vale la pena. Una evaluación completa consume bastante cuota del plan.

## Estructura

```
business-model-evaluator/
├── .claude-plugin/
│   ├── plugin.json                        versión 0.7.3 (ver CHANGELOG.md)
│   └── marketplace.json                   permite instalarlo con /plugin marketplace add
├── agents/                                7 subagentes: abogado del diablo, verificador de evidencia,
│                                          investigador de dominio y analistas de finanzas, mercado, riesgo y tecnología
└── skills/evaluating-business-models/
    ├── SKILL.md                           reglas, flujo CEST, subagentes, tabla de referencias, comandos
    ├── references/                        22 archivos de método
    ├── scripts/                           17 scripts, solo biblioteca estándar (Python >= 3.10)
    └── assets/                            benchmarks (250), precios, Colombia, tasas base, DD, esquemas, plantillas, ejemplo
```

## Instalación solo de la Skill (sin subagentes)

Copiar `skills/evaluating-business-models/` a `~/.claude/skills/` (todos los proyectos) o a `.claude/skills/` del proyecto. Sin el plugin no hay subagentes (abogado del diablo, verificador), así que se recomienda la instalación de arriba.

## Desarrollo

Las 192 pruebas deterministas, los 22 casos de `claude plugin eval` y los generadores se mantienen fuera de este repositorio público, junto con las evaluaciones de propuestas reales.

## Decisiones confirmadas (2026-11-10)

G1 sin evidencia por encima del nivel 2 → `unknown`; N = 3 ejecuciones (5 con alto impacto), desempate NO_GO > INSUFFICIENT_EVIDENCE > CONDITIONAL_GO > GO; regla (c) de CONDITIONAL_GO acotada a drivers del 80 % del swing; G3 falla con un cliente ≥ 50 % sin contrato plurianual protegido ni plan de diversificación **verificable** y avisa desde el 25 %. Constantes en `scripts/gates_and_score.py` y `scripts/aggregate_runs.py`.

## Límites conocidos

- Los umbrales marcados [P] no están calibrados: la calibración requiere el registro prospectivo (`log_evaluation.py`) y años de resultados.
- Probada de punta a punta con el modelo en pruebas de campo; los casos automáticos con el modelo (D.01, D.05 y D.08) siguen pendientes.
- `scan_injection.py` es una ayuda heurística de triaje, no una barrera: la defensa es tratar todo contenido recuperado como dato.
- `check_claims.py` comprueba que cada cifra exista en la evidencia, no que la afirmación sea semánticamente correcta; eso lo revisa `evidence-verifier`.
- Cotejo externo de una muestra de benchmarks y de sus licencias pendiente (REV-013).
- El hook `Stop` opcional (RT-PKG-10, COULD) no se implementó.
- Los precios de modelos (`price_cards.json`) vencen el 2026-12-01/09; las subidas de Gemini deben reverificarse antes del 2026-12-01.
- Solo fuentes gratuitas por defecto; nada de pago es obligatorio.
