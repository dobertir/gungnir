# schema_context.md — CORFO Analytics Platform
_Mantenido por el agente context-builder. Última actualización: 2026-04-08_
_Fuente de datos verificada: `corfo_alimentos.db` — 2009 proyectos, 1060 leads_

---

## Tabla: proyectos

Contiene todos los proyectos de I+D e innovación financiados por CORFO y otras agencias públicas chilenas.
Datos obtenidos mensualmente desde `datainnovacion.cl/api`. Rango temporal: 2009–2025.

### Resumen de campos

| Campo | Nombre para el usuario | Tipo real | Notas técnicas clave |
|---|---|---|---|
| `codigo` | Código del proyecto | TEXT | PK de facto. Formatos variables por época. 0 NULLs. |
| `foco_apoyo` | Foco de apoyo CORFO | TEXT | 5 valores exactos. 0 NULLs. |
| `tipo_intervencion` | Tipo de intervención | TEXT | 2 valores: 'Subsidio' (1661) o 'Ley' (348). 0 NULLs. |
| `instrumento` | Instrumento CORFO (original) | TEXT | 124 variantes crudas. Usar instrumento_homologado. |
| `instrumento_homologado` | Instrumento CORFO (normalizado) | TEXT | 49 valores canónicos. 0 NULLs. Un valor tiene trailing newline. |
| `estado_data` | Estado del proyecto | TEXT | 'FINALIZADO' (1689) o 'VIGENTE' (320). MAYÚSCULAS. |
| `tipo_persona_beneficiario` | Tipo de persona beneficiaria | TEXT | 4 valores + 4 NULLs. Capitalización inconsistente histórica. |
| `rut_beneficiario` | RUT del beneficiario | TEXT | Formato '12345678-9'. 1060 únicos. 0 NULLs. |
| `razon` | Razón social | TEXT | 0 NULLs, 1 vacío (PI-64569). Variantes tipográficas posibles. |
| `titulo_del_proyecto` | Título del proyecto | TEXT | Texto libre. 0 NULLs. Búsqueda semántica con LIKE. |
| `objetivo_general_del_proyecto` | Objetivo general del proyecto | TEXT | Texto libre. 2 NULLs. Complementar búsquedas con título. |
| `año_adjudicacion` | Año de adjudicación | INTEGER | **Comillas dobles obligatorias**. Rango 2009–2025. 0 NULLs. |
| `aprobado_corfo` | Monto aprobado por CORFO (CLP) | TEXT→REAL | **CAST(aprobado_corfo AS REAL) siempre**. Rango 0–3.2B CLP. |
| `aprobado_privado` | Contraparte privada total (CLP) | TEXT→REAL | CAST obligatorio. 0–13.4B CLP. |
| `aprobado_privado_pecuniario` | Contraparte privada en efectivo (CLP) | TEXT→REAL | CAST obligatorio. Subconjunto de aprobado_privado. |
| `monto_consolidado_ley` | Monto bajo Ley I+D (CLP) | TEXT→REAL | CAST obligatorio. Solo relevante cuando tipo_intervencion='Ley'. |
| `tipo_innovacion` | Tipo de innovación | TEXT | 3 valores: Producto/Proceso/Servicio. 105 NULLs. |
| `mercado_objetivo_final` | Mercado objetivo final | TEXT | 28 valores. 0 NULLs. Sector destino de la innovación. |
| `criterio_mujer` | Criterio de género (mujer) | TEXT | 4 valores. Capitalización inconsistente: usar LOWER(). |
| `genero_director` | Género del director/a | TEXT | 3 valores + 1 NULL. 'Masculino' / 'Femenino' / 'Sin determinar'. |
| `sostenible` | ¿Proyecto sostenible? | TEXT | 'Sí' (910) / 'No' (1099). Con tilde — exacto. 0 NULLs. |
| `ods_principal_sostenible` | ODS principal | TEXT | 15 valores (ODS2–ODS15). 1011 NULLs. Solo si sostenible='Sí'. |
| `meta_principal_cod` | Código de meta ODS | TEXT | 65 valores. 1159 NULLs. Solo si sostenible='Sí'. |
| `economia_circular_si_no` | ¿Economía circular? | TEXT | 'Sí' (320) / 'No' (523) / NULL (1166). NULL ≠ No. |
| `modelo_de_circularidad` | Modelo de circularidad | TEXT | 5 valores. 1689 NULLs. Solo proyectos EC. |
| `region_ejecucion` | Región de ejecución | TEXT | 16 regiones chilenas exactas. 0 NULLs. |
| `tramo_ventas` | Tramo de ventas (tamaño empresa) | TEXT | 5 valores. 0 NULLs. Sin ventas/Micro/Pequeña/Mediana/Grande. |
| `inicio_actividad` | Inicio de actividades | TEXT | Formato 'YYYY-MM-DD'. 37 NULLs. |
| `sector_economico` | Sector económico | TEXT | 35 valores + 65 NULLs. Variantes tipográficas — usar LIKE. |
| `patron_principal_asociado` | Patrón principal de circularidad | TEXT | 13 valores. 1689 NULLs. Solo proyectos EC. |
| `tipo_proyecto` | Tipo especial de proyecto | TEXT | 5 valores. 1199 NULLs. Solo proyectos EC/sostenibles/sociales. |
| `r_principal` | Estrategia R principal | TEXT | 10 valores (R0–R9). 1736 NULLs. Solo proyectos EC. |
| `estrategia_r_principal` | Descripción de la estrategia R | TEXT | 3 valores. 1691 NULLs. Solo proyectos EC. |
| `ley_rep_si_no` | ¿Bajo Ley REP? | TEXT | 'Sí' (31) / 'No' (1763) / NULL (215). |
| `ley_rep` | Categoría Ley REP | TEXT | 2 valores. 1979 NULLs. Muy escaso. |
| `ernc` | Tipo de ERNC | TEXT | 7 valores. 1960 NULLs. Solo proyectos energéticos. |
| `tendencia_final` | Tendencia tecnológica | TEXT | 20 valores exactos. 0 NULLs. 'Sin tendencia' = 80.3%. |

---

## Quirks críticos — leer antes de generar SQL

### 1. `año_adjudicacion` — comillas dobles obligatorias
El nombre contiene ñ, lo que requiere comillas dobles en SQLite:
```sql
-- CORRECTO
WHERE "año_adjudicacion" = 2023
GROUP BY "año_adjudicacion"

-- INCORRECTO — falla en SQLite
WHERE año_adjudicacion = 2023
```

### 2. `aprobado_corfo` — TEXT que requiere CAST
Almacenado como texto aunque contiene números. Sin CAST, ORDER BY da resultados incorrectos (orden léxico):
```sql
-- CORRECTO
SUM(CAST(aprobado_corfo AS REAL))
ORDER BY CAST(aprobado_corfo AS REAL) DESC

-- INCORRECTO — '9000000' > '3201035409' lexicográficamente
ORDER BY aprobado_corfo DESC
```
Lo mismo aplica para `aprobado_privado`, `aprobado_privado_pecuniario`, `monto_consolidado_ley`.

### 3. `sostenible` y `economia_circular_si_no` — valores con tilde
```sql
-- CORRECTO
WHERE sostenible = 'Sí'
WHERE economia_circular_si_no = 'Sí'

-- INCORRECTO — no coincide
WHERE sostenible = 'Si'
```

### 4. `economia_circular_si_no` — NULL ≠ No
Los 1166 NULLs son proyectos anteriores al programa EC sin clasificación. No equivalen a 'No'.

### 5. `sector_economico` — variantes tipográficas históricas
Múltiples variantes coexisten para sectores clave. Usar siempre LIKE para capturarlas todas:

**Agrícola** — 3 variantes (703 filas en total):
- `'Agrícola (excepto vitivinícola)'` (694) — canónica
- `'Agrícola (excepto vitivinicola)'` (2) — sin tilde
- `'Agrícola (excepto cultivo de uvas)'` (7) — variante histórica

**Alimentos** — 3 variantes (~580 filas en total):
- `'Alimentos (excepto vitivinícola)'` (550) — canónica
- `'Alimentos (excepto vitivinicola)'` (9) — sin tilde
- `'Alimentos (excepto producción de vino y derivados)'` (21) — variante histórica

```sql
-- CORRECTO — captura todas las variantes
WHERE LOWER(sector_economico) LIKE '%agr%cola%'
WHERE LOWER(sector_economico) LIKE '%alimentos%'

-- INCORRECTO — pierde variantes históricas
WHERE sector_economico = 'Agrícola (excepto vitivinícola)'
WHERE sector_economico = 'Alimentos (excepto vitivinícola)'
```

### 6. `instrumento_homologado` — trailing newline en un valor
Un proyecto (09FC02-6003) tiene instrumento_homologado con newline al final. Usar TRIM() o LIKE.

### 7. `estado_data` — valores en MAYÚSCULAS
```sql
WHERE estado_data = 'VIGENTE'   -- correcto
WHERE estado_data = 'Vigente'   -- no coincide
```

### 8. `criterio_mujer` — capitalización inconsistente
'No' (mayúscula, 1587) y 'no aplica' (minúsculas, 132) coexisten. Usar LOWER():
```sql
WHERE LOWER(criterio_mujer) IN ('incentivo', 'convocatoria')
```

---

## Campo: `tendencia_final` (detalle completo)

**Tipo**: TEXT | **Tabla**: proyectos | **0 NULLs**

Clasifica cada proyecto según la tendencia tecnológica principal, según la taxonomía interna de CORFO. Permite identificar concentraciones de financiamiento en tecnologías emergentes.

**Distribución completa (20 valores)**:

| Valor exacto | Proyectos | Descripción |
|---|---|---|
| `Sin tendencia` | 1614 | Sin clasificación tecnológica específica |
| `Manufactura Avanzada (Advanced Manufacturing)` | 79 | Industria 4.0, automatización, robótica |
| `Alimentos Funcionales` | 70 | Alimentos con propiedades nutricionales mejoradas |
| `Green Technologies (Tecnologías Verdes)` | 68 | Tecnologías de bajo impacto ambiental |
| `Química Verde (Green Chemestry)` | 31 | Procesos químicos sostenibles (nota: 'Chemestry' es typo en la fuente) |
| `Mass customization` | 30 | Producción personalizada a escala |
| `Inteligencia Artificial (IA)` | 28 | Machine learning, deep learning, procesamiento de datos |
| `Internet de las Cosas (IoT)` | 25 | Redes de sensores y dispositivos conectados |
| `Nanotecnología` | 14 | Tecnología a escala nanométrica |
| `Genómica y Edición de Genes` | 11 | Secuenciación genómica, CRISPR y edición genética |
| `Materiales Avanzados (Advanced Materials)` | 11 | Nuevos materiales con propiedades especiales |
| `Biotecnología` | 9 | Aplicaciones de biología molecular, fermentación |
| `Transferencia Tecnológica y Buenas Prácticas` | 6 | Adopción y difusión de tecnología existente |
| `Desarrollo de Drogas (Drug development)` | 4 | Investigación y desarrollo farmacéutico |
| `Clean Energy Technologies` | 3 | Tecnologías de energía limpia |
| `Software de aplicación` | 2 | Desarrollo de software para usos específicos |
| `Realidad Virtual (VR) y/o Realidad Aumentada (AR)` | 1 | Tecnologías de inmersión y superposición digital |
| `Gamificación` | 1 | Aplicación de mecánicas de juego a otros contextos |
| `Drones` | 1 | Vehículos aéreos no tripulados |
| `3D Visualization` | 1 | Visualización y modelado tridimensional |

**Patrones SQL para tendencia_final**:
```sql
-- Proyectos con clasificación tecnológica (excluye 'Sin tendencia')
WHERE tendencia_final != 'Sin tendencia'

-- Proyectos de IA
WHERE LOWER(tendencia_final) LIKE '%inteligencia artificial%'

-- Proyectos de IoT
WHERE LOWER(tendencia_final) LIKE '%internet de las cosas%'

-- Proyectos de biotecnología (nota: el valor exacto es 'Biotecnología' con tilde)
WHERE LOWER(tendencia_final) LIKE '%biotecnolog%'

-- Distribución por tendencia (excluye Sin tendencia)
SELECT tendencia_final, COUNT(*) as total
FROM proyectos
WHERE tendencia_final != 'Sin tendencia'
GROUP BY tendencia_final
ORDER BY total DESC

-- Monto aprobado por tendencia en los últimos 5 años
SELECT tendencia_final, SUM(CAST(aprobado_corfo AS REAL)) as monto_total
FROM proyectos
WHERE "año_adjudicacion" >= 2021
  AND tendencia_final != 'Sin tendencia'
GROUP BY tendencia_final
ORDER BY monto_total DESC
```

---

## Tabla: leads

Pipeline CRM de empresas de interés para contacto comercial.
Datos curados manualmente — **nunca sobrescribir con datos del sync**.
Actualmente: 1060 leads, todos en estado 'No contactado' (CRM recién inicializado).

| Campo | Nombre para el usuario | Tipo real | Notas |
|---|---|---|---|
| `id` | ID del lead | INTEGER | Auto-increment PK. |
| `rut_beneficiario` | RUT del beneficiario | TEXT | JOIN con proyectos.rut_beneficiario. 0 NULLs. |
| `razon_social` | Razón social | TEXT | 0 NULLs, 1 vacío (lead ID 1). |
| `sector_economico` | Sector económico | TEXT | 24 NULLs. Mismo set que proyectos. |
| `region` | Región | TEXT | 0 NULLs. 16 regiones. |
| `tramo_ventas` | Tramo de ventas | TEXT | 0 NULLs. 5 valores. |
| `cantidad_proyectos` | Cantidad de proyectos | INTEGER | Rango 1–71. Promedio ~1.9. |
| `monto_total_aprobado` | Monto total aprobado (CLP) | REAL | Ya es REAL — no necesita CAST. Rango 0–8.1B CLP. |
| `proyectos_ids` | IDs de proyectos | TEXT | Códigos separados por ', '. |
| `fecha_creacion` | Fecha de creación | TIMESTAMP | Auto. Formato 'YYYY-MM-DD HH:MM:SS'. |
| `ultima_actualizacion` | Última actualización | TIMESTAMP | Auto en PUT. |
| `estado_contacto` | Estado de contacto | TEXT | Default 'No contactado'. Actualmente todos. |
| `fecha_contacto` | Fecha de contacto | DATE | Formato YYYY-MM-DD. 1060 NULLs actualmente. |
| `metodo_contacto` | Método de contacto | TEXT | Texto libre. 1060 NULLs actualmente. |
| `persona_contacto` | Persona de contacto | TEXT | Texto libre. 1060 NULLs actualmente. |
| `telefono` | Teléfono | TEXT | Texto libre. 1060 NULLs actualmente. |
| `email` | Email | TEXT | Texto libre. 1060 NULLs actualmente. |
| `notas` | Notas | TEXT | Texto libre. 1060 NULLs actualmente. |
| `interes_nivel` | Nivel de interés | TEXT | 'bajo' / 'medio' / 'alto'. 1060 NULLs actualmente. |
| `proxima_accion` | Próxima acción | TEXT | Texto libre. 1060 NULLs actualmente. |
| `fecha_proxima_accion` | Fecha próxima acción | DATE | Formato YYYY-MM-DD. 1060 NULLs actualmente. |

---

## Patrones de consulta frecuentes

### Conteos y totales básicos
```sql
-- Total de proyectos por sector económico
SELECT sector_economico, COUNT(*) as total
FROM proyectos
WHERE sector_economico IS NOT NULL
GROUP BY sector_economico
ORDER BY total DESC

-- Monto total aprobado por año
SELECT "año_adjudicacion", SUM(CAST(aprobado_corfo AS REAL)) as monto_total
FROM proyectos
GROUP BY "año_adjudicacion"
ORDER BY "año_adjudicacion"

-- Proyectos por región
SELECT region_ejecucion, COUNT(*) as total
FROM proyectos
GROUP BY region_ejecucion
ORDER BY total DESC

-- Proyectos activos (vigentes) por sector
SELECT sector_economico, COUNT(*) as total
FROM proyectos
WHERE estado_data = 'VIGENTE'
  AND sector_economico IS NOT NULL
GROUP BY sector_economico
ORDER BY total DESC
```

### Filtros combinados
```sql
-- Proyectos de una región en un año específico
SELECT razon, titulo_del_proyecto, CAST(aprobado_corfo AS REAL) as monto
FROM proyectos
WHERE region_ejecucion = 'Región Metropolitana de Santiago'
  AND "año_adjudicacion" = 2023
ORDER BY monto DESC

-- Top empresas por monto en el sector alimentos
SELECT razon, rut_beneficiario, SUM(CAST(aprobado_corfo AS REAL)) as monto_total
FROM proyectos
WHERE LOWER(sector_economico) LIKE '%alimentos%'
GROUP BY rut_beneficiario, razon
ORDER BY monto_total DESC
LIMIT 10

-- Proyectos de economía circular por región
SELECT region_ejecucion, COUNT(*) as proyectos_ec
FROM proyectos
WHERE economia_circular_si_no = 'Sí'
GROUP BY region_ejecucion
ORDER BY proyectos_ec DESC
```

### Análisis por instrumento
```sql
-- Proyectos y monto por instrumento (usar homologado)
SELECT instrumento_homologado, COUNT(*) as proyectos,
       SUM(CAST(aprobado_corfo AS REAL)) as monto_total
FROM proyectos
GROUP BY instrumento_homologado
ORDER BY monto_total DESC

-- Proyectos Ley I+D con monto real
SELECT razon, CAST(monto_consolidado_ley AS REAL) as monto_ley
FROM proyectos
WHERE tipo_intervencion = 'Ley'
  AND CAST(monto_consolidado_ley AS REAL) > 0
ORDER BY monto_ley DESC
```

### Análisis de género y sostenibilidad
```sql
-- Proyectos liderados por mujeres por año
SELECT "año_adjudicacion", COUNT(*) as proyectos_mujer
FROM proyectos
WHERE genero_director = 'Femenino'
GROUP BY "año_adjudicacion"
ORDER BY "año_adjudicacion"

-- Proyectos sostenibles por ODS
SELECT ods_principal_sostenible, COUNT(*) as total
FROM proyectos
WHERE sostenible = 'Sí'
GROUP BY ods_principal_sostenible
ORDER BY total DESC

-- Proyectos de economía circular con estrategia R
SELECT r_principal, COUNT(*) as total
FROM proyectos
WHERE economia_circular_si_no = 'Sí'
GROUP BY r_principal
ORDER BY r_principal
```

### Análisis por tamaño de empresa
```sql
-- Monto promedio por tramo de ventas
SELECT tramo_ventas, COUNT(*) as proyectos,
       AVG(CAST(aprobado_corfo AS REAL)) as monto_promedio
FROM proyectos
GROUP BY tramo_ventas
ORDER BY CASE tramo_ventas
  WHEN 'Sin ventas' THEN 1
  WHEN 'Microempresa' THEN 2
  WHEN 'Pequeña' THEN 3
  WHEN 'Mediana' THEN 4
  WHEN 'Grande' THEN 5
  END
```

### Consultas sobre leads (CRM)
```sql
-- Leads con mayor financiamiento CORFO
SELECT razon_social, monto_total_aprobado, cantidad_proyectos, sector_economico
FROM leads
ORDER BY monto_total_aprobado DESC
LIMIT 10

-- Leads por sector y estado de contacto
SELECT sector_economico, estado_contacto, COUNT(*) as total
FROM leads
GROUP BY sector_economico, estado_contacto

-- JOIN leads con proyectos para ver detalle
SELECT l.razon_social, l.monto_total_aprobado, p.titulo_del_proyecto, p."año_adjudicacion"
FROM leads l
JOIN proyectos p ON l.rut_beneficiario = p.rut_beneficiario
ORDER BY l.monto_total_aprobado DESC
```

---

## Búsquedas semánticas en texto libre

Para preguntas del tipo "¿qué empresas desarrollan X?" o "¿qué proyectos son de Y tecnología?", buscar siempre en **ambos** campos: `titulo_del_proyecto` Y `objetivo_general_del_proyecto`. No basta con un único término LIKE; usar múltiples palabras clave sinónimas unidas con OR para maximizar el recall.

**Patrón recomendado — búsqueda multi-keyword**:
```sql
-- Empresas que desarrollan snacks saludables
SELECT DISTINCT razon
FROM proyectos
WHERE LOWER(titulo_del_proyecto) LIKE '%snack%'
   OR LOWER(titulo_del_proyecto) LIKE '%saludable%'
   OR LOWER(titulo_del_proyecto) LIKE '%funcional%'
   OR LOWER(titulo_del_proyecto) LIKE '%colación%'
   OR LOWER(titulo_del_proyecto) LIKE '%nutritivo%'
   OR LOWER(objetivo_general_del_proyecto) LIKE '%snack%'
   OR LOWER(objetivo_general_del_proyecto) LIKE '%saludable%'
   OR LOWER(objetivo_general_del_proyecto) LIKE '%funcional%'
   OR LOWER(objetivo_general_del_proyecto) LIKE '%colación%'
   OR LOWER(objetivo_general_del_proyecto) LIKE '%nutritivo%'
ORDER BY razon
```

**Notas clave**:
- Usar `DISTINCT razon` para evitar duplicar empresas con múltiples proyectos.
- `objetivo_general_del_proyecto` puede contener NULL; LIKE sobre NULL retorna NULL (no falla, simplemente no coincide).
- Ampliar siempre con sinónimos y variantes del término buscado.
- Si el contexto incluye un comentario `<!-- semantic_keywords: ... -->`, usar esas palabras como términos LIKE sobre ambos campos.

---

## Distribuciones clave para el modelo SQL

### sector_economico — top valores (con variantes)
- Agrícola (excepto vitivinícola): ~703 (incluye variantes con/sin tilde)
- Alimentos (excepto vitivinícola): ~580 (incluye variantes)
- Pesca y acuicultura: 200
- Comercio y retail: 144
- Servicios de ingeniería o de conocimiento: 100
- NULL: 65

### region_ejecucion — distribución por región
- Región Metropolitana de Santiago: 619 (30.8%)
- Región de Valparaíso: 292 (14.5%)
- Región de los Lagos: 247 (12.3%)
- Región del Biobío: 183 (9.1%)
- Región del Maule: 154 (7.7%)

### instrumento_homologado — top 10
- Ley I+D: 348
- Súmate a Innovar: 212
- Voucher de innovación: 199
- Programas de difusión y prospección tecnológica: 147
- Prototipos de innovación: 145
- Innova Región: 100
- Programa de I+D Aplicada: 92
- Crea y Valida Empresarial: 77
- Consolida y Expande: 68
- Contratos tecnológicos: 63

### año_adjudicacion — distribución temporal
2009(18), 2010(97), 2011(106), 2012(121), 2013(49), 2014(89), 2015(148),
2016(175), 2017(259 — pico), 2018(122), 2019(98), 2020(124), 2021(186),
2022(164), 2023(120), 2024(93), 2025(40)

### aprobado_corfo — rangos
- Mínimo: 0 CLP
- Máximo: 3.201.035.409 CLP (~3.2 mil millones)
- Promedio: ~55.610.626 CLP (~55.6 millones)
- Suma total en BD: ~111.721.747.998 CLP (~111.7 mil millones)

---

## Modelo de objeto CRM (DOB-114)

Estructura canónica que define qué campos de `proyectos` y `leads` se exponen para exportación o sincronización con un CRM externo (HubSpot u otro). Construida por `build_crm_object(razon)` en `corfo_server.py` y servida via `GET /api/crm/empresa/<razon>`.

### Campos de nivel empresa (agregados desde `proyectos`)

| Campo CRM | Origen | Tipo | Descripción |
|---|---|---|---|
| `crm_id` | `razon` (slugificada) | string | Identificador único para el CRM externo. Ej: `"acme-s-a"`. Generado con regex: lowercase + guiones. |
| `nombre` | `razon` | string | Razón social tal como está almacenada en la BD. |
| `total_adjudicado` | `SUM(CAST(aprobado_corfo AS REAL))` | float | Suma total de montos CORFO aprobados en todos los proyectos de la empresa (CLP). |
| `num_proyectos` | `COUNT(*)` | int | Cantidad de proyectos registrados para esta empresa. |
| `primer_proyecto` | `MIN("año_adjudicacion")` | int \| null | Año del primer proyecto adjudicado. |
| `ultimo_proyecto` | `MAX("año_adjudicacion")` | int \| null | Año del proyecto más reciente. |
| `regiones` | `region_ejecucion` (distintos) | list[str] | Lista ordenada de regiones donde la empresa ha ejecutado proyectos. |
| `sectores` | `sector_economico` (distintos) | list[str] | Lista ordenada de sectores económicos en que ha participado. |
| `tendencias` | `tendencia_final` (distintos, sin "Sin tendencia") | list[str] | Tendencias tecnológicas clasificadas en sus proyectos (excluye el valor genérico "Sin tendencia"). |
| `sostenible` | `ANY(sostenible = 'Sí')` | bool | `true` si al menos uno de sus proyectos tiene clasificación de sostenibilidad. |
| `economia_circular` | `ANY(economia_circular_si_no = 'Sí')` | bool | `true` si al menos uno de sus proyectos pertenece al programa de economía circular. |

### Campos de estado CRM (desde `leads`)

| Campo CRM | Origen | Tipo | Descripción |
|---|---|---|---|
| `en_leads` | `leads.nombre_compania` | bool | `true` si la empresa existe en el pipeline de leads (cualquier usuario). |
| `lead_status` | `leads.status` | string \| null | Estado actual en el pipeline: `Nuevo`, `Contactado`, `En seguimiento`, `Propuesta enviada`, `Cerrado`, o `null` si no está en leads. |

### Campos de nivel proyecto (lista `proyectos`)

Cada elemento del array `proyectos` dentro del objeto CRM tiene:

| Campo CRM | Origen | Tipo | Descripción |
|---|---|---|---|
| `codigo` | `codigo` | string | Código del proyecto (PK de facto en `proyectos`). |
| `nombre_proyecto` | `titulo_del_proyecto` | string | Título descriptivo del proyecto. |
| `año` | `"año_adjudicacion"` | int | Año de adjudicación del financiamiento. |
| `monto` | `CAST(aprobado_corfo AS REAL)` | float \| null | Monto CORFO aprobado en CLP. |
| `region` | `region_ejecucion` | string | Región chilena de ejecución. |
| `sector` | `sector_economico` | string \| null | Sector económico del proyecto. |
| `tipo_innovacion` | `tipo_innovacion` | string \| null | Tipo de innovación: Producto / Proceso / Servicio. |
| `tipo_proyecto` | `tipo_proyecto` | string \| null | Clasificación especial (EC, sostenible, social). |
| `tendencia` | `tendencia_final` | string | Tendencia tecnológica clasificada. |
| `sostenible` | `sostenible == 'Sí'` | bool | `true` si el proyecto tiene clasificación de sostenibilidad. |
| `economia_circular` | `economia_circular_si_no == 'Sí'` | bool | `true` si el proyecto pertenece al programa de economía circular. |

### Endpoint

```
GET /api/crm/empresa/<razon>
Autenticación: viewer o admin (login_required)
200 → objeto CRM completo (JSON)
404 → {"error": "Empresa no encontrada"}
500 → {"error": "Error al consultar la base de datos: ..."}
```

### Uso previsto

Este objeto es la fuente de datos base para:
- **DOB-117**: Configuración de mapeo de campos hacia el esquema de HubSpot u otro CRM.
- **DOB-119**: Exportación real a HubSpot via su API (contactos + empresa + deals).

### Notas de implementación

- `crm_id` se genera con `_slugify()`: convierte a minúsculas, reemplaza cualquier secuencia de caracteres no alfanuméricos con un guion `-`, y elimina guiones al inicio/fin. No requiere librería externa.
- La coincidencia en `leads` se hace por `nombre_compania = razon` (coincidencia exacta), sin filtrar por `user_id`, para reflejar si la empresa está en el pipeline de cualquier usuario.
- `total_adjudicado` puede ser `0.0` si todos los montos son nulos o cero; no retorna `null`.
