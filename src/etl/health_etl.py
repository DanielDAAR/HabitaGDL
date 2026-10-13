# HabitaGDL - Health Establishments ETL

import pandas as pd
from pathlib import Path
from typing import List, Dict
from ..schemas.data_models import HealthEstablishment
from ..config import PATHS, ZMG_MUNICIPIOS_HEALTH


def load_health_clues() -> pd.DataFrame:
    """Load CLUES health establishments"""
    return pd.read_excel(PATHS["health"], sheet_name="CLUES_202606")


def load_health_subclues() -> pd.DataFrame:
    """Load sub-establishments/services"""
    return pd.read_excel(PATHS["health"], sheet_name="SUBCLUES_202606")


def load_health_horarios() -> pd.DataFrame:
    """Load operating hours"""
    return pd.read_excel(PATHS["health"], sheet_name="HORARIOS_202606")


def filter_zgm(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to ZMG municipalities"""
    return df[df["ENTIDAD"] == "JALISCO"].copy()


def filter_zgm_municipios(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to ZMG municipios specifically"""
    return df[df["MUNICIPIO"].isin(ZMG_MUNICIPIOS_HEALTH)].copy()


def parse_health_row(row: pd.Series) -> HealthEstablishment:
    """Parse a CLUES row into HealthEstablishment"""
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

    lat = get_float("LATITUD")
    lon = get_float("LONGITUD")
    
    return HealthEstablishment(
        clues=get_str("CLUES") or "",
        institucion=get_str("CLAVE DE LA INSTITUCION") or "",
        nombre=get_str("NOMBRE DE LA INSTITUCION") or "",
        entidad=get_str("ENTIDAD") or "",
        municipio=get_str("MUNICIPIO") or "",
        localidad=get_str("LOCALIDAD") or "",
        tipo_establecimiento=get_str("NOMBRE TIPO ESTABLECIMIENTO") or "",
        tipologia=get_str("NOMBRE DE TIPOLOGIA") or "",
        subtipologia=get_str("NOMBRE DE SUBTIPOLOGIA") or "",
        lat=lat,
        lon=lon,
        status=get_str("ESTATUS DE OPERACION") or "",
        raw=row.to_dict(),
    )


def load_zgm_health() -> List[HealthEstablishment]:
    """Load and parse ZMG health establishments"""
    df = load_health_clues()
    df_jal = filter_zgm(df)
    df_zgm = filter_zgm_municipios(df_jal)
    
    print(f"Total CLUES: {len(df)}")
    print(f"Jalisco: {len(df_jal)}")
    print(f"ZMG: {len(df_zgm)}")
    
    return [parse_health_row(row) for _, row in df_zgm.iterrows()]


def health_by_municipio_type(records: List[HealthEstablishment]) -> pd.DataFrame:
    """Aggregate health establishments by municipio and type"""
    data = []
    for r in records:
        data.append({
            "municipio": r.municipio,
            "tipo": r.tipo_establecimiento,
            "tipologia": r.tipologia,
            "subtipologia": r.subtipologia,
            "has_coords": r.lat is not None and r.lon is not None,
        })
    
    df = pd.DataFrame(data)
    if df.empty:
        return df
    
    return df.groupby(["municipio", "tipo", "tipologia"]).agg(
        count=("tipo", "count"),
        with_coords=("has_coords", "sum"),
    ).reset_index()


def health_summary(records: List[HealthEstablishment]) -> Dict:
    """Generate summary statistics"""
    from collections import Counter
    
    by_municipio = Counter(r.municipio for r in records)
    by_tipo = Counter(r.tipo_establecimiento for r in records)
    by_tipologia = Counter(r.tipologia for r in records)
    with_coords = sum(1 for r in records if r.lat is not None and r.lon is not None)
    
    return {
        "total": len(records),
        "by_municipio": dict(by_municipio),
        "by_tipo": dict(by_tipo),
        "by_tipologia": dict(by_tipologia),
        "with_coords": with_coords,
        "without_coords": len(records) - with_coords,
    }


def process_health() -> Dict:
    """Full health processing pipeline"""
    print("Loading health data...")
    records = load_zgm_health()
    
    print("Generating aggregates...")
    by_mun_type = health_by_municipio_type(records)
    summary = health_summary(records)
    
    df_records = pd.DataFrame([r.__dict__ for r in records])
    
    return {
        "records": df_records,
        "by_municipio_type": by_mun_type,
        "summary": summary,
    }


def save_processed(results: Dict) -> None:
    """Save processed health data"""
    from ..config import PROCESSED_DIR
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    results["records"].to_parquet(PROCESSED_DIR / "health_establishments.parquet", index=False)
    results["by_municipio_type"].to_parquet(PROCESSED_DIR / "health_by_municipio_type.parquet", index=False)
    
    import json
    with open(PROCESSED_DIR / "health_summary.json", "w", encoding="utf-8") as f:
        json.dump(results["summary"], f, ensure_ascii=False, indent=2)
    
    print(f"Saved health_establishments: {len(results['records'])} rows")
    print(f"Saved health_by_municipio_type: {len(results['by_municipio_type'])} rows")
    print(f"Saved health_summary.json")


if __name__ == "__main__":
    results = process_health()
    save_processed(results)
    print("Done!")
    print(f"Summary: {results['summary']}")