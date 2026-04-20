# datainnovacion.cl API — Reference Documentation

**Explored:** 2026-04-07
**Source:** `https://datainnovacion.cl/api` (documentation page) + live API probing
**Total projects in dataset:** ~10,344 (confirmed by fetching full dataset)

---

## Overview

DataInnovación exposes a read-only REST API covering Chile's InnovaChile public R&D funding portfolio, managed by CORFO. The dataset contains over 10,344 subsidized projects spanning award years 2009–2025. The API is backed by a PHP/Laravel application (PHP 8.4.10) and served through Cloudflare.

This is the canonical upstream data source for the CORFO Analytics Platform. The local SQLite database (`corfo_alimentos.db`) is a downstream copy synced monthly from this API.

---

## Authentication

**Required:** Yes — all endpoints return `{"error":"Necesitas un Token"}` without a valid token.

**Method:** Raw JWT token in the `Authorization` header (no `Bearer` prefix — the `Bearer` prefix causes `{"error":"Token Inválido"}`).

**Public token (as published on the docs page):**
```
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczpcL1wvZGF0YUlubm92YXRpb24uY2wiLCJuYW1lIjoicHVibGljIGFwaUtleSJ9.Ofu3LI0z8uCNYTbZyXd9BeY0sWIDt2NzUBwnHxTtdsA
```

This is a static public JWT signed with HS256. The payload decodes to:
```json
{"iss": "https://dataInnovation.cl", "name": "public apiKey"}
```

**Headers required on every request:**
```
Accept: application/json
Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Note:** Do NOT use `Authorization: Bearer <token>` — the API expects the raw token string without the `Bearer ` prefix.

---

## Base URLs

| URL | Behavior |
|-----|----------|
| `https://datainnovacion.cl/api/v1/` | Primary API base (use this) |
| `https://www.datainnovacion.cl/api/v1/` | Redirects 301 → `https://datainnovacion.cl/api/v1/` |

---

## Endpoints

Only one data endpoint was found to exist. All other paths (`/api/docs`, `/api/schema`, `/api/v2/proyectos`, `/api/v1/sectores`, `/api/v1/instrumentos`, `/api/v1/regiones`, `/api/v1/proyectos/count`, `/api/v1/stats`, `/api/v1/metadata`, `/api/v1/proyectos/{codigo}`) return HTTP 404.

### Summary Table

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/proyectos` | Fetch all CORFO/InnovaChile funded projects |
| GET | `/api` | HTML documentation page (not a data endpoint) |

---

## GET /api/v1/proyectos

The primary (and only) data endpoint. Returns a flat JSON array of project objects.

### Request

```
GET https://datainnovacion.cl/api/v1/proyectos
Accept: application/json
Authorization: <token>
```

### Query Parameters

| Parameter | Type | Example | Description | Observed behavior |
|-----------|------|---------|-------------|-------------------|
| `limit` | integer | `100` | Maximum number of records to return | Works. No limit = returns all ~10,344 records. `limit=10000` returns exactly 10,000. |
| `filter[codigo]` | string | `19CV-12345` | Filter by exact project code | Works. Returns matching records. |
| `filter[rut_beneficiario]` | string | `77295440-9` | Filter by beneficiary RUT | Works. Returns all projects for that company. |
| `filter[tipo_intervencion]` | string | `Ley` or `Subsidio` | Filter by intervention type | Works. Values observed: `Subsidio` (8,927 records), `Ley` (~1,417 records). |
| `filter[estado_data]` | string | `VIGENTE` or `FINALIZADO` | Filter by project status | Works. Use uppercase: `VIGENTE` (1,374 records), `FINALIZADO` (8,970 records). |
| `filter[sostenible]` | string | `Sí` or `No` | Filter by sustainability flag | Works. Values: `Sí`, `No`. |
| `filter[año_adjudicacion]` | string | `2020` or `2020,2021` | Filter by award year(s). Comma-separated for multiple. | Works. Single year or comma-separated list. Range 2009–2025. |
| `page` | integer | `1` | Page number | Has NO effect — returns same records regardless of value. Not a real pagination mechanism. |
| `offset` | integer | `2` | Record offset | Has NO effect — confirmed to return identical results. |

**Important:** The `filter[...]` bracket syntax must be URL-encoded when using curl or similar tools: `filter%5Bcodigo%5D=...`. In Python `requests`, passing params as a dict with key `"filter[codigo]"` works correctly.

**Multiple filters can be combined** — they are ANDed together:
```
?filter[año_adjudicacion]=2022&filter[estado_data]=VIGENTE  →  152 records
```

### Pagination

**There is no true pagination.** The API returns a flat JSON array (not a paginated object). Key findings:

- Default (no `limit`): returns ALL records (~10,344) in a single response (~18.5 MB)
- `limit=N`: returns the first N records
- `page` and `offset` parameters are accepted but have no effect
- No `Link` headers, no `X-Total-Count`, no `next_page_url` in response — the response is a bare JSON array

**Sync strategy recommendation:** Fetch the entire dataset in one request (no `limit`) or use a large `limit` (e.g., `limit=15000`) to future-proof against dataset growth. Use filters like `filter[año_adjudicacion]` for incremental syncs by year.

### CORS

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET
Access-Control-Allow-Headers: Authorization, Accept
Access-Control-Max-Age: 0
```

CORS is fully open. Browser-side requests from any origin are permitted.

### Rate Limits

```
x-ratelimit-limit: 60
x-ratelimit-remaining: 59
```

- **Limit:** 60 requests per window (window duration not specified in headers — no `X-RateLimit-Reset` or `Retry-After` header observed)
- **Assumption:** 60 requests per minute (standard Laravel default)
- **No rate limit headers that reveal reset time**
- A full sync requiring only 1 request (fetching all data at once) will never hit this limit

### Response Structure

The response is a **JSON array** of project objects. No wrapper object, no pagination metadata.

```json
[
  { ... project object ... },
  { ... project object ... }
]
```

### Response Fields (complete field list)

All fields observed from live data, with types and example values:

| Field | JSON Type | Example Value | Notes |
|-------|-----------|---------------|-------|
| `codigo` | string | `"09AAP-6740"` | Unique project code. Format: `YY[instrument]-[number]` |
| `foco_apoyo` | string | `"Renuévate"` | CORFO support focus program name |
| `tipo_intervencion` | string | `"Subsidio"` | `"Subsidio"` or `"Ley"` |
| `instrumento` | string | `"Apoyo A La Atracción De Profesionales Y Técnicos"` | Full instrument name |
| `instrumento_homologado` | string | `"Capital Humano"` | Normalized/standardized instrument category |
| `estado_data` | string | `"FINALIZADO"` | `"FINALIZADO"` or `"VIGENTE"` |
| `tipo_persona_beneficiario` | string | `"Persona Jurídica constituida en Chile"` | Legal entity type |
| `rut_beneficiario` | string | `"77295440-9"` | Chilean RUT (tax ID) of beneficiary company |
| `razon` | string | `"INGENIERIA Y DESARROLLO FORESTAL S.A."` | Company name (razon social) — maps to local DB `razon` column |
| `titulo_del_proyecto` | string | `"biomasa forestal del manejo..."` | Project title (lowercase) |
| `objetivo_general_del_proyecto` | string | `"diseñar un modelo..."` | General objective / abstract |
| `año_adjudicacion` | integer | `2009` | Year the project was awarded. Range: 2009–2025 |
| `aprobado_corfo` | number | `30470785` | CORFO-approved funding in CLP (integer in API, but stored as TEXT in local DB — cast required) |
| `aprobado_privado` | number | `14675894` | Private co-funding amount in CLP |
| `aprobado_privado_pecuniario` | string | `"0"` | Private pecuniary contribution (returned as string) |
| `monto_consolidado_ley` | string | `"0"` | Consolidated Ley amount (returned as string) |
| `tipo_innovacion` | string | `"Producto"` | Innovation type: `"Producto"`, `"Proceso"`, etc. |
| `mercado_objetivo_final` | string | `"Multisectorial"` | Target market |
| `criterio_mujer` | string | `"No"` | Women-led criterion: `"Sí"` or `"No"` |
| `genero_director` | string | `"Sin determinar"` | Director's gender |
| `sostenible` | string | `"Sí"` | Sustainability flag: `"Sí"` or `"No"` |
| `ods_principal_sostenible` | string \| null | `"ODS7"` | Primary UN SDG (e.g. `"ODS7"`, `"ODS12"`). null if not applicable |
| `meta_principal_cod` | string \| null | `"7.b"` | SDG target code. null if not applicable |
| `economia_circular_si_no` | string \| null | `"Sí"` | Circular economy flag: `"Sí"`, `"No"`, or null |
| `modelo_de_circularidad` | string \| null | `"Suministro Circular"` | Circularity model type. null if not applicable |
| `region_ejecucion` | string | `"Región del Biobío"` | Chilean region where project is executed |
| `tramo_ventas` | string | `"Mediana"` | Company size by sales: `"Sin ventas"`, `"Microempresa"`, `"Pequeña"`, `"Mediana"`, `"Grande"` |
| `inicio_actividad` | string | `"1999-06-06"` | Company founding date (ISO 8601) |
| `sector_economico` | string | `"Forestal"` | Economic sector |
| `patron_principal_asociado` | string \| null | `"Intercambiar"` | Associated circular economy pattern. null if not applicable |
| `tipo_proyecto` | string \| null | `"Economía Circular"` | Project type classification. null if not applicable |
| `r_principal` | string \| null | `null` | Principal R strategy. Often null |
| `estrategia_r_principal` | string \| null | `"Uso y fabricación de productos más inteligentes"` | R strategy description. null if not applicable |
| `ley_rep_si_no` | string | `"No"` | Ley REP flag: `"Sí"` or `"No"` |
| `ley_rep` | string \| null | `null` | Ley REP detail. null if `ley_rep_si_no = "No"` |
| `ernc` | string \| null | `"Biocombustible"` | ERNC (renewable energy) type. null if not applicable |
| `tendencia_final` | string | `"Sin tendencia"` | Final trend classification |

**Total fields per record:** 35

### Example Response (1 record, pretty-printed)

```json
[
  {
    "codigo": "09AAP-6740",
    "foco_apoyo": "Renuévate",
    "tipo_intervencion": "Subsidio",
    "instrumento": "Apoyo A La Atracción De Profesionales Y Técnicos",
    "instrumento_homologado": "Capital Humano",
    "estado_data": "FINALIZADO",
    "tipo_persona_beneficiario": "Persona Jurídica constituida en Chile",
    "rut_beneficiario": "77295440-9",
    "razon": "INGENIERIA Y DESARROLLO FORESTAL S.A.",
    "titulo_del_proyecto": "biomasa forestal del manejo sustentable del bosque nativo para la industria termoeléctrica del carbón.",
    "objetivo_general_del_proyecto": "diseñar un modelo de producción de biomasa forestal...",
    "año_adjudicacion": 2009,
    "aprobado_corfo": 30470785,
    "aprobado_privado": 14675894,
    "aprobado_privado_pecuniario": "0",
    "monto_consolidado_ley": "0",
    "tipo_innovacion": "Producto",
    "mercado_objetivo_final": "Multisectorial",
    "criterio_mujer": "No",
    "genero_director": "Sin determinar",
    "sostenible": "Sí",
    "ods_principal_sostenible": "ODS7",
    "meta_principal_cod": "7.b",
    "economia_circular_si_no": "Sí",
    "modelo_de_circularidad": "Suministro Circular",
    "region_ejecucion": "Región del Biobío",
    "tramo_ventas": "Mediana",
    "inicio_actividad": "1999-06-06",
    "sector_economico": "Forestal",
    "patron_principal_asociado": "Intercambiar",
    "tipo_proyecto": "Economía Circular",
    "r_principal": null,
    "estrategia_r_principal": "Uso y fabricación de productos más inteligentes",
    "ley_rep_si_no": "No",
    "ley_rep": null,
    "ernc": "Biocombustible",
    "tendencia_final": "Sin tendencia"
  }
]
```

---

## Code Examples

### Python (as provided by datainnovacion.cl docs)

```python
import os
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

URL = 'https://datainnovacion.cl/api/v1/proyectos'
TOKEN = os.getenv('DATAINNOVACION_TOKEN')  # store in .env, not hardcoded
HEADERS = {'Accept': 'application/json', 'Authorization': TOKEN}

r = requests.get(url=URL, headers=HEADERS)
data = r.json()
df = pd.json_normalize(data)
```

**Note:** Store the token in `.env` as `DATAINNOVACION_TOKEN=<token>`. The public token value is listed in the Authentication section above — do not hardcode it in script files. If the token rotates, update `.env` and check `https://datainnovacion.cl/api` for the new value.

### Python — Filtered fetch (sync script pattern)

```python
import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

URL = 'https://datainnovacion.cl/api/v1/proyectos'
TOKEN = os.getenv('DATAINNOVACION_TOKEN')
HEADERS = {'Accept': 'application/json', 'Authorization': TOKEN}

# Fetch all records (no limit needed — API returns ~10,344 in one call)
response = requests.get(URL, headers=HEADERS, timeout=120)
response.raise_for_status()
data = response.json()
df = pd.json_normalize(data)

# Type normalization required before SQLite upsert:
# aprobado_corfo arrives as int64 from json_normalize, but local DB stores it as TEXT
df['aprobado_corfo'] = df['aprobado_corfo'].astype(str)
df['aprobado_privado'] = df['aprobado_privado'].astype(str)

# Or fetch by year for incremental sync:
params = {'filter[año_adjudicacion]': '2024,2025'}
response = requests.get(URL, headers=HEADERS, params=params, timeout=60)
```

### R (as provided by datainnovacion.cl docs)

```r
library(httr)
library(jsonlite)
library(dplyr)

URL <- "https://datainnovacion.cl/api/v1/proyectos"
TOKEN <- "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
HEADERS <- add_headers("Accept" = "application/json", "Authorization" = TOKEN)

response <- GET(url = URL, config = HEADERS)
data <- fromJSON(content(response, "text"), flatten = TRUE)
```

---

## Infrastructure & Server Details

| Property | Value |
|----------|-------|
| Server | Cloudflare (CDN/proxy) |
| Backend | PHP 8.4.10 (Laravel) |
| Protocol | HTTPS only (HTTP redirects to HTTPS) |
| Content-Type | `application/json` |
| Cache-Control | `no-cache, private` |
| CORS | `Access-Control-Allow-Origin: *` |
| Allowed Methods (CORS) | `GET` only |
| Rate Limit | 60 requests per window |
| Rate Limit Headers | `X-RateLimit-Limit`, `X-RateLimit-Remaining` |
| Rate Limit Reset | Not disclosed in headers |

**Note on SSL:** The server certificate may cause issues with strict certificate revocation checking on Windows (CRYPT_E_NO_REVOCATION_CHECK). Use `requests` with default settings in Python (it uses its own cert bundle and is unaffected). If using curl on Windows, add `-k` flag.

---

## Known Limitations & Gotchas

1. **No true pagination.** `page` and `offset` parameters are accepted but silently ignored. The only way to get a subset of data is with `limit` (returns first N records) or filters.

2. **No record-by-record lookup.** There is no endpoint like `/api/v1/proyectos/{codigo}`. To look up a specific project, use `filter[codigo]=09AAP-6740`.

3. **No total count endpoint.** There is no `/api/v1/proyectos/count` or total count in response headers. The dataset size must be inferred by fetching all records.

4. **`aprobado_corfo` is an integer in the API response** but may arrive as a number type. In the local SQLite DB it is stored as TEXT — always cast with `CAST(aprobado_corfo AS REAL)` in SQL queries.

5. **`aprobado_privado_pecuniario` and `monto_consolidado_ley` are strings** (e.g., `"0"`) even though they represent numeric values. Cast as needed.

6. **`año_adjudicacion` is an integer** in the API (e.g., `2009`). In SQL, double-quote it: `"año_adjudicacion"`.

7. **`estado_data` filter: always use uppercase.** Use `VIGENTE` and `FINALIZADO`. Title-case (`Vigente`) may work in practice but uppercase is the only confirmed-safe form.

8. **No `Bearer` prefix on Authorization header.** Unlike standard OAuth2, this API rejects `Bearer <token>` and requires the raw token string.

9. **Full dataset response is ~18.5 MB.** Budget for this in sync script memory and set an appropriate HTTP timeout (recommend 120+ seconds).

10. **Rate limit window is unknown.** With only 1 request needed for a full sync, this is not a practical concern.

---

## Sync Script Recommendations

For the monthly sync job (`sync/datainnovacion_sync.py`):

> **Critical constraint:** The sync job must only write to the `proyectos` table. **Never touch the `leads` table.** Leads contain manually curated CRM data that will be permanently lost if overwritten.

- **Single full fetch:** `GET /api/v1/proyectos` with no limit. Returns all ~10,344 records in one call. ~18.5 MB response.
- **Incremental option:** Use `filter[año_adjudicacion]` with the current and previous year to capture newly-awarded and recently updated projects.
- **Upsert strategy:** Use `codigo` as the unique key for upserts into the local `proyectos` table.
- **Timeout:** Set `requests.get(..., timeout=120)` — the full dataset fetch can take several seconds.
- **Verify token:** If the API returns `{"error":"Token Inválido"}`, the token has likely rotated. Check `https://datainnovacion.cl/api` for an updated public token.
