# Gungnir — Public Funding Analytics · UX Mockup Handoff

**Target repo:** `corfo_project` (referred to internally as "Proyecto Gungnir")
**For:** Claude Code
**Status:** Hi-fi redesign · ready for implementation
**Date:** April 2026

---

## 1 · What this package is

A hi-fi, clickable UX mockup for the CORFO Analytics Platform that **redesigns the current disconnected-modules experience into an integrated analyst workflow**. The existing app (`corfo_app.html`) works but feels like three separate tools stapled together (Consultas, Dashboard, Leads). This package proposes a single connected flow anchored in the **Empresa 360** view, with a threaded query interface and a proper CRM pipeline.

**Primary user:** An analyst at a consultancy looking for Chilean companies financed by CORFO, to contact as potential clients.

**UX priority #1:** _"Easy to keep track of different consults and leads, easy to get the information out of the app."_

**Files in this folder**

| File | Purpose |
|---|---|
| `Gungnir.html` | Entry point — the interactive prototype |
| `tokens.css` | Design tokens: color, type, spacing, radii, shadows |
| `shell.jsx` | Sidebar, topbar, icons, Card/Chip/Status primitives, formatters |
| `data.jsx` | Seed data derived from `context/schema_context.md` |
| `charts.jsx` | Lightweight SVG charts (Bar, LineChart, Donut, KPI) — no external dep |
| `screens.jsx` | All main screens (Consultas, Dashboard, Leads, Empresa 360, CmdPalette) |
| `README.md` | This document |

**To preview**

Open `Gungnir.html` in a browser. `⌘K`/`Ctrl+K` opens the command palette. Click table rows to drill into empresas; click Kanban cards to open the lead drawer.

---

## 2 · The core problem, and the fix

### Current pain
The existing app has three tabs (Consultas / Dashboard / Leads). Each is fine in isolation, but:
- A consulta produces a table of empresas — but you can't click one to see its full profile
- Leads is a flat spreadsheet with no sense of pipeline stage or upcoming action
- There's no way to thread follow-up questions on a previous consulta — each query starts fresh
- The dashboard has no relationship to either consultas or leads

### Fix — three architectural moves

1. **Empresa 360** becomes the hub. Every empresa mentioned anywhere (consulta result row, lead card, dashboard drill-down) is a link to the same integrated profile: projects, activity log, CRM object, related consultas.
2. **Consultas become threaded conversations.** A consulta is a named, persistent, multi-turn dialogue. Follow-ups stay inside the thread. Results cross-reference the leads pipeline automatically ("5 of 23 results are already in your pipeline").
3. **Leads become a pipeline, not a spreadsheet.** Kanban board by `estado_contacto` with a drawer for editing. A table view remains for bulk work, and a map view (placeholder) for geographic triage.

A **command palette** (`⌘K`) provides instant access across all entity types — the connective tissue.

---

## 3 · Visual system

**Aesthetic brief:** Analytical / finance-BI. Not dark-and-techy; editorial-serious with tabular density.

| Token | Value | Use |
|---|---|---|
| Background | `#F7F6F2` paper | Primary surface |
| Accent | `#2A3C8F` indigo | Primary action, charts, active nav |
| Highlight | `#6B4FBB` violet | Editorial marker, cross-filter, assistant turn, "Gungnir ·" tag |
| Body text | `#2D333E` ink-700 | — |
| Sans | Inter | UI, tables, body |
| Serif | Source Serif 4 | Headings, KPI numbers, assistant responses |
| Mono | JetBrains Mono | Metadata, numbers, RUT, codes |
| Radii | 2–8px | Subtle; avoids "app-y" softness |
| Spacing | 4pt grid | Dense by default (13px body) |

Full palette, semantic colors, and motion tokens live in `tokens.css` under `:root`. All component styles reference these variables — **never hardcode** colors or spacing in the rebuild.

---

## 4 · Screen-by-screen spec

Each section below maps to a screen in the prototype. For each: **purpose · key interactions · data contract · implementation notes**.

### 4.1 Consultas (default screen)

**Purpose.** Ask questions in natural language and keep a threaded, resumable history.

**Layout.** Two-column: sidebar list of past consultas (280px) · active conversation thread.

**Key interactions**
- New consulta button creates a thread with an auto-generated title from the first question.
- Each assistant turn shows: prose answer, collapsible SQL block, result table, **follow-up suggestions**.
- Result table rows link to Empresa 360; toolbar has Filter / Export CSV / **"Agregar a leads"** bulk action.
- Composer supports follow-ups (`⌘↵` to submit); maintains session context.
- Pin button in header saves thread to sidebar "Pinned".

**Data contract**
- `GET /api/consultas` — list (paginated, sortable by recency/pinned)
- `GET /api/consultas/<id>` — full thread with turns
- `POST /api/consultas/<id>/turn` — append a turn (wraps current `/api/query`)
- `POST /api/consultas` — create new thread
- `PUT /api/consultas/<id>/pin` — toggle pin

**Implementation notes**
- The current `/api/query` stays as-is; threading is layered on top. Store threads in a new `consultas` table (id, titulo, user_id, created_at, pinned, updated_at) with a `turnos` child table (id, consulta_id, rol, pregunta, respuesta, sql, resultados_json, created_at).
- Follow-up suggestions: ask Gemini for 3 short continuations after each turn (cheap — include in the explain model's 512-token budget). Cache with the turn.
- "Agregar a leads" calls existing `POST /api/leads` for each selected RUT.

### 4.2 Dashboard

**Purpose.** Orient the analyst: what's in the database right now, where's the money flowing.

**Layout.** KPI strip (4 cards) → cross-filter banner → 4-up chart grid.

**Key interactions**
- Clicking a bar in "Top sectores" or "Instrumentos CORFO" cross-filters the whole dashboard. Banner at top shows active filter; × clears it.
- "Guardar vista" persists the current filter combo to the sidebar **Saved > Reports**.
- "Exportar PDF" renders a print stylesheet (see `@media print` in `tokens.css`).

**Charts**
- `LineChart` — Monto por año (from `"año_adjudicacion"`, SUM of CAST aprobado_corfo)
- `Donut` — Region share (top 6 + "Otras")
- `Bar` — Top sectores (uses LIKE-matched canonical sector names, see schema quirks #5)
- `Bar` — Instrumentos (by `instrumento_homologado`, monto)
- `Bar` — Tendencias (exclude `'Sin tendencia'`)
- `Metric` grid — 6 composition metrics

**Data contract.** Reuse existing `GET /api/dashboard` and `GET /api/dashboard/drill`. Add a `?cross_filter=sector:"Alimentos"` query param that all charts respect.

**Implementation notes**
- Current app uses Recharts. Our mockup uses hand-rolled SVG to stay in the editorial aesthetic, but either works — just match the token colors (`--data-1…8`).
- KPI numbers come from a single `GET /api/dashboard/kpis` (new endpoint, cached 5min).

### 4.3 Leads (pipeline)

**Purpose.** Manage the CRM pipeline of companies to contact.

**Layout.** Stat strip (5 columns: count per estado + monto total) → view switcher (pipeline / tabla / mapa) → detail drawer on selection.

**Key interactions**
- **Pipeline view (Kanban).** 5 columns matching `estado_contacto` values: Nuevo / Contactado / En seguimiento / Propuesta enviada / Cerrado. Cards show razón, región, tramo, monto, próxima acción+fecha. Click → drawer.
- **Tabla view.** Dense table with search, estado filter, región filter. Row click → drawer; razón click → Empresa 360.
- **Mapa view.** Placeholder for a choropleth of Chile. Data is there (`region_ejecucion`) — just needs a GeoJSON of Chilean regions.
- **Drawer.** Editable: estado, interés, próxima_accion, fecha_proxima_accion, notas. "Ver perfil completo" → Empresa 360.

**Data contract.** Existing `/api/leads`, `/api/leads/<id>`, `/api/leads/stats`, `PUT /api/leads/<id>`. No new endpoints needed. Drag-and-drop between Kanban columns issues a `PUT` with new `estado_contacto`.

**Implementation notes**
- Stat strip values come from `/api/leads/stats` — extend that endpoint to return counts per estado and monto pipeline total.
- Preserve the existing whitelist of editable fields on PUT.

### 4.4 Empresa 360 (the hub)

**Purpose.** Single unified view per company. This is where analysis converts to outreach.

**Layout.** Hero header (razón, chips, KPIs, actions) → 4 tabs: **Resumen** / **Proyectos** / **Actividad** / **CRM**.

**Tabs**
- **Resumen.** LineChart of funding over time, analyst notes (editable), contact block, tendencias list, related consultas list.
- **Proyectos.** Full table of all `proyectos` rows for this `rut_beneficiario` (not razón — razón has typo variants). Exportable.
- **Actividad.** Timeline of CRM interactions: calls, emails, meetings, "added to leads" event. New activity button inserts a row.
- **CRM.** Preview of the canonical CRM object (per `build_crm_object(razon)` in `corfo_server.py`). Three actions: Export to HubSpot · Download JSON · Copy.

**Data contract**
- `GET /api/empresa/<razon>` — existing; extend to include `actividad` list and `contacto` block
- `GET /api/crm/empresa/<razon>` — existing; populates the CRM tab verbatim
- `POST /api/empresa/<razon>/actividad` — new; append to activity log
- `PUT /api/empresa/<razon>/notas` — new; save analyst notes

**Implementation notes**
- Activity log is a new table: `actividad` (id, rut_beneficiario, fecha, tipo, con_quien, nota, user_id, created_at).
- Analyst notes live on the `leads` row (reuse `notas` field — already in schema).
- Chips use semantic variants: `pos` for "Sostenible", `violet` (or legacy `ochre`) for "Economía circular", `indigo` (or legacy `navy`) for sector.

### 4.5 Command palette (`⌘K`)

**Purpose.** Fast nav across screens + instant empresa lookup. The connective tissue that makes the app feel unified.

**Sections (in order)**
1. Actions — Nueva consulta, Ir a Dashboard, Ir a Leads
2. Empresas — live search against `proyectos.razon` (fuzzy; use SQLite FTS5 or a loaded-in-memory trigram index)
3. Consultas recientes

**Implementation notes**
- Client-only fuzzy matching is fine up to ~2K entries (we have 1,060 empresas). Load the index once on auth.
- `Esc` closes. `↑/↓` navigates, `↵` activates.

### 4.6 Screens not mocked (handoff placeholders)

These exist in the sidebar and are stubbed out in the prototype as "Pantalla pendiente de mockup". Short spec only.

- **Pinned queries** — filtered variant of Consultas, only pinned threads.
- **Reports** — saved dashboard views. A "vista" = dashboard filter combo + name. Renders as a dashboard with the saved filters applied.
- **Data · Sync & sources** — admin-only; button to trigger `POST /api/sync`, shows last sync time, row count deltas, schema version. Reads from `sync/datainnovacion_sync.py`.
- **Settings** — user preferences (density, default screen), API keys for Gemini (admin), session management.
- **Login** — not mocked. Keep current `.env`-based login; just restyle with the new tokens.

---

## 5 · Component inventory

Reusable pieces that Claude Code should extract into one module:

| Component | Source | Props |
|---|---|---|
| `Sidebar` | `shell.jsx` | `active`, `onNav(id)`, `counts` |
| `Topbar` | `shell.jsx` | `crumbs[]`, `onCmdK`, `right` |
| `SectionHeader` | `shell.jsx` | `title`, `meta`, `right` |
| `Card` | `shell.jsx` | `title`, `subtitle`, `right`, `flush` |
| `Chip` | `shell.jsx` | `variant` = neutral \| indigo \| violet \| navy \| ochre \| pos \| neg \| warn |
| `Status` | `shell.jsx` | `value` — matches `estado_contacto` values |
| `Icon` | `shell.jsx` | 20+ inline SVG icons, 14px default |
| `Bar` / `LineChart` / `Donut` / `KPI` / `Metric` | `charts.jsx` | See file |
| `CmdPalette` | `screens.jsx` | `open`, `onClose`, `onNav`, `onOpenEmpresa` |
| `LeadDrawer` | `screens.jsx` | `lead`, `onClose`, `onOpenEmpresa` |

Formatters: `fmtCLP` (abbreviated), `fmtCLPFull` (full), `fmtN` (Spanish locale number).

---

## 6 · Design tokens (machine-readable summary)

```json
{
  "color": {
    "paper": "#F7F6F2",
    "card": "#FFFFFF",
    "ink": { "900": "#12151A", "700": "#2D333E", "500": "#5A6170", "400": "#838A98", "300": "#B2B6BF", "200": "#DCDFE4", "100": "#EAECEF" },
    "accent": "#1B3A5B",
    "highlight": "#B6862C",
    "data": ["#1B3A5B", "#B6862C", "#5F7A5A", "#8A4A3C", "#6B5B95", "#3E6670", "#A68A64", "#4A5560"],
    "semantic": { "pos": "#2F6B4F", "neg": "#9B3D2E", "warn": "#8A6A1E" }
  },
  "font": {
    "sans":  "Inter, -apple-system, sans-serif",
    "serif": "Source Serif 4, Georgia, serif",
    "mono":  "JetBrains Mono, ui-monospace, monospace"
  },
  "fontSize": { "11": 11, "12": 12, "13": 13, "14": 14, "16": 16, "18": 18, "22": 22, "28": 28, "36": 36 },
  "spacing":  { "1": 4, "2": 8, "3": 12, "4": 16, "5": 20, "6": 24, "8": 32, "10": 40, "12": 48 },
  "radius":   { "1": 2, "2": 4, "3": 6, "4": 8 }
}
```

Source of truth lives in `tokens.css`. Keep this JSON in sync if you extract it.

---

## 7 · Implementation checklist for Claude Code

Work in this order — each phase is independently shippable.

**Phase 1 — Visual refresh (no new backend).**
- [ ] Replace inline `<style>` in `corfo_app.html` with `tokens.css`-derived variables.
- [ ] Swap fonts: Inter / Source Serif 4 / JetBrains Mono (already on Google Fonts).
- [ ] Port `Card`, `Chip`, `Status`, `Icon`, table styles, form styles from `shell.jsx`.
- [ ] Restyle current Consultas / Dashboard / Leads without changing behavior.

**Phase 2 — Empresa 360 (new route).**
- [ ] Add `/empresa/<razon>` client route.
- [ ] Build Hero + tab scaffold.
- [ ] Resumen + Proyectos tabs wire to existing `/api/empresa/<razon>`.
- [ ] CRM tab wires to existing `/api/crm/empresa/<razon>`.
- [ ] New migration: `actividad` table; new endpoints `GET/POST /api/empresa/<razon>/actividad`.
- [ ] Notes wired via `PUT /api/leads/<id>` (notas field).

**Phase 3 — Consultas threading.**
- [ ] Migration: `consultas` + `consulta_turnos` tables.
- [ ] New endpoints: `/api/consultas` CRUD + `/api/consultas/<id>/turn`.
- [ ] Refactor `/api/query` to accept `consulta_id` and append a turn if provided.
- [ ] UI: sidebar list + active thread.
- [ ] Follow-up suggestions (separate Mellea session, 200-token budget).

**Phase 4 — Leads pipeline.**
- [ ] Kanban view with DnD between estado columns.
- [ ] Drawer editor (reuse whitelist on PUT).
- [ ] Stat strip ties to extended `/api/leads/stats`.

**Phase 5 — Polish.**
- [ ] Command palette with FTS5-backed empresa search.
- [ ] Cross-filter on dashboard.
- [ ] Saved views / Reports.
- [ ] Print stylesheet for dashboard PDF export.

---

## 8 · Edge cases & schema gotchas (from `context/schema_context.md`)

Claude Code — when querying, always honor these. They're already in your global `CLAUDE.md` but worth restating in the UX context:

- `"año_adjudicacion"` — always double-quoted (ñ).
- `CAST(aprobado_corfo AS REAL)` — always. The field is TEXT.
- `sostenible = 'Sí'` / `economia_circular_si_no = 'Sí'` — with tilde.
- `economia_circular_si_no` NULL ≠ 'No' — filter carefully.
- `sector_economico` — use `LOWER(...) LIKE '%...%'` to catch typo variants.
- `estado_data` is UPPERCASE (`'VIGENTE'`, `'FINALIZADO'`).
- `criterio_mujer` — `LOWER()` it before matching.
- Empresas with same `razon` can be different companies → **always join/group by `rut_beneficiario`**, not razón.

---

## 9 · What I intentionally did NOT design

Per project constraints:
- **No authentication screens** — current `.env`-based auth stays. Just restyle the login page using tokens.
- **No admin-only UI beyond Sync placeholder** — role-based screens (user management, etc.) are out of scope; the `.env` model only supports 2 users.
- **No mobile layout** — this is an analyst's desktop tool. Breakpoints below 1024px fall back to the current responsive behavior; no specific mobile design.
- **Brand logo.** Gungnir mark lives inline in `shell.jsx` as the `GungnirLogo` component — a spearhead + crossguard + shaft inside a circle. Swap for a hi-res SVG if design produces one; keep the `.brand .logo` slot at 28px.

---

## 10 · Open questions for the owner

Before Phase 2 starts, confirm:

1. **Threading retroactive?** Do we migrate existing `query_log.jsonl` entries into `consultas` rows, or start fresh? _Recommend: start fresh; the log is append-only and pre-dates threading semantics._
2. **Activity log retention.** Keep forever, or archive >12mo? _Recommend: keep forever — it's small and analysts reference old interactions._
3. **HubSpot integration timing.** The CRM tab shows an "Exportar a HubSpot" button. Per `CLAUDE.md`, this is DOB-119 (not yet built). Button should be visible-but-disabled with a tooltip until that epic ships.
4. **"Interés" field.** Schema has `interes_nivel` (bajo/medio/alto). The mockup surfaces it as a dropdown in the drawer and a chip in the table. Confirm this stays first-class vs. hidden behind "advanced".

---

_End of handoff. Questions on any section → ping the design owner before breaking ground._
