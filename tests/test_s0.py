# S0 — test de regresión de los 3 fixes (stdlib + pandas, sin pytest).
# Uso: python tests/test_s0.py  →  exit 0 = todo verde.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.schemas.data_models import HealthEstablishment, norm_mun

fails = []


def check(nombre, cond):
    print(("  OK  " if cond else "  FAIL") + nombre)
    if not cond:
        fails.append(nombre)


# 1. is_zgm con mayúsculas sin acentos (formato CLUES)
h = HealthEstablishment("X", "I", "N", "JALISCO", "ZAPOPAN", "L", "T", "T", "S", 20.0, -103.0, "OP", {})
check("is_zgm ZAPOPAN", h.is_zgm)
h2 = HealthEstablishment("X", "I", "N", "JALISCO", "TONALA", "L", "T", "T", "S", None, None, "OP", {})
check("is_zgm TONALA (sin acento)", h2.is_zgm)
check("norm_mun Tlajomulco", norm_mun("Tlajomulco de Zúñiga") == norm_mun("TLAJOMULCO DE ZUÑIGA"))

# 2. Param: Estación<->Abreviatura cruzadas se corrigen
from src.etl.air_quality_etl import load_air_quality_stations, parse_stations
stations = parse_stations(load_air_quality_stations())
codigos = {s.code for s in stations}
check("COU recuperado", "COU" in codigos)
check("SAN recuperado", "SAN" in codigos)
check("SMT recuperado", "SMT" in codigos)
smt = next(s for s in stations if s.code == "SMT")
check("SMT con coords reales", smt.lat != 0 and smt.lon != 0)

# 3. Services: bloque energía eléctrica con Nacional + Jalisco
from src.etl.iieg_services_etl import load_services, parse_services
svc = parse_services(load_services())
jal = next((s for s in svc if s.entidad == "Jalisco"), None)
check("bloque Jalisco extraído", jal is not None)
check("Jalisco total=2327794", jal is not None and jal.total == 2327794.0)
check("Jalisco pct~99.0", jal is not None and jal.pct_disponen is not None and 98.5 < jal.pct_disponen < 99.5)

print("VERDE" if not fails else f"ROJO: {fails}")
sys.exit(1 if fails else 0)
