# HabitaGDL - Air Quality ETL

import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from ..schemas.data_models import AirQualityReading, AQStation
from ..config import PATHS, AQ_STATIONS, POLLUTANTS, METEO_VARS


def load_air_quality_data() -> pd.DataFrame:
    """Load air quality hourly data"""
    return pd.read_excel(PATHS["air_quality"], sheet_name="Data")


def load_air_quality_stations() -> pd.DataFrame:
    """Load station metadata"""
    return pd.read_excel(PATHS["air_quality"], sheet_name="Param")


def parse_stations(df: pd.DataFrame) -> List[AQStation]:
    """Parse station metadata from Param sheet"""
    stations = []
    for _, row in df.iterrows():
        code = str(row.get("Abreviatura", "")).strip()
        name = str(row.get("Estación", "")).strip()
        # S0-fix: en 3 filas (COU/SAN/SMT) la hoja Param trae las columnas
        # Estación<->Abreviatura cruzadas (código en Estación, nombre en
        # Abreviatura). Si Abreviatura parece nombre y Estación parece código,
        # se intercambian. Sin esto se perdían COU+SAN+SMT (8,784 lecturas c/u).
        if len(code) > 3 and len(name) == 3:
            code, name = name, code
        code = code.upper()
        if not code or code == "NAN":
            continue
        
        coords = str(row.get("Coordenadas", ""))
        lat, lon, alt = None, None, None
        for line in coords.split("\n"):
            line = line.strip()
            if line.startswith("Latitud:"):
                lat = float(line.replace("Latitud:", "").strip())
            elif line.startswith("Longitud:"):
                lon = float(line.replace("Longitud:", "").strip())
            elif line.startswith("Altitud:"):
                alt = int(line.replace("Altitud:", "").replace("msnm", "").strip())
        
        pollutants = [p.strip() for p in str(row.get("Parámetros de medición contaminante", "")).split(",") if p.strip()]
        meteo = [m.strip() for m in str(row.get("Parámetros de medición meteorología", "")).split(",") if m.strip()]
        
        stations.append(AQStation(
            code=code,
            name=name,
            pollutants=pollutants,
            meteo=meteo,
            lat=lat or 0,
            lon=lon or 0,
            altitude=alt or 0,
            address=str(row.get("Dirección", "")).strip(),
            year_installed=int(row.get("Año de instalación", 0)) if pd.notna(row.get("Año de instalación")) else 0,
        ))
    return stations


def parse_readings(df: pd.DataFrame, stations_map: Dict[str, AQStation]) -> List[AirQualityReading]:
    """Parse hourly readings from Data sheet"""
    readings = []
    for _, row in df.iterrows():
        station_code = str(row.get("STATION", "")).strip()
        if station_code not in stations_map:
            continue
        
        station = stations_map[station_code]
        
        date_val = row.get("DATE")
        if isinstance(date_val, str):
            date_val = pd.to_datetime(date_val)
        elif pd.isna(date_val):
            continue
        
        def get_float(col: str) -> Optional[float]:
            val = row.get(col)
            if pd.isna(val):
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None
        
        readings.append(AirQualityReading(
            station=station_code,
            date=date_val,
            hour=float(row.get("HOUR", 0)) if pd.notna(row.get("HOUR")) else 0,
            dia=str(row.get("DIA", "")),
            mes=str(row.get("MES ", "")),
            o3=get_float("O3"),
            no=get_float("NO"),
            no2=get_float("NO2"),
            nox=get_float("NOX"),
            so2=get_float("SO2"),
            co=get_float("CO"),
            pm10=get_float("PM10"),
            pm25=get_float("PM2.5"),
            it=get_float("IT"),
            et=get_float("ET"),
            rh=get_float("RH"),
            ws=get_float("WS"),
            wd=get_float("WD"),
            pp=get_float("PP"),
            atm=get_float("ATM"),
            rs=get_float("RS"),
            uvi=get_float("UVI"),
            station_name=station.name,
            municipio=station.name,  # Will map to municipio
            lat=station.lat,
            lon=station.lon,
        ))
    return readings


def enrich_with_station_info(readings: List[AirQualityReading]) -> List[AirQualityReading]:
    """Enrich readings with station metadata including municipio"""
    from ..config import AQ_STATIONS
    
    for r in readings:
        if r.station in AQ_STATIONS:
            info = AQ_STATIONS[r.station]
            r.municipio = info["municipio"]
            r.lat = info["lat"]
            r.lon = info["lon"]
    return readings


def aggregate_daily(readings: List[AirQualityReading]) -> pd.DataFrame:
    """Aggregate hourly readings to daily averages"""
    df = pd.DataFrame([{
        "station": r.station,
        "date": r.date.date(),
        "municipio": r.municipio,
        "o3": r.o3,
        "no2": r.no2,
        "pm10": r.pm10,
        "pm25": r.pm25,
        "so2": r.so2,
        "co": r.co,
        "ws": r.ws,
        "wd": r.wd,
        "temp": r.et,
        "rh": r.rh,
    } for r in readings])
    
    if df.empty:
        return df
    
    daily = df.groupby(["station", "date", "municipio"]).agg({
        "o3": "mean",
        "no2": "mean",
        "pm10": "mean",
        "pm25": "mean",
        "so2": "mean",
        "co": "mean",
        "ws": "mean",
        "wd": "mean",
        "temp": "mean",
        "rh": "mean",
    }).reset_index()
    
    return daily


def aggregate_monthly(readings: List[AirQualityReading]) -> pd.DataFrame:
    """Aggregate hourly readings to monthly averages"""
    df = pd.DataFrame([{
        "station": r.station,
        "year": r.date.year,
        "month": r.date.month,
        "municipio": r.municipio,
        "o3": r.o3,
        "no2": r.no2,
        "pm10": r.pm10,
        "pm25": r.pm25,
        "so2": r.so2,
        "co": r.co,
        "ws": r.ws,
        "wd": r.wd,
        "temp": r.et,
        "rh": r.rh,
    } for r in readings])
    
    if df.empty:
        return df
    
    monthly = df.groupby(["station", "year", "month", "municipio"]).agg({
        "o3": "mean",
        "no2": "mean",
        "pm10": "mean",
        "pm25": "mean",
        "so2": "mean",
        "co": "mean",
        "ws": "mean",
        "wd": "mean",
        "temp": "mean",
        "rh": "mean",
    }).reset_index()
    
    return monthly


def seasonal_wind_analysis(readings: List[AirQualityReading]) -> pd.DataFrame:
    """Analyze wind patterns by season"""
    df = pd.DataFrame([{
        "station": r.station,
        "date": r.date,
        "municipio": r.municipio,
        "ws": r.ws,
        "wd": r.wd,
        "pm25": r.pm25,
        "pm10": r.pm10,
        "o3": r.o3,
        "no2": r.no2,
    } for r in readings if r.ws is not None and r.wd is not None])
    
    if df.empty:
        return df
    
    def get_season(month: int) -> str:
        if month in [12, 1, 2]:
            return "invierno"
        elif month in [3, 4, 5]:
            return "primavera"
        elif month in [6, 7, 8]:
            return "verano"
        else:
            return "otoño"
    
    df["season"] = df["date"].dt.month.apply(get_season)
    
    # Wind rose data: direction bins
    def wd_bin(wd: float) -> str:
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        idx = int((wd + 11.25) / 22.5) % 16
        return dirs[idx]
    
    df["wd_bin"] = df["wd"].apply(wd_bin)
    
    # Aggregate by season, station, wind direction
    seasonal = df.groupby(["season", "station", "municipio", "wd_bin"]).agg({
        "ws": "mean",
        "pm25": "mean",
        "pm10": "mean",
        "o3": "mean",
        "no2": "mean",
    }).reset_index()
    
    return seasonal


def process_air_quality() -> Dict[str, pd.DataFrame]:
    """Full air quality processing pipeline"""
    print("Loading air quality data...")
    df_data = load_air_quality_data()
    df_stations = load_air_quality_stations()
    
    print(f"Raw readings: {len(df_data)}")
    print(f"Stations: {len(df_stations)}")
    
    print("Parsing stations...")
    stations = parse_stations(df_stations)
    stations_map = {s.code: s for s in stations}
    print(f"Parsed {len(stations)} stations")
    
    print("Parsing readings...")
    readings = parse_readings(df_data, stations_map)
    print(f"Parsed {len(readings)} readings")
    
    print("Enriching with station info...")
    readings = enrich_with_station_info(readings)
    
    print("Aggregating daily...")
    daily = aggregate_daily(readings)
    
    print("Aggregating monthly...")
    monthly = aggregate_monthly(readings)
    
    print("Analyzing seasonal wind patterns...")
    seasonal = seasonal_wind_analysis(readings)
    
    return {
        "stations": pd.DataFrame([s.__dict__ for s in stations]),
        "readings": pd.DataFrame([r.__dict__ for r in readings]),
        "daily": daily,
        "monthly": monthly,
        "seasonal_wind": seasonal,
    }


def save_processed(results: Dict[str, pd.DataFrame]) -> None:
    """Save all processed air quality data"""
    from ..config import PROCESSED_DIR
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    for name, df in results.items():
        out_path = PROCESSED_DIR / f"air_quality_{name}.parquet"
        df.to_parquet(out_path, index=False)
        print(f"Saved {name}: {len(df)} rows -> {out_path}")


if __name__ == "__main__":
    results = process_air_quality()
    save_processed(results)
    print("Done!")