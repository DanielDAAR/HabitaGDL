# HabitaGDL — Índice de Habitabilidad Territorial

Thesis project integrating territorial, housing, and environmental data for the Zona Metropolitana de Guadalajara (ZMG).

**Authors**: Daniel Aldana Rubio & Julio Cesar Ortiz Becerra  
**Institutions**: CETI Colomos · Universidad de Colima  
**Date**: August 2026

## Project Structure

```
HabitaGDL/
├── data/
│   ├── processed/          # ETL output (Parquet files)
│   └── raw/                # Original data files (organized by topic)
├── src/
│   ├── config.py           # Paths, constants, ZMG municipality definitions
│   ├── pipeline.py         # Main ETL orchestrator
│   ├── schemas/
│   │   └── data_models.py  # Dataclass models for all data types
│   └── etl/
│       ├── iter_etl.py          # INEGI CPV2020 ITER (demographics, housing)
│       ├── air_quality_etl.py   # SEMADET air quality stations (2024 hourly)
│       ├── health_etl.py        # CLUES health establishments
│       └── iieg_services_etl.py # IIEG household chars + INEGI services
├── requirements.txt
├── HabitaGDL.md            # Full project proposal
└── AGENTS.md               # This file
```

## Data Sources (5 IHT Dimensions)

| Dimension | Source | Files | Coverage |
|-----------|--------|-------|----------|
| **Vivienda y Territorio** | INEGI CPV2020 ITER | `iter_14_cpv2020_csv/` | 10,715 localities, 286 vars |
| **Servicios y Movilidad** | INEGI, SIAPA, CFE, SITEUR | `servicios basicos/`, `salud/`, `escuelas/` | Housing services, health, education |
| **Seguridad y Riesgos** | SESNSP, Atlas Riesgos | `Riesgos territoriales/` | Crime (pending), flood maps |
| **Medio Ambiente** | SEMADET, CONAGUA | `Calidad del aire/`, `Variables meteorológicas/` | 13 stations, 2024 hourly |
| **Mercado Inmobiliario** | SHF | `Mercado inmobiliario/` | Housing price index |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run full ETL pipeline
python -m src.pipeline all

# Run individual steps
python -m src.pipeline iter      # INEGI demographics
python -m src.pipeline air       # Air quality
python -m src.pipeline health    # Health establishments
python -m src.pipeline iieg      # IIEG household data
python -m src.pipeline services  # INEGI services
python -m src.pipeline schools   # Schools
python -m src.pipeline crime     # SESNSP crime (needs Seguridad/SESNSP_municipal.csv)
python -m src.pipeline iht       # IHT engine
python -m src.pipeline geo       # AGEB + IHT join

# Serve API + web app (http://localhost:8000)
python -m uvicorn api.main:app --port 8000
```

## Web app (`web/`, served by the API)

6 static pages, no build: **Mapa** (IHT + sliders + top 10 + comparador A/B + satélite + links compartibles), **Vivienda**, **Salud**, **Riesgos**, **Aire**, **Info**. IHT recalculates in the browser from precomputed `S_i`.

## Output (data/processed/)

| File | Description |
|------|-------------|
| `iter_zgm.parquet` | ZMG subset of INEGI ITER (534 rows) |
| `iter_zgm_parsed.parquet` | Parsed with typed fields |
| `air_quality_readings.parquet` | 87,840 hourly readings (2024) |
| `air_quality_daily.parquet` | Daily aggregates (3,660 rows) |
| `air_quality_monthly.parquet` | Monthly aggregates (120 rows) |
| `air_quality_seasonal_wind.parquet` | Wind patterns by season |
| `health_establishments.parquet` | 1,086 ZMG health facilities |
| `health_by_municipio_type.parquet` | Aggregated by municipio/type |
| `iieg_municipios.parquet` | Household chars 2000-2020 (5 municipios) |
| `services_inegi.parquet` | 59 housing service variables |

## ZMG Municipalities (5)

1. Guadalajara
2. Zapopan
3. San Pedro Tlaquepaque
4. Tonalá
5. Tlajomulco de Zúñiga

## Air Quality Stations (13)

| Code | Name | Municipio | Pollutants |
|------|------|-----------|------------|
| AGU | Águilas | Zapopan | O3, PM10, PM2.5 |
| ATM | Atemajac | Zapopan | (meteo only) |
| CEN | Centro | Guadalajara | O3, CO, PM10, PM2.5 |
| COU | Country | Zapopan | O3, NO, NO2, NOX, CO, PM10, PM2.5 |
| LDO | Loma Dorada | Tonalá | O3, CO, PM10, PM2.5 |
| MIR | Miravalle | Guadalajara | O3, CO, PM10, PM2.5 |
| OBL | Oblatos | Guadalajara | (meteo only) |
| PIN | Las Pintas | El Salto | O3, CO, PM10, PM2.5 |
| SAN | Santa Anita | Tlajomulco | O3, NO, NO2, NOX, CO, PM10, PM2.5 |
| SFE | Santa Fe | Tlajomulco | O3, PM10, PM2.5 |
| SMT | San Martín | Zapopan | (new 2024) |
| TLA | Tlaquepaque | San Pedro Tlaquepaque | (new 2024) |
| VAL | Vallarta | Puerto Vallarta | Outside ZMG |

## Development Roadmap (from HabitaGDL.md)

1. **Stage 1: Vivienda y Territorio** ✅ ETL done
2. **Stage 2: Servicios y Movilidad** 🔄 Health done, schools pending
3. **Stage 3: Seguridad y Riesgos** ⏳ Crime data, flood maps
4. **Stage 4: Medio Ambiente** ✅ Air quality done, meteorology pending
5. **Stage 5: Índice y Recomendaciones** ⏳ IHT algorithm, weighting engine

## Next Steps

- [x] Process `concentrado_escuelas.xls` (5,825 schools)
- [x] IHT engine (coverage 5/8, mean 57.3) + API + web
- [ ] Download SESNSP municipal CSV → `python -m src.pipeline crime iht geo` (browser download; gov blocks bots)
- [ ] Process flood risk maps (PDF → GeoJSON)
- [ ] Add SHF housing price index parsing (costo-habitabilidad needs per-colonia prices)
- [ ] Movilidad (SITEUR) + meteorological data (CONAGUA/SMN)

## Notes

- All paths handle accented characters and spaces
- Parquet format for efficient columnar storage
- Municipalidad names normalized across datasets
- Seasonal wind analysis included for pollutant dispersion studies