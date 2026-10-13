# HabitaGDL - IIEG and Services ETL

import pandas as pd
from pathlib import Path
from typing import Dict, List
from ..schemas.data_models import IIEGMunicipio, INEGIService
from ..config import PATHS, ZMG_MUNICIPIOS


def load_iieg() -> pd.DataFrame:
    """Load IIEG household characteristics - header row is at index 2 (3rd row)"""
    df = pd.read_excel(PATHS["iieg"], header=None)
    # Row 0: title
    # Row 1: column group headers
    # Row 2: detailed headers (Clave, Nombre, Hogares 2020, etc.)
    # Row 3+: data
    return df


def parse_iieg_row(row: pd.Series) -> IIEGMunicipio:
    """Parse IIEG row - columns: 0=empty, 1=clave, 2=nombre, 3+=data"""
    def get_float(val):
        if pd.isna(val):
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def get_str(val):
        if pd.isna(val):
            return None
        return str(val).strip()

    return IIEGMunicipio(
        clave=get_str(row.iloc[1]) or "",
        nombre=get_str(row.iloc[2]) or "",
        hogares_2020=get_float(row.iloc[3]),
        hogares_masc_2020=get_float(row.iloc[4]),
        hogares_fem_2020=get_float(row.iloc[5]),
        pob_hogares_2020=get_float(row.iloc[6]),
        hogares_2015=get_float(row.iloc[9]),
        hogares_masc_2015=get_float(row.iloc[10]),
        hogares_fem_2015=get_float(row.iloc[11]),
        pob_hogares_2015=get_float(row.iloc[12]),
        hogares_2010=get_float(row.iloc[15]),
        hogares_masc_2010=get_float(row.iloc[16]),
        hogares_fem_2010=get_float(row.iloc[17]),
        pob_hogares_2010=get_float(row.iloc[18]),
        hogares_2000=get_float(row.iloc[21]),
        hogares_masc_2000=get_float(row.iloc[22]),
        hogares_fem_2000=get_float(row.iloc[23]),
        pob_hogares_2000=get_float(row.iloc[24]),
        raw=row.to_dict(),
    )


def load_zgm_iieg() -> List[IIEGMunicipio]:
    """Load IIEG for ZMG municipalities"""
    df = load_iieg()
    # Data starts at row 3 (index 3)
    data_df = df.iloc[3:].copy()
    
    # Filter to ZMG by name (column 2) - include alternative names
    from ..config import ZMG_MUNICIPIOS, ZMG_MUNICIPIOS_ALT
    all_names = ZMG_MUNICIPIOS + list(ZMG_MUNICIPIOS_ALT.keys())
    df_zgm = data_df[data_df.iloc[:, 2].isin(all_names)].copy()
    
    print(f"IIEG total data rows: {len(data_df)}")
    print(f"ZMG rows: {len(df_zgm)}")
    print(f"Municipios found: {df_zgm.iloc[:, 2].unique()}")
    
    return [parse_iieg_row(row) for _, row in df_zgm.iterrows()]


def load_zgm_iieg_df() -> pd.DataFrame:
    """Load IIEG for ZMG municipalities as DataFrame (without raw dict)"""
    records = load_zgm_iieg()
    # Exclude raw dict for parquet compatibility
    data = []
    for r in records:
        d = r.__dict__.copy()
        d.pop('raw', None)
        data.append(d)
    return pd.DataFrame(data)


def load_services() -> pd.DataFrame:
    """Load INEGI basic services export (header=None: la primera fila es dato).

    S0: el archivo trae UNA consulta real (bloque: fila 'Consulta de:...',
    fila encabezado con 'Total|Disponen...', filas por entidad, fila FUENTE)
    precedida por la lista del menú del exportador (filas sin valores)."""
    return pd.read_excel(PATHS["services"], header=None)


def _to_float(val):
    if pd.isna(val):
        return None
    if isinstance(val, str):
        val = val.replace(",", "").replace(" ", "").replace("$", "")
        if val in ("", "-", "N.D.", "ND"):
            return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def parse_services(df: pd.DataFrame) -> List[INEGIService]:
    """Extrae el bloque de datos: variable (de 'Consulta de:... Según: X'),
    fila nacional + fila Jalisco con total/disponen/no_disponen/no_esp."""
    variable = "Servicio INEGI (ver Consulta de:)"
    for _, row in df.iterrows():
        cell = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
        if cell.startswith("Consulta de:"):
            # '... Según: Disponibilidad de energía eléctrica'
            variable = cell.split("Según:")[-1].strip() if "Según:" in cell else cell
            break

    header_idx = None
    for i, row in df.iterrows():
        if str(row.iloc[2]) == "Total" and str(row.iloc[3]).startswith("Disponen"):
            header_idx = i
            break
    if header_idx is None:
        return []

    services = []
    for i in range(header_idx + 1, len(df)):
        row = df.iloc[i]
        nombre = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        if nombre.startswith("FUENTE") or (pd.isna(row.iloc[1]) and pd.isna(row.iloc[2])):
            break
        clave = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        es_nacional = clave == ""
        if es_nacional and nombre != "Total":
            continue
        total = _to_float(row.iloc[2])
        disp = _to_float(row.iloc[3])
        services.append(INEGIService(
            variable=variable,
            entidad_clave=clave if clave else "00",
            entidad="Nacional" if es_nacional else nombre,
            total=total,
            disponen=disp,
            no_disponen=_to_float(row.iloc[4]),
            no_especificado=_to_float(row.iloc[5]),
            pct_disponen=round(disp / total * 100, 2) if total else None,
            raw={},
        ))
        if not es_nacional and (clave == "14" or nombre == "Jalisco"):
            break  # con Nacional + Jalisco basta para la tesis/ZMG
    return services


def process_iieg() -> Dict:
    """Process IIEG data"""
    df = load_zgm_iieg_df()
    return {"records": df}


def process_services() -> Dict:
    """Process INEGI services data (bloque energía eléctrica: Nacional + Jalisco)"""
    df_raw = load_services()
    services = parse_services(df_raw)
    data = []
    for s in services:
        d = s.__dict__.copy()
        d.pop("raw", None)  # dict vacío: pyarrow no lo escribe
        data.append(d)
    return {"records": pd.DataFrame(data), "raw": df_raw}


def save_processed_iieg(results: Dict) -> None:
    from ..config import PROCESSED_DIR
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    results["records"].to_parquet(PROCESSED_DIR / "iieg_municipios.parquet", index=False)
    print(f"Saved IIEG: {len(results['records'])} rows")


def save_processed_services(results: Dict) -> None:
    from ..config import PROCESSED_DIR
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    results["records"].to_parquet(PROCESSED_DIR / "services_inegi.parquet", index=False)
    print(f"Saved services: {len(results['records'])} rows")


if __name__ == "__main__":
    print("Processing IIEG...")
    iieg_results = process_iieg()
    save_processed_iieg(iieg_results)
    
    print("\nProcessing Services...")
    svc_results = process_services()
    save_processed_services(svc_results)
    
    print("\nDone!")