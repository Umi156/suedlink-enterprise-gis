from pathlib import Path
import ezdxf

OUT_DIR = Path("data/raw/cad_deliveries")
OUT_DXF = OUT_DIR / "SL-JAC-BY04-XX-M3-G-0001.dxf"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = ezdxf.new(dxfversion="R2018")
    msp = doc.modelspace()

    # Layer nach ISO 19650 / SuedLink CAD-Standard anlegen
    doc.layers.add("SL_TRASSE_VAR_A", color=3)     # Grün: Vorzugstrasse (gültig, 3D HDD-Unterquerung Main)
    doc.layers.add("SL_TRASSE_VAR_B", color=5)     # Blau: Alternativtrasse Ost (gültig, 3D)
    doc.layers.add("SL_TRASSE_DEFECT", color=1)    # Rot: Fehlerhafte Lieferung (Selbstüberschneidung für QA/QC)

    # 1. Variante A: Gültige 3D-Polylinie im Raum Würzburg (EPSG:25832) inkl. HDD-Düker unter dem Main (Z=158m)
    coords_var_a = [
        (565200.0, 5518500.0, 182.5),
        (566100.0, 5516800.0, 179.0),
        (566950.0, 5515200.0, 174.2),
        (567400.0, 5514350.0, 158.0),  # HDD-Unterquerung Main (Tiefpunkt)
        (567850.0, 5513600.0, 158.4),
        (568600.0, 5512200.0, 176.8),
        (569800.0, 5510400.0, 185.0),
    ]
    msp.add_polyline3d(coords_var_a, dxfattribs={"layer": "SL_TRASSE_VAR_A"})

    # 2. Variante B: Gültige 3D-Alternativtrasse weiter östlich
    coords_var_b = [
        (568500.0, 5518800.0, 195.0),
        (569400.0, 5517100.0, 191.2),
        (570300.0, 5515300.0, 184.5),
        (571100.0, 5513500.0, 162.0),  # HDD-Unterquerung
        (571900.0, 5511800.0, 188.0),
        (572600.0, 5510100.0, 196.4),
    ]
    msp.add_polyline3d(coords_var_b, dxfattribs={"layer": "SL_TRASSE_VAR_B"})

    # 3. Fehlerhafte CAD-Lieferung: Bewusste Selbstüberschneidung (Schleife) für automatische QA/QC-Quarantäne
    coords_defect = [
        (563500.0, 5516000.0, 180.0),
        (564500.0, 5515000.0, 178.5),
        (564000.0, 5514500.0, 177.0),
        (564600.0, 5515600.0, 179.0),  # Kreuzt das vorherige Segment -> 2D Self-Intersection!
        (565200.0, 5513800.0, 175.2),
    ]
    msp.add_polyline3d(coords_defect, dxfattribs={"layer": "SL_TRASSE_DEFECT"})

    doc.saveas(OUT_DXF)
    print(f"FERTIG! 3D ISO-19650 CAD-Datei gespeichert unter: {OUT_DXF.resolve()}")


if __name__ == "__main__":
    main()
