# CLAUDE.md — CORFO Analytics Platform

This file is loaded by Claude Code in every session. Read it fully before acting.

---

## What this project is

A single-user web analytics tool for exploring Chilean public R&D funding projects from CORFO and other agencies. Users ask natural language questions → the system generates SQL → returns answers, charts, and data tables. Users can add companies to a CRM leads pipeline.

**Data source**: `https://datainnovacion.cl/api` — synced monthly via a scheduled job. This is the canonical source of truth. The local SQLite database is a downstream copy.

**Stage**: Proof-of-concept, being built into a deployable product.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask, Flask-CORS |
| AI / SQL generation | Mellea (IBM) with OpenAIBackend → Gemini OpenAI-compat endpoint |
| SQL model | `gemini-2.0-flash` via `generativelanguage.googleapis.com/v1beta/openai/` |
| Explain model | `gemini-2.0-flash` (same model, separate session, 512 max_tokens) |
| Database | SQLite (`corfo_alimentos.db`) — proyectos + leads tables |
| Frontend | React + Recharts in a single HTML file (`corfo_app.html`) |
| Env vars | python-dotenv, `.env` file |
| Scheduling | APScheduler or cron for monthly data sync |

> **Note:** `README.md` may be outdated. This CLAUDE.md is the source of truth for architecture.

---

## How to run

```bash
pip install flask flask-cors pandas openpyxl mellea python-dotenv apscheduler
conda activate work
python corfo_server.py
# → http://localhost:5000
```

`use_reloader=False` is intentional — prevents double initialization of Mellea sessions.

---

## Project structure

```
corfo_project/
├── CLAUDE.md                    ← you are here (global rules)
├── corfo_server.py              ← Flask app, API routes
├── corfo_app.html               ← Single-file React frontend
├── corfo_alimentos.db           ← SQLite database (do not commit)
├── .env                         ← API keys (do not commit)
├── sync/
│   ├── CLAUDE.md                ← sync-specific agent context
│   ├── datainnovacion_sync.py   ← monthly sync job
│   └── schema_migrations/
├── context/
│   ├── CLAUDE.md                ← context-builder agent instructions
│   ├── schema_context.md        ← human-readable schema with business meanings
│   ├── field_dictionary.json    ← machine-readable field definitions
│   └── query_examples.json      ← known good question→SQL pairs
├── tests/
│   ├── CLAUDE.md                ← test agent instructions
│   ├── test_api.py
│   ├── test_sql_generation.py
│   └── benchmark_questions.json ← eval set for NL→SQL accuracy
└── .claude/
    ├── agents/
    │   ├── coder.md
    │   ├── reviewer.md
    │   ├── context-builder.md
    │   ├── test-runner.md
    │   └── linear-coordinator.md
    └── commands/
        ├── pick-issue.md
        └── review-pr.md
```

---

## Key architecture decisions

- **Mellea IVR pattern**: `_generate_sql()` uses `MelleaSession.instruct()` with two `Requirement` validators and `RejectionSamplingStrategy(loop_budget=3)`. Requirements: valid JSON and SELECT-only SQL. Falls back to `result.sample_generations[0]` on full failure.
- **Two lazy Mellea sessions**: `_get_sql_session()` and `_get_explain_session()`. Initialized on first request, reused globally.
- **`SCHEMA_CONTEXT`** is built once at startup from `PRAGMA table_info` + distinct categorical values. Baked into `SQL_INSTRUCTION_TEMPLATE` at import time. The `context/` folder supplements this with richer business meaning.
- **Mellea template syntax**: user variables use `{{variable}}`. Literal `{` `}` must be wrapped in `{% raw %}...{% endraw %}`.
- **`default_to_constraint_checking_alora=False`** on both `OpenAIBackend` instances — required for Gemini compatibility.
- **`aprobado_corfo` is TEXT** — always cast: `CAST(aprobado_corfo AS REAL)` for numeric ops.
- **`año_adjudicacion` is INTEGER**, range 2009–2025. Double-quote in SQL: `"año_adjudicacion"`.
- The `/` route serves `corfo_app.html` via `send_file` — no static directory.
- **Monthly sync**: `datainnovacion.cl/api` is the upstream source. Pull, normalize, and upsert. Never overwrite manually curated leads data.

---

## Database tables

### proyectos
Key columns: `razon` (company), `aprobado_corfo` (TEXT → cast to REAL), `año_adjudicacion` (INTEGER), `region_ejecucion`, `sector_economico`, `tipo_innovacion`, `tipo_proyecto`, `tendencia_final`, `sostenible`, `economia_circular_si_no`.

See `context/schema_context.md` for full field-by-field business meanings.

### leads
CRM pipeline. Editable: `estado_contacto`, `fecha_contacto`, `metodo_contacto`, `persona_contacto`, `telefono`, `email`, `notas`, `interes_nivel`, `proxima_accion`, `fecha_proxima_accion`. `monto_total_aprobado` is REAL. `ultima_actualizacion` auto-set on PUT.

---

## API endpoints

| Method | Route | Description |
|---|---|---|
| GET | `/` | Serves `corfo_app.html` |
| POST | `/api/query` | NL → SQL → answer + chart + dataframe |
| GET | `/api/dashboard` | Pre-aggregated data for 8 dashboard charts |
| GET | `/api/leads` | Leads (filterable by `sector`, `region`, `estado`) |
| GET | `/api/leads/stats` | Total / contacted / pending counts |
| GET | `/api/leads/<id>` | Single lead detail |
| PUT | `/api/leads/<id>` | Update CRM fields (whitelist enforced) |
| POST | `/api/leads` | Add company to leads from query result |
| POST | `/api/export/excel` | Export dataframe to .xlsx |
| POST | `/api/sync` | Trigger manual data sync from datainnovacion.cl |

---

## Agent routing rules

Add to the top of prompts that involve delegation:

### Parallel dispatch (ALL conditions must be met)
- Tasks are independent with no shared state
- Clear file/module boundaries with no overlap
- 2+ agents can complete their work without needing each other's output

### Sequential dispatch (ANY condition triggers)
- Task B depends on output from task A
- Shared files or database state involved
- Unclear scope — need to understand before proceeding

### Typical multi-agent flow for a Linear issue
1. **linear-coordinator** → pulls issue, writes task prompt
2. **coder** → implements the feature
3. In parallel: **test-runner** + **reviewer** → validate the work
4. **linear-coordinator** → updates issue status, posts comment

---

## Code style

- Python: f-strings, type hints where helpful, `log = logging.getLogger("corfo")`
- Error handling: always return `{'error': '...'}` JSON with appropriate HTTP status
- Flask routes thin — business logic in helper functions
- React: functional components, hooks, no class components, no build step
- SQL safety: generated SQL must be SELECT-only. Never INSERT/UPDATE/DELETE via AI
- **Language**: all user-facing text, answers, UI labels in Spanish
- Comments: Spanish for domain logic, English for technical implementation

---

## Constraints

- **Cost**: Ollama (local) preferred. If cloud needed, prefer Gemini free tier
- **No build step**: frontend stays as single HTML file — no npm, no webpack
- **No ORM**: raw SQLite + pandas for all DB operations
- **Data sync**: monthly pull from `datainnovacion.cl/api`. Never modify sync output manually
