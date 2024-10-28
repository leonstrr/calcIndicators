import tkinter as tk
from tkinter import ttk, filedialog
import os
import sys

from gui_modules.gui_helpers import (
    add_hover_effect,
    load_blender_icon,
    update_transparency_entry
)
from gui_modules.callbacks import (
    on_open_input_in_blender,
    select_input_file,
    on_create_lrp_and_clash_detection,
    select_stl_file,
    open_specific_stl_in_blender,
    start_bodenaushub,
    apply_property_filter
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
        command=lambda: select_input_file(button_input_file, input_ifc_file_var),
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
            command=lambda: open_specific_stl_in_blender(zustand0_file_var if zustand_num == 0 else zustand1_file_var,
                                                         blender_executable, open_stl_script),
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

    # --- Hinzufügen der Eingabefelder für Rastergröße und Depot-Distanz --- #
    # Frame für die Eingabefelder
    frame_eingaben = tk.Frame(tab2, bg="#213563")
    frame_eingaben.place(x=150.0, y=250.0, width=900.0, height=100.0)  # Angepasste Position und Größe

    # Eingabefeld für Rastergröße (cell_size)
    tk.Label(
        frame_eingaben,
        text="Rastergröße [m]:    ",
        bg="#213563",
        fg="#FFFFFF",
        font=("Arial", 18)
    ).grid(row=0, column=0, padx=0, pady=10, sticky='w')

    cell_size_var = tk.DoubleVar(value=1.0)  # Standardwert 1.0
    entry_cell_size = tk.Entry(
        frame_eingaben,
        textvariable=cell_size_var,
        width=10,
        bg="#213563",
        fg="#FFFFFF",
        font=("Arial", 16)
    )
    entry_cell_size.grid(row=0, column=1, padx=10, pady=10, sticky='w')

    # Hover-Effekte für das Rastergröße Eingabefeld hinzufügen
    add_hover_effect(entry_cell_size, hover_bg="#505050", normal_bg="#404040")

    # Eingabefeld für Depot-Distanz (depot_distance)
    tk.Label(
        frame_eingaben,
        text="Distanz zur Deponie [m]:",
        bg="#213563",
        fg="#FFFFFF",
        font=("Arial", 18)
    ).grid(row=1, column=0, padx=0, pady=10, sticky='w')

    depot_distance_var = tk.DoubleVar(value=500.0)  # Standardwert 500.0
    entry_depot_distance = tk.Entry(
        frame_eingaben,
        textvariable=depot_distance_var,
        width=10,
        bg="#213563",
        fg='#FFFFFF',
        font=("Arial", 16)
    )
    entry_depot_distance.grid(row=1, column=1, padx=10, pady=10, sticky='w')

    # Hover-Effekte für das Depot-Distanz Eingabefeld hinzufügen
    add_hover_effect(entry_depot_distance, hover_bg="#505050", normal_bg="#404040")

    # Button zum Starten der Bodenaushub-Berechnung
    frame_berechnung = tk.Frame(tab2, bg="#213563")
    frame_berechnung.place(x=150.0, y=370.0, width=900.0, height=80.0)  # Angepasste Position

    button_start_berechnung = tk.Button(
        frame_berechnung,
        text="   Berechnung starten",
        borderwidth=0,
        highlightthickness=0,
        command=lambda: start_bodenaushub(
            zustand0_file_var,
            zustand1_file_var,
            cell_size_var,
            depot_distance_var,
            label_volume,
            label_work
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
    label_volume = tk.Label(
        tab2,
        text="Minimale Arbeit: - zu berechnen - ",
        bg="#213563",
        fg="#FFFFFF",
        font=("Arial", 18)
    )
    label_volume.place(x=150.0, y=470.0)  # Angepasste Position

    # Label zur Anzeige Mengen/Arbeit von/zur Deponie
    label_work = tk.Label(
        tab2,
        text="Davon zum/vom Depot: - zu berechnen - ",
        bg="#213563",
        fg="#FFFFFF",
        font=("Arial", 18)
    )
    label_work.place(x=150.0, y=500.0)  # Angepasste Position

    # --- Inhalte für Tab 3 (Property-Filter) --- #
    # Canvas erstellen mit blauer Hintergrundfarbe und dynamischer Größe
    canvas3 = tk.Canvas(
        tab3,
        bg="#213563",  # Setze den Hintergrund auf Blau
        bd=0,
        highlightthickness=0,
        relief="ridge"
    )
    canvas3.pack(fill='both', expand=True)

    # Titeltext
    canvas3.create_text(
        150.0,
        50.0,
        anchor="nw",
        text="Filter nach Properties",
        fill="#FFFFFF",
        font=("Arial", 28, "bold")
    )

    # Hauptframe für die IFC-Datei-Auswahl
    frame_ifc_2 = tk.Frame(tab3, bg="#213563")
    frame_ifc_2.place(x=150.0, y=100.0, width=900.0, height=48.0)

    # Label für Input IFC-Datei
    label_ifc_2 = tk.Label(
        frame_ifc_2,
        text="Input IFC-Datei:",
        bg="#213563",
        fg="#FFFFFF",
        font=("Arial", 22)
    )
    label_ifc_2.pack(side="left", padx=(0, 10), pady=0)

    # Button zur Auswahl der IFC-Datei
    button_input_file_2 = tk.Button(
        frame_ifc_2,
        text="   Input IFC-Datei auswählen...",
        borderwidth=0,
        highlightthickness=0,
        command=lambda: select_input_file(button_input_file_2, input_ifc_file_var),
        relief="flat",
        fg="#FFFFFF",
        bg="#404040",
        justify="left",
        anchor="w",
        font=("Arial", 16),
        padx=10,  # Padding nach rechts
        pady=5    # Padding nach unten auf 5 angepasst
    )
    button_input_file_2.pack(side="left", fill='both', expand=True, padx=(0, 10), pady=0)

    # Hover-Effekte für den Input-Datei-Button hinzufügen
    add_hover_effect(button_input_file_2, hover_bg="#505050", normal_bg="#404040")

    # Blender-Icon Button zum Öffnen der IFC-Datei in Blender
    button_open_input_blender_2 = tk.Button(
        frame_ifc_2,
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
    button_open_input_blender_2.pack(side="left", padx=(10, 0), pady=0)

    # Hover-Effekte für das Blender-Icon hinzufügen
    add_hover_effect(button_open_input_blender_2, hover_image=blender_icon_hover, normal_image=blender_icon)

    # --- Eingabefelder für Filterbedingungen --- #
    frame_conditions = tk.Frame(tab3, bg="#213563")
    frame_conditions.place(x=150.0, y=180.0, width=900.0, height=120.0)  # Höhe angepasst

    # Label für Filterbedingungen
    label_conditions = tk.Label(
        frame_conditions,
        text="Filterbedingungen (Format: PropertySet.Property=Value):",
        bg="#213563",
        fg="#FFFFFF",
        font=("Arial", 18),
        anchor='w',
        justify='left'
    )
    label_conditions.pack(fill='x', anchor='w')

    # Mehrzeiliges Textfeld für die Eingabe der Bedingungen
    text_conditions = tk.Text(
        frame_conditions,
        bg="#404040",
        fg="#FFFFFF",
        font=("Arial", 16),
        height=4,  # Anzahl der sichtbaren Zeilen
        bd=0
    )
    text_conditions.pack(fill='both', expand=True, anchor='w')
    text_conditions.insert(1.0, "ConcreteCover=0.06\nPset_ConcreteElementGeneral.CastingMethod=INSITU")

    # Hover-Effekte für das Textfeld hinzufügen
    add_hover_effect(text_conditions, hover_bg="#505050", normal_bg="#404040")

    # --- Eingabefelder für Farbe und Transparenz --- #
    frame_colour_transparency = tk.Frame(tab3, bg="#213563")
    frame_colour_transparency.place(x=150.0, y=400.0, width=900.0, height=150.0)  # Höhe angepasst

    # Label für Farbe
    label_colour = tk.Label(
        frame_colour_transparency,
        text="Farbe (R,G,B):",
        bg="#213563",
        fg="#FFFFFF",
        font=("Arial", 18),
        anchor='w'
    )
    label_colour.pack(fill='x', anchor='w')

    # Eingabefeld für Farbe
    entry_colour = tk.Entry(
        frame_colour_transparency,
        bg="#404040",
        fg="#FFFFFF",
        font=("Arial", 16),
        bd=0
    )
    entry_colour.pack(fill='x', anchor='w')
    entry_colour.insert(0, "162,34,35")  # KIT Rot

    # Hover-Effekte für das Farbe-Eingabefeld hinzufügen
    add_hover_effect(entry_colour, hover_bg="#505050", normal_bg="#404040")

    # Label für Transparenz
    label_transparency = tk.Label(
        frame_colour_transparency,
        text="Transparenz (0.0 - 1.0):",
        bg="#213563",
        fg="#FFFFFF",
        font=("Arial", 18),
        anchor='w'
    )
    label_transparency.pack(fill='x', anchor='w')

    # Eingabefeld für Transparenz
    entry_transparency = tk.Entry(
        frame_colour_transparency,
        bg="#404040",
        fg="#FFFFFF",
        font=("Arial", 16),
        bd=0
    )
    entry_transparency.pack(fill='x', anchor='w')
    entry_transparency.insert(0, "0.0")  # Standardtransparenz

    # Hover-Effekte für das Transparenz-Eingabefeld hinzufügen
    add_hover_effect(entry_transparency, hover_bg="#505050", normal_bg="#404040")

    # --- Button zum Starten des Filters --- #
    frame_filter_button = tk.Frame(tab3, bg="#213563")
    frame_filter_button.place(x=150.0, y=310.0, width=900.0, height=80.0)  # Position angepasst

    button_start_filter = tk.Button(
        frame_filter_button,
        text="   Filter anwenden und in Blender öffnen",
        borderwidth=0,
        highlightthickness=0,
        command=lambda: apply_property_filter(
            input_ifc_file_var.get(),
            text_conditions.get("1.0", tk.END),  # Eingabe aus dem Text-Widget
            entry_colour.get(),
            entry_transparency.get(),
            blender_executable,
            open_ifc_script
        ),
        relief="flat",
        fg="#FFFFFF",
        bg="#404040",
        font=("Arial", 18, 'bold'),
        padx=0,
        pady=0
    )
    button_start_filter.pack(fill="both", expand=True)

    # Hover-Effekte für den Start-Filter Button hinzufügen
    add_hover_effect(button_start_filter, hover_bg="#505050", normal_bg="#404040")

    window.resizable(True, True)  # Ermögliche Fensteranpassung für größere Inhalte
    window.mainloop()

