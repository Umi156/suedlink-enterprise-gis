import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
import requests
import geopandas as gpd

PROCESSED_DIR = Path("data/processed")
OUT_GPKG = PROCESSED_DIR / "unterfranken_infrastruktur_dlm250_25832.gpkg"
WFS_URL = "https://geodatenzentrum.de"

# Bounding Box rund um Würzburg in EPSG:25832 (xmin, ymin, xmax, ymax)
BBOX_25832 = "545000,5495000,595000,5545000,urn:ogc:def:crs:EPSG::25832"


def discover_layers() -> dict[str, str]:
    """Fragt GetCapabilities per modernem HTTP/1.1 (requests) ab und liest alle <FeatureType> Name + Title."""
    resp = requests.get(
        WFS_URL,
        params={"service": "WFS", "version": "2.0.0", "request": "GetCapabilities"},
        timeout=60,
    )
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    discovered = {}
    for ft in root.iter():
        if ft.tag.endswith("FeatureType"):
            name_el = next((c for c in ft if c.tag.endswith("Name")), None)
            title_el = next((c for c in ft if c.tag.endswith("Title")), None)
            if name_el is not None and name_el.text:
                tech_name = name_el.text.strip()
                title = title_el.text.strip() if (title_el is not None and title_el.text) else tech_name
                discovered[tech_name] = title
    return discovered


def fetch_wfs_gml3(type_name: str, out_layer: str):
    """Lädt Features per HTTP/1.1 GET (GML3) in EPSG:25832 herunter."""
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": type_name,
        "srsName": "urn:ogc:def:crs:EPSG::25832",
        "outputFormat": "gml3",
        "bbox": BBOX_25832,
    }
    print(f"[BKG WFS] Lade '{out_layer}' ({type_name}) im Raum Würzburg...")
    resp = requests.get(WFS_URL, params=params, timeout=90)
    resp.raise_for_status()

    if "html" in resp.headers.get("Content-Type", "").lower():
        raise ValueError(f"Server lieferte HTML statt GML für {type_name}")

    gdf = gpd.read_file(BytesIO(resp.content))
    if gdf.crs is None or gdf.crs.to_epsg() != 25832:
        gdf = gdf.set_crs(epsg=25832, allow_override=True)

    gdf.to_file(OUT_GPKG, layer=out_layer, driver="GPKG")
    print(f"      -> {len(gdf)} Features in '{out_layer}' (EPSG:25832) gespeichert.")


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if OUT_GPKG.exists():
        OUT_GPKG.unlink()

    print("[BKG WFS] Ermittle verfügbare DLM250-Layer dynamisch...")
    layers = discover_layers()
    print(f"[BKG WFS] {len(layers)} Layer entdeckt.")

    targets = [
        (["fließgewässer", "fliessgewaesser", "44001_l"], "dlm250_gewaesser"),
        (["straßenachse", "strassenachse", "42003_l"], "dlm250_strassen"),
        (["bahnstrecke", "42014_l"], "dlm250_schienen"),
    ]

    for keywords, out_layer in targets:
        matched = next(
            (
                tech for tech, title in layers.items()
                if any(k in tech.lower() or k in title.lower() for k in keywords)
                and tech.endswith("_l")
            ),
            None,
        )
        if not matched:
            print(f"[WARNUNG] Kein passender Linien-Layer für {keywords} gefunden.")
            continue

        fetch_wfs_gml3(matched, out_layer)

    if OUT_GPKG.exists():
        print(f"FERTIG! Amtliche Kreuzungsdaten gespeichert unter: {OUT_GPKG}")


if __name__ == "__main__":
    main()
