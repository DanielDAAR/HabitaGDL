# AGENTS.md — HabitaGDL

## What this repo is

**HabitaGDL** (Índice de Habitabilidad Territorial) — a thesis project integrating territorial, housing, and environmental data for the Zona Metropolitana de Guadalajara. Authors: Daniel Aldana Rubio & Julio Cesar Ortiz Becerra (CETI Colomos · Universidad de Colima, Aug 2026).

Remote: `https://github.com/DanielDAAR/HabitaGDL.git`

Evolving project: started as data + proposal, now includes Python ETL pipeline (`src/`). No build system, tests, or CI yet.

## Key documents

- **`HabitaGDL.md`** — Full project proposal (objectives, data sources, 5-stage plan, IHT methodology)
- **`README.md`** — Project overview, quick start, data dictionary
- **`src/config.py`** — All paths, constants, ZMG definitions, station metadata

## Project structure

```
src/
├── config.py           # Paths, ZMG municipios, AQ stations, pollutants
├── pipeline.py         # Main ETL orchestrator (CLI: python -m src.pipeline <step>)
├── schemas/
│   └── data_models.py  # Dataclasses: IterLocalidad, AirQualityReading, HealthEstablishment, etc.
└── etl/
    ├── iter_etl.py              # INEGI CPV2020 ITER (demographics, housing)
    ├── air_quality_etl.py       # SEMADET air quality (13 stations, 2024 hourly)
    ├── health_etl.py            # CLUES health establishments (1,086 in ZMG)
    └── iieg_services_etl.py     # IIEG household chars + INEGI services
```

## Development roadmap (from `HabitaGDL.md`)

| Stage | Focus | Status |
|-------|-------|--------|
| 1 | Vivienda y Territorio (INEGI ITER) | ✅ ETL done |
| 2 | Servicios y Movilidad | 🔄 Health done, schools pending |
| 3 | Seguridad y Riesgos | ⏳ Crime, flood maps |
| 4 | Medio Ambiente | ✅ Air quality done, meteorology pending |
| 5 | Índice y Recomendaciones | ⏳ IHT algorithm |

## Commands

```bash
# Install deps
pip install -r requirements.txt

# Run full pipeline
python -m src.pipeline all

# Individual steps
python -m src.pipeline iter      # INEGI ITER (534 ZMG localities)
python -m src.pipeline air       # Air quality (87K hourly → daily/monthly/seasonal)
python -m src.pipeline health    # Health establishments (1,086 in ZMG)
python -m src.pipeline iieg      # IIEG household data (5 municipios)
python -m src.pipeline services  # INEGI services (59 variables)
```

## Processed output (`data/processed/`)

| File | Rows | Description |
|------|------|-------------|
| `iter_zgm.parquet` | 534 | ZMG subset of INEGI ITER |
| `iter_zgm_parsed.parquet` | 534 | Typed fields via dataclass |
| `air_quality_readings.parquet` | 87,840 | Hourly readings 2024 |
| `air_quality_daily.parquet` | 3,660 | Daily aggregates |
| `air_quality_monthly.parquet` | 120 | Monthly aggregates |
| `air_quality_seasonal_wind.parquet` | 369 | Wind patterns by season |
| `health_establishments.parquet` | 1,086 | ZMG health facilities |
| `health_by_municipio_type.parquet` | 135 | Aggregated by municipio/type |
| `iieg_municipios.parquet` | 5 | Household chars 2000-2020 |
| `services_inegi.parquet` | 59 | Housing service variables |
| `health_summary.json` | — | Summary stats |

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