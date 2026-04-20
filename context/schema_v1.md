# schema_v1.md — Esquema Unificado CORFO Analytics Platform

_Creado por el agente coder. DOB-72. Fecha: 2026-04-10_
_Estado: diseño documentado — migración SQL en `sync/schema_migrations/001_schema_v1.sql`_

---

## Resumen ejecutivo del diseño

El esquema v1 introduce dos tablas nuevas (`empresas` y `adjudicaciones`) sin eliminar ni
modificar la tabla `proyectos` existente. Esto preserva compatibilidad total con el código
actual mientras habilita un modelo de datos más limpio para las consultas NL→SQL futuras
y para el CRM de leads.

**Regla de oro**: la tabla `leads` es curada manualmente y nunca es sobrescrita por el sync.

---

## Decisiones de diseño clave

### ¿`empresas` como tabla separada o embebida en `proyectos`?

**Decisión: tabla separada.**

Justificación:
- Un mismo `rut_beneficiario` puede aparecer en múltiples proyectos (promedio ~1.9 proyectos
  por RUT, máximo 71). Sin tabla `empresas`, los campos de empresa se repiten en cada fila de
  `proyectos`, creando inconsistencias cuando el nombre o tramo de ventas varía entre registros.
- La tabla `leads` ya referencia empresas por `rut_beneficiario`. Materializar `empresas`
  evita un JOIN costoso cada vez que el CRM necesita datos básicos de la empresa.
- Para NL→SQL, tener `empresas` como entidad propia simplifica preguntas del tipo
  "¿cuántas empresas del sector alimentos...?" sin agregar antes por RUT.

### ¿`adjudicaciones` como vista o tabla materializada?

**Decisión: tabla materializada, populada durante el sync.**

Justificación:
- Una vista sobre `proyectos` recalcula los agregados en cada consulta. Con 2009+ filas y
  múltiples SUM(CAST(...)) sobre TEXT, el costo es aceptable hoy pero crecerá con el tiempo.
- El sync mensual ya itera sobre todos los proyectos. Mantener `adjudicaciones` actualizada
  en ese mismo paso no añade complejidad significativa.
- Las consultas más frecuentes (top empresas por monto, distribución por año/sector) se
  vuelven triviales con una tabla plana de adjudicaciones agregadas por empresa+año.
- Una tabla materializada puede ser indexada, lo que no es posible en SQLite con vistas.

### Nivel de normalización

Se elige **normalización mínima suficiente**:
- `empresas` extrae solo los atributos estables de la empresa (rut, nombre, sector, región,
  tramo de ventas, fecha de inicio).
- `proyectos` conserva todos sus campos originales sin cambios (retrocompatibilidad).
- `adjudicaciones` agrega por empresa+año, capturando los totales de financiamiento.

No se normalizan las tablas de categorías (sectores, regiones, instrumentos) porque el
beneficio en una BD SQLite de un solo usuario es mínimo frente al costo de complejidad
en las consultas NL→SQL.

---

## Diagrama de relaciones

```
proyectos (existente)
│  codigo  PK
│  rut_beneficiario ──────────────────── empresas
│  razon                                  │  rut_beneficiario  PK
│  año_adjudicacion                       │  razon_social_canonical
│  aprobado_corfo (TEXT)                  │  sector_economico
│  ... (37 columnas totales)              │  region_ejecucion_principal
│                                         │  tramo_ventas
│                                         │  inicio_actividad
│                                         │  total_proyectos
│                                         │  monto_total_aprobado_corfo (REAL)
│                                         │  created_at / updated_at
│
└── empresas.rut_beneficiario ──── adjudicaciones
                                     │  rut_beneficiario  FK → empresas
                                     │  año_adjudicacion
                                     │  proyectos_count
                                     │  monto_corfo (REAL)
                                     │  monto_privado (REAL)
                                     │  monto_ley (REAL)
                                     │  PRIMARY KEY (rut_beneficiario, año_adjudicacion)

leads (existente — solo curación manual)
│  id  PK
│  rut_beneficiario  UNIQUE → empresas.rut_beneficiario
│  ... (campos CRM — nunca sobrescribir)
```

---

## Tabla: `empresas` (nueva)

Entidad canónica de empresa. Una fila por RUT único. Derivada de `proyectos` durante el sync.

### Definición

```sql
CREATE TABLE IF NOT EXISTS empresas (
    rut_beneficiario             TEXT PRIMARY KEY,
    razon_social_canonical       TEXT NOT NULL,
    sector_economico             TEXT,
    region_ejecucion_principal   TEXT,
    tramo_ventas                 TEXT,
    inicio_actividad             TEXT,
    total_proyectos              INTEGER NOT NULL DEFAULT 0,
    monto_total_aprobado_corfo   REAL NOT NULL DEFAULT 0.0,
    primera_adjudicacion         INTEGER,    -- año del primer proyecto
    ultima_adjudicacion          INTEGER,    -- año del proyecto más reciente
    tipo_persona_beneficiario    TEXT,
    created_at                   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at                   TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Semántica de campos

| Campo | Significado | Notas |
|---|---|---|
| `rut_beneficiario` | RUT chileno (SII). Formato `12345678-9`. | PK. Identificador fiscal único. |
| `razon_social_canonical` | Nombre de empresa más reciente/canónico. | Tomado del proyecto más reciente por `año_adjudicacion`. Pueden existir variantes históricas en `proyectos.razon`. |
| `sector_economico` | Sector económico principal. | Tomado del proyecto más reciente. Mismas variantes que `proyectos.sector_economico` — usar LIKE. |
| `region_ejecucion_principal` | Región donde más proyectos ha ejecutado la empresa. | Modo estadístico (valor más frecuente) calculado durante sync. |
| `tramo_ventas` | Tamaño de la empresa según ventas. | Tomado del proyecto más reciente. 5 valores: Sin ventas / Microempresa / Pequeña / Mediana / Grande. |
| `inicio_actividad` | Fecha de inicio de actividades (SII). | Formato TEXT `YYYY-MM-DD`. Puede ser NULL. |
| `total_proyectos` | Cantidad total de proyectos adjudicados. | Calculado como COUNT(*) en proyectos para este RUT. |
| `monto_total_aprobado_corfo` | Suma total de fondos CORFO recibidos (CLP). | REAL — ya agregado. Equivalente a `leads.monto_total_aprobado`. |
| `primera_adjudicacion` | Año del primer proyecto. | INTEGER. Mismo quirk: columna creada con comillas dobles en proyectos. |
| `ultima_adjudicacion` | Año del proyecto más reciente. | INTEGER. |
| `tipo_persona_beneficiario` | Tipo jurídico del beneficiario. | Tomado del proyecto más reciente. Capitalización inconsistente histórica — usar LOWER(). |
| `created_at` | Timestamp de creación del registro. | ISO-8601 UTC. |
| `updated_at` | Timestamp de última actualización por el sync. | ISO-8601 UTC. Actualizado en cada sync si hay cambios. |

### Relaciones

- `empresas.rut_beneficiario` ← referenciado por `proyectos.rut_beneficiario` (sin FK explícita para compatibilidad con SQLite y el sync por lotes)
- `empresas.rut_beneficiario` ← referenciado por `leads.rut_beneficiario`
- `empresas.rut_beneficiario` ← referenciado por `adjudicaciones.rut_beneficiario`

---

## Tabla: `adjudicaciones` (nueva)

Granularidad empresa × año. Una fila por (rut_beneficiario, año_adjudicacion).
Facilita análisis temporales de financiamiento sin necesidad de agregar `proyectos` en tiempo de consulta.

### Definición

```sql
CREATE TABLE IF NOT EXISTS adjudicaciones (
    rut_beneficiario    TEXT NOT NULL,
    "año_adjudicacion"  INTEGER NOT NULL,
    proyectos_count     INTEGER NOT NULL DEFAULT 0,
    monto_corfo         REAL NOT NULL DEFAULT 0.0,
    monto_privado       REAL NOT NULL DEFAULT 0.0,
    monto_ley           REAL NOT NULL DEFAULT 0.0,
    sectores            TEXT,   -- comma-separated unique sectors that year (GROUP_CONCAT(DISTINCT))
    instrumentos        TEXT,   -- comma-separated unique instrumento_homologado that year
    PRIMARY KEY (rut_beneficiario, "año_adjudicacion")
);
```

### Semántica de campos

| Campo | Significado | Notas |
|---|---|---|
| `rut_beneficiario` | RUT de la empresa. | Parte de la PK compuesta. FK implícita a `empresas`. |
| `año_adjudicacion` | Año del grupo de proyectos. | INTEGER. Comillas dobles obligatorias por la ñ. Rango 2009–2025. |
| `proyectos_count` | Cantidad de proyectos adjudicados ese año. | ≥1 siempre. |
| `monto_corfo` | Suma de `aprobado_corfo` (CLP) ese año. | REAL. Calculado con CAST(aprobado_corfo AS REAL) desde proyectos. |
| `monto_privado` | Suma de `aprobado_privado` (CLP) ese año. | REAL. Contraparte privada total. |
| `monto_ley` | Suma de `monto_consolidado_ley` (CLP) ese año. | REAL. Solo relevante cuando tipo_intervencion = 'Ley'. |
| `sectores` | Sectores económicos del año, separados por `,`. | TEXT. `GROUP_CONCAT(DISTINCT sector_economico)`. Permite filtrar por sector sin JOIN a proyectos. |
| `instrumentos` | Instrumentos homologados del año, separados por `,`. | TEXT. `GROUP_CONCAT(DISTINCT instrumento_homologado)`. Permite ver qué instrumentos usó la empresa por año. |

### Relaciones

- `adjudicaciones.rut_beneficiario` → `empresas.rut_beneficiario` (FK implícita)

---

## Tabla: `proyectos` (existente — sin cambios)

La tabla existente se preserva intacta. Ver `context/schema_context.md` para la documentación
completa de sus 37 columnas.

**Notas de compatibilidad**:
- No se renombra, no se modifica, no se agregan columnas en v1.
- El campo `codigo` es la PK de facto (no tiene constraint PRIMARY KEY declarado — legacy).
- `aprobado_corfo` es TEXT y siempre requiere `CAST(aprobado_corfo AS REAL)`.
- `"año_adjudicacion"` requiere comillas dobles en todas las consultas SQL.

---

## Tabla: `leads` (existente — solo curación manual)

Sin cambios. Ver `context/schema_context.md` para documentación completa.

**Regla absoluta**: el sync mensual nunca toca esta tabla. Los campos CRM son curados
manualmente por el usuario y no tienen equivalente en la API de datainnovacion.cl.

---

## Notas de migración

### Qué cambia respecto al esquema actual

| Aspecto | Antes (v0) | Después (v1) |
|---|---|---|
| Entidad empresa | Embebida en cada fila de `proyectos` | Tabla `empresas` con una fila por RUT |
| Agregados por empresa | Calculados on-the-fly con GROUP BY | Pre-calculados en `empresas` y `adjudicaciones` |
| Tabla `proyectos` | Sin cambios | Sin cambios (retrocompatible) |
| Tabla `leads` | Sin cambios | Sin cambios (datos CRM preservados) |
| `proyectos_vec` | Sin cambios | Sin cambios (embeddings) |

### Proceso de migración seguro

1. Ejecutar `sync/schema_migrations/001_schema_v1.sql` — crea las tablas nuevas si no existen.
2. Poblar `empresas` y `adjudicaciones` con un script de backfill (ver sección siguiente).
3. Verificar conteos: `SELECT COUNT(*) FROM empresas` debe dar ~1060 (un RUT por empresa).
4. El código existente en `corfo_server.py` sigue funcionando sin cambios (solo usa `proyectos` y `leads`).
5. En fases posteriores, actualizar `corfo_server.py` para leer de `empresas` cuando corresponda.

**No** se hace DROP de `proyectos` ni se modifica su esquema en v1.

### Script de backfill (ejecución única)

Después de aplicar la migración DDL, poblar las tablas nuevas desde los datos existentes:

```sql
-- Poblar empresas desde proyectos
INSERT OR REPLACE INTO empresas (
    rut_beneficiario,
    razon_social_canonical,
    sector_economico,
    region_ejecucion_principal,
    tramo_ventas,
    inicio_actividad,
    total_proyectos,
    monto_total_aprobado_corfo,
    primera_adjudicacion,
    ultima_adjudicacion,
    tipo_persona_beneficiario,
    updated_at
)
SELECT
    rut_beneficiario,
    -- razon_social_canonical: nombre del proyecto más reciente
    (SELECT razon FROM proyectos p2
     WHERE p2.rut_beneficiario = p.rut_beneficiario
     ORDER BY "año_adjudicacion" DESC LIMIT 1) AS razon_social_canonical,
    -- sector: del proyecto más reciente
    (SELECT sector_economico FROM proyectos p2
     WHERE p2.rut_beneficiario = p.rut_beneficiario
     ORDER BY "año_adjudicacion" DESC LIMIT 1) AS sector_economico,
    -- región: moda (región más frecuente)
    (SELECT region_ejecucion FROM proyectos p2
     WHERE p2.rut_beneficiario = p.rut_beneficiario
     GROUP BY region_ejecucion
     ORDER BY COUNT(*) DESC LIMIT 1) AS region_ejecucion_principal,
    -- tramo_ventas: del proyecto más reciente
    (SELECT tramo_ventas FROM proyectos p2
     WHERE p2.rut_beneficiario = p.rut_beneficiario
     ORDER BY "año_adjudicacion" DESC LIMIT 1) AS tramo_ventas,
    -- inicio_actividad: del proyecto más reciente
    (SELECT inicio_actividad FROM proyectos p2
     WHERE p2.rut_beneficiario = p.rut_beneficiario
     ORDER BY "año_adjudicacion" DESC LIMIT 1) AS inicio_actividad,
    COUNT(*) AS total_proyectos,
    SUM(CAST(aprobado_corfo AS REAL)) AS monto_total_aprobado_corfo,
    MIN("año_adjudicacion") AS primera_adjudicacion,
    MAX("año_adjudicacion") AS ultima_adjudicacion,
    (SELECT tipo_persona_beneficiario FROM proyectos p2
     WHERE p2.rut_beneficiario = p.rut_beneficiario
     ORDER BY "año_adjudicacion" DESC LIMIT 1) AS tipo_persona_beneficiario,
    datetime('now') AS updated_at
FROM proyectos p
WHERE rut_beneficiario IS NOT NULL
  AND rut_beneficiario != ''
GROUP BY rut_beneficiario;

-- Poblar adjudicaciones desde proyectos
INSERT OR REPLACE INTO adjudicaciones (
    rut_beneficiario,
    "año_adjudicacion",
    proyectos_count,
    monto_corfo,
    monto_privado,
    monto_ley,
    sectores,
    instrumentos
)
SELECT
    rut_beneficiario,
    "año_adjudicacion",
    COUNT(*) AS proyectos_count,
    SUM(CAST(aprobado_corfo AS REAL)) AS monto_corfo,
    SUM(CAST(aprobado_privado AS REAL)) AS monto_privado,
    SUM(CAST(monto_consolidado_ley AS REAL)) AS monto_ley,
    GROUP_CONCAT(DISTINCT sector_economico) AS sectores,
    GROUP_CONCAT(DISTINCT instrumento_homologado) AS instrumentos
FROM proyectos
WHERE rut_beneficiario IS NOT NULL
  AND rut_beneficiario != ''
GROUP BY rut_beneficiario, "año_adjudicacion";
```

---

## Estrategia de sync mensual

### Tablas sincronizadas desde la API

| Tabla | Fuente | Estrategia |
|---|---|---|
| `proyectos` | datainnovacion.cl/api | Upsert por `codigo` (sin cambios respecto a v0) |
| `empresas` | Derivada de `proyectos` | Reconstruir tras sync de proyectos: INSERT OR REPLACE por `rut_beneficiario` |
| `adjudicaciones` | Derivada de `proyectos` | Reconstruir tras sync de proyectos: INSERT OR REPLACE por `(rut_beneficiario, año_adjudicacion)` |

### Tablas protegidas (nunca tocar en el sync)

| Tabla | Razón |
|---|---|
| `leads` | Datos CRM curados manualmente. El sync nunca debe insertar, actualizar ni borrar filas en esta tabla. |

### Orden de operaciones en el sync

1. Upsert `proyectos` desde la API (lógica existente en `datainnovacion_sync.py`).
2. Reconstruir `empresas` con INSERT OR REPLACE (SELECT desde `proyectos` agrupado por `rut_beneficiario`).
3. Reconstruir `adjudicaciones` con INSERT OR REPLACE (SELECT desde `proyectos` agrupado por `rut_beneficiario, año_adjudicacion`).
4. Registrar resultado en `_sync_log`.
5. **No tocar** `leads`.

---

## Patrones SQL habilitados por el esquema v1

### Consultas sobre empresas (antes requerían GROUP BY en proyectos)

```sql
-- Top 10 empresas por monto total recibido
SELECT razon_social_canonical, monto_total_aprobado_corfo, total_proyectos
FROM empresas
ORDER BY monto_total_aprobado_corfo DESC
LIMIT 10;

-- Empresas del sector alimentos en la RM
SELECT razon_social_canonical, total_proyectos, monto_total_aprobado_corfo
FROM empresas
WHERE LOWER(sector_economico) LIKE '%alimentos%'
  AND LOWER(region_ejecucion_principal) LIKE '%metropolitana%'
ORDER BY monto_total_aprobado_corfo DESC;
```

### Análisis temporal por empresa (antes imposible sin doble agregación)

```sql
-- Evolución anual del financiamiento para una empresa
SELECT "año_adjudicacion", monto_corfo, proyectos_count
FROM adjudicaciones
WHERE rut_beneficiario = '76031602-4'
ORDER BY "año_adjudicacion";

-- Empresas que recibieron fondos en más de 5 años distintos
SELECT e.razon_social_canonical, COUNT(*) AS años_con_fondos
FROM adjudicaciones a
JOIN empresas e ON e.rut_beneficiario = a.rut_beneficiario
GROUP BY a.rut_beneficiario
HAVING años_con_fondos > 5
ORDER BY años_con_fondos DESC;
```

### Integración con CRM leads

```sql
-- Leads con datos de empresa enriquecidos
SELECT l.razon_social, l.estado_contacto, e.monto_total_aprobado_corfo,
       e.total_proyectos, e.primera_adjudicacion, e.ultima_adjudicacion
FROM leads l
JOIN empresas e ON e.rut_beneficiario = l.rut_beneficiario
ORDER BY e.monto_total_aprobado_corfo DESC;
```

---

## Índices recomendados

```sql
-- Para JOINs leads → empresas
CREATE INDEX IF NOT EXISTS idx_empresas_rut ON empresas (rut_beneficiario);

-- Para filtros por sector y región (consultas NL→SQL más frecuentes)
CREATE INDEX IF NOT EXISTS idx_empresas_sector ON empresas (sector_economico);
CREATE INDEX IF NOT EXISTS idx_empresas_region ON empresas (region_ejecucion_principal);

-- Para series temporales en adjudicaciones
CREATE INDEX IF NOT EXISTS idx_adj_rut ON adjudicaciones (rut_beneficiario);
CREATE INDEX IF NOT EXISTS idx_adj_anio ON adjudicaciones ("año_adjudicacion");
```

---

## Limitaciones conocidas del esquema v1

1. **`razon_social_canonical`** puede ser vacío o una variante tipográfica si el proyecto más
   reciente tiene un nombre corrupto. La lógica de backfill toma el proyecto con mayor
   `año_adjudicacion`; si hay empate, SQLite elige arbitrariamente.

2. **`region_ejecucion_principal`** usa la moda (región más frecuente). Una empresa que opera
   en dos regiones con igual cantidad de proyectos obtendrá una región arbitraria.

3. **`aprobado_corfo` sigue siendo TEXT en `proyectos`**. Las tablas nuevas almacenan los
   agregados ya como REAL, pero cualquier consulta directa a `proyectos` sigue requiriendo
   el CAST. Este quirk se preserva intencionalmente para no modificar el esquema legacy.

4. **Sin FKs declaradas**: SQLite soporta FK con `PRAGMA foreign_keys = ON`, pero el código
   actual no las habilita. Las relaciones son por convención de nombres, no por constraint.
   Esto es intencional para simplificar el sync por lotes.

5. **`proyectos_vec`**: la tabla de embeddings existente no se documenta aquí. Continúa
   operando independientemente del esquema v1.
