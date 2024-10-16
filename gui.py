from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, PhotoImage, ttk
import os
import ifcopenshell
import sys
import subprocess
import datetime
import ast

from modules.lichtraumprofil import create_lrp_and_perform_clash_detection
from modules.bodenaushub import (
    create_raster, point_in_triangle, barycentric_interpolation, interpolate_height,
    calculate_bounding_box, visualize_mesh, calculate_discrete_volume,
    visualize_volume_distribution_2d, visualize_volume_bars_3d,
    calculate_distance_matrix, calculate_transport_work, optimize_transport,
    calculate_minimum_work
)
from modules.property_filter import property_filer

# DPI-Awareness aktivieren (nur für Windows)
if sys.platform == "win32":
    try:
        from ctypes import windll
        windll.user32.SetProcessDPIAware()
    except Exception as e:
        print(f"Fehler beim Setzen der DPI-Awareness: {e}")

# Pfad zur Blender-Executable
blender_executable = "C:/Programme/Blender Foundation/Blender 4.2/blender.exe"

# Globale Variable für die Input IFC-Datei
input_ifc_file = None

# Pfad zum Blender-Skript
open_ifc_script = os.path.join(os.path.dirname(__file__), "scripts", "open_ifc.py")


def load_blender_icon():
    """Lädt das Blender-Icon und das Hover-Icon."""
    global blender_icon, blender_icon_hover
    try:
        blender_icon = PhotoImage(file=os.path.join("assets", "blender_icon.png"))
        blender_icon_hover = PhotoImage(file=os.path.join("assets", "blender_icon_hover.png"))
    except Exception as e:
        messagebox.showerror("Fehler", f"Blender-Icon konnte nicht geladen werden:\n{e}")
        # Da wir keine Fallback-Optionen mehr haben, brechen wir das Programm ab
        raise e  # Optional: Programm abbrechen, wenn Icons nicht geladen werden können


def open_in_blender(file_path):
    """Öffnet eine IFC-Datei in Blender."""
    if not os.path.isfile(blender_executable):
        messagebox.showerror("Fehler", f"Blender wurde nicht gefunden unter:\n{blender_executable}")
        return
    if not os.path.isfile(open_ifc_script):
        messagebox.showerror("Fehler", f"Blender-Skript wurde nicht gefunden unter:\n{open_ifc_script}")
        return
    if not os.path.isfile(file_path):
        messagebox.showerror("Fehler", f"Die Datei wurde nicht gefunden:\n{file_path}")
        return
    try:
        subprocess.Popen([
            blender_executable,
            "--python", open_ifc_script,
            "--",                    # Trennt Blender-Argumente von Skript-Argumenten
            file_path
        ])
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Öffnen von Blender: {e}")


def on_open_input_in_blender():
    """Handler zum Öffnen des Input-Modells in Blender."""
    global input_ifc_file
    if not input_ifc_file:
        messagebox.showwarning("Warnung", "Bitte zuerst eine Input IFC-Datei auswählen.")
        return
    open_in_blender(input_ifc_file)


def select_input_file(button_input_file):
    """Öffnet einen Dateidialog zum Auswählen der Input-IFC-Datei."""
    global input_ifc_file
    file_path = filedialog.askopenfilename(
        filetypes=[("IFC Files", "*.ifc")],
        title="Input IFC-Datei auswählen"
    )
    if file_path:
        input_ifc_file = file_path
        # Aktualisiere den Button-Text mit dem Dateinamen
        button_input_file.config(text=f"   Input IFC: {Path(file_path).name}")


def generate_output_file_path(input_path):
    """Generiert einen automatischen Output-Dateipfad basierend auf dem Input."""
    input_path = Path(input_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{input_path.stem}_output_{timestamp}{input_path.suffix}"
    return input_path.parent / output_filename


def on_create_lrp_and_clash_detection(entry_1):
    """Handler zum Erstellen des Lichtraumprofils und Durchführen der Clash Detection."""
    global input_ifc_file
    if not input_ifc_file:
        messagebox.showwarning("Warnung", "Bitte eine Input IFC-Datei auswählen.")
        return

    lrp_text = entry_1.get("1.0", "end-1c")
    try:
        lrp_data = ast.literal_eval(lrp_text)
        if not isinstance(lrp_data, list):
            raise ValueError("Die Koordinaten müssen eine Liste sein.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Bitte gültige Koordinaten für das Lichtraumprofil eingeben.\n{e}")
        return

    # Generiere automatisch einen Output-Dateipfad
    output_ifc_file = generate_output_file_path(input_ifc_file)

    # Lichtraumprofil erstellen und Clash Detection durchführen
    try:
        create_lrp_and_perform_clash_detection(input_ifc_file, output_ifc_file, lrp_data)
        open_in_blender(output_ifc_file)  # Öffne die neue IFC-Datei in Blender
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler bei der Verarbeitung: {e}")


def add_hover_effect(widget, hover_bg=None, normal_bg=None, hover_image=None, normal_image=None):
    """
    Fügt einem Widget Hover-Effekte hinzu.

    :param widget: Das Widget, dem die Effekte hinzugefügt werden sollen.
    :param hover_bg: Hintergrundfarbe beim Hover.
    :param normal_bg: Hintergrundfarbe bei Nicht-Hover.
    :param hover_image: Bild beim Hover (für Image-Buttons).
    :param normal_image: Bild bei Nicht-Hover (für Image-Buttons).
    """
    if hover_bg and normal_bg:
        def on_enter(event):
            widget.config(bg=hover_bg)

        def on_leave(event):
            widget.config(bg=normal_bg)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    if hover_image and normal_image:
        def on_enter_img(event):
            widget.config(image=hover_image)

        def on_leave_img(event):
            widget.config(image=normal_image)

        widget.bind("<Enter>", on_enter_img)
        widget.bind("<Leave>", on_leave_img)


def main():
    """Hauptfunktion zur Erstellung der GUI."""
    global input_ifc_file

    # Erstellung des Fensters
    window = tk.Tk()

    # Skalierung anpassen
    window.tk.call('tk', 'scaling', 1.0)

    # Fenstergröße anpassen
    window.geometry("1200x800")
    window.configure(bg="#FFFFFF")
    window.title("Automatisierte Berechnung von Nachhaltigkeitsindikatoren v.0.1")

    # Laden des Blender-Icons und des Hover-Icons
    load_blender_icon()

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
    canvas = tk.Canvas(
        tab1,
        bg="#213563",  # Setze den Hintergrund auf Blau
        bd=0,
        highlightthickness=0,
        relief="ridge"
    )
    canvas.pack(fill='both', expand=True)

    # Titeltext
    canvas.create_text(
        150.0,
        100.0,
        anchor="nw",
        text="Lichtraumprofil und Clash Testing",
        fill="#FFFFFF",
        font=("Arial", 28, "bold")
    )

    # Frames für die Dateiauswahl und Blender-Buttons
    frame_input = tk.Frame(tab1, bg="#213563")
    frame_input.place(x=150.0, y=200.0, width=900.0, height=48.0)

    # Input IFC-Datei Text
    canvas.create_text(
        150.0,
        165.0,
        anchor="nw",
        text="Input IFC-Datei:",
        fill="#FFFFFF",
        font=("Arial", 20)
    )

    # Input-Datei Button
    button_input_file = tk.Button(
        frame_input,
        text="   Input IFC-Datei auswählen...",
        borderwidth=0,
        highlightthickness=0,
        command=lambda: select_input_file(button_input_file),
        relief="flat",
        fg="#FFFFFF",
        bg="#404040",
        justify="left",
        anchor="w",
        font=("Arial", 16),
        padx=10,  # Padding nach rechts
        pady=10    # Padding nach unten
    )
    button_input_file.pack(side="left", fill="both", expand=True, padx=(0, 10))

    # Hover-Effekte für das Input-Datei Button hinzufügen
    add_hover_effect(button_input_file, hover_bg="#505050", normal_bg="#404040")

    # Button zum Öffnen des Input-Modells in Blender mit Hover-Effekten
    button_open_input_blender = tk.Button(
        frame_input,
        image=blender_icon,
        borderwidth=0,
        highlightthickness=0,
        command=on_open_input_in_blender,
        relief="flat",
        bg="#213563",
        width=48,
        height=48
    )
    button_open_input_blender.pack(side="left", padx=(10, 0), pady=0)  # Angepasstes Padding

    # Hover-Effekte für das Blender-Icon hinzufügen
    add_hover_effect(button_open_input_blender, hover_image=blender_icon_hover, normal_image=blender_icon)

    # Button für Lichtraumprofil erstellen & Clash Detection durchführen
    frame_actions = tk.Frame(tab1, bg="#213563")
    frame_actions.place(x=150.0, y=450, width=900.0, height=80.0)

    button_combined = tk.Button(
        frame_actions,
        text="   Lichtraumprofil erstellen und Clash Detection ausführen",
        borderwidth=0,
        highlightthickness=0,
        command=lambda: on_create_lrp_and_clash_detection(entry_1),
        relief="flat",
        fg="#FFFFFF",
        bg="#404040",
        font=("Arial", 20, 'bold'),
        padx=10,
        pady=10
    )
    button_combined.pack(side="left", fill="both", expand=True, padx=(0, 0), pady=10)

    # Hover-Effekte für das combined Button hinzufügen
    add_hover_effect(button_combined, hover_bg="#505050", normal_bg="#404040")

    # --- Text und Eingabefeld für LRP-Koordinaten --- #
    canvas.create_text(
        150.0,
        315.0,
        anchor="nw",
        text="Koordinaten des LRPs bezogen auf den Nullpunkt:",
        fill="#FFFFFF",
        font=("Arial", 20)
    )

    # Einzug im Text-Widget durch Tag-Konfiguration
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
        y=350.0,
        width=900.0,
        height=48.0  # Erhöhte Höhe für mehr Platz
    )
    # Tag für linken und vertikalen Einzug
    entry_1.tag_configure(
        "indent",
        lmargin1=30,  # Linker Einzug erhöht
        lmargin2=30,  # Linker Einzug für Zeilen nach der ersten erhöht
        spacing1=15,   # Abstand oberhalb des Absatzes
        spacing3=15    # Abstand unterhalb des Absatzes
    )
    # Standardwert für die Koordinaten mit Einzug
    entry_1.insert("1.0", "[(-14.5, 0.0), (14.5, 0.0), (14.5, 7.5), (-14.5, 7.5)]", "indent")

    # Hover-Effekte für das Eingabefeld hinzufügen
    add_hover_effect(entry_1, hover_bg="#505050", normal_bg="#404040")

    # --- Weitere Tabs Inhalte --- #
    # Tab 2: Bodenaushub Berechnungen
    label_tab2 = tk.Label(tab2, text="Berechnungen zum Bodenaushub", font=("Arial", 20))
    label_tab2.pack(pady=20)
    # Weitere Widgets hinzufügen

    # Tab 3: Property-Filter
    label_tab3 = tk.Label(tab3, text="Filter nach Property Sets", font=("Arial", 20))
    label_tab3.pack(pady=20)
    # Weitere Widgets hinzufügen

    window.resizable(False, False)
    window.mainloop()


if __name__ == "__main__":
    main()
