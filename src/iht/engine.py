# HabitaGDL — Motor IHT v1 (Índice de Habitabilidad Territorial 0-100)
#
# IHT = sum(w_i * S_i) / sum(w disponibles); S_i en 0-100 (min-max ZMG).
# V1 calcula 5/8 dimensiones (cobertura=5): vivienda, servicios, salud,
# educación, ambiente. Movilidad/riesgos → NaN (datos S1-S2).
# Seguridad se activa a 6/8 cuando existe crime_mun_year.parquet (SESNSP).
# Cercanía salud/educación/aire = haversine vectorizado (localidad↔puntos).

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict
from ..schemas.data_models import norm_mun

DIMENSIONES = ["vivienda", "servicios", "movilidad", "salud",
               "educacion", "seguridad", "riesgos", "ambiente"]

PESOS_DEFAULT = {"vivienda": .15, "servicios": .18, "movilidad": .12,
                 "salud": .15, "educacion": .14, "seguridad": .04,
                 "riesgos": .10, "ambiente": .12}
PRESETS = {
    "default": PESOS_DEFAULT,
    "familias": {"vivienda": .15, "servicios": .15, "movilidad": .10,
                 "salud": .20, "educacion": .20, "seguridad": .05,
                 "riesgos": .10, "ambiente": .05},
    "aire": {"vivienda": .10, "servicios": .10, "movilidad": .10,
             "salud": .15, "educacion": .10, "seguridad": .03,
             "riesgos": .07, "ambiente": .35},
}
RADIO_KM = 2.0
# Umbral metodológico: localidades con <10 viviendas habitadas no reciben
# IHT (los % con denominador mínimo son ruido: 1/1 = 100%). 201/534 ZMG
# están bajo el umbral — se reportan con nota, no se inventan.
MIN_VIVIENDAS = 10


def _dms(s) -> float:
    """Convierte DMS INEGI ("20°40'35.000\" N") a decimal. *, None, NaN → nan.

    S1: ITER trae LATITUD/LONGITUD en grados-minutos-segundos, no decimal;
    sin esto TODA la cercanía (salud/educación/aire) salía NaN."""
    import math
    import re
    if s is None or (isinstance(s, float) and math.isnan(s)):
        return np.nan
    s = str(s).strip()
    if s in ("*", "", "nan", "None"):
        return np.nan
    m = re.search(r"(\d+)[^\d]+(\d+)'([\d.]+)", s)
    if not m:
        try:
            return float(s)
        except ValueError:
            return np.nan
    dec = int(m.group(1)) + int(m.group(2)) / 60 + float(m.group(3)) / 3600
    if s.strip()[-1] in ("W", "O", "S"):
        dec = -dec
    return dec


def _haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def _minmax(s: pd.Series, invertir=False) -> pd.Series:
    mn, mx = s.min(skipna=True), s.max(skipna=True)
    if pd.isna(mn) or pd.isna(mx) or mx == mn:
        return pd.Series(np.nan, index=s.index)
    out = (s - mn) / (mx - mn) * 100
    return 100 - out if invertir else out


def _pct(df: pd.DataFrame, col: str, den: str) -> pd.Series:
    if col not in df.columns or den not in df.columns:
        return pd.Series(np.nan, index=df.index)
    d = pd.to_numeric(df[den], errors="coerce").replace(0, np.nan)
    return pd.to_numeric(df[col], errors="coerce") / d * 100


def cercania(latlon_loc: pd.DataFrame, puntos: pd.DataFrame) -> pd.DataFrame:
    """Para cada localidad: n puntos en RADIO_KM + distancia al más cercano."""
    pts = puntos.dropna(subset=["lat", "lon"]).copy()
    plat = pd.to_numeric(pts["lat"], errors="coerce").to_numpy()
    plon = pd.to_numeric(pts["lon"], errors="coerce").to_numpy()
    out_n, out_d = [], []
    for _, r in latlon_loc.iterrows():
        try:
            la, lo = float(r["lat"]), float(r["lon"])
        except (TypeError, ValueError):
            out_n.append(np.nan)
            out_d.append(np.nan)
            continue
        d = _haversine_km(la, lo, plat, plon)
        out_n.append(int((d <= RADIO_KM).sum()))
        out_d.append(float(d.min()) if len(d) else np.nan)
    return pd.DataFrame({"n_cercanos": out_n, "dist_min_km": out_d},
                        index=latlon_loc.index)


def _latlon(df: pd.DataFrame, lat_c: str, lon_c: str) -> pd.DataFrame:
    def flex(v):
        n = pd.to_numeric([v], errors="coerce")[0]
        return n if pd.notna(n) else _dms(v)
    return pd.DataFrame({"lat": df[lat_c].apply(flex),
                         "lon": df[lon_c].apply(flex)})


def _latlon_simple(df: pd.DataFrame, lat_c: str, lon_c: str) -> pd.DataFrame:
    out = pd.DataFrame({"lat": pd.to_numeric(df[lat_c], errors="coerce"),
                        "lon": pd.to_numeric(df[lon_c], errors="coerce")})
    return out


def calcular_iht(pesos: Dict[str, float] = None) -> pd.DataFrame:
    from ..config import PROCESSED_DIR
    pesos = pesos or PESOS_DEFAULT
    it = pd.read_parquet(PROCESSED_DIR / "iter_zgm.parquet")
    den = "TVIVPARHAB"
    # Fuera del IHT: fila agregada 'Total del Municipio' (no es localidad).
    it = it[~it["NOM_LOC"].astype(str).str.startswith("Total del")].copy()
    it["__viv"] = pd.to_numeric(it[den], errors="coerce")
    elegible = (it["__viv"] >= MIN_VIVIENDAS).fillna(False)

    dims = pd.DataFrame(index=it.index)

    def dim_score(parts):
        """Promedio de indicadores disponibles (NaN no envenena)."""
        t = pd.concat(parts, axis=1)
        return t.mean(axis=1, skipna=True).where(t.notna().any(axis=1))

    dims["vivienda"] = dim_score([
        100 - _pct(it, "VPH_PISOTI", den),
        _pct(it, "VPH_3YMASC", den),
        _pct(it, "VPH_2YMASD", den)])
    dims["servicios"] = dim_score([
        _pct(it, "VPH_C_ELEC", den),
        _pct(it, "VPH_DRENAJ", den),
        (_pct(it, "VPH_TINACO", den).fillna(0) +
         _pct(it, "VPH_CISTER", den).fillna(0)),
        _pct(it, "VPH_AGUADV", den)])
    for c in ["vivienda", "servicios"]:
        dims[c] = _minmax(dims[c])

    loc = _latlon(it, "LATITUD", "LONGITUD")
    try:
        salud = pd.read_parquet(PROCESSED_DIR / "health_establishments.parquet")
        cs = cercania(loc, _latlon(salud, "lat", "lon"))
        dims["salud"] = _minmax(np.log1p(cs["n_cercanos"].fillna(0)))
    except FileNotFoundError:
        dims["salud"] = np.nan
    try:
        esc = pd.read_parquet(PROCESSED_DIR / "escuelas.parquet")
        ce = cercania(loc, _latlon(esc, "lat", "lon"))
        dims["educacion"] = _minmax(np.log1p(ce["n_cercanos"].fillna(0)))
    except FileNotFoundError:
        dims["educacion"] = np.nan
    try:
        aq = pd.read_parquet(PROCESSED_DIR / "air_quality_daily.parquet")
        pm = aq.groupby("station")["pm25"].mean()
        from ..config import AQ_STATIONS
        est = pd.DataFrame(
            [{"station": k, "lat": v["lat"], "lon": v["lon"],
              "pm25": pm.get(k, np.nan)} for k, v in AQ_STATIONS.items()
             if v["lat"] != 0]).dropna(subset=["pm25"])
        da = cercania(loc, est.rename(columns={"lat": "lat", "lon": "lon"}))
        # asignación simple y trazable: PM2.5 anual de la estación más cercana
        pm_loc = []
        elat = est["lat"].to_numpy()
        elon = est["lon"].to_numpy()
        epm = est["pm25"].to_numpy()
        for _, r in loc.iterrows():
            try:
                d = _haversine_km(float(r["lat"]), float(r["lon"]), elat, elon)
                pm_loc.append(float(epm[int(np.argmin(d))]))
            except (TypeError, ValueError):
                pm_loc.append(np.nan)
        dims["ambiente"] = _minmax(pd.Series(pm_loc, index=it.index), invertir=True)
    except FileNotFoundError:
        dims["ambiente"] = np.nan

    try:
        cr = pd.read_parquet(PROCESSED_DIR / "crime_mun_year.parquet")
        ultimo = int(cr["anio"].max())
        tot = cr[cr["anio"] == ultimo].set_index("municipio_norm")["tasa_100k"]
        inv = _minmax(tot, invertir=True)  # menos delitos = más puntos
        dims["seguridad"] = it["NOM_MUN"].map(norm_mun).map(inv)
    except FileNotFoundError:
        dims["seguridad"] = np.nan

    for d in ["movilidad", "riesgos"]:
        dims[d] = np.nan

    w = pd.Series({d: pesos.get(d, 0) for d in DIMENSIONES})
    wsum = dims.notna().mul(w).sum(axis=1)
    iht = (dims.mul(w).sum(axis=1, skipna=True) / wsum).clip(0, 100)
    sin_coords = loc[["lat", "lon"]].isna().any(axis=1)
    valida = elegible & ~sin_coords
    nota = pd.Series("ok", index=it.index)
    nota[~elegible] = "sin viviendas suficientes (<10)"
    nota[elegible & sin_coords] = "sin coordenadas"
    iht = iht.where(valida, np.nan)

    return pd.DataFrame({
        "clave": it["ENTIDAD"].astype(str) + "-" + it["MUN"].astype(str) + "-" + it["LOC"].astype(str),
        "nom_loc": it["NOM_LOC"], "municipio": it["NOM_MUN"],
        **{d: dims[d].round(1) for d in DIMENSIONES},
        "cobertura": dims.notna().sum(axis=1),
        "IHT": iht.round(1),
        "nota": nota,
    })


def save_iht(df: pd.DataFrame) -> Path:
    from ..config import PROCESSED_DIR
    out = PROCESSED_DIR / "iht_localidad.parquet"
    df.to_parquet(out, index=False)
    print(f"Saved IHT: {len(df)} localidades, "
          f"media={df['IHT'].mean():.1f}, cobertura={df['cobertura'].mode().iloc[0]}/8")
    return out
