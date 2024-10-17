# gui.py

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, PhotoImage, ttk
import os
import sys
import datetime
import ast

from modules.lichtraumprofil import create_lrp_and_perform_clash_detection
from modules.bodenaushub import perform_bodenaushub, visualize_results
from modules.property_filter import property_filer

from gui_modules.gui_helpers import (
    add_hover_effect,
    load_blender_icon,
    open_in_blender,
    open_stl_in_blender,
    generate_output_file_path
)
from gui_modules.callbacks import (
    on_open_input_in_blender,
    select_input_file,
    on_create_lrp_and_clash_detection,
    select_stl_file,
    open_specific_stl_in_blender,
    start_bodenaushub
)

# DPI-Awareness aktivieren (nur für Windows)
if sys.platform == "win32":
    try:
        from ctypes import windll
        windll.user32.SetProcessDPIAware()
    except Exception as e:
        print(f"Fehler beim Setzen der DPI-Awareness: {e}")

# Pfad zur Blender-Executable
blender_executable = "C:/Programme/Blender Foundation/Blender 4.2/blender.exe"

# Pfade zu den Blender-Skripten
open_ifc_script = os.path.join(os.path.dirname(__file__), "scripts", "open_ifc.py")
open_stl_script = os.path.join(os.path.dirname(__file__), "scripts", "open_stl.py")  # Neuer Skriptpfad

def test_open_blender(blender_executable, open_stl_script):
    """Testet das Öffnen von Blender mit einer Beispiel-Datei."""
    test_file = "C:/Pfad/zu/deiner/Beispiel.stl"  # Ändere diesen Pfad zu einer existierenden STL-Datei
    open_stl_in_blender([test_file], blender_executable, open_stl_script)

def main():
    """Hauptfunktion zur Erstellung der GUI."""

    # Erstellung des Fensters
    window = tk.Tk()

    # Skalierung anpassen
    window.tk.call('tk', 'scaling', 1.0)

    # Fenstergröße anpassen
    window.geometry("1200x800")  # Größer für die Grafiken
    window.configure(bg="#FFFFFF")
    window.title("Automatisierte Berechnung von Nachhaltigkeitsindikatoren v.0.1")

    # Laden des Blender-Icons und des Hover-Icons
    blender_icon, blender_icon_hover = load_blender_icon()

    # Erstellen der StringVar-Variablen
    input_ifc_file_var = tk.StringVar()
    zustand0_file_var = tk.StringVar()
    zustand1_file_var = tk.StringVar()

    # Stil für die Notebook-Tabs definieren
    style = ttk.Style()
    style.theme_use('clam')  # Verwende das 'clam' Theme für bessere Anpassungsmöglichkeiten

    style.configure('TNotebook.Tab',
                    background="#404040",  # Hintergrundfarbe der Tabs
                    foreground="#FFFFFF",  # Textfarbe der Tabs
                    padding=[10, 5],       # Innenabstand
                    font=('Arial', 16, 'bold'))  # Schriftart und -größe

    # Definiere die Farben für ausgewählte und aktive Tabs
    style.map('TNotebook.Tab',
              background=[('selected', '#606060'), ('active', '#505050')],
              foreground=[('selected', '#FFFFFF'), ('active', '#FFFFFF')])

    # Notebook und Tabs erstellen
    notebook = ttk.Notebook(window)
    notebook.pack(expand=True, fill='both')

    # Tab 1: Lichtraumprofil und Clash Detection
    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text='Lichtraumprofil')

    # Tab 2: Bodenaushub Berechnungen
    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text='Bodenaushub')

    # Tab 3: Property-Filter
    tab3 = ttk.Frame(notebook)
    notebook.add(tab3, text='Property-Filter')

    # --- Inhalte für Tab 1 (Lichtraumprofil) --- #
    # Canvas erstellen mit blauer Hintergrundfarbe und dynamischer Größe
    canvas1 = tk.Canvas(
        tab1,
        bg="#213563",  # Setze den Hintergrund auf Blau
        bd=0,
        highlightthickness=0,
        relief="ridge"
    )
    canvas1.pack(fill='both', expand=True)

    # Titeltext
    canvas1.create_text(
        150.0,
        50.0,
        anchor="nw",
        text="Lichtraumprofil und Clash Testing",
        fill="#FFFFFF",
        font=("Arial", 28, "bold")
    )

    # Hauptframe für die IFC-Datei-Auswahl
    frame_ifc = tk.Frame(tab1, bg="#213563")
    frame_ifc.place(x=150.0, y=100.0, width=900.0, height=48.0)  # Höhe auf 48.0 angepasst

    # Label für Input IFC-Datei
    label_ifc = tk.Label(
        frame_ifc,
        text="Input IFC-Datei:",
        bg="#213563",
        fg="#FFFFFF",
        font=("Arial", 22)
    )
    label_ifc.pack(side="left", padx=(0, 10), pady=0)

    # Button zur Auswahl der IFC-Datei
    button_input_file = tk.Button(
        frame_ifc,
        text="   Input IFC-Datei auswählen...",
        borderwidth=0,
        highlightthickness=0,
        command=lambda: select_input_file(button_input_file, input_ifc_file_var, zustand0_file_var, zustand1_file_var),
        relief="flat",
        fg="#FFFFFF",
        bg="#404040",
        justify="left",
        anchor="w",
        font=("Arial", 16),
        padx=10,  # Padding nach rechts
        pady=5    # Padding nach unten auf 5 angepasst
    )
    button_input_file.pack(side="left", fill='both', expand=True, padx=(0, 10), pady=0)


    # Hover-Effekte für den Input-Datei-Button hinzufügen
    add_hover_effect(button_input_file, hover_bg="#505050", normal_bg="#404040")

    # Blender-Icon Button zum Öffnen der IFC-Datei in Blender
    button_open_input_blender = tk.Button(
        frame_ifc,
        image=blender_icon,
        borderwidth=0,
        highlightthickness=0,
        command=lambda: on_open_input_in_blender(
            input_ifc_file_var.get(),
            blender_executable,
            open_ifc_script
        ),
        relief="flat",
        bg="#213563",
        width=48,
        height=48
    )
    button_open_input_blender.pack(side="left", padx=(10, 0), pady=0)

    # Hover-Effekte für das Blender-Icon hinzufügen
    add_hover_effect(button_open_input_blender, hover_image=blender_icon_hover, normal_image=blender_icon)

    # Button für Lichtraumprofil erstellen & Clash Detection durchführen
    frame_actions1 = tk.Frame(tab1, bg="#213563")
    frame_actions1.place(x=150.0, y=320.0, width=900.0, height=80.0)  # Position auf y=320.0 verschoben

    button_combined = tk.Button(
        frame_actions1,
        text="   Lichtraumprofil erstellen und Clash Detection ausführen",
        borderwidth=0,
        highlightthickness=0,
        command=lambda: on_create_lrp_and_clash_detection(
            entry_1, input_ifc_file_var.get(), blender_executable, open_ifc_script
        ),
        relief="flat",
        fg="#FFFFFF",
        bg="#404040",
        font=("Arial", 22, 'bold'),
        padx=10,
        pady=10
    )
    button_combined.pack(side="left", fill="both", expand=True, padx=(0, 0), pady=10)

    # Hover-Effekte für das combined Button hinzufügen
    add_hover_effect(button_combined, hover_bg="#505050", normal_bg="#404040")

    # --- Text und Eingabefeld für LRP-Koordinaten --- #
    # Koordinaten Label
    canvas1.create_text(
        150.0,
        180.0,
        anchor="nw",
        text="Koordinaten des LRPs bezogen auf den Nullpunkt:",
        fill="#FFFFFF",
        font=("Arial", 22)
    )

    # Eingabefeld für Koordinaten mit angepasster Höhe
    entry_1 = tk.Text(
        tab1,
        bd=0,
        bg="#404040",
        fg="#FFFFFF",
        highlightthickness=0,
        font=("Arial", 16)
    )
    entry_1.place(
        x=150.0,
        y=210.0,
        width=900.0,
        height=48.0  # Höhe auf 48.0 angepasst
    )
    # Tag für linken und vertikalen Einzug
    entry_1.tag_configure(
         "indent",
        lmargin1=30,  # Linker Einzug erhöht
        lmargin2=30,  # Linker Einzug für Zeilen nach der ersten erhöht
        spacing1=14,    # Abstand oberhalb des Absatzes reduziert
        spacing3=14     # Abstand unterhalb des Absatzes reduziert
    )
    entry_1.tag_configure(
        "large_font",
        font=("Arial", 17),
    )
    # Standardwert für die Koordinaten mit Einzug
    entry_1.insert("1.0", "[(-14.5, 0.0), (14.5, 0.0), (14.5, 7.5), (-14.5, 7.5)]", ("indent", "large_font"))

    # Hover-Effekte für das Eingabefeld hinzufügen
    add_hover_effect(entry_1, hover_bg="#505050", normal_bg="#404040")

    # --- Inhalte für Tab 2 (Bodenaushub) --- #
    # Canvas erstellen mit blauer Hintergrundfarbe und dynamischer Größe
    canvas2 = tk.Canvas(
        tab2,
        bg="#213563",
        bd=0,
        highlightthickness=0,
        relief="ridge"
    )
    canvas2.pack(fill='both', expand=True)

    # Titeltext für Tab 2
    canvas2.create_text(
        150.0,
        50.0,
        anchor="nw",
        text="Bodenaushub Berechnungen",
        fill="#FFFFFF",
        font=("Arial", 28, "bold")
    )

    # Hauptframe für Bodenaushub-Tabs
    frame_bodenaushub = tk.Frame(tab2, bg="#213563")
    frame_bodenaushub.place(x=150.0, y=100.0, width=900.0, height=400.0)  # Erhöhte Höhe für mehr Platz

    # Funktion zur Erstellung eines Zustands-Frames
    def create_zustand_frame(parent, zustand_num, text_label):
        """Erstellt einen Frame für einen bestimmten Zustand mit Label, Button und Blender-Icon."""
        frame = tk.Frame(parent, bg="#213563")
        frame.pack(pady=10, fill='x')  # Vertikaler Abstand zwischen den Frames

        # Label für den Zustand
        label = tk.Label(
            frame,
            text=text_label,
            bg="#213563",
            fg="#FFFFFF",
            font=("Arial", 22)
        )
        label.pack(side="left", padx=(0, 10))

        # Button zur Auswahl der STL-Datei
        button = tk.Button(
            frame,
            text=f"   STL-Datei Zustand {zustand_num} auswählen...",
            borderwidth=0,
            highlightthickness=0,
            command=lambda: select_stl_file(button, f"zustand{zustand_num}_file", zustand0_file_var, zustand1_file_var),
            relief="flat",
            fg="#FFFFFF",
            bg="#404040",
            justify="left",
            anchor="w",
            font=("Arial", 16),
            padx=10,
            pady=10
        )
        button.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Hover-Effekte für den Button hinzufügen
        add_hover_effect(button, hover_bg="#505050", normal_bg="#404040")

        # Blender-Icon Button
        blender_button = tk.Button(
            frame,
            image=blender_icon,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: open_specific_stl_in_blender(zustand0_file_var if zustand_num == 0 else zustand1_file_var, blender_executable, open_stl_script),
            relief="flat",
            bg="#213563",
            width=48,
            height=48
        )
        blender_button.pack(side="left", padx=(10, 0), pady=0)

        # Hover-Effekte für das Blender-Icon hinzufügen
        add_hover_effect(blender_button, hover_image=blender_icon_hover, normal_image=blender_icon)

    # Erstellung der Frames für Zustand 0 und Zustand 1
    create_zustand_frame(frame_bodenaushub, 0, "STL-Datei Zustand 0 auswählen:")
    create_zustand_frame(frame_bodenaushub, 1, "STL-Datei Zustand 1 auswählen:")

    # Button zum Starten der Bodenaushub-Berechnung
    frame_berechnung = tk.Frame(tab2, bg="#213563")
    frame_berechnung.place(x=150.0, y=320.0, width=900.0, height=80.0)  # Angepasste Position

    button_start_berechnung = tk.Button(
        frame_berechnung,
        text="   Berechnung starten",
        borderwidth=0,
        highlightthickness=0,
        command=lambda: start_bodenaushub(
            zustand0_file_var,
            zustand1_file_var,
            blender_executable,
            open_stl_script,
            label_min_work
        ),
        relief="flat",
        fg="#FFFFFF",
        bg="#404040",
        font=("Arial", 22, 'bold'),
        padx=10,
        pady=10
    )
    button_start_berechnung.pack(side="left", fill="both", expand=True, padx=(0, 0), pady=10)

    # Hover-Effekte für das Start-Berechnung Button hinzufügen
    add_hover_effect(button_start_berechnung, hover_bg="#505050", normal_bg="#404040")

    # Label zur Anzeige der minimalen Arbeit
    label_min_work = tk.Label(
        tab2,
        text="Minimale Arbeit: N/A",
        bg="#213563",
        fg="#FFFFFF",
        font=("Arial", 16)
    )
    label_min_work.place(x=150.0, y=420.0)  # Angepasste Position

    # --- Inhalte für Tab 3 (Property-Filter) --- #
    label_tab3 = tk.Label(tab3, text="Filter nach Property Sets", font=("Arial", 22))
    label_tab3.pack(pady=20)
    # Weitere Widgets hinzufügen

    window.resizable(True, True)  # Ermögliche Fensteranpassung für größere Inhalte
    window.mainloop()


if __name__ == "__main__":
    main()
