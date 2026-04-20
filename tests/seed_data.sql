-- seed_data.sql
-- Dataset semilla para pruebas internas del CORFO Analytics Platform.
-- Crea y puebla las tablas proyectos y leads con datos representativos.
-- Diseñado para ejecutarse contra una conexión SQLite en memoria (:memory:).
--
-- Cobertura del dataset:
--   • 30 filas en proyectos
--   • Sectores: Alimentos, Forestal, Tecnologías de la información,
--               Minero, Agrícola, Biotecnológico, Energético
--   • Regiones: ≥ 5 distintas
--   • Años: 2009–2025 (varios)
--   • estado_data: VIGENTE y FINALIZADO
--   • sostenible: Sí y No
--   • tipo_innovacion: Proceso, Producto, Servicio, y NULL
--   • tipo_proyecto: NULL y valores especiales (Economía Circular, etc.)
--   • tendencia_final: Sin tendencia + varios valores con tendencia
--   • aprobado_corfo: almacenado como TEXT (crítico)
--   • 3 filas en leads

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLA: proyectos
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS proyectos (
    codigo                      TEXT,
    foco_apoyo                  TEXT,
    tipo_intervencion           TEXT,
    instrumento                 TEXT,
    instrumento_homologado      TEXT,
    estado_data                 TEXT,
    tipo_persona_beneficiario   TEXT,
    rut_beneficiario            TEXT,
    razon                       TEXT,
    titulo_del_proyecto         TEXT,
    objetivo_general_del_proyecto TEXT,
    "año_adjudicacion"          INTEGER,
    aprobado_corfo              TEXT,
    aprobado_privado            TEXT,
    aprobado_privado_pecuniario TEXT,
    monto_consolidado_ley       TEXT,
    tipo_innovacion             TEXT,
    mercado_objetivo_final      TEXT,
    criterio_mujer              TEXT,
    genero_director             TEXT,
    sostenible                  TEXT,
    ods_principal_sostenible    TEXT,
    meta_principal_cod          TEXT,
    economia_circular_si_no     TEXT,
    modelo_de_circularidad      TEXT,
    region_ejecucion            TEXT,
    tramo_ventas                TEXT,
    inicio_actividad            TEXT,
    sector_economico            TEXT,
    patron_principal_asociado   TEXT,
    tipo_proyecto               TEXT,
    r_principal                 TEXT,
    estrategia_r_principal      TEXT,
    ley_rep_si_no               TEXT,
    ley_rep                     TEXT,
    ernc                        TEXT,
    tendencia_final             TEXT
);

-- 30 filas representativas
-- Fila 1: Alimentos / Metropolitana / 2023 / VIGENTE / Sí / Producto / Economía Circular
INSERT INTO proyectos VALUES (
    'SEED-0001','Desarrolla innovación con I+D','Subsidio','I+D Aplicada',
    'I+D Aplicada en Empresas','VIGENTE','PERSONA JURIDICA COMERCIAL','12345678-9',
    'ALIMENTOS NUTRITIVOS SA','Desarrollo de alimento funcional con proteína vegetal',
    'Desarrollar un alimento funcional rico en proteínas de origen vegetal',
    2023,'85000000','25000000','15000000','0',
    'Producto','Alimentos (excepto producción de vino y derivados)',
    'No','Masculino','Sí','ODS2','ODS2-META1',
    'Sí','Recuperación de Recursos',
    'Región Metropolitana de Santiago','Mediana','2005-03-15',
    'Alimentos (excepto vitivinícola)',NULL,
    'Economía Circular','R8 Reciclar','Reciclar materiales al final del ciclo',
    'No',NULL,NULL,'Alimentos Funcionales'
);

-- Fila 2: Alimentos / Valparaíso / 2021 / FINALIZADO / No / Proceso / NULL tipo_proyecto
INSERT INTO proyectos VALUES (
    'SEED-0002','Desarrolla innovación','Subsidio','Innova Región',
    'Innova Región','FINALIZADO','PERSONA JURIDICA COMERCIAL','23456789-0',
    'PROCESADORA DEL MAR LTDA','Optimización de proceso de enlatado de pescado',
    'Mejorar la eficiencia del proceso de enlatado reduciendo mermas',
    2021,'42000000','12000000','0','0',
    'Proceso','Alimentos (excepto producción de vino y derivados)',
    'No','Femenino','No',NULL,NULL,
    'No',NULL,
    'Región de Valparaíso','Pequeña','1998-07-01',
    'Alimentos (excepto vitivinícola)',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Sin tendencia'
);

-- Fila 3: Forestal / Biobío / 2019 / FINALIZADO / No / Proceso / NULL tipo_proyecto
INSERT INTO proyectos VALUES (
    'SEED-0003','Desarrolla innovación con I+D','Subsidio','I+D Aplicada',
    'I+D Aplicada en Empresas','FINALIZADO','PERSONA JURIDICA COMERCIAL','34567890-1',
    'MADERERA SUR SpA','Proceso de secado de madera con menor consumo energético',
    'Reducir el consumo energético en el proceso de secado de madera nativa',
    2019,'67000000','20000000','10000000','0',
    'Proceso','Forestal (incluye muebles y papel)','No','Masculino',
    'No',NULL,NULL,
    'No',NULL,
    'Región del Biobío','Grande','1985-11-20',
    'Forestal',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Sin tendencia'
);

-- Fila 4: Tecnologías de la información / Metropolitana / 2024 / VIGENTE / No / Producto / NULL
INSERT INTO proyectos VALUES (
    'SEED-0004','Desarrolla innovación con I+D','Subsidio','Crea y Valida',
    'Crea y Valida I+D+i Empresarial','VIGENTE','PERSONA JURIDICA COMERCIAL','45678901-2',
    'TECNODATA SA','Plataforma de IA para análisis de cadena de suministro',
    'Crear una plataforma de inteligencia artificial para optimizar logística',
    2024,'120000000','40000000','40000000','0',
    'Producto','Telecomunicaciones y tecnologías de la información',
    'Incentivo','Masculino','No',NULL,NULL,
    'No',NULL,
    'Región Metropolitana de Santiago','Mediana','2010-04-01',
    'Tecnologías de la información',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Inteligencia Artificial (IA)'
);

-- Fila 5: Minería / Antofagasta / 2020 / FINALIZADO / Sí / Proceso / Producción Sostenible
INSERT INTO proyectos VALUES (
    'SEED-0005','Desarrolla innovación con I+D','Subsidio','I+D Aplicada',
    'I+D Aplicada en Empresas','FINALIZADO','PERSONA JURIDICA COMERCIAL','56789012-3',
    'MINERA NORTE SpA','Sistema de recuperación de agua en procesos mineros',
    'Desarrollar sistema de tratamiento y reutilización de aguas de proceso',
    2020,'250000000','80000000','50000000','0',
    'Proceso','Minería y metalurgia extractiva',
    'No','Masculino','Sí','ODS12','ODS12-META2',
    'No',NULL,
    'Región de Antofagasta','Grande','2002-09-15',
    'Minero',NULL,
    'Producción Sostenible',NULL,NULL,
    'No',NULL,'Eficiencia Energética','Green Technologies (Tecnologías Verdes)'
);

-- Fila 6: Agrícola / Araucanía / 2022 / VIGENTE / Sí / Producto / NULL
INSERT INTO proyectos VALUES (
    'SEED-0006','Desarrolla innovación','Subsidio','Capital Semilla',
    'Capital Semilla','VIGENTE','Persona Jurídica constituida en Chile','67890123-4',
    'AGRICOLA ARAUCANA SA','Desarrollo de variedad de trigo resistente a sequía',
    'Obtener mediante mejoramiento genético convencional una variedad de trigo',
    2022,'18000000','5000000','0','0',
    'Producto','Agropecuario (excepto fruticultura y vitivinicultura)',
    'Convocatoria','Femenino','Sí','ODS2','ODS2-META2',
    'No',NULL,
    'Región de La Araucanía','Pequeña','2008-01-10',
    'Agrícola',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Sin tendencia'
);

-- Fila 7: Biotecnológico / Metropolitana / 2018 / FINALIZADO / Sí / Producto / NULL
INSERT INTO proyectos VALUES (
    'SEED-0007','Desarrolla innovación con I+D','Subsidio','I+D Aplicada',
    'I+D Aplicada en Empresas','FINALIZADO','PERSONA JURIDICA COMERCIAL','78901234-5',
    'BIOTECH CHILE SA','Desarrollo de probiótico para ganado bovino',
    'Desarrollar y validar un probiótico para mejorar el rendimiento lácteo',
    2018,'95000000','30000000','20000000','0',
    'Producto','Agropecuario (excepto fruticultura y vitivinicultura)',
    'No','Femenino','Sí','ODS9','ODS9-META1',
    'No',NULL,
    'Región Metropolitana de Santiago','Mediana','2001-06-20',
    'Biotecnológico',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Biotecnología'
);

-- Fila 8: Energético / O'Higgins / 2016 / FINALIZADO / Sí / Proceso / Producción Sostenible
INSERT INTO proyectos VALUES (
    'SEED-0008','Renuévate','Subsidio','Innova Región',
    'Innova Región','FINALIZADO','PERSONA JURIDICA COMERCIAL','89012345-6',
    'ENERGÍAS LIMPIAS SA','Sistema de generación solar para secado de frutas',
    'Instalar y validar sistema fotovoltaico para proceso de deshidratación',
    2016,'55000000','18000000','0','0',
    'Proceso','Agropecuario (excepto fruticultura y vitivinicultura)',
    'No','Masculino','Sí','ODS7','ODS7-META1',
    'No',NULL,
    'Región del Libertador General Bernardo O''Higgins','Pequeña','2003-02-28',
    'Energético',NULL,
    'Producción Sostenible',NULL,NULL,
    'No',NULL,'Energía solar','Clean Energy Technologies'
);

-- Fila 9: Alimentos / Los Lagos / 2025 / VIGENTE / No / Servicio / NULL
INSERT INTO proyectos VALUES (
    'SEED-0009','Consolida y Expande','Subsidio','Innovación Empresarial Individual',
    'Innovación Empresarial Individual','VIGENTE','PERSONA JURIDICA COMERCIAL','90123456-7',
    'SALMON DE LOS LAGOS SpA','Plataforma digital de trazabilidad para salmón',
    'Desarrollar plataforma de trazabilidad IoT para exportación de salmón',
    2025,'70000000','22000000','12000000','0',
    'Servicio','Pesca y acuicultura',
    'No','Masculino','No',NULL,NULL,
    'No',NULL,
    'Región de Los Lagos','Mediana','2012-08-05',
    'Alimentos (excepto vitivinícola)',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Internet de las Cosas (IoT)'
);

-- Fila 10: Tecnologías de la información / Metropolitana / 2023 / VIGENTE / No / Producto / NULL
INSERT INTO proyectos VALUES (
    'SEED-0010','Desarrolla innovación con I+D','Ley','Ley I+D',
    'Ley I+D','VIGENTE','PERSONA JURIDICA COMERCIAL','01234567-8',
    'SOFTWARECHILE SA','Motor de análisis predictivo para retail',
    'Desarrollar algoritmos de ML para predicción de demanda en retail',
    2023,'180000000','60000000','60000000','180000000',
    'Producto','Telecomunicaciones y tecnologías de la información',
    'No','Masculino','No',NULL,NULL,
    'No',NULL,
    'Región Metropolitana de Santiago','Grande','1995-10-11',
    'Tecnologías de la información',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Software de aplicación'
);

-- Fila 11: Forestal / Biobío / 2014 / FINALIZADO / No / Proceso / NULL
INSERT INTO proyectos VALUES (
    'SEED-0011','Desarrolla innovación','Subsidio','Innova Región',
    'Innova Región','FINALIZADO','PERSONA JURIDICA COMERCIAL','11234567-K',
    'PAPELERA PACIFICO SA','Proceso de blanqueo de celulosa sin cloro',
    'Desarrollar proceso ECF para blanqueo de celulosa con menor impacto ambiental',
    2014,'130000000','45000000','30000000','0',
    'Proceso','Forestal (incluye muebles y papel)',
    'No','Masculino','No',NULL,NULL,
    'No',NULL,
    'Región del Biobío','Grande','1972-05-14',
    'Forestal',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Química Verde (Green Chemestry)'
);

-- Fila 12: Agrícola / Maule / 2011 / FINALIZADO / No / Producto / NULL
INSERT INTO proyectos VALUES (
    'SEED-0012','Desarrolla innovación','Subsidio','Capital Semilla',
    'Capital Semilla','FINALIZADO','PERSONA JURIDICA COMERCIAL','22345678-1',
    'VINAS DEL SUR LTDA','Variedad de uva resistente a hongos para vino orgánico',
    'Desarrollar variedad de cepa resistente a botrytis para producción orgánica',
    2011,'15000000','4000000','0','0',
    'Producto','Vitivinicultura',
    'No','Masculino','No',NULL,NULL,
    'No',NULL,
    'Región del Maule','Microempresa','2007-12-01',
    'Agrícola',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Sin tendencia'
);

-- Fila 13: Biotecnológico / Valparaíso / 2017 / FINALIZADO / Sí / Producto / NULL
INSERT INTO proyectos VALUES (
    'SEED-0013','Desarrolla innovación con I+D','Subsidio','I+D Aplicada',
    'I+D Aplicada en Empresas','FINALIZADO','PERSONA JURIDICA COMERCIAL','33456789-2',
    'GENOMICA SUR SA','Kit de diagnóstico molecular para enfermedades de salmonidos',
    'Desarrollar herramienta de diagnóstico basada en PCR para patógenos del salmón',
    2017,'210000000','70000000','50000000','0',
    'Producto','Pesca y acuicultura',
    'No','Femenino','Sí','ODS14','ODS14-META1',
    'No',NULL,
    'Región de Valparaíso','Mediana','1999-03-22',
    'Biotecnológico',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Genómica y Edición de Genes'
);

-- Fila 14: Alimentos / Metropolitana / 2009 / FINALIZADO / No / Proceso / NULL
INSERT INTO proyectos VALUES (
    'SEED-0014','Desarrolla innovación','Subsidio','Innova Región',
    'Innova Región','FINALIZADO','PERSONA JURIDICA COMERCIAL','44567890-3',
    'CONSERVAS TRADICION SA','Mejora de línea de producción de conservas vegetales',
    'Optimizar el proceso de conservación de hortalizas para exportación',
    2009,'30000000','10000000','0','0',
    'Proceso','Alimentos (excepto producción de vino y derivados)',
    'No','Masculino','No',NULL,NULL,
    'No',NULL,
    'Región Metropolitana de Santiago','Mediana','1980-08-30',
    'Alimentos (excepto vitivinícola)',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Sin tendencia'
);

-- Fila 15: Minería / Atacama / 2022 / VIGENTE / Sí / Proceso / Habilitador para la EC
INSERT INTO proyectos VALUES (
    'SEED-0015','Desarrolla innovación con I+D','Subsidio','I+D Aplicada',
    'I+D Aplicada en Empresas','VIGENTE','PERSONA JURIDICA COMERCIAL','55678901-4',
    'COBRE VERDE SpA','Proceso hidrometalúrgico para recuperación de cobre de relaves',
    'Desarrollar proceso de lixiviación para recuperar cobre de relaves mineros',
    2022,'330000000','110000000','80000000','0',
    'Proceso','Minería y metalurgia extractiva',
    'No','Masculino','Sí','ODS12','ODS12-META3',
    'Sí','Recuperación de Recursos',
    'Región de Atacama','Grande','2008-03-10',
    'Minero',NULL,
    'Habilitador para la EC','R9 Recuperar','Recuperar cobre de relaves',
    'No',NULL,NULL,'Green Technologies (Tecnologías Verdes)'
);

-- Fila 16: Tecnologías de la información / Biobío / 2015 / FINALIZADO / No / Servicio / NULL
INSERT INTO proyectos VALUES (
    'SEED-0016','Consolida y Expande','Subsidio','Innovación Empresarial Individual',
    'Innovación Empresarial Individual','FINALIZADO','PERSONA JURIDICA COMERCIAL','66789012-5',
    'CONECTATECH LTDA','Plataforma SaaS de gestión de PYMES forestales',
    'Desarrollar software de gestión integral para empresas forestales medianas',
    2015,'28000000','8000000','0','0',
    'Servicio','Telecomunicaciones y tecnologías de la información',
    'No','Femenino','No',NULL,NULL,
    'No',NULL,
    'Región del Biobío','Pequeña','2011-07-19',
    'Tecnologías de la información',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Software de aplicación'
);

-- Fila 17: Alimentos / Los Lagos / 2020 / FINALIZADO / No / Proceso / NULL
INSERT INTO proyectos VALUES (
    'SEED-0017','Desarrolla innovación','Subsidio','Innova Región',
    'Innova Región','FINALIZADO','PERSONA JURIDICA COMERCIAL','77890123-6',
    'QUESOS PATAGONICOS SA','Proceso de maduración controlada de quesos artesanales',
    'Desarrollar protocolo de maduración para quesos artesanales de exportación',
    2020,'22000000','7000000','0','0',
    'Proceso','Alimentos (excepto producción de vino y derivados)',
    'No','Femenino','No',NULL,NULL,
    'No',NULL,
    'Región de Los Lagos','Pequeña','2000-04-18',
    'Alimentos (excepto vitivinícola)',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Sin tendencia'
);

-- Fila 18: Agrícola / Araucanía / 2024 / VIGENTE / Sí / Producto / Economía Circular
INSERT INTO proyectos VALUES (
    'SEED-0018','Desarrolla innovación con I+D','Subsidio','Crea y Valida',
    'Crea y Valida I+D+i Empresarial','VIGENTE','PERSONA JURIDICA COMERCIAL','88901234-7',
    'FERTIL NATURAL SpA','Biofertilizante a partir de residuos de la agroindustria',
    'Desarrollar y validar biofertilizante producido con residuos orgánicos',
    2024,'48000000','15000000','8000000','0',
    'Producto','Agropecuario (excepto fruticultura y vitivinicultura)',
    'Incentivo','Femenino','Sí','ODS2','ODS2-META3',
    'Sí','Suministro Circular',
    'Región de La Araucanía','Pequeña','2016-02-14',
    'Agrícola',NULL,
    'Economía Circular','R2 Reducir','Reducir residuos orgánicos de la agroindustria',
    'No',NULL,NULL,'Biotecnología'
);

-- Fila 19: Energético / Metropolitana / 2021 / VIGENTE / Sí / Proceso / NULL
INSERT INTO proyectos VALUES (
    'SEED-0019','Desarrolla innovación con I+D','Subsidio','I+D Aplicada',
    'I+D Aplicada en Empresas','VIGENTE','PERSONA JURIDICA COMERCIAL','99012345-8',
    'HIDRÓGENO CHILE SA','Electrolizador de bajo costo para producción de H2 verde',
    'Desarrollar electrolizador de membrana de intercambio protónico de bajo costo',
    2021,'500000000','170000000','120000000','0',
    'Proceso','Energía y minería',
    'No','Masculino','Sí','ODS7','ODS7-META2',
    'No',NULL,
    'Región Metropolitana de Santiago','Grande','2018-09-03',
    'Energético',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Clean Energy Technologies'
);

-- Fila 20: Tecnologías de la información / Valparaíso / 2013 / FINALIZADO / No / Producto / NULL
INSERT INTO proyectos VALUES (
    'SEED-0020','Desarrolla innovación','Subsidio','Capital Semilla',
    'Capital Semilla','FINALIZADO','Persona Jurídica constituida en Chile','10234567-9',
    'ROBOTICA VALPO SA','Brazo robótico para empaque en línea de alimentos',
    'Desarrollar robot colaborativo adaptado para líneas de empaque de alimentos',
    2013,'35000000','11000000','0','0',
    'Producto','Telecomunicaciones y tecnologías de la información',
    'No','Masculino','No',NULL,NULL,
    'No',NULL,
    'Región de Valparaíso','Pequeña','2009-11-25',
    'Tecnologías de la información',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Manufactura Avanzada (Advanced Manufacturing)'
);

-- Fila 21: Alimentos / Coquimbo / 2023 / VIGENTE / Sí / Producto / NULL
INSERT INTO proyectos VALUES (
    'SEED-0021','Desarrolla innovación con I+D','Subsidio','I+D Aplicada',
    'I+D Aplicada en Empresas','VIGENTE','PERSONA JURIDICA COMERCIAL','21345678-0',
    'PALTA ANDINA SA','Recubrimiento comestible para extender vida útil de paltas',
    'Desarrollar recubrimiento bioactivo que retarde la oxidación de paltas de exportación',
    2023,'62000000','20000000','10000000','0',
    'Producto','Alimentos (excepto producción de vino y derivados)',
    'No','Femenino','Sí','ODS12','ODS12-META1',
    'No',NULL,
    'Región de Coquimbo','Mediana','2006-07-07',
    'Alimentos (excepto vitivinícola)',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Alimentos Funcionales'
);

-- Fila 22: Minería / Antofagasta / 2012 / FINALIZADO / No / Proceso / NULL
INSERT INTO proyectos VALUES (
    'SEED-0022','Desarrolla innovación con I+D','Subsidio','I+D Aplicada',
    'I+D Aplicada en Empresas','FINALIZADO','PERSONA JURIDICA COMERCIAL','32456789-1',
    'EXPLOSIVOS INDUSTRIALES SA','Desarrollo de explosivo de bajo impacto ambiental',
    'Formular explosivo emulsificado con menores emisiones de nitrógeno',
    2012,'145000000','48000000','30000000','0',
    'Proceso','Minería y metalurgia extractiva',
    'No','Masculino','No',NULL,NULL,
    'No',NULL,
    'Región de Antofagasta','Grande','1968-04-20',
    'Minero',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Sin tendencia'
);

-- Fila 23: Biotecnológico / Biobío / 2025 / VIGENTE / Sí / Producto / NULL
INSERT INTO proyectos VALUES (
    'SEED-0023','Desarrolla innovación con I+D','Subsidio','Crea y Valida',
    'Crea y Valida I+D+i Empresarial','VIGENTE','PERSONA JURIDICA COMERCIAL','43567890-2',
    'BIOPHARMA CHILE SA','Anticuerpo monoclonal para tratamiento de mastitis bovina',
    'Desarrollar anticuerpo monoclonal terapéutico para mastitis en ganado lechero',
    2025,'280000000','95000000','70000000','0',
    'Producto','Agropecuario (excepto fruticultura y vitivinicultura)',
    'Incentivo','Femenino','Sí','ODS3','ODS3-META1',
    'No',NULL,
    'Región del Biobío','Mediana','2014-01-09',
    'Biotecnológico',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Desarrollo de Drogas (Drug development)'
);

-- Fila 24: Alimentos / Metropolitana / 2010 / FINALIZADO / No / Proceso / NULL
INSERT INTO proyectos VALUES (
    'SEED-0024','Desarrolla innovación','Subsidio','Innova Región',
    'Innova Región','FINALIZADO','PERSONA JURIDICA COMERCIAL','54678901-3',
    'CECINAS ARTIGIANO SA','Mejora de proceso de curado de cecinas artesanales',
    'Desarrollar proceso de curado de cecinas con reducción de nitratos',
    2010,'19000000','6000000','0','0',
    'Proceso','Alimentos (excepto producción de vino y derivados)',
    'No','Masculino','No',NULL,NULL,
    'No',NULL,
    'Región Metropolitana de Santiago','Pequeña','1992-03-15',
    'Alimentos (excepto vitivinícola)',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Sin tendencia'
);

-- Fila 25: Tecnologías de la información / Metropolitana / 2022 / VIGENTE / No / Servicio / NULL
INSERT INTO proyectos VALUES (
    'SEED-0025','Entorno para la innovación','Subsidio','Innovación Empresarial Individual',
    'Innovación Empresarial Individual','VIGENTE','PERSONA JURIDICA COMERCIAL','65789012-4',
    'CLOUDAGRO SpA','Servicio de analítica climática para agricultores via app móvil',
    'Desarrollar servicio de analítica climática usando datos satelitales y ML',
    2022,'58000000','19000000','10000000','0',
    'Servicio','Telecomunicaciones y tecnologías de la información',
    'Convocatoria','Femenino','No',NULL,NULL,
    'No',NULL,
    'Región Metropolitana de Santiago','Pequeña','2019-06-30',
    'Tecnologías de la información',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Inteligencia Artificial (IA)'
);

-- Fila 26: Forestal / Araucanía / 2018 / FINALIZADO / Sí / Proceso / Consultoría sostenibilidad
INSERT INTO proyectos VALUES (
    'SEED-0026','Desarrolla innovación','Subsidio','Innova Región',
    'Innova Región','FINALIZADO','ORG. SIN FINES DE LUCRO','76890123-5',
    'BOSQUE VIVO FUNDACION','Protocolo de manejo sustentable de bosque nativo',
    'Diseñar y validar protocolo de certificación para manejo de bosque nativo',
    2018,'25000000','8000000','0','0',
    'Proceso','Forestal (incluye muebles y papel)',
    'Convocatoria','Femenino','Sí','ODS15','ODS15-META1',
    'No',NULL,
    'Región de La Araucanía','Sin ventas','2004-09-12',
    'Forestal',NULL,
    'Consultoría o estudios para la sostenibilidad',NULL,NULL,
    'No',NULL,NULL,'Transferencia Tecnológica y Buenas Prácticas'
);

-- Fila 27: Alimentos / Maule / 2024 / VIGENTE / Sí / Producto / Economía Circular
INSERT INTO proyectos VALUES (
    'SEED-0027','Desarrolla innovación con I+D','Subsidio','I+D Aplicada',
    'I+D Aplicada en Empresas','VIGENTE','PERSONA JURIDICA COMERCIAL','87901234-6',
    'VINO CIRCULAR SA','Aprovechamiento de orujo de uva para ingredientes funcionales',
    'Extraer polifenoles de orujo de uva para producir ingredientes funcionales',
    2024,'75000000','25000000','15000000','0',
    'Producto','Alimentos (excepto producción de vino y derivados)',
    'No','Masculino','Sí','ODS12','ODS12-META4',
    'Sí','Recuperación de Recursos',
    'Región del Maule','Mediana','2003-11-23',
    'Alimentos (excepto vitivinícola)',NULL,
    'Economía Circular','R8 Reciclar','Valorizar residuos vitícolas',
    'No',NULL,NULL,'Alimentos Funcionales'
);

-- Fila 28: Energético / Coquimbo / 2016 / FINALIZADO / Sí / Proceso / Producción Sostenible
INSERT INTO proyectos VALUES (
    'SEED-0028','Renuévate','Subsidio','Innova Región',
    'Innova Región','FINALIZADO','PERSONA JURIDICA COMERCIAL','98012345-7',
    'SOLAR NORTE SA','Panel solar de bajo costo para zonas rurales aisladas',
    'Adaptar tecnología fotovoltaica de bajo costo para comunidades rurales sin red',
    2016,'42000000','14000000','0','0',
    'Proceso','Energía y minería',
    'No','Masculino','Sí','ODS7','ODS7-META3',
    'No',NULL,
    'Región de Coquimbo','Microempresa','2013-05-06',
    'Energético',NULL,
    'Producción Sostenible',NULL,NULL,
    'No',NULL,'Energía solar','Clean Energy Technologies'
);

-- Fila 29: Biotecnológico / Metropolitana / 2013 / FINALIZADO / No / Producto / NULL (Ley I+D)
INSERT INTO proyectos VALUES (
    'SEED-0029','Desarrolla innovación con I+D','Ley','Ley I+D',
    'Ley I+D','FINALIZADO','PERSONA JURIDICA COMERCIAL','09123456-K',
    'FERMENTACIONES SA','Enzima industrial para mejora de rendimiento en molienda',
    'Desarrollar mediante fermentación una enzima celulasa de alta eficiencia',
    2013,'310000000','100000000','70000000','310000000',
    'Producto','Alimentos (excepto producción de vino y derivados)',
    'No','Masculino','No',NULL,NULL,
    'No',NULL,
    'Región Metropolitana de Santiago','Grande','1988-06-28',
    'Biotecnológico',NULL,
    NULL,NULL,NULL,
    'No',NULL,NULL,'Biotecnología'
);

-- Fila 30: Agrícola / Valparaíso / 2019 / VIGENTE / No / Servicio / Innovación Social
INSERT INTO proyectos VALUES (
    'SEED-0030','Entorno para la innovación','Subsidio','Innovación Empresarial Individual',
    'Innovación Empresarial Individual','VIGENTE','Persona Natural','19234567-8',
    'CAMPO DIGITAL','App de gestión agrícola para pequeños agricultores',
    'Desarrollar aplicación móvil para planificación y registro de labores agrícolas',
    2019,'12000000','3000000','0','0',
    'Servicio','Telecomunicaciones y tecnologías de la información',
    'Convocatoria','Masculino','No',NULL,NULL,
    'No',NULL,
    'Región de Valparaíso','Microempresa','2017-03-01',
    'Agrícola',NULL,
    'Innovación Social',NULL,NULL,
    'No',NULL,NULL,'Software de aplicación'
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLA: leads
-- ─────────────────────────────────────────────────────────────────────────────
-- Columnas CRM editables: estado_contacto, fecha_contacto, metodo_contacto,
-- persona_contacto, telefono, email, notas, interes_nivel, proxima_accion,
-- fecha_proxima_accion, ultima_actualizacion.
-- monto_total_aprobado es REAL (no TEXT).

CREATE TABLE IF NOT EXISTS leads (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    rut_beneficiario        TEXT,
    razon_social            TEXT,
    sector_economico        TEXT,
    region                  TEXT,
    tramo_ventas            TEXT,
    cantidad_proyectos      INTEGER,
    monto_total_aprobado    REAL,
    proyectos_ids           TEXT,
    estado_contacto         TEXT DEFAULT 'No contactado',
    fecha_contacto          TEXT,
    metodo_contacto         TEXT,
    persona_contacto        TEXT,
    telefono                TEXT,
    email                   TEXT,
    notas                   TEXT,
    interes_nivel           TEXT,
    proxima_accion          TEXT,
    fecha_proxima_accion    TEXT,
    ultima_actualizacion    TEXT
);

-- 3 leads correspondientes a empresas presentes en proyectos

-- Lead 1: TECNODATA SA — contactada, interés alto
INSERT INTO leads (
    rut_beneficiario, razon_social, sector_economico, region, tramo_ventas,
    cantidad_proyectos, monto_total_aprobado, proyectos_ids,
    estado_contacto, fecha_contacto, metodo_contacto, persona_contacto,
    telefono, email, notas, interes_nivel, proxima_accion,
    fecha_proxima_accion, ultima_actualizacion
) VALUES (
    '45678901-2','TECNODATA SA','Tecnologías de la información',
    'Región Metropolitana de Santiago','Mediana',
    1, 120000000.0, 'SEED-0004',
    'Contactado','2026-03-15','Email','Juan Pérez',
    '+56912345678','jperez@tecnodata.cl',
    'Interesados en demostración del sistema de analítica',
    'alto','Reunión presencial',
    '2026-04-20','2026-03-15T10:30:00'
);

-- Lead 2: ALIMENTOS NUTRITIVOS SA — pendiente de contacto
INSERT INTO leads (
    rut_beneficiario, razon_social, sector_economico, region, tramo_ventas,
    cantidad_proyectos, monto_total_aprobado, proyectos_ids,
    estado_contacto, fecha_contacto, metodo_contacto, persona_contacto,
    telefono, email, notas, interes_nivel, proxima_accion,
    fecha_proxima_accion, ultima_actualizacion
) VALUES (
    '12345678-9','ALIMENTOS NUTRITIVOS SA','Alimentos (excepto vitivinícola)',
    'Región Metropolitana de Santiago','Mediana',
    1, 85000000.0, 'SEED-0001',
    'No contactado', NULL, NULL, NULL,
    NULL, NULL,
    'Empresa con proyecto de economía circular activo — prioridad media',
    'medio', 'Llamada telefónica',
    '2026-04-30','2026-04-07T09:00:00'
);

-- Lead 3: MINERA NORTE SpA — en negociación
INSERT INTO leads (
    rut_beneficiario, razon_social, sector_economico, region, tramo_ventas,
    cantidad_proyectos, monto_total_aprobado, proyectos_ids,
    estado_contacto, fecha_contacto, metodo_contacto, persona_contacto,
    telefono, email, notas, interes_nivel, proxima_accion,
    fecha_proxima_accion, ultima_actualizacion
) VALUES (
    '56789012-3','MINERA NORTE SpA','Minero',
    'Región de Antofagasta','Grande',
    1, 250000000.0, 'SEED-0005',
    'Contactado','2026-02-28','Teléfono','María González',
    '+56987654321','mgonzalez@mineranorte.cl',
    'Ya se realizó llamada inicial. Solicitan propuesta formal de servicios.',
    'alto','Enviar propuesta',
    '2026-04-10','2026-02-28T14:00:00'
);
