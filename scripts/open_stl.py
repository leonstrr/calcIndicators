import bpy
import sys
import os

def import_stl(filepath):
    """
    Importiert eine STL-Datei in Blender.

    Parameters:
    filepath (str): Der vollständige Pfad zur STL-Datei.

    Returns:
    None
    """
    if not os.path.isfile(filepath):
        print(f"Datei nicht gefunden: {filepath}")
        return
    try:
        bpy.ops.import_mesh.stl(filepath=filepath)
        print(f"Importiert: {filepath}")
    except Exception as e:
        print(f"Fehler beim Importieren von {filepath}: {e}")


def main():
    """
    Hauptfunktion zum Importieren von STL-Dateien.
    Erwartet, dass die Dateipfade nach dem '--' Argument übergeben werden.

    Returns:
    None
    """
    argv = sys.argv
    # Finden des '--' Arguments, um die STL-Dateipfade zu extrahieren
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    if not argv:
        print("Keine STL-Dateien angegeben. Verwende das Format:")
        print("blender --background --python open_stl.py -- <pfad_zur_stl1> <pfad_zur_stl2> ...")
        return

    for filepath in argv:
        import_stl(filepath)


if __name__ == "__main__":
    main()
