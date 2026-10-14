# HabitaGDL — Arquitectura de Software e Infraestructura de Despliegue

**Proyecto:** HabitaGDL — Índice de Habitabilidad Territorial
**Autores:** Daniel Alejandro Aldana Rubio, Julio Cesar Ortiz Becerra
**Instituciones:** CETI Colomos · Universidad de Colima
**Fecha:** Agosto de 2026

---

## 1. Resumen Ejecutivo

El presente documento establece la propuesta de arquitectura de software e infraestructura para el sistema HabitaGDL, cuyo objetivo es integrar, procesar y analizar información urbana multidimensional (datos censales, ambientales, delictivos, de riesgos y movilidad) en la Zona Metropolitana de Guadalajara (ZMG).

Para garantizar un alto rendimiento en el procesamiento espacial, permitir el recálculo dinámico e inmediato del Índice de Habitabilidad Territorial (IHT) y mantener una gestión eficiente de los recursos operativos, se propone un esquema híbrido. Este esquema combina el Patrón de Diseño Modelo-Vista-Controlador (MVC) para la estructuración lógica del sistema, y una Arquitectura Cliente-Servidor Basada en Cómputo Bajo Demanda (Serverless) para el esquema de despliegue e infraestructura en la nube.

> Fórmula base del índice:
>
> `IHT = Σ(w_i × S_i)` donde `Σ w_i = 1.0` y `S_i ∈ [0, 100]`

---

## 2. Descripción Conceptual del Sistema

La arquitectura propuesta separa rigurosamente la organización lógica del código del modelo de ejecución y hospedaje, asegurando un desarrollo modular y una operación escalable.

```text
+-----------------------------------------------------------------------------------+
|                                 VISTA (View)                                      |
|  - Capa de Presentación e Interfaz de Usuario                                     |
|  - Distribuida mediante Red de Entrega de Contenidos (CDN)                        |
|  - Motor de Cálculo Local: Recalcula el IHT en el navegador del usuario           |
+-----------------------------------------------------------------------------------+
                                          │
                            Peticiones HTTP │ Respuestas JSON / Vectoriales
                                          ▼
+-----------------------------------------------------------------------------------+
|                             CONTROLADOR (Controller)                              |
|  - Funciones de Servidor Ejecutadas Bajo Demanda (Serverless)                     |
|  - Valida solicitudes, gestiona la lógica de entrada y coordina consultas         |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                                MODELO (Model)                                     |
|  - Lógica de Negocio y Reglas de Normalización Territorial (S_i)                  |
|  - Base de Datos Espacial Administrada (Consultas y Geoprocesamiento)             |
|  - Pipeline de Extracción, Transformación y Carga de Datos (ETL Offline)          |
+-----------------------------------------------------------------------------------+
```

---

## 3. Estructura y Funcionamiento del Sistema (Adaptada a lo construido)

> Decisión de compatibilidad: se mantiene MVC como organización lógica.
> El despliegue se adapta a lo real del repo: ETL Python offline + Parquet
> en `data/processed/` + API ligera FastAPI + cálculo IHT en cliente.
> PostGIS administrado y funciones serverless puras pasan a Fase 2 (escalamiento futuro).

### 3.1 Patrón de Organización Lógica: Modelo-Vista-Controlador (MVC)

* **Modelo (Model) — ya construido:** `src/etl/*_etl.py` + `src/iht/engine.py`.
  Normaliza a `S_i ∈ [0, 100]` y guarda `iht_localidad.parquet` (529 filas,
  cobertura 5/8: vivienda, servicios, salud, educación, ambiente;
  movilidad/seguridad/riesgos = NaN hasta Etapas 2-3).
* **Controlador (Controller) — en construcción:** `api/main.py` (FastAPI).
  Lee Parquet directo con pandas/DuckDB, sin PostGIS. Expone `S_i` por zona.
* **Vista (View) — siguiente paso:** SPA React/Next + MapLibre en CDN.
  Recibe matriz liviana de `S_i` y recalcula `IHT = Σ w_i S_i` en browser.

### 3.2 Modelo de Despliegue: Fase 0 (MVP tesis) → Fase 2 (escalamiento)

**Fase 0 — lo que se implementa ahora (cero costo):**

* **Vista:** SPA estática en CDN (Vercel/Netlify/GitHub Pages).
* **Controlador:** un solo servicio FastAPI + Uvicorn (`api/main.py`) que lee
  `data/processed/*.parquet` con pandas. Sin connection pooler (no hay DB).
* **Modelo:** ETL offline `python -m src.pipeline all` + `iht_localidad.parquet`
  + `ageb_zmg.geojson` / `iht_ageb.geojson` ya generados.
* **Recálculo IHT:** en navegador, con `S_i` precargados (< 200 ms, sin red).

**Fase 2 — solo si el tráfico lo exige (fuera del alcance de tesis):**

* Migrar Parquet → PostGIS administrado + pooler.
* Partir FastAPI en funciones bajo demanda.
* CI/CD automático a la nube.

---

## 4. Justificación Técnica y Beneficios

### 4.1 Ventajas de la Organización Lógica con MVC

* **Desacoplamiento y Desarrollo Paralelo:** Permite dividir el trabajo técnico de forma eficiente. La interfaz gráfica (Vista) puede modificarse o rediseñarse sin alterar los algoritmos de cruce espacial ni las consultas almacenadas en el Modelo.
* **Trazabilidad Metodológica y Rigor Académico:** Al aislar los algoritmos de normalización e integración dentro del Modelo, resulta sencillo auditar la metodología del IHT, verificar las fuentes de origen de cada dato y documentar el proceso ante evaluaciones técnicas.
* **Reutilización de Componentes:** Las funciones de normalización espacial del Modelo pueden ser reutilizadas por diferentes controladores para generar reportes en distintos formatos (vistas interactivas, reportes imprimibles o APIs de consulta).

### 4.2 Ventajas de la Infraestructura Cómputo Bajo Demanda (Serverless)

* **Optimización Total de Costos Operativos:** Al no requerir un servidor encendido continuamente las 24 horas, se eliminan los costos fijos de infraestructura. El consumo de cómputo ocurre estrictamente cuando un usuario realiza consultas.
* **Cero Mantenimiento de Infraestructura:** No requiere la administración manual de sistemas operativos, parches de seguridad, servidores web ni balanceadores de carga. Toda la atención del equipo se enfoca en el análisis territorial y la lógica del proyecto.
* **Despliegue Continuo Automatizado (CI/CD):** La infraestructura permite integrar pipelines de actualización automática: cada modificación validada en el repositorio de código se compila y despliega en la nube en cuestión de segundos.
* **Escalabilidad Elástica:** Ante un incremento repentino en el número de usuarios simultáneos, el sistema crea instancias de ejecución paralelas en tiempo real, evitando caídas o saturación del servicio.

### 4.3 Estrategia de Rendimiento en el Cliente (Client-Side Computation)

Para maximizar la fluidez de la plataforma, el sistema adopta un modelo de ejecución distribuido:

* La función de backend bajo demanda envía una matriz liviana con los valores `S_i` (puntajes normalizados por dimensión) para cada zona urbana.
* Cuando el usuario ajusta las barras de prioridad (`w_i`), el recálculo de la fórmula `IHT = Σ w_i S_i` se ejecuta directamente en el navegador del cliente.
* Esto elimina la latencia de red, permitiendo que la coloración del mapa se actualice en tiempo real (< 16 ms) a medida que el usuario interactúa con la interfaz.

---

## 5. Matriz de Componentes de la Arquitectura

| Componente del Proyecto | Capa MVC | Función Conceptual | Modelo de Ejecución / Despliegue |
|---|---|---|---|
| Censo e Indicadores Espaciales | Modelo | Almacenamiento de vectoriales urbanos y tabulares censales. | Base de Datos Espacial Administrada |
| Normalización y Cruces (S_i) | Modelo | Algoritmos de escalamiento y uniones espaciales. | Pipeline ETL + Base de Datos Espacial |
| Endpoints de Consulta por Zona | Controlador | Recepción de filtros, autenticación y coordinación de respuesta. | Funciones de Servidor Bajo Demanda (Serverless) |
| Interfaz, Mapas y Gráficas | Vista | Renderizado de mapas de calor, sliders e indicadores visuales. | Red de Distribución de Contenidos (CDN) |
| Recálculo Interactivo del IHT | Vista / Cliente | Operación matemática `IHT = Σ w_i S_i` en tiempo real. | Procesamiento Local (Navegador del Usuario) |

---

## 6. Plan de Implementación (Adaptado al avance real)

* **Fase 0 — Hecho:** ETL ITER + aire + salud + escuelas + IIEG + servicios
  (`data/processed/` 18 archivos), motor IHT v1 5/8 dims, join IHT×AGEB
  (`ageb_zmg.geojson`, `iht_ageb.geojson`).
* **Fase 1 — En curso:** API FastAPI `api/main.py` (este commit): sirve `S_i`,
  top cercanos salud/escuelas por haversine, estaciones y series diarias de aire.
* **Fase 2 — Siguiente:** Vista (6 páginas: `/`, `/vivienda`, `/salud-educacion`,
  `/seguridad-riesgos`, `/aire`, `/metodologia`) + sliders `w_i` con recálculo cliente.
* **Fase 3 — Fuera de tesis:** PostGIS + serverless + CI/CD + seguridad/movilidad/riesgos
  reales cuando haya datos SESNSP/SITEUR e inundación vectorizada.
