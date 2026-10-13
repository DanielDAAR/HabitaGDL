# HabitaGDL — ETL escuelas (SIGED/SEP, archivo .xls que en realidad es HTML)

import pandas as pd
from typing import Dict, List
from ..schemas.data_models import norm_mun

# La columna 12 trae 'TLAQUEPAQUE' a secas; el resto del proyecto usa el
# nombre INEGI 'San Pedro Tlaquepaque'.
ALIAS_MUN = {"TLAQUEPAQUE": "SAN PEDRO TLAQUEPAQUE"}
# El .xls es HTML en latin1 mal decodificado (Ñ/Á → U+FFFD). Se mapea la
# forma corrupta observada a su normalizado correcto. Verificado 13-oct-2026.
MOJI_ALIAS = {"TLAJOMULCO DE Z\ufffd\ufffdIGA": norm_mun("Tlajomulco de Zúñiga"),
              "TONAL\ufffd": norm_mun("Tonalá")}
ZMG_NORM = [norm_mun(m) for m in [
    "Guadalajara", "Zapopan", "San Pedro Tlaquepaque",
    "Tonalá", "Tlajomulco de Zúñiga",
]]

COLS = {0: "cct", 2: "turno", 3: "nombre", 5: "nivel",
        6: "modalidad", 7: "sostenimiento", 12: "municipio",
        35: "lon", 36: "lat"}


def load_schools_raw() -> pd.DataFrame:
    from ..config import PATHS
    return pd.read_html(PATHS["schools"])[0]


def parse_schools(df: pd.DataFrame) -> pd.DataFrame:
    out = df.rename(columns=COLS)[list(COLS.values())].copy()
    out["municipio_norm"] = out["municipio"].astype(str).map(
        lambda m: norm_mun(MOJI_ALIAS.get(m.strip().upper(),
                                          ALIAS_MUN.get(m.strip().upper(), m))))
    out = out[out["municipio_norm"].isin(ZMG_NORM)].copy()
    out["lat"] = pd.to_numeric(out["lat"], errors="coerce")
    out["lon"] = pd.to_numeric(out["lon"], errors="coerce")
    out["nivel"] = out["nivel"].astype(str).str.strip().str.upper()
    out["sostenimiento"] = out["sostenimiento"].astype(str).str.strip().str.upper()
    return out.reset_index(drop=True)


def agg_municipio_nivel(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby(["municipio_norm", "nivel", "sostenimiento"]).size().reset_index(
        name="n_escuelas")


def process_schools() -> Dict:
    df = parse_schools(load_schools_raw())
    return {"records": df, "agg": agg_municipio_nivel(df)}


def save_processed_schools(results: Dict) -> None:
    from ..config import PROCESSED_DIR
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    results["records"].to_parquet(PROCESSED_DIR / "escuelas.parquet", index=False)
    results["agg"].to_parquet(
        PROCESSED_DIR / "escuelas_por_municipio_nivel.parquet", index=False)
    print(f"Saved escuelas: {len(results['records'])} rows, "
          f"con coords: {results['records']['lat'].notna().sum()}")
