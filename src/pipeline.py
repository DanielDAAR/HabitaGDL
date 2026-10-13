# HabitaGDL - Main ETL Pipeline

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .etl.iter_etl import load_iter_full, filter_zgm, iter_localidades_zgm, iter_to_dataframe, save_processed
from .etl.air_quality_etl import process_air_quality, save_processed as save_aq
from .etl.health_etl import process_health, save_processed as save_health
from .etl.iieg_services_etl import process_iieg, process_services, save_processed_iieg, save_processed_services
from .config import PROCESSED_DIR, ZMG_MUNICIPIOS


def run_iter_etl():
    """Run INEGI ITER ETL"""
    print("=" * 50)
    print("Running ITER ETL...")
    print("=" * 50)
    
    df = load_iter_full()
    print(f"Total rows: {len(df)}")
    
    df_zgm = filter_zgm(df)
    print(f"ZMG rows: {len(df_zgm)}")
    print(f"Municipios: {df_zgm['NOM_MUN'].unique()}")
    
    # Save ZMG subset
    out_path = PROCESSED_DIR / "iter_zgm.parquet"
    df_zgm.to_parquet(out_path, index=False)
    print(f"Saved: {out_path}")
    
    # Also save as parsed objects
    records = iter_localidades_zgm()
    df_parsed = iter_to_dataframe(records)
    out_path2 = PROCESSED_DIR / "iter_zgm_parsed.parquet"
    df_parsed.to_parquet(out_path2, index=False)
    print(f"Saved parsed: {out_path2}")
    
    return df_zgm


def run_air_quality_etl():
    """Run Air Quality ETL"""
    print("=" * 50)
    print("Running Air Quality ETL...")
    print("=" * 50)
    
    results = process_air_quality()
    save_aq(results)
    
    return results


def run_health_etl():
    """Run Health ETL"""
    print("=" * 50)
    print("Running Health ETL...")
    print("=" * 50)
    
    results = process_health()
    save_health(results)
    
    return results


def run_iieg_etl():
    """Run IIEG ETL"""
    print("=" * 50)
    print("Running IIEG ETL...")
    print("=" * 50)
    
    results = process_iieg()
    save_processed_iieg(results)
    
    return results


def run_services_etl():
    """Run Services ETL"""
    print("=" * 50)
    print("Running Services ETL...")
    print("=" * 50)
    
    results = process_services()
    save_processed_services(results)
    
    return results


def run_all():
    """Run all ETL processes"""
    print("=" * 60)
    print("HABITAGDL - FULL ETL PIPELINE")
    print("=" * 60)
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    try:
        results["iter"] = run_iter_etl()
    except Exception as e:
        print(f"ERROR in ITER ETL: {e}")
        results["iter"] = None
    
    try:
        results["air_quality"] = run_air_quality_etl()
    except Exception as e:
        print(f"ERROR in Air Quality ETL: {e}")
        results["air_quality"] = None
    
    try:
        results["health"] = run_health_etl()
    except Exception as e:
        print(f"ERROR in Health ETL: {e}")
        results["health"] = None
    
    try:
        results["iieg"] = run_iieg_etl()
    except Exception as e:
        print(f"ERROR in IIEG ETL: {e}")
        results["iieg"] = None
    
    try:
        results["services"] = run_services_etl()
    except Exception as e:
        print(f"ERROR in Services ETL: {e}")
        results["services"] = None
    
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    
    for name, result in results.items():
        status = "OK" if result is not None else "FAILED"
        print(f"  {name}: {status}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="HabitaGDL ETL Pipeline")
    parser.add_argument(
        "step",
        nargs="?",
        choices=["all", "iter", "air", "health", "iieg", "services"],
        default="all",
        help="ETL step to run",
    )
    args = parser.parse_args()
    
    if args.step == "all" or args.step is None:
        run_all()
    elif args.step == "iter":
        run_iter_etl()
    elif args.step == "air":
        run_air_quality_etl()
    elif args.step == "health":
        run_health_etl()
    elif args.step == "iieg":
        run_iieg_etl()
    elif args.step == "services":
        run_services_etl()


if __name__ == "__main__":
    main()