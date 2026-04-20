# Modelo de Entidades — CORFO Analytics Platform
_Documento de diseño. BD actual: tabla `proyectos` desnormalizada (37 columnas). Este documento define las entidades lógicas y mapea cada atributo a la columna existente._

---

## Por qué importa

Este modelo guía la normalización futura de la base de datos y le entrega al agente de SQL un mapa conceptual claro de qué columnas pertenecen a cada dominio, evitando confusiones al generar consultas que mezclan atributos del proyecto con atributos de la empresa o del financiamiento.

---

## Entidad: Proyecto

### Identidad
- **Clave primaria**: `codigo` (TEXT, único, sin NULLs — ej: `"PI-64569"`)

### Atributos (→ columna DB)
| Atributo | Columna | Tipo | Notas |
|---|---|---|---|
| Título del proyecto | `titulo_del_proyecto` | TEXT | — |
| Objetivo general | `objetivo_general_del_proyecto` | TEXT | — |
| Estado | `estado_data` | TEXT | Solo 2 valores: `'VIGENTE'` / `'FINALIZADO'` |
| Tipo de innovación | `tipo_innovacion` | TEXT | Valores: Proceso, Producto, Servicio. 1 NULL. |
| Tipo especial de proyecto | `tipo_proyecto` | TEXT | Solo proyectos especiales (EC, sostenible, social). Muchos NULLs. |
| Mercado objetivo | `mercado_objetivo_final` | TEXT | 28 valores, sin NULLs |
| Tendencia tecnológica | `tendencia_final` | TEXT | 20 valores; incluye `'Sin tendencia'`. Sin NULLs. |
| ¿Sostenible? | `sostenible` | TEXT | `'Sí'` / `'No'`. Sin NULLs. |
| ODS principal | `ods_principal_sostenible` | TEXT | Solo aplica si `sostenible = 'Sí'`. 1 NULL. |
| Meta ODS | `meta_principal_cod` | TEXT | Código de meta ONU asociada al ODS principal. |
| ¿Economía circular? | `economia_circular_si_no` | TEXT | `'Sí'` / `'No'`. 1 NULL. |
| Modelo de circularidad | `modelo_de_circularidad` | TEXT | Solo aplica si `economia_circular_si_no = 'Sí'`. 5 valores. |
| ERNC | `ernc` | TEXT | Tipo de energía renovable. Solo proyectos energéticos. 7 valores. |
| Patrón principal | `patron_principal_asociado` | TEXT | Clasificación interna de patrón de innovación. |
| Inicio de actividades | `inicio_actividad` | TEXT | Fecha SII de la empresa (`'YYYY-MM-DD'`). Pertenece conceptualmente a Empresa, pero está en esta tabla. |

### Relaciones
- Cada Proyecto tiene exactamente una **Adjudicación** (`codigo` → clave foránea implícita).
- Cada Proyecto fue ejecutado por exactamente una **Empresa** (`rut_beneficiario`).
- Cada Proyecto fue financiado por exactamente un **Organismo Financiador** (implícito: CORFO).
- Cada Proyecto fue ejecutado en exactamente una **Región** (`region_ejecucion`).

---

## Entidad: Empresa (Beneficiario)

### Identidad
- **Clave de negocio**: `rut_beneficiario` (TEXT, formato `'12345678-9'`)

### Atributos (→ columna DB)
| Atributo | Columna | Tipo | Notas |
|---|---|---|---|
| RUT | `rut_beneficiario` | TEXT | Identificador fiscal chileno único. Usar para deduplicar. |
| Razón social | `razon` | TEXT | Nombre legal de la empresa o persona. |
| Tipo de persona | `tipo_persona_beneficiario` | TEXT | 4 valores: persona jurídica comercial, org. sin fines de lucro, persona natural, etc. 1 NULL. |
| Tramo de ventas | `tramo_ventas` | TEXT | Tamaño: Sin ventas < Microempresa < Pequeña < Mediana < Grande. Sin NULLs. |
| Criterio mujer | `criterio_mujer` | TEXT | Si el proyecto aplicó criterio de género. Inconsistencia de capitalización: usar `LOWER()`. |
| Género del director | `genero_director` | TEXT | Masculino / Femenino / Sin determinar. 1 NULL. |
| Sector económico | `sector_economico` | TEXT | 34 valores con variantes tipográficas. Usar `LOWER(sector_economico) LIKE '%keyword%'`. 1 NULL. |

### Nota de deduplicación
`razon` puede tener variantes tipográficas distintas para el mismo `rut_beneficiario` (ej: tildes, mayúsculas, abreviaciones). Para contar empresas únicas siempre usar `COUNT(DISTINCT rut_beneficiario)`, no `COUNT(DISTINCT razon)`.

---

## Entidad: Organismo Financiador

### Identidad
El organismo financiador no tiene columna de nombre en la tabla actual — todos los registros corresponden a **CORFO**. La identidad se expresa a través del instrumento utilizado.

### Atributos (→ columna DB)
| Atributo | Columna | Tipo | Notas |
|---|---|---|---|
| Foco de apoyo | `foco_apoyo` | TEXT | Línea estratégica CORFO. 5 valores exactos, sin NULLs. |
| Tipo de intervención | `tipo_intervencion` | TEXT | `'Subsidio'` o `'Ley'` (beneficio tributario Ley I+D). Solo 2 valores. |
| Instrumento (raw) | `instrumento` | TEXT | Nombre original del instrumento tal como viene de la fuente. |
| Instrumento normalizado | `instrumento_homologado` | TEXT | Versión limpia y canónica. **Preferir sobre `instrumento`**. 49 valores, sin NULLs. |
| Estrategia R (EC) | `r_principal` | TEXT | Jerarquía R0–R9 de economía circular. Solo aplica con `economia_circular_si_no = 'Sí'`. 1 NULL. |
| Estrategia R descripción | `estrategia_r_principal` | TEXT | Descripción textual de la estrategia R. |
| ¿Acoge Ley I+D? | `ley_rep_si_no` | TEXT | Indica si el proyecto se acoge al régimen de la Ley de I+D. |
| Código Ley I+D | `ley_rep` | TEXT | Código o referencia de la Ley I+D aplicada. |

---

## Entidad: Adjudicación (Award)

### Identidad
La Adjudicación no tiene clave propia en el modelo actual — está implícitamente vinculada a cada fila de `proyectos` a través de `codigo`. En una normalización futura tendría `codigo` como clave foránea.

### Atributos (→ columna DB)
| Atributo | Columna | Tipo | Notas |
|---|---|---|---|
| Año de adjudicación | `año_adjudicacion` | INTEGER | Rango 2009–2025. Sin NULLs. **Siempre entre comillas dobles en SQL**: `"año_adjudicacion"`. |
| Monto aprobado CORFO | `aprobado_corfo` | TEXT | Pesos chilenos (CLP). **Siempre**: `CAST(aprobado_corfo AS REAL)` para operaciones numéricas. |
| Contraparte privada total | `aprobado_privado` | TEXT | Aporte privado total (pecuniario + en especie). Requiere `CAST`. |
| Contraparte privada en efectivo | `aprobado_privado_pecuniario` | TEXT | Solo la parte en dinero del aporte privado. Requiere `CAST`. |
| Monto bajo Ley I+D | `monto_consolidado_ley` | TEXT | Monto acogido al beneficio tributario. Mayormente cero. Requiere `CAST`. Solo relevante cuando `tipo_intervencion = 'Ley'`. |

### Quirks de tipos (campos TEXT que necesitan CAST)
Todos los campos de monto en `proyectos` están almacenados como TEXT. Regla sin excepciones:

```sql
-- Correcto
SUM(CAST(aprobado_corfo AS REAL))
AVG(CAST(aprobado_privado AS REAL))

-- Incorrecto — produce orden lexicográfico o error silencioso
ORDER BY aprobado_corfo DESC
SUM(aprobado_corfo)
```

---

## Entidad: Región

### Identidad
- **Clave de negocio**: `region_ejecucion` (nombre completo de la región, ej: `'Región Metropolitana de Santiago'`)

### Atributos (→ columna DB)
| Atributo | Columna | Tipo | Notas |
|---|---|---|---|
| Nombre de la región | `region_ejecucion` | TEXT | 16 valores (todas las regiones de Chile). Sin NULLs. Nombres completos con tildes. |

### Nota de consultas
El nombre completo es requerido para coincidencia exacta. Para búsquedas flexibles usar `LIKE`:

```sql
WHERE region_ejecucion LIKE '%metropolitana%'
WHERE region_ejecucion LIKE '%araucan%'
```

---

## Resumen de relaciones entre entidades

```
Empresa (rut_beneficiario)
    │
    │  1 : N
    ▼
Proyecto (codigo) ──── 1 : 1 ────► Adjudicación (año, montos)
    │                                    │
    │  N : 1                             │ N : 1
    ▼                                    ▼
Región (region_ejecucion)     Organismo Financiador (instrumento)
```

| Relación | Cardinalidad | Columna de unión |
|---|---|---|
| Empresa → Proyecto | 1 a N (una empresa puede tener varios proyectos) | `rut_beneficiario` |
| Proyecto → Adjudicación | 1 a 1 (cada proyecto tiene un evento de adjudicación) | `codigo` (implícita, misma fila) |
| Proyecto → Región | N a 1 (varios proyectos por región) | `region_ejecucion` |
| Proyecto → Organismo Financiador | N a 1 (actualmente siempre CORFO) | `instrumento_homologado` |

---

## Desnormalización actual

Las 5 entidades coexisten en la tabla `proyectos` como columnas planas. No hay JOINs necesarios para consultas dentro del dominio de proyectos. Las implicancias prácticas son:

| Situación | Solución en el modelo actual |
|---|---|
| Contar empresas únicas | `COUNT(DISTINCT rut_beneficiario)` — nunca `COUNT(DISTINCT razon)` |
| Agrupar por empresa | `GROUP BY rut_beneficiario` + `MIN(razon)` para el nombre |
| Agrupar por organismo/instrumento | `GROUP BY instrumento_homologado` |
| Agrupar por región | `GROUP BY region_ejecucion` |
| Filtrar por año | `WHERE "año_adjudicacion" = 2023` (comillas dobles obligatorias) |
| Sumar montos | `SUM(CAST(aprobado_corfo AS REAL))` (CAST obligatorio) |

La tabla `leads` es una entidad separada del pipeline CRM. Se relaciona con `proyectos` a través de `rut_beneficiario` (en leads: implícito vía `proyectos_ids`) y no forma parte de este modelo de entidades de proyectos.
