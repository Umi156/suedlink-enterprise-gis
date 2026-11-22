import urllib.request
from pathlib import Path
import geopandas as gpd
from sqlalchemy import create_engine

Path("webgis/static").mkdir(parents=True, exist_ok=True)
Path("data/webgis_snapshot").mkdir(parents=True, exist_ok=True)

urllib.request.urlretrieve(
    "https://unpkg.com",
    "webgis/static/leaflet.css",
)
urllib.request.urlretrieve(
    "https://unpkg.com",
    "webgis/static/leaflet.js",
)
print("Leaflet CSS & JS downloaded.")

eng = create_engine("postgresql+psycopg2://gis_admin:SuedLink2026Secure@127.0.0.1:5435/suedlink_sdi")

queries = {
    "alignments": "SELECT route_id, variant_name, section_code, voltage_kv, iso19650_doc_id, ROUND(length_m::numeric, 1)::float AS length_m, ROUND(min_elevation_z::numeric, 1)::float AS min_elevation_z, planning_status, ST_Transform(ST_Force2D(ST_CurveToLine(geom)), 4326) AS geom FROM suedlink_prod.cable_alignments",
    "buffers": "SELECT buffer_id, variant_name, buffer_type, ROUND(area_sqm::numeric, 1)::float AS area_sqm, ST_Transform(ST_CurveToLine(geom), 4326) AS geom FROM suedlink_prod.corridor_buffers",
    "conflicts": "SELECT conflict_id, variant_name, conflict_type, constraint_name, recommended_method, ROUND(COALESCE(overlap_area_sqm, 0)::numeric, 1)::float AS overlap_area_sqm, ST_Transform(ST_Force2D(ST_CurveToLine(geom)), 4326) AS geom FROM suedlink_prod.spatial_conflicts",
    "natura": "SELECT id, site_code, site_name, protection_type, ST_Transform(ST_CurveToLine(geom), 4326) AS geom FROM suedlink_prod.env_natura2000",
    "quarantine": "SELECT error_id, source_file, cad_layer, qa_error_reason, TO_CHAR(detected_at, 'YYYY-MM-DD HH24:MI') AS detected_at, ST_Transform(ST_Force2D(ST_CurveToLine(geom)), 4326) AS geom FROM suedlink_qa.cad_rejected_features",
}

for name, sql in queries.items():
    gpd.read_postgis(sql, eng, geom_col="geom").to_file(
        f"data/webgis_snapshot/{name}.geojson", driver="GeoJSON"
    )
    print(f"Exported {name}.geojson")

print("ALL ASSETS & GEOJSON SNAPSHOTS READY!")
