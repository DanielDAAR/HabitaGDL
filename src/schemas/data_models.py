# HabitaGDL - Data schemas and models

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import unicodedata


def norm_mun(s: Optional[str]) -> str:
    """Normaliza nombre de municipio: mayúsculas, sin acentos, sin espacios extra.
    S0-fix: CLUES trae 'ZAPOPAN'/'TONALA' y el Enum trae 'Zapopan'/'Tonalá';
    sin normalizar, HealthEstablishment.is_zgm siempre era False."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s).strip().upper())
    return "".join(c for c in s if not unicodedata.combining(c))


class MunicipioZMG(str, Enum):
    GUADALAJARA = "Guadalajara"
    ZAPOPAN = "Zapopan"
    SAN_PEDRO_TLAQUEPAQUE = "San Pedro Tlaquepaque"
    TONALA = "Tonalá"
    TLAJOMULCO_DE_ZUNIGA = "Tlajomulco de Zúñiga"


class TamanoLocalidad(str, Enum):
    HASTA_249 = "1"
    DE_250_A_499 = "2"
    DE_500_A_999 = "3"
    DE_1000_A_2499 = "4"
    DE_2500_A_4999 = "5"
    DE_5000_A_9999 = "6"
    DE_10000_A_14999 = "7"
    DE_15000_A_19999 = "8"
    DE_20000_A_24999 = "9"
    DE_25000_A_49999 = "10"
    DE_50000_A_99999 = "11"
    DE_100000_A_199999 = "12"
    DE_200000_A_499999 = "13"
    DE_500000_A_999999 = "14"
    DE_1000000_MAS = "15"


@dataclass
class IterLocalidad:
    """INEGI ITER 2020 - locality/AGEB level record"""
    entidad: str
    nom_ent: str
    mun: str
    nom_mun: str
    loc: str
    nom_loc: str
    longitud: Optional[str]
    latitud: Optional[str]
    altitud: Optional[str]
    pobtot: Optional[int]
    pobfem: Optional[int]
    pobmas: Optional[int]
    
    # Age groups
    p_0a2: Optional[int] = None
    p_3ymas: Optional[int] = None
    p_5ymas: Optional[int] = None
    p_12ymas: Optional[int] = None
    p_15ymas: Optional[int] = None
    p_18ymas: Optional[int] = None
    p_60ymas: Optional[int] = None
    
    # Education
    p15pri_in: Optional[int] = None
    p15pri_co: Optional[int] = None
    p15sec_in: Optional[int] = None
    p15sec_co: Optional[int] = None
    graproes: Optional[float] = None
    
    # Economic
    pea: Optional[int] = None
    pocupada: Optional[int] = None
    pdesocup: Optional[int] = None
    
    # Housing
    vph_autom: Optional[int] = None
    vph_moto: Optional[int] = None
    vph_bici: Optional[int] = None
    vph_inter: Optional[int] = None
    vph_pc: Optional[int] = None
    vph_cel: Optional[int] = None
    vph_stvp: Optional[int] = None
    vph_refri: Optional[int] = None
    vph_lavad: Optional[int] = None
    vph_micro: Optional[int] = None
    vph_horno: Optional[int] = None
    vph_tv: Optional[int] = None
    vph_dren: Optional[int] = None
    vph_cister: Optional[int] = None
    
    # Raw row data for extensibility
    raw: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_zgm(self) -> bool:
        return norm_mun(self.nom_mun) in [norm_mun(m.value) for m in MunicipioZMG]

    @property
    def municipio_enum(self) -> Optional[MunicipioZMG]:
        for m in MunicipioZMG:
            if norm_mun(m.value) == norm_mun(self.nom_mun):
                return m
        return None


@dataclass
class AirQualityReading:
    """Hourly air quality reading from SEMADET station"""
    station: str
    date: datetime
    hour: float
    dia: str  # Excel formula
    mes: str  # Excel formula
    
    # Pollutants (ppm or ug/m3)
    o3: Optional[float] = None
    no: Optional[float] = None
    no2: Optional[float] = None
    nox: Optional[float] = None
    so2: Optional[float] = None
    co: Optional[float] = None
    pm10: Optional[float] = None
    pm25: Optional[float] = None
    
    # Meteorological
    it: Optional[float] = None  # Internal temp
    et: Optional[float] = None  # External temp
    rh: Optional[float] = None  # Relative humidity
    ws: Optional[float] = None  # Wind speed
    wd: Optional[float] = None  # Wind direction
    pp: Optional[float] = None  # Precipitation
    atm: Optional[float] = None  # Atmospheric pressure
    rs: Optional[float] = None  # Solar radiation
    uvi: Optional[float] = None  # UV index
    
    # Computed
    station_name: Optional[str] = None
    municipio: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


@dataclass
class AQStation:
    """Air quality monitoring station metadata"""
    code: str
    name: str
    pollutants: List[str]
    meteo: List[str]
    lat: float
    lon: float
    altitude: int
    address: str
    year_installed: int


@dataclass
class HealthEstablishment:
    """Health establishment from CLUES"""
    clues: str
    institucion: str
    nombre: str
    entidad: str
    municipio: str
    localidad: str
    tipo_establecimiento: str
    tipologia: str
    subtipologia: str
    lat: Optional[float]
    lon: Optional[float]
    status: str
    raw: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_zgm(self) -> bool:
        return norm_mun(self.municipio) in [norm_mun(m.value) for m in MunicipioZMG]


@dataclass
class IIEGMunicipio:
    """IIEG household characteristics by municipality"""
    clave: str
    nombre: str
    hogares_2020: float
    hogares_masc_2020: float
    hogares_fem_2020: float
    pob_hogares_2020: float
    hogares_2015: float
    hogares_masc_2015: float
    hogares_fem_2015: float
    pob_hogares_2015: float
    hogares_2010: float
    hogares_masc_2010: float
    hogares_fem_2010: float
    pob_hogares_2010: float
    hogares_2000: float
    hogares_masc_2000: float
    hogares_fem_2000: float
    pob_hogares_2000: float
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class INEGIService:
    """Viviendas por entidad según un servicio (bloque del export INEGI).

    S0: el XLS 'INEGI_exporta_...' NO trae 59 variables con datos; trae UNA
    consulta real ('Disponibilidad de energía eléctrica' por entidad) + la
    lista del menú como filas sin valores. Este modelo guarda ese bloque con
    su fila nacional y su fila Jalisco. Las demás variables de servicios para
    la ZMG salen de ITER (VPH_DREN, VPH_CISTER, etc. en iter_zgm.parquet)."""
    variable: str
    entidad_clave: str = ""
    entidad: str = ""
    total: Optional[float] = None
    disponen: Optional[float] = None
    no_disponen: Optional[float] = None
    no_especificado: Optional[float] = None
    pct_disponen: Optional[float] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ZMGUnifiedRecord:
    """Unified record for a ZMG locality/AGEB combining all dimensions"""
    # Geography
    entidad: str
    nom_ent: str
    mun: str
    nom_mun: str
    loc: str
    nom_loc: str
    longitud: Optional[float]
    latitud: Optional[float]
    altitud: Optional[float]
    
    # Demographics (from ITER)
    pobtot: Optional[int] = None
    pobfem: Optional[int] = None
    pobmas: Optional[int] = None
    p_0a2: Optional[int] = None
    p_60ymas: Optional[int] = None
    graproes: Optional[float] = None
    
    # Housing
    vph_inter: Optional[int] = None
    vph_pc: Optional[int] = None
    vph_cel: Optional[int] = None
    vph_refri: Optional[int] = None
    vph_lavad: Optional[int] = None
    vph_dren: Optional[int] = None
    vph_cister: Optional[int] = None
    vph_autom: Optional[int] = None
    
    # Economic
    pea: Optional[int] = None
    pocupada: Optional[int] = None
    
    # Air quality (aggregated)
    aq_o3_mean: Optional[float] = None
    aq_pm25_mean: Optional[float] = None
    aq_pm10_mean: Optional[float] = None
    aq_no2_mean: Optional[float] = None
    aq_station_count: int = 0
    
    # Health
    health_total: int = 0
    health_hospitals: int = 0
    health_consulta: int = 0
    
    # Education (placeholder)
    schools_total: int = 0
    
    # Services
    services_raw: Dict[str, Any] = field(default_factory=dict)
    
    # IIEG
    iieg_hogares_2020: Optional[float] = None
    iieg_pob_hogares_2020: Optional[float] = None
    
    # Metadata
    source_iter: bool = False
    source_aq: bool = False
    source_health: bool = False
    source_iieg: bool = False