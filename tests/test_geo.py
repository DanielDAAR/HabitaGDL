# S1-geo — tests AGEB + join IHT x AGEB (stdlib + pandas + geopandas).
# Uso: python tests/test_geo.py  →  exit 0 = todo verde.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

fails = []


def check(nombre, cond):
    print(("  OK  " if cond else "  FAIL") + nombre)
    if not cond:
        fails.append(nombre)


import geopandas as gpd
import pandas as pd

ageb = gpd.read_file("data/processed/ageb_zmg.geojson")
check("1724 AGEBs ZMG", len(ageb) == 1724)
gdl = ageb[ageb["CVE_MUN"] == "039"]
check("GDL con 442 AGEBs (cierra QA-1)", len(gdl) == 442)

from src.iht import join_iht_ageb
j = join_iht_ageb()
n = int(j["IHT"].notna().sum())
check("AGEBs con IHT > 90%", n / len(j) > 0.90)
check("IHT AGEB en [0,100]",
      bool(((j["IHT"].dropna() >= 0) & (j["IHT"].dropna() <= 100)).all()))
gdl_iht = j[(j["CVE_MUN"] == "039") & j["IHT"].notna()]
check("GDL con IHT > 400 AGEBs", len(gdl_iht) > 400)
print(f"AGEBs con IHT: {n}/{len(j)}, media={j['IHT'].mean():.1f}")
print("TOP 3 AGEB:\n" + j.nlargest(3, "IHT")[
    ["CVEGEO", "NOM_MUN", "nom_loc_ref", "IHT"]].to_string(index=False))

print("VERDE" if not fails else f"ROJO: {fails}")
sys.exit(1 if fails else 0)
