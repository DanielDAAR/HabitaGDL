# HabitaGDL — ETL AGEB urbana (marco geoestadístico, geometrías para el mapa)
#
# Fuente: CONABIO geoportal, AGEB urbana nacional 2019 (compilada de INEGI),
# http://www.conabio.gob.mx/informacion/gis/maps/geo/agbumge19gw.zip
# Descarga con: python %TEMP%/dl_ageb.py (script fuera del repo).
# El .zip nacional (42 MB) NO se commitea (ver .gitignore); solo el subset ZMG.

import geopandas as gpd
from typing import Dict

ZMG_CLAVES = {"039", "097", "098", "101", "120"}  # GDL, Tlajomulco, Tlaquepaque, Tonalá, Zapopan
MUN_NOMBRE = {"039": "Guadalajara", "097": "Tlajomulco de Zúñiga",
              "098": "San Pedro Tlaquepaque", "101": "Tonalá", "120": "Zapopan"}


def _fix_mojibake(s: str) -> str:
    """DBF en UTF-8 leído como latin1 ('AcatlÃ¡n' → 'Acatlán')."""
    try:
        return s.encode("latin1").decode("utf8")
    except (UnicodeError, AttributeError):
        return s


def load_ageb_zmg() -> "gpd.GeoDataFrame":
    from ..config import BASE_DIR
    zf = BASE_DIR / "Mapas" / "ageb_urbana_nacional_2019.zip"
    a = gpd.read_file(f"zip://{zf}!agbumge19gw.shp")
    z = a[(a["CVE_ENT"] == "14") & (a["CVE_MUN"].isin(ZMG_CLAVES))].copy()
    z["NOM_MUN"] = z["CVE_MUN"].map(MUN_NOMBRE)
    z["NOM_LOC"] = z["CVE_LOC"].astype(str)
    return z.reset_index(drop=True)


def process_ageb() -> Dict:
    return {"records": load_ageb_zmg()}


def save_processed_ageb(results: Dict) -> None:
    from ..config import PROCESSED_DIR
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = results["records"]
    df.to_file(PROCESSED_DIR / "ageb_zmg.geojson", driver="GeoJSON")
    df.drop(columns=["geometry"]).to_parquet(
        PROCESSED_DIR / "ageb_zmg.parquet", index=False)
    por_mun = df.groupby("CVE_MUN").size().to_dict()
    print(f"Saved ageb_zmg: {len(df)} AGEBs {por_mun}")
