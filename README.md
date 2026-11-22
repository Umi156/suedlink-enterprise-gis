# ⚡ SuedLink 525 kV HVDC — Enterprise Spatial Data Infrastructure & FME QA/QC Portal

![Esri ArcGIS](https://shields.io)
![Safe Software FME](https://shields.io)
![PostgreSQL](https://shields.io)
![PostGIS](https://shields.io)
![Python](https://shields.io)
![FastAPI](https://shields.io)
![Streamlit](https://shields.io)
![Leaflet](https://shields.io)
![Docker](https://shields.io)
![GitHub Actions](https://shields.io)
![ISO 19650](https://shields.io)

**Section BY-04 (Würzburg, Bavaria) • ETRS89 / UTM32N (`EPSG:25832`) & `DHHN2016` • ISO 19650 Compliant**

An end-to-end Enterprise GIS, CAD/BIM ETL quality-gate, and multi-channel WebGIS architecture built for high-voltage underground cable corridor planning (**SuedLink Section BY-04, Würzburg**).

---

## 🌐 Live Interactive Demos (3-Tier Cloud Portfolio)

| Platform | Live Link | Capabilities Demonstrated |
| :--- | :--- | :--- |
| **1. Esri ArcGIS Online Enterprise Web App** | **[Launch ArcGIS Online Instant App](https://www.arcgis.com/apps/instant/sidebar/index.html?appid=e668b57def8646a8ab0d7fb9f02d0d60)** | Esri Hosted Feature Layers, custom cartographic symbology (crossings, 45° hatches, buffers), interactive layer switcher & pop-ups |
| **2. GitHub Pages Hub & Playable Pipeline Tour** | **[Launch Interactive WebGIS & FME Tour](https://Umi156.github.io/suedlink-enterprise-gis/)** | Static Leaflet WebGIS, clickable 4-step FME/PostGIS/ArcGIS Pro walkthrough, conflict matrix zoom & defect quarantine inspector |
| **3. Streamlit 3D & MCDA Spatial Studio** | **[Launch Streamlit Analytics Studio](https://streamlit.app)** | Interactive Folium map, Plotly conflict analytics, 3D HDD borehole profile (`DHHN2016`), MCDA risk sliders & ISO 19650 validator |

---

## 🏗️ Enterprise System Architecture

```text
[AutoCAD Civil 3D / BIM (.dxf)] ──► [FME Workbench QA/QC Gatekeeper]
                                        ├──► Valid (EPSG:25832 / ISO 19650) ──► [PostGIS 3.4: suedlink_prod]
                                        └──► Self-Intersection Defect      ──► [PostGIS 3.4: suedlink_qa]
                                                                                      │
                    ┌─────────────────────────────────┬───────────────────────────────┴───────────────────────────────┐
                    ▼                                 ▼                                                               ▼
       [ArcGIS Pro (.sde Client)]        [FastAPI GeoJSON REST API (:8000)]                             [Streamlit Spatial Studio (:8501)]
       2D/3D Editing & Cartography       Decoupled Spatial Services + Leaflet                           MCDA Weighting, 3D Profile & Exports
```

## 🛠️ Core Technical Stack
* **Desktop & Enterprise GIS:** Esri ArcGIS Pro (direct `.sde` PostgreSQL connection on `localhost,5435`), ArcGIS Online Hosted Feature Layers & Instant Apps
* **ETL & Automated QA/QC:** FME Form / Workbench (`Reprojector`, `GeometryValidator`, ISO 19650 container validation, automated quarantine routing)
* **Spatial Database:** PostgreSQL 16 + PostGIS 3.4 (`ST_Buffer`, `ST_Intersection`, `ST_Length`, `ST_ZMin`, `ST_CurveToLine`, GIST spatial indexes)
* **WebGIS & Analytics:** Python 3.11, FastAPI, GeoPandas, Shapely, Leaflet.js, Streamlit, Folium, Plotly
* **DevOps & CI/CD:** Docker Compose (4-container local SDI) & GitHub Actions automated GeoJSON/Python/Docker validation

## 🔒 KRITIS Data Governance Note
Because exact 525 kV SuedLink cable trench coordinates and borehole depths are restricted under German Critical Infrastructure (**KRITIS**) regulations, this repository models a realistic engineering twin of **Section BY-04 (Würzburg)** in `EPSG:25832` / `DHHN2016` paired with German environmental reference boundaries (`Natura 2000`) to demonstrate production-grade CAD/BIM QA/QC and spatial conflict analytics.

