from main import create_lrp_profile, perform_clash_detection, save_ifc_file, process_elements
from pathlib import Path
from tkinter import Tk, Canvas, Text, Button, Frame, filedialog, messagebox, PhotoImage
import os
import ifcopenshell
import sys
import subprocess

# DPI-Awareness aktivieren
if sys.platform == "win32":
    try:
        from ctypes import windll
        windll.user32.SetProcessDPIAware()
    except Exception as e:
        print(f"Fehler beim Setzen der DPI-Awareness: {e}")

# Globale Variablen für die Datei-Pfade
input_ifc_file = None
output_ifc_file = None

# Pfad zur Blender-Executable
blender_executable = "C:/Programme/Blender Foundation/Blender 4.2/blender.exe"

# Erstellung des Fensters
window = Tk()

# Skalierung anpassen
window.tk.call('tk', 'scaling', 1.0)

# Fenstergröße anpassen
window.geometry("1200x800")
window.configure(bg="#FFFFFF")

# Canvas erstellen
canvas = Canvas(
    window,
    bg="#FFFFFF",
    height=800,
    width=1200,
    bd=0,
    highlightthickness=0,
    relief="ridge"
)
canvas.place(x=0, y=0)

# Hintergrund-Rechteck
canvas.create_rectangle(
    0.0,
    0.0,
    1200.0,
    800.0,
    fill="#213563",
    outline=""
)

# Titeltext
canvas.create_text(
    150.0,  # Angepasst für größere Fenster
    100.0,
    anchor="nw",
    text="Lichtraumprofil und Clash Testing",
    fill="#FFFFFF",
    font=("Arial", 28, "bold")
)

# Frames für die Dateiauswahl und Blender-Buttons
frame_input = Frame(window, bg="#213563")
frame_input.place(x=150.0, y=200.0, width=900.0, height=48.0)

frame_output = Frame(window, bg="#213563")
frame_output.place(x=150.0, y=350.0, width=900.0, height=48.0)

# Input IFC-Datei Text
canvas.create_text(
    150.0,
    170.0,
    anchor="nw",
    text="Input IFC-Datei:",
    fill="#FFFFFF",
    font=("Arial", 20)
)

# Output IFC-Datei Text
canvas.create_text(
    150.0,
    320.0,
    anchor="nw",
    text="Output IFC-Datei:",
    fill="#FFFFFF",
    font=("Arial", 20)
)

# Pfad zum Blender-Skript
open_ifc_script = os.path.join(os.path.dirname(__file__), "scripts", "open_ifc.py")

# Funktion zum Laden des Blender-Icons
def load_blender_icon():
    global blender_icon
    try:
        blender_icon = PhotoImage(file=os.path.join("assets", "blender_icon.png"))
    except Exception as e:
        messagebox.showerror("Fehler", f"Blender-Icon konnte nicht geladen werden:\n{e}")
        blender_icon = None  # Fallback, falls das Icon nicht geladen werden kann

# Laden des Blender-Icons nach Erstellung des Root-Fensters
load_blender_icon()

# Funktion zum Öffnen eines IFC-Modells in Blender
def open_in_blender(file_path):
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
        messagebox.showinfo("Erfolg", f"Blender wurde geöffnet und IFC-Datei wird geladen:\n{os.path.basename(file_path)}")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Öffnen von Blender: {e}")


# Funktion zum Öffnen des Input-Modells in Blender
def on_open_input_in_blender():
    if not input_ifc_file:
        messagebox.showwarning("Warnung", "Bitte zuerst eine Input IFC-Datei auswählen.")
        return
    open_in_blender(input_ifc_file)

# Funktion zum Öffnen des Output-Modells in Blender
def on_open_output_in_blender():
    if not output_ifc_file:
        messagebox.showwarning("Warnung", "Bitte zuerst eine Output IFC-Datei auswählen.")
        return
    open_in_blender(output_ifc_file)

# Funktionen zum Auswählen der Dateien
def select_input_file():
    global input_ifc_file
    file_path = filedialog.askopenfilename(
        filetypes=[("IFC Files", "*.ifc")],
        title="Input IFC-Datei auswählen"
    )
    if file_path:
        input_ifc_file = file_path
        # Aktualisiere den Button-Text mit dem Dateinamen
        button_input_file.config(text=f"   Input IFC: {os.path.basename(file_path)}")

def select_output_file():
    global output_ifc_file
    file_path = filedialog.asksaveasfilename(
        defaultextension=".ifc",
        filetypes=[("IFC Files", "*.ifc")],
        title="Output IFC-Datei auswählen"
    )
    if file_path:
        output_ifc_file = file_path
        # Aktualisiere den Button-Text mit dem Dateinamen
        button_output_file.config(text=f"   Output IFC: {os.path.basename(file_path)}")

# Funktion zum Erstellen des Lichtraumprofils
def on_create_lrp_profile():
    if not input_ifc_file or not output_ifc_file:
        messagebox.showwarning("Warnung", "Bitte Input und Output IFC-Datei auswählen.")
        return
    lrp_text = entry_1.get("1.0", "end-1c")
    try:
        lrp_data = eval(lrp_text)
        if not isinstance(lrp_data, list):
            raise ValueError("Die Koordinaten müssen eine Liste sein.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Bitte gültige Koordinaten für das Lichtraumprofil eingeben.\n{e}")
        return

    # IFC-Datei laden
    try:
        model = ifcopenshell.open(input_ifc_file)
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden der IFC-Datei: {e}")
        return

    # Lichtraumprofil erstellen
    try:
        lrp_element = create_lrp_profile(model, lrp_data)
        messagebox.showinfo("Erfolg", "Lichtraumprofil wurde erfolgreich erstellt.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Erstellen des Lichtraumprofils: {e}")
        return

    # IFC-Datei speichern
    try:
        save_ifc_file(model, output_ifc_file)
        messagebox.showinfo("Erfolg", "IFC-Datei mit Lichtraumprofil wurde gespeichert.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Speichern der IFC-Datei: {e}")

# Funktion zum Durchführen des Clash Tests
def on_perform_clash_test():
    if not input_ifc_file or not output_ifc_file:
        messagebox.showwarning("Warnung", "Bitte Input und Output IFC-Datei auswählen.")
        return

    # IFC-Datei laden
    try:
        model = ifcopenshell.open(input_ifc_file)
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden der IFC-Datei: {e}")
        return

    # Lichtraumprofil finden
    all_built_elements = model.by_type("IfcBuiltElement")
    try:
        lrp_element = process_elements(all_built_elements, name_filter="Lichtraumprofil")
    except ValueError as e:
        messagebox.showerror("Fehler", f"Fehler beim Finden des Lichtraumprofils: {e}")
        return

    # Clash Detection durchführen
    try:
        model = perform_clash_detection(model, lrp_element)
        messagebox.showinfo("Erfolg", "Clash Detection wurde erfolgreich durchgeführt.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler bei der Clash Detection: {e}")
        return

    # IFC-Datei speichern
    try:
        save_ifc_file(model, output_ifc_file)
        messagebox.showinfo("Erfolg", "IFC-Datei nach Clash Detection wurde gespeichert.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Speichern der IFC-Datei: {e}")

# Text für LRP-Koordinaten
canvas.create_text(
    150.0,
    450.0,  # Verschoben von 500 auf 450
    anchor="nw",
    text="Koordinaten des LRPs bezogen auf den Nullpunkt:",
    fill="#FFFFFF",
    font=("Arial", 20)
)

# Einzug im Text-Widget durch Tag-Konfiguration
entry_1 = Text(
    window,
    bd=0,
    bg="#404040",
    fg="#FFFFFF",
    highlightthickness=0,
    font=("Arial", 16)
)
entry_1.place(
    x=150.0,
    y=500.0,  # Verschoben von 550 auf 500
    width=900.0,
    height=48.0  # Höhe erhöhen (optional: auf 100.0 erhöhen für mehr Platz)
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

# Frames für die Aktionen unten
frame_actions = Frame(window, bg="#213563")
frame_actions.place(x=150.0, y=600.0, width=900.0, height=80.0)  # Geändert von y=650 auf y=600

# Button für Lichtraumprofil erstellen
button_3 = Button(
    frame_actions,
    text="   Lichtraumprofil erstellen",
    borderwidth=0,
    highlightthickness=0,
    command=on_create_lrp_profile,
    relief="flat",
    fg="#FFFFFF",
    bg="#404040",
    font=("Arial", 20),
    padx=10,
    pady=10
)
button_3.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=10)

# Button für Clash Test durchführen
button_4 = Button(
    frame_actions,
    text="   Clash Test durchführen",
    borderwidth=0,
    highlightthickness=0,
    command=on_perform_clash_test,
    relief="flat",
    fg="#FFFFFF",
    bg="#404040",
    font=("Arial", 20),
    padx=10,
    pady=10
)
button_4.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=10)

# Buttons innerhalb der Frames

# Button für Input-Datei
button_input_file = Button(
    frame_input,
    text="   Input IFC-Datei auswählen",
    borderwidth=0,
    highlightthickness=0,
    command=select_input_file,
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

# Button zum Öffnen des Input-Modells in Blender
if blender_icon:
    button_open_input_blender = Button(
        frame_input,
        image=blender_icon,
        borderwidth=0,
        highlightthickness=0,
        command=on_open_input_in_blender,
        relief="flat",
        bg="#404040",
        width=48,
        height=48
    )
    button_open_input_blender.pack(side="left", padx=(10, 0), pady=0)  # Angepasstes Padding
else:
    # Fallback, falls das Icon nicht geladen werden konnte
    button_open_input_blender = Button(
        frame_input,
        text="🌀",
        borderwidth=0,
        highlightthickness=0,
        command=on_open_input_in_blender,
        relief="flat",
        fg="#FFFFFF",
        bg="#404040",
        font=("Arial", 16),
        padx=10,
        pady=10
    )
    button_open_input_blender.pack(side="left", padx=(10, 0), pady=10)

# Button für Output-Datei
button_output_file = Button(
    frame_output,
    text="   Output IFC-Datei auswählen",
    borderwidth=0,
    highlightthickness=0,
    command=select_output_file,
    relief="flat",
    fg="#FFFFFF",
    bg="#404040",
    justify="left",
    anchor="w",
    font=("Arial", 16),
    padx=10,
    pady=10
)
button_output_file.pack(side="left", fill="both", expand=True, padx=(0, 10))

# Button zum Öffnen des Output-Modells in Blender
if blender_icon:
    button_open_output_blender = Button(
        frame_output,
        image=blender_icon,
        borderwidth=0,
        highlightthickness=0,
        command=on_open_output_in_blender,
        relief="flat",
        bg="#404040",
        width=48,
        height=48
    )
    button_open_output_blender.pack(side="left", padx=(10, 0), pady=0)  # Angepasstes Padding
else:
    # Fallback, falls das Icon nicht geladen werden konnte
    button_open_output_blender = Button(
        frame_output,
        text="🌀",
        borderwidth=0,
        highlightthickness=0,
        command=on_open_output_in_blender,
        relief="flat",
        fg="#FFFFFF",
        bg="#404040",
        font=("Arial", 16),
        padx=10,
        pady=10
    )
    button_open_output_blender.pack(side="left", padx=(10, 0), pady=10)

window.resizable(False, False)
window.mainloop()
