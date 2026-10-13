HabitaGDL: Índice de Habitabilidad Territorial — Propuesta de Proyecto, Fuentes y Historias de Usuario
Autores: Daniel Alejandro Aldana Rubio, Julio Cesar Ortiz Becerra
Instituciones: Centro de Enseñanza Técnica Industrial (CETI) Colomos · Universidad de Colima
Fecha: Agosto de 2026
1. Resumen Ejecutivo y Propuesta de Proyecto
Al buscar dónde vivir en la Zona Metropolitana de Guadalajara (ZMG), la información disponible se concentra casi siempre en el precio. Los portales inmobiliarios no explican el contexto de servicios, transporte, salud, seguridad, riesgos territoriales o medio ambiente. HabitaGDL integra todos estos datos oficiales y meteorológicos (incluyendo patrones de viento y dispersión de contaminantes) en un solo sistema interactivo, ofreciendo una calificación objetiva (Índice de Habitabilidad Territorial - IHT) del 0 al 100 y evaluando la relación real entre costo y calidad de vida.
2. Fuentes de Datos Oficiales y Enlaces Directos
Toda la información ingresada al sistema mantiene una trazabilidad completa con sus fuentes originales:
Categoría
Fuentes Oficiales y Archivos
Enlaces de Origen
 
Demografía, vivienda y territorio
INEGI (Censo CPV 2020 / AGEB, ENIGH 2024, DENUE). 
https://www.inegi.org.mx/programas/ccpv/2020/
https://www.inegi.org.mx/app/descarga/
https://www.inegi.org.mx/app/mapa/denue/
https://www.inegi.org.mx/programas/enigh/nc/2024/
Servicios básicos e infraestructura
SIAPA, CFE, Secretaría de Transporte Jalisco, SITEUR, Mi Macro, IIEG.
https://www.inegi.org.mx/sistemas/Olap/Proyectos/bd/censos/cpv2020/Viviendas.asp
https://iieg.gob.mx/ns/?page_id=36831
Salud y educación
Secretaría de Salud Jalisco, SIGED/SEP, CLUES (1,086 establecimientos). Archivo: concentrado_escuelas.xls.
https://ssj.jalisco.gob.mx/salud-publica/estadisticas-e-indicadores/directorio-de-servicios-medicos-asistenciales-y-administrativos-del-sector-salud
https://siged.sep.gob.mx/SIGED/escuelas.html
http://www.dgis.salud.gob.mx/contenidos/intercambio/clues_gobmx.html
Seguridad
SESNSP, Fiscalía del Estado de Jalisco (Adquisición vía Web Scraping con Python).
Web Scraping oficial / Reportes públicos
Riesgos territoriales
IIEG, Atlas de Riesgos, Protección Civil Jalisco (Inundaciones).
https://iieg.gob.mx/ns/?page_id=132
Calidad del aire
SEMADET Jalisco, Red de Monitoreo Atmosférico (87,840 lecturas), SINAICA.
https://aire.jalisco.gob.mx/Dhistoricos
Variables meteorológicas
CONAGUA – Servicio Meteorológico Nacional (SMN) y SEMADET (Viento, Temp, Humedad, Precipitación).
https://smn.conagua.gob.mx/tools/GUI/EMAS.php
Mercado inmobiliario
SHF (Índice de precios), RUV, portales inmobiliarios públicos.
https://www.gob.mx/shf/documentos/indice-shf-de-precios-de-la-vivienda-en-mexico-2025-a-2026
Información estatal integrada
IIEG (Instituto de Información Estadística y Geográfica de Jalisco).
https://iieg.gob.mx/ns/?page_id=7489
https://iieg.gob.mx/ns/?page_id=25306

3. Cálculo del Índice de Habitabilidad Territorial (IHT)
El IHT es una métrica compuesta (escala 0-100) construida sobre 8 dimensiones ponderadas:
IHT = ∑ (wi × Si)     donde     ∑ wi = 1.0
Donde Si es el puntaje de la dimensión (normalizado a 0-100) y wi es el peso configurado por el usuario.
Métrica de Costo-Habitabilidad:
Score Costo-Habitabilidad = IHT / (Precio Normalizado)
4. Historias de Usuario (User Stories) y Criterios de Aceptación
US-01: Visualización de características de vivienda
Como buscador de vivienda, quiero ver indicadores de vivienda por zona para que pueda evaluar la calidad de la infraestructura habitacional.
Criterios de Aceptación:
Muestra variables clave: Viviendas con agua entubada, drenaje, viviendas con energia electrica, vivienda con internet, Vivienda con piso firme, con refri, lavadora, automovil, moto, con bici y se mostraran advertencias de indicadores bajos para servicios ineficientes en rojo.
Permite comparar entre localidades y municipios ZMG mostraran dos paneles con los indicadores ordenados y clasificados por color para una facil comparacion.


US-02: Localización de establecimientos de salud
Como familia con niños, quiero ver hospitales, clínicas y centros de salud cercanos a una zona para que pueda evaluar acceso a servicios médicos.
Criterios de Aceptación:
Muestra un top 10 de los hospitales mas cercanos, poniendo su distancia, la accesibilidad (si es pública o privada) y en caso de ser privada promedio de costos .
Filtro por tipo: Hospitalización, Consulta Externa, Asistencia Social, Apoyo.
Filtro por tipología: Hospital General, Centro de Salud, Clínica, etc.
Mapa interactivo con marcadores por tipo de establecimiento.
US-03: Acceso a escuelas por zona
Como padre de familia, quiero ver escuelas (públicas y privadas) por nivel educativo cerca de una localidad para que pueda evaluar opciones educativas para mis hijos.
Criterios de Aceptación:

Muestra un top 10 de las escuelas mas cercanas, poniendo su distancia, la accesibilidad (si es pública o privada) y en caso de ser privada promedio de costos.
Filtro por nivel: preescolar, primaria, secundaria, media superior, superior y se actualiza el top 10.
Filtro por sostenimiento: público, privado se actualiza el top 10.

US-04: Servicios básicos por vivienda
Como comprador de vivienda, quiero ver porcentaje de viviendas con agua, drenaje, electricidad, internet por zona para que pueda comparar infraestructura básica entre opciones.
Criterios de Aceptación:


Indicadores clave: lista la disponibilidad de agua entubada, drenaje, energía eléctrica, internet, cisterna/aljibe con colores.
Presentación como % de viviendas con servicio / total viviendas en la localidad.
Comparación entre municipios ZMG en tabla comparativa de forma ordenada.

US-05: Visualización de incidencia delictiva por municipio
Como ciudadano preocupado por seguridad, quiero ver tasas de delitos por municipio y tipo de delito para que pueda comparar seguridad entre zonas de la ZMG.
Criterios de Aceptación:

Métricas: delitos por 100,000 habitantes (tasa).
Filtros: tipo de delito, año, municipio.
Se muestra una gráfica de barras laterales que organizan la información por el tipo de delito.
US-06: Mapa de riesgos de inundación
Como comprador de vivienda, quiero ver zonas susceptibles a inundación superpuestas a localidades para que pueda evitar zonas de alto riesgo.
Criterios de Aceptación:


Integra cartografía oficial.
Capas: susceptibilidad alta, media, baja, sin riesgo.
Cruce espacial: localidad -> riesgo de inundación (sí/no, nivel).
se muestra un indicador del riesgo de inundación a través de colores por nivel y en gris en caso de no haber 

US-07: Calidad del aire histórica por estación
Como persona con sensibilidad respiratoria, quiero ver promedios diarios/mensuales de PM2.5, PM10, O3, NO2 por estación de monitoreo para que pueda identificar zonas con mejor calidad del aire.
Criterios de Aceptación:


Contaminantes: O3 (ppm), NO2 (ppm), PM10 (µg/m³), PM2.5 (µg/m³), SO2, CO; solamente se mostrarán de manera general los parámetros que estén consideradamente altos y en caso de querer ver todos se mostrará una lista ordenada con colores de cada parámetro.
Filtro por rango de fechas.
Se podrían comparar con otras zonas a través de una tabla comparativa que muestra de manera organizada los datos y por colores.


US-8: Cálculo del Índice de Habitabilidad Territorial (IHT)
Como tomador de decisiones, quiero ver un índice compuesto (0-100) que integre todas las dimensiones de habitabilidad por localidad para que pueda comparar zonas objetivamente.
Criterios de Aceptación:

se clasificaron 8 dimensiones: Vivienda, Servicios, Movilidad, Salud, Educación, Seguridad, Riesgos, Ambiente.

Se podrá configurar los pesos mediante varios range slider.
Se actualiza el índice cada que haya un modificación en los pesos



US-9: Métrica Costo-Habitabilidad y recomendaciones
Como buscador de vivienda con presupuesto definido, quiero ver zonas con mejor relación costo-habitabilidad para que pueda identificar oportunidades de valor.
Criterios de Aceptación:
Input: presupuesto máximo (compra/renta), pesos IHT personalizados.
Output: ranking de localidades por score Costo-Habitabilidad = IHT / (precio normalizado).
Se podrán filtrar por: tipo de vivienda, metros cuadrados, municipio.
Top 10 zonas "mejor valor" Teniendo en cuenta todos los inputs se mostrarán en una lista en el cual si le picas a una colonia se va a mostrará a través de una ventana emergente el desglose de su índice y tendras un link para ver el desglose de toda la información (habitacional,calidad de vida etc) en su ventana específico.




