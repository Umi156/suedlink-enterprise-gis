import os
import re
from pathlib import Path
import pandas as pd
import geopandas as gpd
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
from sqlalchemy import create_engine, text

st.set_page_config(page_title="SuedLink 525 kV HVDC — Spatial Studio", page_icon="⚡", layout="wide")

DB_URL = os.getenv("DB_URL", "postgresql+psycopg2://gis_admin:SuedLink2026Secure@127.0.0.1:5435/suedlink_sdi")
SNAP = Path(__file__).resolve().parent.parent / "data" / "webgis_snapshot"

QUERIES = {
    "alignments": "SELECT route_id, variant_name, section_code, voltage_kv, iso19650_doc_id, ROUND(length_m::numeric,1)::float AS length_m, ROUND(min_elevation_z::numeric,1)::float AS min_elevation_z, planning_status, ST_Transform(ST_Force2D(ST_CurveToLine(geom)),4326) AS geom FROM suedlink_prod.cable_alignments",
    "buffers": "SELECT buffer_id, variant_name, buffer_type, ROUND(area_sqm::numeric,1)::float AS area_sqm, ST_Transform(ST_CurveToLine(geom),4326) AS geom FROM suedlink_prod.corridor_buffers",
    "conflicts": "SELECT conflict_id, variant_name, conflict_type, constraint_name, recommended_method, ROUND(COALESCE(overlap_area_sqm,0)::numeric,1)::float AS overlap_area_sqm, ST_Transform(ST_Force2D(ST_CurveToLine(geom)),4326) AS geom FROM suedlink_prod.spatial_conflicts",
    "natura": "SELECT id, site_code, site_name, protection_type, ST_Transform(ST_CurveToLine(geom),4326) AS geom FROM suedlink_prod.env_natura2000",
    "quarantine": "SELECT error_id, source_file, cad_layer, qa_error_reason, TO_CHAR(detected_at,'YYYY-MM-DD HH24:MI') AS detected_at, ST_Transform(ST_Force2D(ST_CurveToLine(geom)),4326) AS geom FROM suedlink_qa.cad_rejected_features",
}


@st.cache_data(ttl=60)
def load_data():
    try:
        eng = create_engine(DB_URL, connect_args={"connect_timeout": 2})
        with eng.connect() as c:
            c.execute(text("SELECT 1"))
        return "Live PostGIS 3.4 SDI", {k: gpd.read_postgis(q, eng, geom_col="geom") for k, q in QUERIES.items()}
    except Exception:
        return "GitHub Cloud GeoJSON Snapshot", {k: gpd.read_file(SNAP / f"{k}.geojson") for k in QUERIES}

mode, data = load_data()
alignments, buffers, conflicts, natura, quarantine = data["alignments"], data["buffers"], data["conflicts"], data["natura"], data["quarantine"]

st.title("⚡ SuedLink 525 kV HVDC — Enterprise Spatial Studio & QA/QC Portal")
st.caption(f"Section BY-04 (Würzburg) • EPSG:25832 / DHHN2016 • FME 2025 ISO 19650 Pipeline • Source: **{mode}**")

with st.sidebar:
    st.header("🎛️ Corridor Filters")
    sel_var = st.multiselect("Route Variants", sorted(alignments["variant_name"].unique()), default=sorted(alignments["variant_name"].unique()))
    sel_met = st.multiselect("Construction Method", sorted(conflicts["recommended_method"].unique()), default=sorted(conflicts["recommended_method"].unique()))
    sel_cnf = st.multiselect("Conflict Category", sorted(conflicts["conflict_type"].unique()), default=sorted(conflicts["conflict_type"].unique()))
    show_buf = st.checkbox("10m & 25m Buffers", True)
    show_nat = st.checkbox("Natura 2000 / NSG Zones", True)
    show_qa = st.checkbox("QA/QC Quarantined Defect", True)
    basemap = st.radio("Basemap", ["CartoDB positron", "CartoDB dark_matter", "OpenStreetMap"], index=0)
    st.error(f"🚨 QA Gatekeeper: {len(quarantine)} CAD Defect Quarantined")

f_align = alignments[alignments["variant_name"].isin(sel_var)]
f_buf = buffers[buffers["variant_name"].isin(sel_var)]
f_conf = conflicts[(conflicts["variant_name"].isin(sel_var)) & (conflicts["recommended_method"].isin(sel_met)) & (conflicts["conflict_type"].isin(sel_cnf))]

va = alignments[alignments["variant_name"] == "SL_TRASSE_VAR_A"].iloc[0]
vb = alignments[alignments["variant_name"] == "SL_TRASSE_VAR_B"].iloc[0]
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("VAR_A Length", f"{va['length_m']:,.1f} m", f"Min Z: {va['min_elevation_z']} m")
c2.metric("VAR_B Length", f"{vb['length_m']:,.1f} m", f"Min Z: {vb['min_elevation_z']} m")
c3.metric("Filtered Conflicts", f"{len(f_conf)}", f"of {len(conflicts)} total")
c4.metric("HDD Crossings", f"{len(f_conf[f_conf['recommended_method'] == 'HDD_Horizontal_Drilling'])}", "Trenchless Bore")
c5.metric("QA Quarantined", f"{len(quarantine)} Defect", "Self-Intersection Blocked", delta_color="inverse")

t_map, t_stat, t_3d, t_qa, t_mcda, t_iso = st.tabs(["🗺️ WebGIS Map", "📊 Conflict Analytics", "📐 3D HDD Profile", "🛡️ QA Audit & Export", "⚖️ MCDA Decision", "📋 ISO 19650 & SQL"])

with t_map:
    m = folium.Map(location=[49.775, 9.955], zoom_start=12, tiles=basemap)
    if show_nat and not natura.empty:
        folium.GeoJson(natura, name="Natura 2000", style_function=lambda _: {"color": "#16a34a", "weight": 1, "fillOpacity": 0.18}, tooltip=folium.GeoJsonTooltip(fields=["site_code", "site_name", "protection_type"])).add_to(m)
    if show_buf and not f_buf.empty:
        folium.GeoJson(f_buf, name="Buffers", style_function=lambda f: {"color": "#0d9488" if f["properties"]["buffer_type"] == "Schutzstreifen_10m" else "#0284c7", "weight": 1.5, "fillOpacity": 0.12}, tooltip=folium.GeoJsonTooltip(fields=["variant_name", "buffer_type", "area_sqm"])).add_to(m)
    if not f_align.empty:
        folium.GeoJson(f_align, name="Alignments", style_function=lambda f: {"color": "#10b981" if f["properties"]["variant_name"] == "SL_TRASSE_VAR_A" else "#2563eb", "weight": 5}, tooltip=folium.GeoJsonTooltip(fields=["variant_name", "length_m", "min_elevation_z", "iso19650_doc_id"])).add_to(m)
    if not f_conf.empty:
        folium.GeoJson(f_conf, name="Conflicts", style_function=lambda f: {"color": "#dc2626" if f["properties"]["conflict_type"] in ["Waterway_Crossing", "Natura2000_Overlap"] else "#f59e0b", "weight": 8}, tooltip=folium.GeoJsonTooltip(fields=["variant_name", "conflict_type", "constraint_name", "recommended_method", "overlap_area_sqm"])).add_to(m)
    if show_qa and not quarantine.empty:
        folium.GeoJson(quarantine, name="Quarantine", style_function=lambda _: {"color": "#e11d48", "weight": 4, "dashArray": "8, 6"}, tooltip=folium.GeoJsonTooltip(fields=["source_file", "cad_layer", "qa_error_reason"])).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    st_folium(m, width=None, height=600, returned_objects=[])

with t_stat:
    summary = f_conf.groupby(["variant_name", "conflict_type"], as_index=False).agg(count=("conflict_id", "count"), area_sqm=("overlap_area_sqm", "sum"))
    col1, col2 = st.columns(2)
    col1.plotly_chart(px.bar(summary, x="conflict_type", y="count", color="variant_name", barmode="group", title="Crossing Count by Category"), use_container_width=True)
    col2.plotly_chart(px.bar(summary, x="conflict_type", y="area_sqm", color="variant_name", barmode="group", title="Affected Easement / Habitat Area (m²)"), use_container_width=True)
    st.dataframe(f_conf.drop(columns=["geom"]), use_container_width=True, hide_index=True)

with t_3d:
    prof = pd.DataFrame({
        "Station_km": [0.0, 1.8, 3.5, 4.4, 5.2, 6.8, 9.32, 0.0, 2.0, 4.1, 5.8, 7.6, 9.62],
        "Elevation_DHHN2016_m": [182.5, 179.0, 174.2, 158.0, 158.4, 176.8, 185.0, 195.0, 191.2, 184.5, 162.0, 188.0, 196.4],
        "Variant": ["SL_TRASSE_VAR_A"] * 7 + ["SL_TRASSE_VAR_B"] * 6,
    })
    fig = px.line(prof, x="Station_km", y="Elevation_DHHN2016_m", color="Variant", markers=True, title="3D HDD Elevation Profile (DHHN2016)")
    fig.add_hline(y=167.0, line_dash="dash", line_color="#38bdf8", annotation_text="Main River Bed (~167 m)")
    st.plotly_chart(fig, use_container_width=True)

with t_qa:
    st.dataframe(quarantine.drop(columns=["geom"]), use_container_width=True, hide_index=True)
    d1, d2 = st.columns(2)
    d1.download_button("⬇️ Download Conflicts (GeoJSON)", f_conf.to_json(), "suedlink_conflicts.geojson", "application/geo+json")
    d2.download_button("⬇️ Download QA Audit (CSV)", quarantine.drop(columns=["geom"]).to_csv(index=False), "suedlink_qa_audit.csv", "text/csv")

with t_mcda:
    w1, w2, w3 = st.columns(3)
    wl = w1.slider("Weight: Route Length", 0.0, 1.0, 0.30, 0.05)
    wh = w2.slider("Weight: HDD Crossings", 0.0, 1.0, 0.45, 0.05)
    we = w3.slider("Weight: Habitat Area", 0.0, 1.0, 0.25, 0.05)
    ah = len(conflicts[(conflicts["variant_name"] == "SL_TRASSE_VAR_A") & (conflicts["recommended_method"] == "HDD_Horizontal_Drilling")])
    bh = len(conflicts[(conflicts["variant_name"] == "SL_TRASSE_VAR_B") & (conflicts["recommended_method"] == "HDD_Horizontal_Drilling")])
    ae = conflicts[conflicts["variant_name"] == "SL_TRASSE_VAR_A"]["overlap_area_sqm"].sum()
    be = conflicts[conflicts["variant_name"] == "SL_TRASSE_VAR_B"]["overlap_area_sqm"].sum()
    sa = round((wl * (va["length_m"] / 10000)) + (wh * (ah / 5)) + (we * (ae / 60000)), 3)
    sb = round((wl * (vb["length_m"] / 10000)) + (wh * (bh / 5)) + (we * (be / 60000)), 3)
    r1, r2, r3 = st.columns(3)
    r1.metric("VAR_A Risk Score", f"{sa:.3f}", f"{ah} HDD | {ae:,.0f} m²")
    r2.metric("VAR_B Risk Score", f"{sb:.3f}", f"{bh} HDD | {be:,.0f} m²")
    r3.metric("Recommended Variant", "SL_TRASSE_VAR_A" if sa <= sb else "SL_TRASSE_VAR_B", "Lower Risk Index Wins")

with t_iso:
    fn = st.text_input("ISO 19650 Container Validator:", "SL-JAC-BY04-XX-M3-G-0001.dxf")
    if re.match(r"^SL-[A-Z]{3}-BY\d{2}-[A-Z0-9]{2}-M3-G-\d{4}\.(dxf|dwg|ifc)$", fn):
        st.success(f"✅ Valid ISO 19650 Deliverable: {fn}")
    else:
        st.error(f"❌ Invalid ISO 19650 Filename: {fn}")
    st.code("SELECT variant_name, ROUND(ST_Length(geom)::numeric,1) AS len_m, ST_ZMin(geom) AS min_z FROM suedlink_prod.cable_alignments;", language="sql")
    st.dataframe(alignments.drop(columns=["geom"]), use_container_width=True, hide_index=True)
