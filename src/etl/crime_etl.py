# HabitaGDL — ETL delitos (SESNSP, fuero común municipal)
#
# NO requiere webscraping: el SESNSP publica descarga directa oficial en
# https://www.gob.mx/sesnsp/acciones-y-programas/datos-abiertos-de-incidencia-delictiva
# (también espejo en datos.gob.mx, dataset "incidencia_delictiva").
# Paso manual único: descargar "Incidencia delictiva municipal" (CSV,
# metodología 2015-2025 o 2026) y guardarlo como PATHS["sesnsp"].
# El pipeline falla en suave (FileNotFoundError → paso omitido) si falta.

import json
import pandas as pd
from typing import Dict
from ..schemas.data_models import norm_mun, MunicipioZMG

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
ZMG_NORM = [norm_mun(m.value) for m in MunicipioZMG]

# CVE_MUN INEGI de los 5 ZMG (Jalisco = entidad 14)
ZMG_CVES = {"039", "120", "097", "101", "122"}  # GDL, Zapopan, Tlaquepaque, Tonalá, Tlajomulco


def load_sesnsp_raw() -> pd.DataFrame:
    from ..config import PATHS
    fp = PATHS["sesnsp"]
    if not fp.exists():
        raise FileNotFoundError(
            f"Falta {fp}. Descarga 'Incidencia delictiva municipal' (CSV) de "
            "https://www.gob.mx/sesnsp/acciones-y-programas/"
            "datos-abiertos-de-incidencia-delictiva y guárdalo ahí.")
    try:
        return pd.read_csv(fp, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(fp, encoding="latin1")


def _pick(df: pd.DataFrame, cands) -> str:
    low = {str(c).strip().lower(): c for c in df.columns}
    for c in cands:
        if c.lower() in low:
            return low[c.lower()]
    raise KeyError(f"Sin columna {cands} en {list(df.columns)[:8]}")


def parse_crime(df: pd.DataFrame) -> pd.DataFrame:
    c_ent = _pick(df, ["clave_ent", "cve_entidad", "entidad_federativa_clave"])
    c_mun = _pick(df, ["cve_municipio", "clave_mun", "municipio_clave"])
    c_nom = _pick(df, ["municipio"])
    c_ano = _pick(df, ["año", "ano", "year"])
    c_del = _pick(df, ["tipo de delito", "tipo_delito", "delito"])
    meses = [m for m in MESES if m in df.columns or m.lower() in
             [str(c).lower() for c in df.columns]]
    if not meses:  # columnas en minúsculas
        meses = [c for c in df.columns if str(c).strip().lower() in
                 [m.lower() for m in MESES]]
    df = df[pd.to_numeric(df[c_ent], errors="coerce") == 14].copy()
    df["__mun"] = df[c_mun].astype(str).str.zfill(3)
    df = df[df["__mun"].isin(ZMG_CVES)].copy()
    df["municipio_norm"] = df[c_nom].astype(str).map(norm_mun)
    df["delito"] = df[c_del].astype(str).str.strip()
    df["anio"] = pd.to_numeric(df[c_ano], errors="coerce").astype("Int64")
    for m in meses:
        df[m] = pd.to_numeric(df[m], errors="coerce").fillna(0)
    df["total"] = df[meses].sum(axis=1)
    out = df.groupby(["__mun", "municipio_norm", "anio", "delito"],
                     as_index=False)["total"].sum()
    out = out.rename(columns={"__mun": "cve_mun"})
    return out.sort_values(["anio", "cve_mun", "total"], ascending=[False, True, False])


def add_tasas(df: pd.DataFrame) -> pd.DataFrame:
    """Tasa por 100k hab con POBTOT del ITER (suma localidades, sin agregados)."""
    from ..config import PROCESSED_DIR
    it = pd.read_parquet(PROCESSED_DIR / "iter_zgm.parquet")
    it = it[~it["NOM_LOC"].astype(str).str.startswith("Total del")].copy()
    pob = it.groupby(it["NOM_MUN"].map(norm_mun))["POBTOT"].apply(
        lambda s: pd.to_numeric(s, errors="coerce").sum()).to_dict()
    df = df.copy()
    df["pob"] = df["municipio_norm"].map(pob)
    df["tasa_100k"] = (df["total"] / df["pob"] * 100000).round(1)
    return df


def process_crime() -> Dict:
    df = add_tasas(parse_crime(load_sesnsp_raw()))
    by_mun_year = df.groupby(["cve_mun", "municipio_norm", "anio"],
                             as_index=False).agg(total=("total", "sum"),
                                                 tasa_100k=("tasa_100k", "sum"),
                                                 n_delitos=("delito", "nunique"))
    return {"records": df, "by_mun_year": by_mun_year}


def save_processed_crime(results: Dict) -> None:
    from ..config import PROCESSED_DIR
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    results["records"].to_parquet(PROCESSED_DIR / "crime_municipio.parquet", index=False)
    results["by_mun_year"].to_parquet(
        PROCESSED_DIR / "crime_mun_year.parquet", index=False)
    (PROCESSED_DIR / "crime_summary.json").write_text(json.dumps({
        "rows": len(results["records"]),
        "anios": sorted(int(a) for a in results["records"]["anio"].dropna().unique()),
        "municipios": sorted(results["records"]["municipio_norm"].unique()),
    }, ensure_ascii=False), encoding="utf-8")
    print(f"Saved crime: {len(results['records'])} rows "
          f"({results['records']['anio'].max()} último año)")
