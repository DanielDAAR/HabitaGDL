# S1 — tests de escuelas + motor IHT (stdlib + pandas, sin pytest).
# Uso: python tests/test_s1.py  →  exit 0 = todo verde.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

fails = []


def check(nombre, cond):
    print(("  OK  " if cond else "  FAIL") + nombre)
    if not cond:
        fails.append(nombre)


# 1. Escuelas ZMG
from src.etl.schools_etl import load_schools_raw, parse_schools
esc = parse_schools(load_schools_raw())
check("escuelas ZMG=5825", len(esc) == 5825)
check("5 municipios", esc["municipio_norm"].nunique() == 5)
check("coords válidas GDL/ZPN",
      esc["lat"].notna().sum() > 5000)
check("hay pública y privada",
      set(esc["sostenimiento"].str.upper().unique()) >= {"PÚBLICO", "PRIVADO"})

# 2. Motor IHT
from src.iht import calcular_iht, PESOS_DEFAULT, PRESETS
check("pesos default suman 1", abs(sum(PESOS_DEFAULT.values()) - 1.0) < 1e-9)
for nombre, p in PRESETS.items():
    check(f"preset {nombre} suma 1", abs(sum(p.values()) - 1.0) < 1e-9)

iht = calcular_iht()
val = iht[iht["IHT"].notna()]
import pandas as pd
n_iter = len(pd.read_parquet("data/processed/iter_zgm.parquet"))
n_tot = (pd.read_parquet("data/processed/iter_zgm.parquet")["NOM_LOC"].astype(str).str.startswith("Total del")).sum()
check(f"todas las localidades menos agregados ({n_iter - n_tot})", len(iht) == n_iter - n_tot)
check("IHT válidos en [0,100]",
      bool(((val["IHT"] >= 0) & (val["IHT"] <= 100)).all()) and len(val) > 200)
check("cobertura=5/8 en válidos", bool((val["cobertura"] == 5).all()))
check("top > bottom +10", val["IHT"].max() > val["IHT"].min() + 10)
top = val.nlargest(3, "IHT")[["nom_loc", "municipio", "IHT"]]
print("TOP 3:\n" + top.to_string(index=False))

print("VERDE" if not fails else f"ROJO: {fails}")
sys.exit(1 if fails else 0)
