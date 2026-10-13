# HabitaGDL — IHT v2: baja el IHT de localidad a AGEB (polígonos para el mapa)
#
# Metodología honesta (va a la tesis §2): el IHT se CALCULA a nivel localidad
# (único grano con variables ITER). Cada AGEB urbana HEREDA el IHT de la
# localidad que contiene su centroide (point-in-polygon del centroide
# INEGI). AGEBs sin localidad asignable quedan con IHT NaN + nota.
# Esto cierra el hallazgo QA-1 para el MAPA (GDL: 4 filas → 442 AGEBs);
# los números siguen siendo de localidad y así se etiquetan en la UI.

import geopandas as gpd
import pandas as pd
from typing import Dict

DIMS = ["vivienda", "servicios", "movilidad", "salud",
        "educacion", "seguridad", "riesgos", "ambiente"]


def join_iht_ageb() -> gpd.GeoDataFrame:
    from ..config import PROCESSED_DIR
    from .engine import _dms
    ageb = gpd.read_file(PROCESSED_DIR / "ageb_zmg.geojson")
    iht = pd.read_parquet(PROCESSED_DIR / "iht_localidad.parquet")
    it = pd.read_parquet(PROCESSED_DIR / "iter_zgm.parquet")
    it = it[~it["NOM_LOC"].astype(str).str.startswith("Total del")].copy()

    pts = gpd.GeoDataFrame(
        it[["NOM_LOC", "NOM_MUN", "ENTIDAD", "MUN", "LOC"]],
        geometry=gpd.points_from_xy(
            it["LONGITUD"].apply(_dms), it["LATITUD"].apply(_dms)),
        crs="EPSG:4326").dropna(subset=["geometry"])
    # S1-geo-fix: point-in-polygon solo cubre localidades DENTRO de AGEBs
    # urbanas (45/1724); los pueblos rurales quedan fuera por definición.
    # Join correcto: cada AGEB hereda el IHT de la localidad válida MÁS
    # CERCANA a su centroide (distancia guardada en dist_km = trazabilidad).
    pts["_key"] = (pts["ENTIDAD"].astype(str) + "-" + pts["MUN"].astype(str) +
                   "-" + pts["LOC"].astype(str))
    valid = pts[pts["_key"].isin(
        set(iht[iht["IHT"].notna()]["clave"]))].to_crs("EPSG:32613")
    cents = ageb.to_crs("EPSG:32613").copy()
    cents["geometry"] = cents.centroid
    match = gpd.sjoin_nearest(cents[["CVEGEO", "geometry"]], valid,
                              how="left", distance_col="dist_m")
    match["dist_km"] = (match["dist_m"] / 1000).round(2)
    match["clave"] = match["_key"]
    key = match["clave"].fillna("")

    cols = ["clave", "IHT", "cobertura", "nota"] + DIMS
    info = iht.set_index("clave", drop=False)[cols]
    ageb2 = ageb.set_index("CVEGEO").loc[match.set_index("CVEGEO").index].copy()
    ageb2["IHT"] = key.map(info["IHT"]).values
    ageb2["cobertura"] = key.map(info["cobertura"]).values
    for d in DIMS:
        ageb2[d] = key.map(info[d]).values
    ageb2["nom_loc_ref"] = match["NOM_LOC"].values
    ageb2["dist_km"] = match["dist_km"].values.round(2)
    ageb2["nota"] = ("IHT de localidad mas cercana (" +
                     match["NOM_LOC"].fillna("?") + " a " +
                     match["dist_km"].round(1).astype(str) + " km)").values
    return ageb2.reset_index()


def process_iht_ageb() -> Dict:
    return {"records": join_iht_ageb()}


def save_processed_iht_ageb(results: Dict) -> None:
    from ..config import PROCESSED_DIR
    df = results["records"]
    df.to_file(PROCESSED_DIR / "iht_ageb.geojson", driver="GeoJSON")
    n = int(df["IHT"].notna().sum())
    print(f"Saved iht_ageb: {len(df)} AGEBs, con IHT: {n} "
          f"({n / len(df) * 100:.1f}%), media={df['IHT'].mean():.1f}")
