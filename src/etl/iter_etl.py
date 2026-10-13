# HabitaGDL - INEGI ITER 2020 ETL

import pandas as pd
from pathlib import Path
from typing import Iterator, Optional, List
from ..schemas.data_models import IterLocalidad, TamanoLocalidad, MunicipioZMG
from ..config import PATHS


def load_iter_csv(chunksize: int = 1000) -> Iterator[pd.DataFrame]:
    """Load ITER CSV in chunks"""
    return pd.read_csv(
        PATHS["iter_csv"],
        encoding="utf-8-sig",
        chunksize=chunksize,
        low_memory=False,
    )


def load_iter_full() -> pd.DataFrame:
    """Load full ITER dataset"""
    return pd.read_csv(
        PATHS["iter_csv"],
        encoding="utf-8-sig",
        low_memory=False,
    )


def load_iter_dictionary() -> pd.DataFrame:
    """Load ITER data dictionary"""
    return pd.read_csv(
        PATHS["iter_dict"],
        encoding="utf-8-sig",
        header=None,
    )


def load_iter_catalog() -> pd.DataFrame:
    """Load locality size catalog"""
    return pd.read_csv(
        PATHS["iter_catalog"],
        encoding="utf-8-sig",
    )


def filter_zgm(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to ZMG municipalities"""
    return df[df["NOM_MUN"].isin([m.value for m in MunicipioZMG])].copy()


def parse_iter_row(row: pd.Series) -> IterLocalidad:
    """Parse a DataFrame row into IterLocalidad"""
    def get_int(col: str) -> Optional[int]:
        val = row.get(col)
        if pd.isna(val):
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    def get_float(col: str) -> Optional[float]:
        val = row.get(col)
        if pd.isna(val):
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def get_str(col: str) -> Optional[str]:
        val = row.get(col)
        if pd.isna(val):
            return None
        return str(val).strip()

    return IterLocalidad(
        entidad=get_str("ENTIDAD") or "",
        nom_ent=get_str("NOM_ENT") or "",
        mun=get_str("MUN") or "",
        nom_mun=get_str("NOM_MUN") or "",
        loc=get_str("LOC") or "",
        nom_loc=get_str("NOM_LOC") or "",
        longitud=get_str("LONGITUD"),
        latitud=get_str("LATITUD"),
        altitud=get_str("ALTITUD"),
        pobtot=get_int("POBTOT"),
        pobfem=get_int("POBFEM"),
        pobmas=get_int("POBMAS"),
        p_0a2=get_int("P_0A2"),
        p_3ymas=get_int("P_3YMAS"),
        p_5ymas=get_int("P_5YMAS"),
        p_12ymas=get_int("P_12YMAS"),
        p_15ymas=get_int("P_15YMAS"),
        p_18ymas=get_int("P_18YMAS"),
        p_60ymas=get_int("P_60YMAS"),
        p15pri_in=get_int("P15PRI_IN"),
        p15pri_co=get_int("P15PRI_CO"),
        p15sec_in=get_int("P15SEC_IN"),
        p15sec_co=get_int("P15SEC_CO"),
        graproes=get_float("GRAPROES"),
        pea=get_int("PEA"),
        pocupada=get_int("POCUPADA"),
        pdesocup=get_int("PDESOCUP"),
        vph_autom=get_int("VPH_AUTOM"),
        vph_moto=get_int("VPH_MOTO"),
        vph_bici=get_int("VPH_BICI"),
        vph_inter=get_int("VPH_INTER"),
        vph_pc=get_int("VPH_PC"),
        vph_cel=get_int("VPH_CEL"),
        vph_stvp=get_int("VPH_STVP"),
        vph_refri=get_int("VPH_REFRI"),
        vph_lavad=get_int("VPH_LAVAD"),
        vph_micro=get_int("VPH_MICRO"),
        vph_horno=get_int("VPH_HORNO"),
        vph_tv=get_int("VPH_TV"),
        vph_dren=get_int("VPH_DREN"),
        vph_cister=get_int("VPH_CISTER"),
        raw=row.to_dict(),
    )


def iter_localidades_zgm() -> List[IterLocalidad]:
    """Get all ZMG localities as IterLocalidad objects"""
    df = load_iter_full()
    df_zgm = filter_zgm(df)
    return [parse_iter_row(row) for _, row in df_zgm.iterrows()]


def iter_to_dataframe(records: List[IterLocalidad]) -> pd.DataFrame:
    """Convert IterLocalidad list to DataFrame"""
    return pd.DataFrame([r.__dict__ for r in records])


def save_processed(df: pd.DataFrame, filename: str) -> Path:
    """Save processed DataFrame to parquet"""
    out_path = PATHS["iter_csv"].parent.parent.parent.parent.parent / "data" / "processed" / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    return out_path


if __name__ == "__main__":
    # Quick test
    df = load_iter_full()
    print(f"Total rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    
    df_zgm = filter_zgm(df)
    print(f"ZMG rows: {len(df_zgm)}")
    print(f"ZMG municipios: {df_zgm['NOM_MUN'].unique()}")
    
    # Test parsing
    records = iter_localidades_zgm()
    print(f"Parsed {len(records)} records")
    if records:
        print(f"First: {records[0].nom_mun} - {records[0].nom_loc} - POBTOT: {records[0].pobtot}")