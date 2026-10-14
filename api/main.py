# HabitaGDL API — Fase 1 (MVP tesis)
# FastAPI ligera que lee data/processed/*.parquet directo (sin PostGIS).
# Desbloquea las 6 páginas: /, /vivienda, /salud-educacion,
# /seguridad-riesgos, /aire, /metodologia.

from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"

DIMENSIONES = ["vivienda", "servicios", "movilidad", "salud",
               "educacion", "seguridad", "riesgos", "ambiente"]
PESOS_DEFAULT = {"vivienda": .15, "servicios": .18, "movilidad": .12,
                 "salud": .15, "educacion": .14, "seguridad": .04,
                 "riesgos": .10, "ambiente": .12}

app = FastAPI(title="HabitaGDL API", version="1.0.0-mvp")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache: dict = {}


def _load(name: str) -> pd.DataFrame:
    if name not in _cache:
        fp = PROC / name
        if not fp.exists():
            raise HTTPException(404, f"Falta {name}: corre python -m src.pipeline all")
        _cache[name] = pd.read_parquet(fp)
    return _cache[name]


def _records(df: pd.DataFrame) -> list:
    """Parquet→JSON seguro: ndarray/listas→list, NaN→None."""
    df = df.replace({np.nan: None})
    out = []
    for rec in df.to_dict("records"):
        clean = {}
        for k, v in rec.items():
            if isinstance(v, np.ndarray):
                v = v.tolist()
            if isinstance(v, (list, tuple)):
                clean[k] = [None if (isinstance(x, float) and np.isnan(x)) else x for x in v]
            elif isinstance(v, float) and np.isnan(v):
                clean[k] = None
            else:
                clean[k] = v
        out.append(clean)
    return out


def _haversine_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def _recalcular(df: pd.DataFrame, pesos: dict) -> pd.DataFrame:
    w = pd.Series({d: float(pesos.get(d, 0)) for d in DIMENSIONES})
    wsum = df[DIMENSIONES].notna().mul(w).sum(axis=1)
    iht = (df[DIMENSIONES].mul(w).sum(axis=1, skipna=True) / wsum).clip(0, 100)
    out = df.copy()
    out["IHT"] = iht.round(1)
    return out


@app.get("/health")
def health():
    return {"ok": True, "processed_files": len(list(PROC.glob("*.parquet")))}


@app.get("/api/v1/localidades")
def localidades(municipio: str = "", search: str = "",
                limit: int = 50, offset: int = 0):
    df = _load("iht_localidad.parquet")
    if municipio:
        df = df[df["municipio"].str.contains(municipio, case=False, na=False)]
    if search:
        df = df[df["nom_loc"].str.contains(search, case=False, na=False)]
    total = len(df)
    page = df.iloc[offset:offset + limit].replace({np.nan: None})
    return {"total": total, "items": page.to_dict("records")}


@app.get("/api/v1/localidades/{clave}")
def localidad(clave: str):
    df = _load("iht_localidad.parquet")
    row = df[df["clave"] == clave]
    if row.empty:
        raise HTTPException(404, "Localidad no encontrada")
    return row.iloc[0].replace({np.nan: None}).to_dict()


@app.get("/api/v1/iht")
def iht(municipio: str = "",
        vivienda: float = PESOS_DEFAULT["vivienda"],
        servicios: float = PESOS_DEFAULT["servicios"],
        movilidad: float = PESOS_DEFAULT["movilidad"],
        salud: float = PESOS_DEFAULT["salud"],
        educacion: float = PESOS_DEFAULT["educacion"],
        seguridad: float = PESOS_DEFAULT["seguridad"],
        riesgos: float = PESOS_DEFAULT["riesgos"],
        ambiente: float = PESOS_DEFAULT["ambiente"],
        limit: int = 10):
    """Recalcula IHT on-the-fly desde S_i guardados. El front puede replicar
    esta misma fórmula en JS para actualización <200ms sin red."""
    limit = max(1, min(limit, 100))
    df = _load("iht_localidad.parquet")
    if municipio:
        df = df[df["municipio"].str.contains(municipio, case=False, na=False)]
    pesos = {"vivienda": vivienda, "servicios": servicios, "movilidad": movilidad,
             "salud": salud, "educacion": educacion, "seguridad": seguridad,
             "riesgos": riesgos, "ambiente": ambiente}
    df = _recalcular(df.dropna(subset=["IHT"], how="all"), pesos)
    top = df.sort_values("IHT", ascending=False).head(limit).replace({np.nan: None})
    return {"pesos": pesos, "items": top.to_dict("records")}


@app.get("/api/v1/salud")
def salud(lat: float, lon: float, radio: float = 5.0,
          tipo: str = "", limit: int = 10):
    df = _load("health_establishments.parquet").dropna(subset=["lat", "lon"])
    if tipo:
        df = df[df["tipo_establecimiento"].str.contains(tipo, case=False, na=False)]
    d = _haversine_km(lat, lon, df["lat"].to_numpy(), df["lon"].to_numpy())
    df = df.assign(dist_km=np.round(d, 2))
    df = df[d <= radio].sort_values("dist_km").head(limit)
    return {"total": len(df), "items": df.replace({np.nan: None}).to_dict("records")}


@app.get("/api/v1/escuelas")
def escuelas(lat: float, lon: float, radio: float = 5.0,
             nivel: str = "", sost: str = "", limit: int = 10):
    df = _load("escuelas.parquet").dropna(subset=["lat", "lon"])
    if nivel:
        df = df[df["nivel"].str.contains(nivel, case=False, na=False)]
    if sost:
        df = df[df["sostenimiento"].str.contains(sost, case=False, na=False)]
    d = _haversine_km(lat, lon, df["lat"].to_numpy(), df["lon"].to_numpy())
    df = df.assign(dist_km=np.round(d, 2))
    df = df[d <= radio].sort_values("dist_km").head(limit)
    return {"total": len(df), "items": df.replace({np.nan: None}).to_dict("records")}


@app.get("/api/v1/seguridad")
def seguridad(municipio: str = "", anio: int = 0, delito: str = ""):
    try:
        df = _load("crime_mun_year.parquet" if not delito else "crime_municipio.parquet")
    except HTTPException:
        raise HTTPException(404, "Sin datos SESNSP: descarga el CSV municipal a Seguridad/SESNSP_municipal.csv y corre python -m src.pipeline crime")
    if municipio:
        df = df[df["municipio_norm"] == municipio.strip().upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")]
    if anio:
        df = df[df["anio"] == anio]
    if delito and "delito" in df.columns:
        df = df[df["delito"].str.contains(delito, case=False, na=False)]
    return {"total": len(df), "items": df.replace({np.nan: None}).to_dict("records")}


@app.get("/api/v1/aire/estaciones")
def estaciones():
    df = _load("air_quality_stations.parquet")
    return {"total": len(df), "items": _records(df)}


@app.get("/api/v1/aire/lecturas")
def lecturas(estacion: str, param: str = "pm25",
             desde: str = "", hasta: str = "", limit: int = 500):
    limit = max(1, min(limit, 5000))
    df = _load("air_quality_daily.parquet")
    col = "station" if "station" in df.columns else "estacion"
    df = df[df[col] == estacion]
    if desde and "date" in df.columns:
        df = df[df["date"].astype(str) >= desde]
    if hasta and "date" in df.columns:
        df = df[df["date"].astype(str) <= hasta]
    cols = list(dict.fromkeys(c for c in ["date", param, "pm25", "pm10", "o3", "no2"] if c in df.columns))
    return {"estacion": estacion, "items": df[cols].head(limit).replace({np.nan: None}).to_dict("records")}


@app.get("/api/v1/aire/seasonal-wind")
def seasonal_wind(estacion: str = ""):
    df = _load("air_quality_seasonal_wind.parquet")
    if estacion:
        col = "station" if "station" in df.columns else "estacion"
        df = df[df[col] == estacion]
    return {"total": len(df), "items": df.replace({np.nan: None}).to_dict("records")}


@app.get("/api/v1/geo/iht-ageb")
def geo_iht_ageb():
    fp = PROC / "iht_ageb.geojson"
    if not fp.exists():
        raise HTTPException(404, "Falta iht_ageb.geojson: corre python -m src.pipeline geo")
    return FileResponse(fp, media_type="application/geo+json")


# Vista estática (6 páginas en web/). Se monta al final para no tapar /docs ni /api.
WEB = BASE / "web"
if WEB.exists():
    app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
