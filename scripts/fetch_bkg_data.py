import argparse
import zipfile
from io import BytesIO
from pathlib import Path
import requests
import geopandas as gpd

RAW_DIR = Path("data/raw/bkg_vg250")
PROCESSED_DIR = Path("data/processed")
OUT_GPKG = PROCESSED_DIR / "unterfranken_gemeinden_25832.gpkg"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SuedLink-GIS-Pipeline/1.0"
}


def fetch_via_wfs() -> gpd.GeoDataFrame:
    """Variante 1: Direkter Abruf über BKG OGC WFS (GML3 + BBOX für Raum Würzburg/Unterfranken)."""
    wfs_url = "https://sgx.geodatenzentrum.de/wfs_vg250"
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "vg250:vg250_gem",
        "srsName": "urn:ogc:def:crs:EPSG::25832",
        "outputFormat": "gml3",
        "bbox": "535000,5495000,615000,5575000,urn:ogc:def:crs:EPSG::25832"
    }
    print("[WFS] Frage Gemeinden im Raum Würzburg/Unterfranken über BKG OGC WFS (GML3, EPSG:25832) ab...")
    response = requests.get(wfs_url, params=params, headers=HEADERS, timeout=60)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    if "html" in content_type or response.content.lstrip().startswith(b"<!DOCTYPE"):
        raise ValueError(f"Server hat HTML statt GML zurückgegeben (Content-Type: {content_type})")

    gdf = gpd.read_file(BytesIO(response.content))
    if "ars" in gdf.columns:
        gdf = gdf[gdf["ars"].astype(str).str.startswith("096")].copy()
    elif "ARS" in gdf.columns:
        gdf = gdf[gdf["ARS"].astype(str).str.startswith("096")].copy()

    if gdf.crs is None or gdf.crs.to_epsg() != 25832:
        gdf = gdf.set_crs(epsg=25832, allow_override=True)
    return gdf


def fetch_via_zip() -> gpd.GeoDataFrame:
    """Variante 2: Download des BKG VG250-EW GeoPackage-Archivs + Filter auf Unterfranken."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    url = "https://bund.de"
    zip_path = RAW_DIR / "vg250_utm32s.zip"

    print("[ZIP] Lade BKG VG250-EW Gesamtarchiv (EPSG:25832) herunter...")
    response = requests.get(url, headers=HEADERS, stream=True, timeout=120)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    if "html" in content_type:
        raise ValueError("Download-Server hat HTML statt einer ZIP-Datei geliefert.")

    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print("[ZIP] Entpacke Archiv...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(RAW_DIR)

    gpkg_files = list(RAW_DIR.rglob("*.gpkg"))
    if not gpkg_files:
        raise FileNotFoundError("Keine GeoPackage-Datei im BKG-Archiv gefunden.")

    gpkg_path = gpkg_files[0]
    print(f"[ZIP] Lese und filtere Gemeinden aus {gpkg_path.name}...")
    gdf_gem = gpd.read_file(gpkg_path, layer="vg250_gem")
    ars_col = "ARS" if "ARS" in gdf_gem.columns else "ars"
    return gdf_gem[gdf_gem[ars_col].astype(str).str.startswith("096")].copy()


def main():
    parser = argparse.ArgumentParser(description="BKG VG250 Datenabruf (WFS & ZIP Fallback)")
    parser.add_argument(
        "--mode",
        choices=["auto", "wfs", "zip"],
        default="auto",
        help="auto = erst WFS, bei Fehler ZIP | wfs = nur WFS | zip = nur ZIP-Download"
    )
    args = parser.parse_args()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if args.mode == "wfs":
        gdf_unterfranken = fetch_via_wfs()
    elif args.mode == "zip":
        gdf_unterfranken = fetch_via_zip()
    else:
        try:
            gdf_unterfranken = fetch_via_wfs()
        except Exception as e:
            print(f"[WARNUNG] WFS-Abruf nicht möglich ({type(e).__name__}: {e}). Wechsle zu ZIP-Download...")
            gdf_unterfranken = fetch_via_zip()

    gdf_unterfranken.to_file(OUT_GPKG, layer="gemeinden_unterfranken", driver="GPKG")
    print(f"FERTIG! {len(gdf_unterfranken)} Gemeinden (EPSG:{gdf_unterfranken.crs.to_epsg()}) gespeichert unter: {OUT_GPKG}")


if __name__ == "__main__":
    main()
