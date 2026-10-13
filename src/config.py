# HabitaGDL - Project configuration
# Data paths and constants

from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = BASE_DIR  # Original data is in root subdirectories
PROCESSED_DIR = DATA_DIR / "processed"

# Raw data paths
PATHS = {
    "iter_csv": RAW_DIR / "Demografía, vivienda y territorio" / "iter_14_cpv2020_csv" / "iter_14_cpv2020" / "conjunto_de_datos" / "conjunto_de_datos_iter_14CSV20.csv",
    "iter_dict": RAW_DIR / "Demografía, vivienda y territorio" / "iter_14_cpv2020_csv" / "iter_14_cpv2020" / "diccionario_datos" / "diccionario_datos_iter_14CSV20.csv",
    "iter_catalog": RAW_DIR / "Demografía, vivienda y territorio" / "iter_14_cpv2020_csv" / "iter_14_cpv2020" / "catalogos" / "tam_loc.csv.csv",
    "iter_meta": RAW_DIR / "Demografía, vivienda y territorio" / "iter_14_cpv2020_csv" / "iter_14_cpv2020" / "metadatos" / "metadatos_iter_14_cpv2020.txt",
    "air_quality": RAW_DIR / "Calidad del aire" / "BD_2024.xlsx",
    "health": RAW_DIR / "Salud y educación" / "ESTABLECIMIENTO_SALUD_202606.xlsx",
    "schools": RAW_DIR / "Salud y educación" / "concentrado_escuelas.xls",
    "services": RAW_DIR / "servicios basicos y infrastuctura" / "INEGI_exporta_28_8_2026_17_13_54.xls",
    "iieg": RAW_DIR / "Información estatal integrada" / "IIEGHogCaracteristicas.xlsx",
    "shf_pdf": RAW_DIR / "Mercado inmobiliario" / "I_ndice_SHF_T2_2026.pdf",
    "flood_pdf": RAW_DIR / "Riesgos territoriales" / "Inundaciones70x60.pdf",
}

# ZMG municipalities (INEGI names - exact match from ITER data)
ZMG_MUNICIPIOS = [
    "Guadalajara",
    "Zapopan",
    "San Pedro Tlaquepaque",
    "Tonalá",
    "Tlajomulco de Zúñiga",
]

# Alternative names for matching across datasets
ZMG_MUNICIPIOS_ALT = {
    "Tlaquepaque": "San Pedro Tlaquepaque",
    "Tlajomulco de Zúñiga": "Tlajomulco de Zúñiga",
}

# ZMG municipalities as they appear in health data (uppercase, no accents)
ZMG_MUNICIPIOS_HEALTH = [
    "GUADALAJARA",
    "ZAPOPAN",
    "SAN PEDRO TLAQUEPAQUE",
    "TONALA",
    "TLAJOMULCO DE ZUÑIGA",
]

# Target CRS for spatial data
TARGET_CRS = "EPSG:4326"  # WGS84

# Air quality stations in ZMG
AQ_STATIONS = {
    "AGU": {"name": "Águilas", "municipio": "Zapopan", "lat": 20.630982, "lon": -103.416711},
    "ATM": {"name": "Atemajac", "municipio": "Zapopan", "lat": 20.719626, "lon": -103.355412},
    "CEN": {"name": "Centro", "municipio": "Guadalajara", "lat": 20.673844, "lon": -103.333243},
    "COU": {"name": "Country", "municipio": "Zapopan", "lat": 20.698071, "lon": -103.358119},
    "LDO": {"name": "Loma Dorada", "municipio": "Tonalá", "lat": 20.631665, "lon": -103.256809},
    "MIR": {"name": "Miravalle", "municipio": "Guadalajara", "lat": 20.614511, "lon": -103.343352},
    "OBL": {"name": "Oblatos", "municipio": "Guadalajara", "lat": 20.700501, "lon": -103.296648},
    "PIN": {"name": "Las Pintas", "municipio": "El Salto", "lat": 20.576708, "lon": -103.326533},
    "SAN": {"name": "Santa Anita", "municipio": "Tlajomulco de Zúñiga", "lat": 20.551970, "lon": -103.447256},
    "SFE": {"name": "Santa Fe", "municipio": "Tlajomulco de Zúñiga", "lat": 20.528954, "lon": -103.377180},
    "SMT": {"name": "Santa Margarita", "municipio": "Zapopan", "lat": 20.723836, "lon": -103.431768},  # S0: coords reales de hoja Param
    "TLA": {"name": "Tlaquepaque", "municipio": "San Pedro Tlaquepaque", "lat": 20.640941, "lon": -103.312497},  # S0: coords reales de hoja Param
    "VAL": {"name": "Vallarta", "municipio": "Puerto Vallarta", "lat": 20.680141, "lon": -103.398572},  # Fuera de ZMG: solo referencia
}

# Pollutants of interest
POLLUTANTS = ["O3", "NO2", "NOX", "PM10", "PM2.5", "SO2", "CO"]
METEO_VARS = ["IT", "ET", "RH", "WS", "WD", "PP", "ATM", "RS", "UVI"]