-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create dedicated enterprise schemas
CREATE SCHEMA IF NOT EXISTS suedlink_raw;
CREATE SCHEMA IF NOT EXISTS suedlink_prod;
CREATE SCHEMA IF NOT EXISTS suedlink_qa;

-- 1. Reference Layer: Protected Environmental Areas (Natura 2000 / FFH)
CREATE TABLE IF NOT EXISTS suedlink_prod.env_natura2000 (
    id SERIAL PRIMARY KEY,
    site_code VARCHAR(50),
    site_name VARCHAR(255),
    protection_type VARCHAR(50) DEFAULT 'FFH_Natura2000',
    geom GEOMETRY(MultiPolygon, 25832) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_env_natura2000_geom ON suedlink_prod.env_natura2000 USING GIST (geom);

-- 2. Reference Layer: Crossing Infrastructure (Rivers, Roads, Railways)
CREATE TABLE IF NOT EXISTS suedlink_prod.ref_crossing_infrastructure (
    id SERIAL PRIMARY KEY,
    infra_category VARCHAR(50) NOT NULL, -- 'Waterway', 'Road', 'Railway'
    infra_name VARCHAR(255),
    geom GEOMETRY(MultiLineString, 25832) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ref_crossing_geom ON suedlink_prod.ref_crossing_infrastructure USING GIST (geom);

-- 3. Core Engineering Layer: 525 kV Underground Cable Alignment (3D!)
CREATE TABLE IF NOT EXISTS suedlink_prod.cable_alignments (
    route_id SERIAL PRIMARY KEY,
    iso19650_doc_id VARCHAR(100) NOT NULL,
    section_code VARCHAR(20) NOT NULL DEFAULT 'SL-BY-04',
    variant_name VARCHAR(100) NOT NULL,
    voltage_kv INTEGER DEFAULT 525,
    planning_status VARCHAR(30) DEFAULT 'In_Review' CHECK (
        planning_status IN ('Draft', 'In_Review', 'Approved_PFB', 'As_Built')
    ),
    length_m NUMERIC(12, 2),
    min_elevation_z NUMERIC(8, 2),
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geom GEOMETRY(MultiLineStringZ, 25832) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cable_alignments_geom ON suedlink_prod.cable_alignments USING GIST (geom);

-- 4. Automated Corridor Buffer Zones (10m Schutzstreifen & 25m Arbeitsstreifen)
CREATE TABLE IF NOT EXISTS suedlink_prod.corridor_buffers (
    buffer_id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES suedlink_prod.cable_alignments(route_id) ON DELETE CASCADE,
    variant_name VARCHAR(100) NOT NULL,
    buffer_type VARCHAR(30) NOT NULL CHECK (
        buffer_type IN ('Schutzstreifen_10m', 'Arbeitsstreifen_25m')
    ),
    area_sqm NUMERIC(14, 2),
    geom GEOMETRY(MultiPolygon, 25832) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_corridor_buffers_geom ON suedlink_prod.corridor_buffers USING GIST (geom);

-- 5. Automated Spatial Conflict Register (Raumwiderstand & Kreuzungsbauwerke)
CREATE TABLE IF NOT EXISTS suedlink_prod.spatial_conflicts (
    conflict_id SERIAL PRIMARY KEY,
    variant_name VARCHAR(100) NOT NULL,
    conflict_type VARCHAR(50) NOT NULL, -- 'Natura2000_Overlap', 'Waterway_Crossing', 'Road_Crossing', 'Railway_Crossing'
    constraint_name VARCHAR(255),
    recommended_method VARCHAR(50),     -- 'Open_Trench' vs 'HDD_Horizontal_Drilling'
    overlap_area_sqm NUMERIC(12, 2) DEFAULT 0,
    geom GEOMETRY(Geometry, 25832) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_spatial_conflicts_geom ON suedlink_prod.spatial_conflicts USING GIST (geom);

-- 6. QA/QC Quarantine Table for Rejected CAD Geometries
CREATE TABLE IF NOT EXISTS suedlink_qa.cad_rejected_features (
    error_id SERIAL PRIMARY KEY,
    source_file VARCHAR(255),
    cad_layer VARCHAR(100),
    qa_error_reason VARCHAR(255),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geom GEOMETRY(Geometry, 25832)
);
