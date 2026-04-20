# sync/CLAUDE.md

This folder owns the monthly data sync from `https://datainnovacion.cl/api`.

## Sync rules (never violate)
- Sync runs at most once per month. Do not add more frequent schedules without explicit approval.
- Sync ONLY updates the `proyectos` table. It must NEVER touch the `leads` table.
- Use upsert logic (INSERT OR REPLACE by primary key). Do not truncate and reload.
- If the API is unreachable, log the error and abort — do not leave the DB in a partial state.
- After every sync, update the `_sync_log` table with timestamp, rows fetched, rows upserted, and status.

## API notes
- Base URL: `https://datainnovacion.cl/api`
- Explore endpoints before assuming structure — the API may have changed
- Paginate if the API supports it — do not assume a single response contains all records
- Map API fields to DB columns using `context/field_dictionary.json`

## Coder instructions for this module
- Read `context/field_dictionary.json` before writing any field mapping code
- After a sync that adds or renames columns, invoke @context-builder to update context files
- Use `requests` for HTTP. No additional HTTP libraries.
- Log with `log = logging.getLogger("corfo.sync")`
