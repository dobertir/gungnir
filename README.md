# CORFO Analytics Platform

Herramienta de análisis de proyectos de I+D financiados por CORFO y otras agencias chilenas. Los usuarios hacen preguntas en lenguaje natural, el sistema genera SQL automáticamente y devuelve respuestas, gráficos y tablas de datos. Incluye un pipeline CRM simplificado para gestionar leads de empresas.

**Estado:** Prueba de concepto en camino a producto desplegable.

**Fuente de datos:** [datainnovacion.cl/api](https://datainnovacion.cl/api) — sincronización mensual automática. La base de datos local SQLite es una copia downstream.

---

## Prerrequisitos

- Python 3.11 (recomendado via [Miniconda](https://docs.conda.io/en/latest/miniconda.html))
- Una clave de API de [Groq](https://console.groq.com/) (capa gratuita disponible) — se usa como backend LLM
- Git

---

## Instalacion

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd <nombre-carpeta>
```

### 2. Crear y activar el entorno conda (recomendado)

```bash
conda create -n work python=3.11 -y
conda activate work
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y completa los valores:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales reales (ver seccion "Variables de entorno" mas abajo).

### 5. Obtener la base de datos inicial

La base de datos `corfo_alimentos.db` no se incluye en el repositorio. Hay dos opciones:

**Opcion A — Ejecutar el sync inicial:**
```bash
python sync/datainnovacion_sync.py
```

**Opcion B — Solicitar al equipo una copia del `.db` actual** y colocarla en la raiz del proyecto.

### 6. Iniciar el servidor

```bash
conda activate work
python corfo_server.py
```

El servidor estara disponible en `http://localhost:5000`.

---

## Variables de entorno

Todas las variables van en el archivo `.env` en la raiz del proyecto. Nunca subas este archivo al repositorio.

| Variable | Requerida | Descripcion |
|---|---|---|
| `ADMIN_USERNAME` | Si | Nombre de usuario del administrador |
| `ADMIN_PASSWORD` | Si | Contrasena del administrador (texto plano — el servidor la hashea internamente) |
| `ADMIN_ROLE` | No | Rol del admin: `admin` o `viewer` (por defecto: `admin`) |
| `VIEWER_USERNAME` | No | Nombre de usuario del segundo usuario (solo lectura) |
| `VIEWER_PASSWORD` | No | Contrasena del segundo usuario |
| `SECRET_KEY` | Recomendada | Clave secreta para firmar las cookies de sesion Flask. Si se omite, se genera una aleatoria en cada reinicio (las sesiones no sobreviven reinicios). |
| `GROQ_API_KEY` | Si | API key de Groq — se usa como backend LLM via endpoint OpenAI-compatible |
| `DATAINNOVACION_TOKEN` | Si | Token de autenticacion para la API de datainnovacion.cl (necesario para el sync mensual) |
| `DATABASE_URL` | No | URL de conexion PostgreSQL para produccion. Si se omite, se usa SQLite local. Formato: `postgresql://user:pass@host:5432/dbname` |
| `DB_PATH` | No | Ruta al archivo SQLite. Por defecto: `corfo_alimentos.db` en la carpeta del proyecto. |
| `PORT` | No | Puerto del servidor Flask. Por defecto: `5000`. |
| `FLASK_ENV` | No | Modo de Flask. Usar `development` para activar debug. |

---

## Como usar la aplicacion

Abre `http://localhost:5000` en el navegador. La interfaz tiene tres secciones principales:

- **Dashboard** — graficos precalculados del universo de proyectos CORFO.
- **Consultas** — escribe una pregunta en espanol (ej. "¿Cuales son las 10 empresas con mayor financiamiento?") y el sistema genera SQL y responde automaticamente.
- **Leads** — pipeline CRM para registrar y hacer seguimiento de empresas de interes.

---

## Estructura del proyecto

```
.
├── corfo_server.py          # Backend Flask: rutas API, generacion SQL con Mellea, auth
├── corfo_app.html           # Frontend React en un solo archivo HTML (sin build step)
├── corfo_alimentos.db       # Base de datos SQLite (NO incluida en el repo)
├── .env                     # Variables de entorno con secretos (NO incluido en el repo)
├── .env.example             # Plantilla de variables de entorno sin valores reales
├── requirements.txt         # Dependencias Python con versiones exactas
├── migrate_data.py          # Utilidad para migrar datos entre SQLite y PostgreSQL
├── build_embeddings.py      # Script auxiliar para construccion de embeddings
├── Procfile                 # Configuracion para despliegue en plataformas como Heroku/Railway
├── sync/
│   ├── datainnovacion_sync.py   # Job de sincronizacion mensual con datainnovacion.cl/api
│   ├── entity_resolution.py     # Normalizacion de nombres de empresas
│   └── schema_migrations/       # Migraciones de esquema de base de datos
├── context/
│   ├── schema_context.md        # Esquema con significado de negocio (alimenta el prompt AI)
│   ├── field_dictionary.json    # Definiciones de campos en formato maquina
│   └── query_examples.json      # Pares pregunta→SQL correctos (usados en evaluacion)
└── tests/
    ├── test_api.py
    ├── test_sql_generation.py
    ├── test_drill_down.py
    ├── test_empresa_perfil.py
    └── benchmark_questions.json # Set de evaluacion para precision NL→SQL
```

---

## Arquitectura tecnica

| Capa | Tecnologia |
|---|---|
| Backend | Python 3.11, Flask, Flask-CORS |
| Generacion SQL (IA) | Mellea (IBM) con OpenAIBackend → Groq (endpoint OpenAI-compatible) |
| Modelo LLM | `llama-3.1-8b-instant` via Groq |
| Base de datos | SQLite (`corfo_alimentos.db`) — tablas `proyectos` y `leads` |
| Frontend | React + Recharts en un solo archivo HTML |
| Sincronizacion | APScheduler — sync mensual el dia 1 de cada mes a las 03:00 |

**Patron IVR de Mellea:** Cada pregunta pasa por hasta 3 intentos automaticos. Se rechaza cualquier respuesta que no sea JSON valido o que contenga SQL no-SELECT. Si los 3 intentos fallan, se devuelve el mejor resultado parcial junto con un aviso en la UI.

---

## Ejecutar los tests

```bash
conda activate work
pytest tests/
```

---

## Sincronizacion de datos

El job de sync corre automaticamente el dia 1 de cada mes. Para ejecutarlo manualmente:

```bash
# Via script directo
python sync/datainnovacion_sync.py

# Via API (requiere autenticacion admin)
curl -X POST http://localhost:5000/api/sync \
  -H "Content-Type: application/json" \
  --cookie "session=<tu-cookie-de-sesion>"
```

---

## Notas de seguridad

- `corfo_alimentos.db` contiene datos publicos pero nunca debe subirse al repo (puede crecer mucho).
- `.env` contiene credenciales reales — esta en `.gitignore` por defecto.
- El SQL generado por la IA es siempre SELECT-only. Las rutas de generacion no admiten INSERT/UPDATE/DELETE.
- `use_reloader=False` es intencional — evita la doble inicializacion de las sesiones Mellea.
