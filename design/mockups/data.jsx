// data.jsx — Seed data derived from real schema (schema_context.md)
// Deliberately small, representative subset — enough to look real.

// Top sectors (from distribuciones clave)
const SECTORS = [
  { name: 'Agrícola (excepto vitivinícola)', n: 703 },
  { name: 'Alimentos (excepto vitivinícola)', n: 580 },
  { name: 'Pesca y acuicultura', n: 200 },
  { name: 'Comercio y retail', n: 144 },
  { name: 'Servicios de ingeniería', n: 100 },
  { name: 'Vitivinícola', n: 87 },
  { name: 'Biotecnología aplicada', n: 62 },
];

// Regions
const REGIONS = [
  { name: 'Metropolitana de Santiago', n: 619, pct: 30.8 },
  { name: 'Valparaíso', n: 292, pct: 14.5 },
  { name: 'Los Lagos', n: 247, pct: 12.3 },
  { name: 'Biobío', n: 183, pct: 9.1 },
  { name: 'Maule', n: 154, pct: 7.7 },
  { name: "O'Higgins", n: 121, pct: 6.0 },
  { name: 'Araucanía', n: 98, pct: 4.9 },
  { name: 'Coquimbo', n: 74, pct: 3.7 },
];

// Years 2009–2025 with counts
const YEARS = [
  { y: 2009, n: 18 },  { y: 2010, n: 97 },  { y: 2011, n: 106 }, { y: 2012, n: 121 },
  { y: 2013, n: 49 },  { y: 2014, n: 89 },  { y: 2015, n: 148 }, { y: 2016, n: 175 },
  { y: 2017, n: 259 }, { y: 2018, n: 122 }, { y: 2019, n: 98 },  { y: 2020, n: 124 },
  { y: 2021, n: 186 }, { y: 2022, n: 164 }, { y: 2023, n: 120 }, { y: 2024, n: 93 },
  { y: 2025, n: 40 },
];

// Tech trends
const TENDENCIAS = [
  { name: 'Manufactura Avanzada', n: 79 },
  { name: 'Alimentos Funcionales', n: 70 },
  { name: 'Green Technologies', n: 68 },
  { name: 'Química Verde', n: 31 },
  { name: 'Mass customization', n: 30 },
  { name: 'Inteligencia Artificial', n: 28 },
  { name: 'Internet de las Cosas', n: 25 },
  { name: 'Nanotecnología', n: 14 },
];

// Instruments
const INSTRUMENTOS = [
  { name: 'Ley I+D', n: 348, monto: 28400e6 },
  { name: 'Súmate a Innovar', n: 212, monto: 12100e6 },
  { name: 'Voucher de innovación', n: 199, monto: 3200e6 },
  { name: 'Difusión tecnológica', n: 147, monto: 5600e6 },
  { name: 'Prototipos de innovación', n: 145, monto: 8900e6 },
  { name: 'Innova Región', n: 100, monto: 4700e6 },
  { name: 'I+D Aplicada', n: 92, monto: 14300e6 },
];

// Lead companies (representative, realistic Chilean names)
const LEADS = [
  { id: 1, razon: 'Agrícola Las Cruces SpA',            rut: '76.123.456-7', sector: 'Agrícola (excepto vitivinícola)', region: 'Maule',        tramo: 'Mediana', proyectos: 8,  monto: 1240e6, tendencias: ['Alimentos Funcionales','Green Technologies'], estado: 'En seguimiento', interes: 'alto',  actualizada: '2026-04-12', proxima: 'Enviar propuesta', proxima_fecha: '2026-04-22' },
  { id: 2, razon: 'Viña Altos del Maipo S.A.',          rut: '96.551.210-K', sector: 'Vitivinícola',                    region: 'Metropolitana', tramo: 'Grande',  proyectos: 12, monto: 3470e6, tendencias: ['Mass customization','IoT'],                    estado: 'Contactado',     interes: 'alto',  actualizada: '2026-04-10', proxima: 'Reunión técnica', proxima_fecha: '2026-04-19' },
  { id: 3, razon: 'Salmones Austral Ltda.',             rut: '77.890.123-4', sector: 'Pesca y acuicultura',             region: 'Los Lagos',     tramo: 'Grande',  proyectos: 15, monto: 5120e6, tendencias: ['Biotecnología','Green Technologies'],          estado: 'Propuesta enviada', interes: 'alto', actualizada: '2026-04-08', proxima: 'Seguimiento', proxima_fecha: '2026-04-21' },
  { id: 4, razon: 'Alimentos Nutralis SpA',             rut: '76.445.900-1', sector: 'Alimentos (excepto vitivinícola)', region: 'Valparaíso',   tramo: 'Pequeña', proyectos: 4,  monto: 420e6,  tendencias: ['Alimentos Funcionales'],                       estado: 'Contactado',     interes: 'medio', actualizada: '2026-04-05', proxima: 'Llamada', proxima_fecha: '2026-04-20' },
  { id: 5, razon: 'BioIngeniería Andes S.A.',           rut: '96.772.339-5', sector: 'Biotecnología aplicada',          region: 'Metropolitana', tramo: 'Mediana', proyectos: 7,  monto: 980e6,  tendencias: ['Biotecnología','Genómica'],                    estado: 'Nuevo',          interes: 'alto',  actualizada: '2026-04-14', proxima: 'Primer contacto', proxima_fecha: '2026-04-18' },
  { id: 6, razon: 'Frutícola del Valle Ltda.',          rut: '77.220.118-3', sector: 'Agrícola (excepto vitivinícola)', region: "O'Higgins",     tramo: 'Mediana', proyectos: 6,  monto: 710e6,  tendencias: ['Green Technologies'],                          estado: 'En seguimiento', interes: 'medio', actualizada: '2026-04-03', proxima: 'Enviar info técnica', proxima_fecha: '2026-04-17' },
  { id: 7, razon: 'Packaging Circular SpA',             rut: '76.990.112-8', sector: 'Servicios de ingeniería',         region: 'Biobío',        tramo: 'Pequeña', proyectos: 3,  monto: 285e6,  tendencias: ['Green Technologies','Química Verde'],          estado: 'Cerrado',        interes: 'bajo',  actualizada: '2026-03-28', proxima: '—', proxima_fecha: null },
  { id: 8, razon: 'Tecnovin Chile Ltda.',               rut: '77.554.221-K', sector: 'Vitivinícola',                    region: 'Maule',         tramo: 'Pequeña', proyectos: 2,  monto: 140e6,  tendencias: ['IoT'],                                          estado: 'Nuevo',          interes: 'medio', actualizada: '2026-04-15', proxima: 'Primer contacto', proxima_fecha: '2026-04-19' },
  { id: 9, razon: 'Frutos Secos del Norte S.A.',        rut: '96.889.004-1', sector: 'Agrícola (excepto vitivinícola)', region: 'Coquimbo',      tramo: 'Mediana', proyectos: 5,  monto: 620e6,  tendencias: ['Alimentos Funcionales'],                       estado: 'Contactado',     interes: 'alto',  actualizada: '2026-04-11', proxima: 'Reunión', proxima_fecha: '2026-04-23' },
  { id: 10, razon: 'Acuícola Patagonia Ltda.',          rut: '77.112.889-2', sector: 'Pesca y acuicultura',             region: 'Los Lagos',     tramo: 'Grande',  proyectos: 11, monto: 2340e6, tendencias: ['IoT','Biotecnología'],                         estado: 'En seguimiento', interes: 'alto',  actualizada: '2026-04-09', proxima: 'Visita terreno', proxima_fecha: '2026-04-25' },
  { id: 11, razon: 'Agroexportadora Central SpA',       rut: '76.334.778-9', sector: 'Agrícola (excepto vitivinícola)', region: 'Valparaíso',    tramo: 'Mediana', proyectos: 6,  monto: 890e6,  tendencias: ['IoT','Green Technologies'],                    estado: 'Nuevo',          interes: 'medio', actualizada: '2026-04-16', proxima: '—', proxima_fecha: null },
  { id: 12, razon: 'Lácteos del Sur S.A.',              rut: '96.445.001-K', sector: 'Alimentos (excepto vitivinícola)', region: 'Los Lagos',    tramo: 'Grande',  proyectos: 9,  monto: 1870e6, tendencias: ['Alimentos Funcionales','Manufactura Avanzada'], estado: 'Propuesta enviada', interes: 'alto', actualizada: '2026-04-07', proxima: 'Revisión propuesta', proxima_fecha: '2026-04-20' },
];

// Saved consultas (history threaded as conversations)
const CONSULTAS = [
  {
    id: 'c-2026-041',
    titulo: 'Empresas de alimentos funcionales 2022-2025',
    fecha: 'hace 2 horas',
    pinned: true,
    mensajes: 4,
    preview: '¿Qué empresas desarrollan alimentos funcionales y han recibido más de $500M en los últimos 4 años?',
    tags: ['alimentos','funcionales','2022-2025'],
    resultados: 23,
  },
  {
    id: 'c-2026-040',
    titulo: 'Top empresas sector acuícola Los Lagos',
    fecha: 'ayer',
    pinned: true,
    mensajes: 2,
    preview: 'Rankea empresas de pesca y acuicultura en Los Lagos por monto total aprobado.',
    tags: ['acuicultura','los-lagos','ranking'],
    resultados: 42,
  },
  {
    id: 'c-2026-039',
    titulo: 'Proyectos de IA en agricultura',
    fecha: 'hace 3 días',
    pinned: false,
    mensajes: 6,
    preview: '¿Cuántos proyectos usan IA o machine learning en el sector agrícola? Cruza con región.',
    tags: ['IA','agrícola','tendencias'],
    resultados: 11,
  },
  {
    id: 'c-2026-038',
    titulo: 'Mujeres directoras — evolución 2019-2024',
    fecha: 'hace 4 días',
    pinned: false,
    mensajes: 3,
    preview: 'Muestra la evolución anual de proyectos liderados por mujeres.',
    tags: ['género','evolución'],
    resultados: 287,
  },
  {
    id: 'c-2026-037',
    titulo: 'Economía circular — empresas activas',
    fecha: 'la semana pasada',
    pinned: false,
    mensajes: 5,
    preview: 'Empresas con 2+ proyectos de economía circular, ordenadas por monto.',
    tags: ['EC','ranking'],
    resultados: 34,
  },
];

// Current consulta detail — the active conversation
const CONSULTA_ACTIVA = {
  id: 'c-2026-041',
  titulo: 'Empresas de alimentos funcionales 2022-2025',
  turnos: [
    {
      rol: 'user',
      pregunta: '¿Qué empresas desarrollan alimentos funcionales y han recibido más de $500M en los últimos 4 años?',
      fecha: 'hace 2 horas',
    },
    {
      rol: 'assistant',
      respuesta: 'Encontré **23 empresas** que cumplen ambos criterios. El sector está fuertemente concentrado en la Región Metropolitana (9 empresas, 39%) y Valparaíso (5 empresas, 22%). Las 3 empresas líderes concentran el 41% del financiamiento total.',
      sql: `SELECT razon, rut_beneficiario,
       COUNT(*) AS proyectos,
       SUM(CAST(aprobado_corfo AS REAL)) AS monto_total,
       region_ejecucion
FROM proyectos
WHERE (LOWER(tendencia_final) LIKE '%alimentos funcionales%'
       OR LOWER(titulo_del_proyecto) LIKE '%funcional%'
       OR LOWER(objetivo_general_del_proyecto) LIKE '%funcional%')
  AND "año_adjudicacion" >= 2022
GROUP BY rut_beneficiario, razon, region_ejecucion
HAVING SUM(CAST(aprobado_corfo AS REAL)) > 500000000
ORDER BY monto_total DESC;`,
      resultados: [
        { razon: 'Alimentos Nutralis SpA',     rut: '76.445.900-1', proyectos: 4, monto: 1820e6, region: 'Valparaíso' },
        { razon: 'Agrícola Las Cruces SpA',    rut: '76.123.456-7', proyectos: 3, monto: 1240e6, region: 'Maule' },
        { razon: 'BioFoods Andes S.A.',        rut: '96.112.443-7', proyectos: 5, monto: 1180e6, region: 'Metropolitana' },
        { razon: 'Lácteos del Sur S.A.',       rut: '96.445.001-K', proyectos: 3, monto: 1070e6, region: 'Los Lagos' },
        { razon: 'Frutos Secos del Norte S.A.',rut: '96.889.004-1', proyectos: 3, monto: 920e6,  region: 'Coquimbo' },
        { razon: 'Nutrigen Chile SpA',         rut: '77.665.002-8', proyectos: 2, monto: 780e6,  region: 'Metropolitana' },
        { razon: 'Fortifica Alimentos Ltda.',  rut: '76.998.112-0', proyectos: 2, monto: 690e6,  region: 'Metropolitana' },
        { razon: 'Alimar Funcional S.A.',      rut: '96.221.778-2', proyectos: 2, monto: 640e6,  region: 'Valparaíso' },
        { razon: 'Proteínas del Pacífico SpA', rut: '77.998.331-5', proyectos: 3, monto: 590e6,  region: 'Biobío' },
        { razon: 'Oats & Grains Chile Ltda.',  rut: '76.112.008-1', proyectos: 2, monto: 540e6,  region: 'O\'Higgins' },
      ],
      followups: [
        '¿Cuáles de estas están ya en mi pipeline de leads?',
        'Muestra la evolución de esta lista año por año',
        'Cruza con tendencia "Green Technologies"',
      ],
      fecha: 'hace 2 horas',
    },
    {
      rol: 'user',
      pregunta: '¿Cuáles de estas están ya en mi pipeline de leads?',
      fecha: 'hace 1 hora',
    },
    {
      rol: 'assistant',
      respuesta: 'De las 23 empresas, **5 están en tu pipeline** de leads. 2 en estado "En seguimiento", 2 "Contactado", 1 "Nuevo". Las otras 18 son leads potenciales no agregados.',
      sql: `SELECT p.razon,
       l.estado_contacto,
       l.interes_nivel,
       l.proxima_accion
FROM proyectos p
LEFT JOIN leads l ON l.rut_beneficiario = p.rut_beneficiario
WHERE /* ... misma condición anterior ... */
  AND l.id IS NOT NULL;`,
      resultados: [
        { empresa: 'Alimentos Nutralis SpA',   estado: 'Contactado',     interes: 'medio', accion: 'Llamada el 2026-04-20' },
        { empresa: 'Agrícola Las Cruces SpA',  estado: 'En seguimiento', interes: 'alto',  accion: 'Enviar propuesta' },
        { empresa: 'Lácteos del Sur S.A.',     estado: 'Propuesta enviada', interes: 'alto', accion: 'Revisión propuesta' },
        { empresa: 'Frutos Secos del Norte S.A.', estado: 'Contactado',  interes: 'alto',  accion: 'Reunión el 2026-04-23' },
        { empresa: 'BioFoods Andes S.A.',      estado: 'Nuevo',          interes: 'medio', accion: '—' },
      ],
      followups: [
        'Agrega las 18 empresas faltantes como nuevos leads',
        'Muéstrame el perfil de BioFoods Andes',
      ],
      fecha: 'hace 1 hora',
    },
  ],
};

// Example questions
const EXAMPLES = [
  'Top 10 empresas por monto en el sector pesca',
  'Proyectos de IA aprobados en 2024',
  'Evolución del financiamiento en Los Lagos',
  'Empresas con proyectos de economía circular',
  'Distribución por ODS 2022–2025',
];

// Empresa 360 — a detailed company profile
const EMPRESA = {
  razon: 'Agrícola Las Cruces SpA',
  rut: '76.123.456-7',
  region: 'Maule',
  sector: 'Agrícola (excepto vitivinícola)',
  tramo: 'Mediana',
  primerProyecto: 2015,
  ultimoProyecto: 2024,
  totalProyectos: 8,
  totalMonto: 1240e6,
  sostenible: true,
  economiaCircular: true,
  tendencias: ['Alimentos Funcionales','Green Technologies','IoT'],
  leadStatus: 'En seguimiento',
  interes: 'alto',
  contacto: { nombre: 'Jaime Urrutia', cargo: 'Gerente I+D', email: 'jurrutia@lascruces.cl', telefono: '+56 75 222 3344' },
  notas: 'Empresa muy activa en financiamiento CORFO. Trayectoria consistente desde 2015. Foco reciente en productos funcionales con ingredientes nativos. Buen candidato para propuesta de consultoría de expansión.',
  proyectos: [
    { codigo: '24IN-285432', titulo: 'Desarrollo de snacks funcionales con berries andinos', año: 2024, monto: 280e6, instrumento: 'Prototipos de innovación', estado: 'VIGENTE', tendencia: 'Alimentos Funcionales' },
    { codigo: '23CR-223891', titulo: 'Sistema IoT para monitoreo de cultivos orgánicos',    año: 2023, monto: 210e6, instrumento: 'Consolida y Expande',       estado: 'VIGENTE', tendencia: 'Internet de las Cosas' },
    { codigo: '22IN-198442', titulo: 'Frutos deshidratados con alto contenido antioxidante', año: 2022, monto: 195e6, instrumento: 'Crea y Valida Empresarial', estado: 'FINALIZADO', tendencia: 'Alimentos Funcionales' },
    { codigo: '21SI-167331', titulo: 'Compostaje industrial de residuos agrícolas',         año: 2021, monto: 140e6, instrumento: 'Súmate a Innovar',          estado: 'FINALIZADO', tendencia: 'Green Technologies' },
    { codigo: '20VO-128874', titulo: 'Validación de empaque biodegradable',                 año: 2020, monto: 92e6,  instrumento: 'Voucher de innovación',     estado: 'FINALIZADO', tendencia: 'Green Technologies' },
    { codigo: '18IN-098221', titulo: 'Mejoramiento de variedad nativa de frutilla',         año: 2018, monto: 145e6, instrumento: 'Prototipos de innovación',  estado: 'FINALIZADO', tendencia: 'Sin tendencia' },
    { codigo: '16DF-068443', titulo: 'Difusión buenas prácticas en agricultura sustentable', año: 2016, monto: 85e6, instrumento: 'Difusión tecnológica',       estado: 'FINALIZADO', tendencia: 'Green Technologies' },
    { codigo: '15PI-048117', titulo: 'Cadena de frío para berries frescos',                 año: 2015, monto: 93e6,  instrumento: 'Prototipos de innovación',  estado: 'FINALIZADO', tendencia: 'Sin tendencia' },
  ],
  actividad: [
    { fecha: '2026-04-12', tipo: 'Llamada',     con: 'Jaime Urrutia', nota: 'Interés en apoyo para próxima postulación I+D Aplicada' },
    { fecha: '2026-04-05', tipo: 'Email',       con: 'Jaime Urrutia', nota: 'Enviada brochure de servicios' },
    { fecha: '2026-03-28', tipo: 'Reunión',     con: 'Equipo I+D',    nota: 'Sesión exploratoria — interesados en 2 instrumentos' },
    { fecha: '2026-03-15', tipo: 'Agregado a leads', con: '—',        nota: 'Identificada vía consulta "Top empresas alimentos funcionales"' },
  ],
};

Object.assign(window, { SECTORS, REGIONS, YEARS, TENDENCIAS, INSTRUMENTOS, LEADS, CONSULTAS, CONSULTA_ACTIVA, EXAMPLES, EMPRESA });
