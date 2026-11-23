# âš¡ SuedLink 525 kV HVDC â€” Enterprise Spatial Data Infrastructure & FME QA/QC Portal

![ArcGIS](https://shields.io/badge/Esri-ArcGIS_Pro-0079C1?style=for-the-badge&logo=esri) ![FME](https://shields.io/badge/ETL-FME_Workbench-F58220?style=for-the-badge&logo=safe) ![PostGIS](https://shields.io/badge/PostGIS-3.4-2E8B57?style=for-the-badge&logo=postgresql) ![Python](https://shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python) ![FastAPI](https://shields.io/badge/FastAPI-REST-009688?style=for-the-badge&logo=fastapi) ![Streamlit](https://shields.io/badge/Streamlit-Studio-FF4B4B?style=for-the-badge&logo=streamlit) ![Leaflet](https://shields.io/badge/Leaflet-WebGIS-199900?style=for-the-badge&logo=leaflet) ![Docker](https://shields.io/badge/Docker-SDI-2496ED?style=for-the-badge&logo=docker) ![CI](https://shields.io/badge/CI-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions)


**Section BY-04 (WÃ¼rzburg, Bavaria) â€¢ ETRS89 / UTM32N (`EPSG:25832`) & `DHHN2016` â€¢ ISO 19650 Compliant**

An end-to-end Enterprise GIS, CAD/BIM ETL quality-gate, and multi-channel WebGIS architecture built for high-voltage underground cable corridor planning (**SuedLink Section BY-04, WÃ¼rzburg**).

---

## ðŸŒ Live Interactive Demos (3-Tier Cloud Portfolio)

| Platform | Live Link | Capabilities Demonstrated |
| :--- | :--- | :--- |
| **1. Esri ArcGIS Online Enterprise Web App** | **[Launch ArcGIS Online Instant App](https://www.arcgis.com/apps/instant/sidebar/index.html?appid=e668b57def8646a8ab0d7fb9f02d0d60)** | Esri Hosted Feature Layers, custom cartographic symbology (crossings, 45Â° hatches, buffers), interactive layer switcher & pop-ups |
| **2. GitHub Pages Hub & Playable Pipeline Tour** | **[Launch Interactive WebGIS & FME Tour](https://Umi156.github.io/suedlink-enterprise-gis/)** | Static Leaflet WebGIS, clickable 4-step FME/PostGIS/ArcGIS Pro walkthrough, conflict matrix zoom & defect quarantine inspector |
| **3. Streamlit 3D & MCDA Spatial Studio** | **[Launch Streamlit Analytics Studio](https://suedlink-enterprise-gis-toxhwaagx8danxcfnuxzhx.streamlit.app/)** | Interactive Folium map, Plotly conflict analytics, 3D HDD borehole profile (`DHHN2016`), MCDA risk sliders & ISO 19650 validator |

---

## ðŸ—ï¸ Enterprise System Architecture

```text
[AutoCAD Civil 3D / BIM (.dxf)] â”€â”€â–º [FME Workbench QA/QC Gatekeeper]
                                        â”œâ”€â”€â–º Valid (EPSG:25832 / ISO 19650) â”€â”€â–º [PostGIS 3.4: suedlink_prod]
                                        â””â”€â”€â–º Self-Intersection Defect      â”€â”€â–º [PostGIS 3.4: suedlink_qa]
                                                                                      â”‚
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â–¼                                 â–¼                                                               â–¼
       [ArcGIS Pro (.sde Client)]        [FastAPI GeoJSON REST API (:8000)]                             [Streamlit Spatial Studio (:8501)]
       2D/3D Editing & Cartography       Decoupled Spatial Services + Leaflet                           MCDA Weighting, 3D Profile & Exports
```

## ðŸ› ï¸ Core Technical Stack
* **Desktop & Enterprise GIS:** Esri ArcGIS Pro (direct `.sde` PostgreSQL connection on `localhost,5435`), ArcGIS Online Hosted Feature Layers & Instant Apps
* **ETL & Automated QA/QC:** FME Form / Workbench (`Reprojector`, `GeometryValidator`, ISO 19650 container validation, automated quarantine routing)
* **Spatial Database:** PostgreSQL 16 + PostGIS 3.4 (`ST_Buffer`, `ST_Intersection`, `ST_Length`, `ST_ZMin`, `ST_CurveToLine`, GIST spatial indexes)
* **WebGIS & Analytics:** Python 3.11, FastAPI, GeoPandas, Shapely, Leaflet.js, Streamlit, Folium, Plotly
* **DevOps & CI/CD:** Docker Compose (4-container local SDI) & GitHub Actions automated GeoJSON/Python/Docker validation

## ðŸ”’ KRITIS Data Governance Note
Because exact 525 kV SuedLink cable trench coordinates and borehole depths are restricted under German Critical Infrastructure (**KRITIS**) regulations, this repository models a realistic engineering twin of **Section BY-04 (WÃ¼rzburg)** in `EPSG:25832` / `DHHN2016` paired with German environmental reference boundaries (`Natura 2000`) to demonstrate production-grade CAD/BIM QA/QC and spatial conflict analytics.




---

## 🔄 End-to-End Pipeline Breakdown (A to Z)

1. **Data Ingestion (CAD/BIM & Environmental Reference):** Ingests AutoCAD Civil 3D / BIM `.dxf` alignments (`SL-JAC-BY04-XX-M3-G-0001.dxf`) alongside official German Natura 2000 conservation boundaries (`EPSG:25832`).
2. **Automated ETL & QA/QC Gatekeeper (FME & Python):** Validates ISO 19650 naming conventions, enforces 3D coordinate transformation (`ETRS89 / UTM32N` + `DHHN2016`), and runs OGC topological checks (`GeometryValidator`). Valid 3D lines route to `suedlink_prod`; self-intersecting defects quarantine in `suedlink_qa.cad_rejected_features`.
3. **Enterprise Spatial Database (PostgreSQL 16 + PostGIS 3.4):** Executes server-side spatial SQL (`ST_Buffer` for 10m/25m safety corridors, `ST_Intersection` for environmental/infrastructure conflict matrices, `ST_ZMin` for HDD trenchless borehole depth).
4. **Multi-Channel Delivery (Desktop + Backend + Frontend):**
   * **Desktop GIS:** Esri ArcGIS Pro connects directly via `.sde` (`localhost,5435`) for 2D/3D cartography and publishes Hosted Feature Layers to ArcGIS Online.
   * **Backend REST API:** FastAPI (`:8000`) serves decoupled GeoJSON endpoints (`/api/layers/*`) with automatic snapshot fallback.
   * **Frontend WebGIS & Analytics:** Leaflet Interactive Portal (`:8000` & GitHub Pages) and Streamlit Spatial Studio (`:8501` & Streamlit Cloud) deliver 3D longitudinal profiles, MCDA risk weighting, and CSV/GeoJSON exports.
5. **DevSecOps & CI/CD (Docker Compose + GitHub Actions):** 4-container local SDI (`db`, `pgadmin`, `fastapi_webgis`, `streamlit_studio`) externalizes secrets via `.env` / `.env.example`, while `.github/workflows` validates GeoJSON schemas, CRS bounds, and Python syntax on every push.

---

## 🔄 End-to-End Pipeline Breakdown (A to Z)

1. **Data Ingestion (CAD/BIM & Environmental Reference):** Ingests AutoCAD Civil 3D / BIM `.dxf` alignments (`SL-JAC-BY04-XX-M3-G-0001.dxf`) alongside official German Natura 2000 conservation boundaries (`EPSG:25832`).
2. **Automated ETL & QA/QC Gatekeeper (FME & Python):** Validates ISO 19650 naming conventions, enforces 3D coordinate transformation (`ETRS89 / UTM32N` + `DHHN2016`), and runs OGC topological checks (`GeometryValidator`). Valid 3D lines route to `suedlink_prod`; self-intersecting defects quarantine in `suedlink_qa.cad_rejected_features`.
3. **Enterprise Spatial Database (PostgreSQL 16 + PostGIS 3.4):** Executes server-side spatial SQL (`ST_Buffer` for 10m/25m safety corridors, `ST_Intersection` for environmental/infrastructure conflict matrices, `ST_ZMin` for HDD trenchless borehole depth).
4. **Multi-Channel Delivery (Desktop + Backend + Frontend):**
   * **Desktop GIS:** Esri ArcGIS Pro connects directly via `.sde` (`localhost,5435`) for 2D/3D cartography and publishes Hosted Feature Layers to ArcGIS Online.
   * **Backend REST API:** FastAPI (`:8000`) serves decoupled GeoJSON endpoints (`/api/layers/*`) with automatic snapshot fallback.
   * **Frontend WebGIS & Analytics:** Leaflet Interactive Portal (`:8000` & GitHub Pages) and Streamlit Spatial Studio (`:8501` & Streamlit Cloud) deliver 3D longitudinal profiles, MCDA risk weighting, and CSV/GeoJSON exports.
5. **DevSecOps & CI/CD (Docker Compose + GitHub Actions):** 4-container local SDI (`db`, `pgadmin`, `fastapi_webgis`, `streamlit_studio`) externalizes secrets via `.env` / `.env.example`, while `.github/workflows` validates GeoJSON schemas, CRS bounds, and Python syntax on every push.