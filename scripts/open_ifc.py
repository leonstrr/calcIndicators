import bpy
import sys

# Argumente nach '--' erhalten
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

if not argv:
    print("Kein Dateipfad übergeben.")
    sys.exit(1)

ifc_file_path = argv[0]

# Optional: Überprüfen, ob die Datei existiert
import os
if not os.path.isfile(ifc_file_path):
    print(f"Die IFC-Datei wurde nicht gefunden: {ifc_file_path}")
    sys.exit(1)

# IFC-Projekt laden
try:
    bpy.ops.bim.load_project(should_start_fresh_session=True, filepath=ifc_file_path)
    print(f"IFC-Datei erfolgreich geladen: {ifc_file_path}")
except Exception as e:
    print(f"Fehler beim Laden der IFC-Datei: {e}")
    sys.exit(1)
