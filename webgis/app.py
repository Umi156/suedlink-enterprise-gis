import os
import json
from pathlib import Path
import geopandas as gpd
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine

app = FastAPI(title="SuedLink Section BY-04 Enterprise WebGIS API")
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5435")
DB_NAME = os.getenv("DB_NAME", "suedlink_sdi")
DB_USER = os.getenv("DB_USER", "gis_admin")
DB_PASS = os.getenv("DB_PASS", "SuedLink2026Secure")

ENGINE = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
DB_CONFIG = {"host": DB_HOST, "port": int(DB_PORT), "dbname": DB_NAME, "user": DB_USER, "password": DB_PASS}


def json_ok(payload) -> Response:
    return Response(content=json.dumps(payload, default=str), media_type="application/json")


def geojson_from_postgis(sql: str) -> Response:
    gdf = gpd.read_postgis(sql, ENGINE, geom_col="geom")
    return Response(content=gdf.to_json(), media_type="application/json")


def query_rows(sql: str) -> list[dict]:
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]


@app.get("/", response_class=HTMLResponse)
def serve_portal():
    return (Path(__file__).parent / "index.html").read_text(encoding="utf-8")


@app.get("/api/kpis")
def get_kpis():
    return json_ok({
        "routes": query_rows("SELECT variant_name, ROUND(length_m::numeric,1)::float AS length_m, ROUND(min_elevation_z::numeric,1)::float AS min_elevation_z, voltage_kv, iso19650_doc_id, planning_status FROM suedlink_prod.cable_alignments ORDER BY variant_name;"),
        "conflicts": query_rows("SELECT variant_name, conflict_type, COUNT(*)::int AS count, ROUND(COALESCE(SUM(overlap_area_sqm),0)::numeric,1)::float AS total_sqm FROM suedlink_prod.spatial_conflicts GROUP BY variant_name, conflict_type ORDER BY variant_name, conflict_type;"),
        "quarantine": query_rows("SELECT error_id, source_file, cad_layer, qa_error_reason, TO_CHAR(detected_at,'YYYY-MM-DD HH24:MI') AS detected_at FROM suedlink_qa.cad_rejected_features;"),
    })


@app.get("/api/layers/alignments")
def layer_alignments():
    return geojson_from_postgis("SELECT route_id, variant_name, section_code, voltage_kv, iso19650_doc_id, ROUND(length_m::numeric,1)::float AS length_m, ROUND(min_elevation_z::numeric,1)::float AS min_elevation_z, ST_Transform(ST_Force2D(ST_CurveToLine(geom)),4326) AS geom FROM suedlink_prod.cable_alignments;")


@app.get("/api/layers/buffers")
def layer_buffers():
    return geojson_from_postgis("SELECT buffer_id, variant_name, buffer_type, ROUND(area_sqm::numeric,1)::float AS area_sqm, ST_Transform(ST_CurveToLine(geom),4326) AS geom FROM suedlink_prod.corridor_buffers;")


@app.get("/api/layers/conflicts")
def layer_conflicts():
    return geojson_from_postgis("SELECT conflict_id, variant_name, conflict_type, constraint_name, recommended_method, ROUND(COALESCE(overlap_area_sqm,0)::numeric,1)::float AS overlap_area_sqm, ST_Transform(ST_Force2D(ST_CurveToLine(geom)),4326) AS geom FROM suedlink_prod.spatial_conflicts;")


@app.get("/api/layers/natura2000")
def layer_natura2000():
    return geojson_from_postgis("SELECT id, site_code, site_name, protection_type, ST_Transform(ST_CurveToLine(geom),4326) AS geom FROM suedlink_prod.env_natura2000;")


@app.get("/api/layers/quarantine")
def layer_quarantine():
    return geojson_from_postgis("SELECT error_id, source_file, cad_layer, qa_error_reason, ST_Transform(ST_Force2D(ST_CurveToLine(geom)),4326) AS geom FROM suedlink_qa.cad_rejected_features;")

