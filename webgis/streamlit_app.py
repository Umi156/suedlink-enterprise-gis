import os
import pandas as pd
import geopandas as gpd
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine

st.set_page_config(
    page_title="SuedLink 525 kV HVDC — Enterprise Spatial Studio (BY-04)",
    page_icon="⚡",
    layout="wide",
)

SNAP = os.path.join(os.path.dirname(__file__), "..", "data", "webgis_snapshot")


def _clean(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    for c in gdf.columns:
        if c != "geometry":
            gdf[c] = gdf[c].apply(lambda v: str(v) if hasattr(v, "isoformat") else v)
    return gdf


@st.cache_data
def load_layers():
    db = os.getenv(
        "DATABASE_URL",
        "postgresql://gis_admin:suedlink_secret_2026@localhost:5435/suedlink_sdi",
    )
    try:
        eng = create_engine(db, connect_args={"connect_timeout": 2})
        with eng.connect() as conn:
            aln = gpd.read_postgis("SELECT * FROM suedlink_prod.cable_alignments", conn, geom_col="geom").to_crs(4326)
            buf = gpd.read_postgis("SELECT * FROM suedlink_prod.safety_buffers", conn, geom_col="geom").to_crs(4326)
            cnf = gpd.read_postgis("SELECT * FROM suedlink_prod.spatial_conflicts", conn, geom_col="geom").to_crs(4326)
            nat = gpd.read_postgis("SELECT * FROM suedlink_prod.natura2000_sites", conn, geom_col="geom").to_crs(4326)
            qar = gpd.read_postgis("SELECT * FROM suedlink_qa.cad_rejected_features", conn, geom_col="geom").to_crs(4326)
        mode = "Live PostGIS 3.4 (localhost:5435)"
    except Exception:
        aln = gpd.read_file(os.path.join(SNAP, "alignments.geojson"))
        buf = gpd.read_file(os.path.join(SNAP, "buffers.geojson"))
        cnf = gpd.read_file(os.path.join(SNAP, "conflicts.geojson"))
        nat = gpd.read_file(os.path.join(SNAP, "natura.geojson"))
        qar = gpd.read_file(os.path.join(SNAP, "quarantine.geojson"))
        mode = "Cloud GeoJSON Snapshot (EPSG:25832 -> WGS84)"
    return _clean(aln), _clean(buf), _clean(cnf), _clean(nat), _clean(qar), mode


alignments, buffers, conflicts, natura, quarantine, data_source = load_layers()

st.sidebar.header("🎛️ Corridor Filters")
variants = sorted(alignments["variant_name"].dropna().unique().tolist())
sel_v = st.sidebar.multiselect("Route Variants", variants, default=variants)
methods = sorted(conflicts["recommended_method"].dropna().unique().tolist())
sel_m = st.sidebar.multiselect("Construction Method", methods, default=methods)
cats = sorted(conflicts["conflict_type"].dropna().unique().tolist())
sel_c = st.sidebar.multiselect("Conflict Category", cats, default=cats)

show_buf = st.sidebar.checkbox("10m & 25m Buffers", value=True)
show_nat = st.sidebar.checkbox("Natura 2000 / NSG Zones", value=True)
show_qa = st.sidebar.checkbox("QA/QC Quarantined Defect", value=True)
basemap = st.sidebar.radio("Basemap", ["CartoDB positron", "CartoDB dark_matter", "OpenStreetMap"])

f_aln = alignments[alignments["variant_name"].isin(sel_v)]
f_buf = buffers[buffers["variant_name"].isin(sel_v)]
f_conf = conflicts[
    conflicts["variant_name"].isin(sel_v)
    & conflicts["recommended_method"].isin(sel_m)
    & conflicts["conflict_type"].isin(sel_c)
]

st.title("⚡ SuedLink 525 kV HVDC — Enterprise Spatial Analytics & FME QA/QC Studio")
st.caption(f"Section BY-04 (Würzburg) • ETRS89 / UTM32N (EPSG:25832) & DHHN2016 • Source: **{data_source}**")

k1, k2, k3, k4, k5 = st.columns(5)
va = alignments[alignments["variant_name"] == "SL_TRASSE_VAR_A"]
vb = alignments[alignments["variant_name"] == "SL_TRASSE_VAR_B"]
k1.metric("VAR_A Length", f"{va['length_m'].iloc:,.1f} m", f"Min Z: {va['min_elevation_z'].iloc:.1f} m")
k2.metric("VAR_B Length", f"{vb['length_m'].iloc:,.1f} m", f"Min Z: {vb['min_elevation_z'].iloc:.1f} m")
k3.metric("Filtered Conflicts", f"{len(f_conf)}", f"of {len(conflicts)} total")
k4.metric("HDD Crossings", f"{int((f_conf['recommended_method'] == 'HDD_Horizontal_Drilling').sum())}", "Trenchless Bore")
k5.metric("FME Quarantined", f"{len(quarantine)}", "Self-Intersection Blocked", delta_color="inverse")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🗺️ WebGIS Map",
    "📊 Conflict Analytics",
    "📐 3D HDD Profile",
    "🛡️ QA Audit & Export",
    "⚖️ MCDA Decision",
    "📋 ISO 19650 & SQL",
])
with tab1:
    m = folium.Map(location=[49.78, 9.96], zoom_start=12, tiles=basemap)
    if show_nat and not natura.empty:
        folium.GeoJson(
            natura, name="Natura 2000",
            style_function=lambda _: {"color": "#16a34a", "weight": 1.2, "fillOpacity": 0.16},
            tooltip=folium.GeoJsonTooltip(fields=[c for c in ["site_code", "site_name"] if c in natura.columns]),
        ).add_to(m)
    if show_buf and not f_buf.empty:
        folium.GeoJson(
            f_buf, name="Safety Buffers",
            style_function=lambda _: {"color": "#0d9488", "weight": 1, "fillOpacity": 0.14},
        ).add_to(m)
    if not f_aln.empty:
        folium.GeoJson(
            f_aln, name="3D Alignments",
            style_function=lambda f: {
                "color": "#16a34a" if f["properties"].get("variant_name") == "SL_TRASSE_VAR_A" else "#0284c7",
                "weight": 4.5,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=[c for c in ["variant_name", "length_m", "min_elevation_z", "iso19650_doc_id"] if c in f_aln.columns]
            ),
        ).add_to(m)
    if not f_conf.empty:
        folium.GeoJson(
            f_conf, name="Spatial Conflicts",
            style_function=lambda f: {
                "color": "#dc2626" if f["properties"].get("conflict_type") in ["Waterway_Crossing", "Natura2000_Overlap"] else "#ea580c",
                "weight": 7, "fillOpacity": 0.65,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=[c for c in ["variant_name", "conflict_type", "recommended_method", "overlap_area_sqm"] if c in f_conf.columns]
            ),
        ).add_to(m)
    if show_qa and not quarantine.empty:
        folium.GeoJson(
            quarantine, name="FME Quarantine",
            style_function=lambda _: {"color": "#e11d48", "weight": 4.5, "dashArray": "8, 6"},
            tooltip=folium.GeoJsonTooltip(
                fields=[c for c in ["source_file", "cad_layer", "qa_error_reason"] if c in quarantine.columns]
            ),
        ).add_to(m)
    folium.LayerControl().add_to(m)
    st_folium(m, width=None, height=560, returned_objects=[])

with tab2:
    st.subheader("Spatial Conflict Breakdown by Variant & Category")
    if not f_conf.empty:
        c1, c2 = st.columns(2)
        grp = f_conf.groupby(["variant_name", "conflict_type"], as_index=False).agg(
            conflict_count=("conflict_type", "count"),
            total_area_sqm=("overlap_area_sqm", "sum"),
        )
        cmap = {"SL_TRASSE_VAR_A": "#16a34a", "SL_TRASSE_VAR_B": "#0284c7"}
        with c1:
            st.plotly_chart(px.bar(grp, x="conflict_type", y="conflict_count", color="variant_name", barmode="group",
                                   title="Conflict Count", color_discrete_map=cmap), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(grp, x="conflict_type", y="total_area_sqm", color="variant_name", barmode="group",
                                   title="Overlap Area (m²)", color_discrete_map=cmap), use_container_width=True)
    st.dataframe(f_conf.drop(columns=["geom", "geometry"], errors="ignore"), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("3D Longitudinal Borehole & Trench Elevation Profile (DHHN2016)")
    fig_z = go.Figure()
    for _, row in f_aln.iterrows():
        coords = list(row.geometry.coords)
        xs = [i * (row["length_m"] / max(len(coords) - 1, 1)) for i in range(len(coords))]
        zs = [c if len(c) > 2 else row["min_elevation_z"] for c in coords]
        fig_z.add_trace(go.Scatter(
            x=xs, y=zs, mode="lines+markers", name=row["variant_name"],
            line=dict(width=3, color="#16a34a" if row["variant_name"] == "SL_TRASSE_VAR_A" else "#0284c7"),
        ))
    fig_z.add_hline(y=168.0, line_dash="dash", line_color="#38bdf8", annotation_text="River Main (~168 m DHHN2016)")
    fig_z.update_layout(xaxis_title="Chainage (m)", yaxis_title="Elevation Z (m DHHN2016)", height=430)
    st.plotly_chart(fig_z, use_container_width=True)

with tab4:
    st.subheader("FME Automated QA/QC Quarantine Gatekeeper & Engineering Exports")
    st.error("🚨 Quarantined CAD Defect Blocked From Production (`suedlink_qa.cad_rejected_features`)")
    st.dataframe(quarantine.drop(columns=["geom", "geometry"], errors="ignore"), use_container_width=True, hide_index=True)
    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "⬇️ Download Filtered Conflicts (CSV)",
            data=f_conf.drop(columns=["geom", "geometry"], errors="ignore").to_csv(index=False),
            file_name="suedlink_by04_conflicts.csv", mime="text/csv",
        )
    with d2:
        st.download_button(
            "⬇️ Download Filtered Conflicts (GeoJSON)",
            data=f_conf.to_json(),
            file_name="suedlink_by04_conflicts.geojson", mime="application/geo+json",
        )

with tab5:
    st.subheader("Multi-Criteria Decision Analysis (MCDA) — Variant Ranking")
    w_nat = st.slider("Weight: Natura 2000 Overlap", 1, 10, 8)
    w_wat = st.slider("Weight: Waterway / HDD Borehole", 1, 10, 7)
    w_for = st.slider("Weight: Forest Clearing Impact", 1, 10, 5)
    w_ind = st.slider("Weight: Industrial / Utility Crossing", 1, 10, 4)
    wmap = {"Natura2000_Overlap": w_nat, "Waterway_Crossing": w_wat, "Forest_Crossing": w_for, "Industrial_Area": w_ind}
    rows = []
    for v in variants:
        sub = conflicts[conflicts["variant_name"] == v]
        rows.append({"Variant": v, "Conflicts": len(sub), "Weighted Risk Score": sum(wmap.get(t, 3) for t in sub["conflict_type"])})
    mcda_df = pd.DataFrame(rows).sort_values("Weighted Risk Score")
    st.dataframe(mcda_df, use_container_width=True, hide_index=True)
    st.success(f"✅ Preferred Corridor under Current Weights: **{mcda_df.iloc[0]['Variant']}**")

with tab6:
    st.subheader("ISO 19650 BIM/CAD Validator & PostGIS Spatial SQL")
    sid = st.text_input("Test ISO 19650 Container ID", value="SL-JAC-BY04-XX-M3-G-0001.dxf")
    pts = sid.replace(".dxf", "").split("-")
    if len(pts) == 7:
        st.success(f"✅ Valid ISO 19650: Project={pts}, Originator={pts}, Zone={pts}, Level={pts}, Type={pts}, Role={pts}, Num={pts}")
    else:
        st.warning("⚠️ Expected 7 hyphen-delimited fields: PROJECT-ORIGINATOR-ZONE-LEVEL-TYPE-ROLE-NUMBER.dxf")
    st.code(
        "SELECT variant_name, ROUND(ST_Length(geom)::numeric, 1) AS length_m, "
        "ROUND(ST_ZMin(geom)::numeric, 1) AS min_z FROM suedlink_prod.cable_alignments;",
        language="sql",
    )
