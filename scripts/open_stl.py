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
        bpy.ops.wm.stl_import(filepath=filepath)
        print(f"Importiert: {filepath}")
    except Exception as e:
        print(f"Fehler beim Importieren von {filepath}: {e}")


def main():
    """
    Hauptfunktion zum Importieren von STL-Dateien.
    Erwartet, dass der Dateipfad nach dem '--' Argument übergeben wird.

    Returns:
    None
    """
    argv = sys.argv
    # Finden des '--' Arguments, um den STL-Dateipfad zu extrahieren
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    if not argv:
        print("Keine STL-Datei angegeben. Verwende das Format:")
        print("blender --background --python open_stl.py -- <pfad_zur_stl>")
        return

    stl_file = argv[0]
    import_stl(stl_file)


if __name__ == "__main__":
    main()
