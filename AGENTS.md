# AGENTS.md — HabitaGDL

## What this repo is

**HabitaGDL** (Índice de Habitabilidad Territorial) — a thesis project integrating territorial, housing, and environmental data for the Zona Metropolitana de Guadalajara. Authors: Daniel Aldana Rubio & Julio Cesar Ortiz Becerra (CETI Colomos · Universidad de Colima, Aug 2026).

Remote: `https://github.com/DanielDAAR/HabitaGDL.git`

Evolving project: data + proposal + Python ETL (`src/`) + FastAPI backend (`api/`, reads Parquet direct, no DB) + 6-page static web (`web/`, MapLibre, client-side IHT recalc). No build system, tests, or CI yet.

## Key documents

- **`HabitaGDL.md`** — Full project proposal (objectives, data sources, 5-stage plan, IHT methodology)
- **`Habitagdl Arquitectura.md`** — Adapted architecture: MVC logic + Fase 0 (Parquet + FastAPI + CDN + client compute), PostGIS/serverless deferred to Fase 2
- **`CONTEXTO_APP.md`** — Frontend spec (routes, components, API contract)
- **`README.md`** — Project overview, quick start, data dictionary
- **`src/config.py`** — All paths, constants, ZMG definitions, station metadata
- **`.agents/product-marketing-context-global.md`** — LATAM/MXN product context for marketing skills

## Project structure

```
src/
├── config.py           # Paths, ZMG municipios, AQ stations, pollutants
├── pipeline.py         # Main ETL orchestrator (CLI: python -m src.pipeline <step>)
├── schemas/
│   └── data_models.py  # Dataclasses + norm_mun + MunicipioZMG
├── iht/
│   ├── engine.py       # IHT motor: S_i 0-100, cobertura 5 (6 con SESNSP)
│   └── ageb_join.py    # Join IHT×AGEB → iht_ageb.geojson
└── etl/
    ├── iter_etl.py              # INEGI CPV2020 ITER (demographics, housing)
    ├── air_quality_etl.py       # SEMADET air quality (13 stations, 2024 hourly)
    ├── health_etl.py            # CLUES health establishments (1,086 in ZMG)
    ├── schools_etl.py           # SIGED schools (5,825)
    ├── ageb_etl.py              # AGEB polygons (1,724)
    ├── crime_etl.py             # SESNSP municipal (needs Seguridad/SESNSP_municipal.csv, soft-fails)
    └── iieg_services_etl.py     # IIEG household chars + INEGI services
api/
├── main.py             # FastAPI: localidades, iht, salud, escuelas, aire, seguridad, geo + serves web/
web/                   # 6 static pages (MapLibre CDN, no build): index, vivienda, salud-educacion, seguridad-riesgos, aire, metodologia
```

## Development roadmap (from `HabitaGDL.md`)

| Stage | Focus | Status |
|-------|-------|--------|
| 1 | Vivienda y Territorio (INEGI ITER) | ✅ ETL done (534 ZMG, 286 vars) |
| 2 | Servicios y Movilidad | ✅ Health (1,086) + schools (5,825) done, movilidad pendiente |
| 3 | Seguridad y Riesgos | 🔄 Crime ETL coded, needs `Seguridad/SESNSP_municipal.csv` (official download, gov blocks bots); flood PDF pending vectorization |
| 4 | Medio Ambiente | ✅ Air quality done (114,192 lecturas, 13 estaciones) |
| 5 | Índice y Recomendaciones | ✅ IHT engine done (cobertura 5/8, media 57.3; 6/8 con SESNSP) + API + web 6 páginas; costo-hab pendiente (no hay precios por colonia) |

## Commands

```bash
# Install deps
pip install -r requirements.txt

# Run full pipeline
python -m src.pipeline all

# Individual steps
python -m src.pipeline iter      # INEGI ITER (534 ZMG localities)
python -m src.pipeline air       # Air quality (114K hourly → daily/monthly/seasonal)
python -m src.pipeline health    # Health establishments (1,086 in ZMG)
python -m src.pipeline iieg      # IIEG household data (5 municipios)
python -m src.pipeline services  # INEGI services
python -m src.pipeline schools   # Schools (5,825)
python -m src.pipeline crime     # SESNSP crime (soft-fails without CSV)
python -m src.pipeline iht       # IHT engine → iht_localidad.parquet
python -m src.pipeline geo       # AGEB + IHT×AGEB join → iht_ageb.geojson

# Serve API + web (http://localhost:8000)
python -m uvicorn api.main:app --port 8000
```

## Processed output (`data/processed/`)

| File | Rows | Description |
|------|------|-------------|
| `iter_zgm.parquet` | 534 | ZMG subset of INEGI ITER (286 vars) |
| `iter_zgm_parsed.parquet` | 534 | Typed fields via dataclass |
| `air_quality_readings.parquet` | 114,192 | Hourly readings 2024 |
| `air_quality_daily.parquet` | 4,758 | Daily aggregates |
| `air_quality_monthly.parquet` | 156 | Monthly aggregates |
| `air_quality_seasonal_wind.parquet` | 382 | Wind patterns by season |
| `air_quality_stations.parquet` | 13 | Station catalog |
| `health_establishments.parquet` | 1,086 | ZMG health facilities |
| `health_by_municipio_type.parquet` | 135 | Aggregated by municipio/type |
| `escuelas.parquet` | 5,825 | Schools with coords |
| `escuelas_por_municipio_nivel.parquet` | 92 | Aggregated by municipio/nivel |
| `ageb_zmg.parquet` / `.geojson` | 1,724 | AGEB polygons |
| `iht_localidad.parquet` | 529 | IHT + 8 S_i per locality |
| `iht_ageb.geojson` | 1,724 | IHT joined to AGEB (map layer) |
| `crime_municipio.parquet` | — | SESNSP by municipio/año/delito (needs CSV) |
| `iieg_municipios.parquet` | 5 | Household chars 2000-2020 |
| `services_inegi.parquet` | 15 | Housing service variables |
| `health_summary.json` / `crime_summary.json` | — | Summary stats |

## Data layout (raw)

| Directory | Contents |
|---|---|
| `Demografía, vivienda y territorio/` | INEGI CPV2020 ITER (CSV + dict + catalogs + meta) |
| `Calidad del aire/` | `BD_2024.xlsx` (13 stations, PM2.5/PM10/O3/NO2 + meteo) |
| `Salud y educación/` | `ESTABLECIMIENTO_SALUD_202606.xlsx` (CLUES), `concentrado_escuelas.xls` |
| `servicios basicos y infrastuctura/` | `INEGI_exporta_*.xls` |
| `Información estatal integrada/` | `IIEGHogCaracteristicas.xlsx` |
| `Mercado inmobiliario/` | `I_ndice_SHF_T2_2026.pdf` |
| `Riesgos territoriales/` | `Inundaciones70x60.pdf` |
| `Mapas/` | Empty — placeholder for spatial layers |
| `Variables meteorológicas/` | Empty — placeholder for wind/temp/precip |

## Main dataset

`Demografía, vivienda y territorio/iter_14_cpv2020_csv/iter_14_cpv2020/conjunto_de_datos/conjunto_de_datos_iter_14CSV20.csv`

- ~10,715 rows, Jalisco localities (AGEB/municipality level)
- 286 columns (demographics, housing, education, economic, etc.)
- Companion: dictionary, catalogs, metadata

## Scope & constraints

- Geography: 5 ZMG municipios (Guadalajara, Zapopan, San Pedro Tlaquepaque, Tonalá, Tlajomulco de Zúñiga)
- Formats: CSV/XLS/XLSX/PDF — no databases yet
- Python 3.14+ for ETL/analysis (pandas, pyarrow)
- Public sources: INEGI, IIEG, SEMADET, SIAPA, CFE, SESNSP, SHF, CONAGUA
- **Path handling**: names contain spaces and accented characters — use `pathlib` and raw strings
- Municipality names differ across datasets — normalized via `ZMG_MUNICIPIOS` / `ZMG_MUNICIPIOS_HEALTH` / `ZMG_MUNICIPIOS_ALT` in `config.py`