from main import create_lrp_profile, perform_clash_detection, save_ifc_file, process_elements
from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, filedialog, messagebox
import os
import ifcopenshell
import sys

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
        button_input_file.config(text=f"Input IFC: {os.path.basename(file_path)}")

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
        button_output_file.config(text=f"Output IFC: {os.path.basename(file_path)}")

# Funktion zum Erstellen des Lichtraumprofils
def on_create_lichtraumprofil():
    if not input_ifc_file or not output_ifc_file:
        messagebox.showwarning("Warnung", "Bitte Input und Output IFC-Datei auswählen.")
        return
    lrp_text = entry_1.get("1.0", "end-1c")
    try:
        lrp_data = eval(lrp_text)
        if not isinstance(lrp_data, list):
            raise ValueError
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

# Erstellung des Fensters
window = Tk()

# Skalierung anpassen
window.tk.call('tk', 'scaling', 1.0)

window.geometry("1000x700")
window.configure(bg="#FFFFFF")

canvas = Canvas(
    window,
    bg="#FFFFFF",
    height=700,
    width=1000,
    bd=0,
    highlightthickness=0,
    relief="ridge"
)
canvas.place(x=0, y=0)

# Hintergrund-Rechteck
canvas.create_rectangle(
    0.0,
    0.0,
    1000.0,
    700.0,
    fill="#213563",
    outline=""
)

# Titeltext
canvas.create_text(
    100.0,  # 132.0 * 1.6667
    73.5,   # 42.0 * 1.75
    anchor="nw",
    text="Automatisches Erstellen des Lichtraumprofils und Clash Testing",
    fill="#FFFFFF",
    font=("Arial", 26, "bold")
)

# Input IFC-Datei Text
canvas.create_text(
    101.7,  # 61.0 * 1.6667
    171.5,  # 98.0 * 1.75
    anchor="nw",
    text="Input IFC-Datei:",
    fill="#FFFFFF",
    font=("Arial", 18)
)

# Output IFC-Datei Text
canvas.create_text(
    101.7,
    281.75,  # 161.0 * 1.75
    anchor="nw",
    text="Output IFC-Datei:",
    fill="#FFFFFF",
    font=("Arial", 18)
)

# Button für Input-Datei
button_input_file = Button(
    window,
    text="   Input IFC-Datei auswählen",  # Einzug mit Leerzeichen
    borderwidth=0,
    highlightthickness=0,
    command=select_input_file,
    relief="flat",
    fg="#FFFFFF",
    bg="#404040",
    wraplength=750,
    justify="left",
    anchor="w",
    font=("Arial", 16),
    padx=10,  # Padding nach rechts
    pady=5    # Padding nach unten
)
button_input_file.place(
    x=101.7,
    y=224.0,  # 128.0 * 1.75
    width=796.0,  # 477.0 * 1.6667
    height=40.0
)

# Button für Output-Datei
button_output_file = Button(
    window,
    text="   Output IFC-Datei auswählen",  # Einzug mit Leerzeichen
    borderwidth=0,
    highlightthickness=0,
    command=select_output_file,
    relief="flat",
    fg="#FFFFFF",
    bg="#404040",
    wraplength=750,
    justify="left",
    anchor="w",
    font=("Arial", 16),
    padx=10,  # Padding nach rechts
    pady=5    # Padding nach unten
)
button_output_file.place(
    x=101.7,
    y=332.5,  # 190.0 * 1.75
    width=796.0,
    height=40.0
)

# Text für LRP-Koordinaten
canvas.create_text(
    101.7,
    407.75,  # 233.0 * 1.75
    anchor="nw",
    text="Koordinaten des LRPs bezogen auf den Nullpunkt:",
    fill="#FFFFFF",
    font=("Arial", 18)
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
    x=101.7,
    y=460.25,  # 263.0 * 1.75
    width=796.0,
    height=40.0
)

# Tag für linken und vertikalen Einzug
entry_1.tag_configure(
    "indent",
    lmargin1=20,  # Linker Einzug
    lmargin2=20,  # Linker Einzug für Zeilen nach der ersten
    spacing1=10,   # Abstand oberhalb des Absatzes
    spacing3=10    # Abstand unterhalb des Absatzes
)
# Standardwert für die Koordinaten mit Einzug
entry_1.insert("1.0", "[(-14.5, 0.0), (14.5, 0.0), (14.5, 7.5), (-14.5, 7.5)]", "indent")

# Button für Lichtraumprofil erstellen
button_3 = Button(
    window,
    text="   Lichtraumprofil erstellen",  # Einzug mit Leerzeichen
    borderwidth=0,
    highlightthickness=0,
    command=on_create_lichtraumprofil,
    relief="flat",
    fg="#FFFFFF",
    bg="#404040",
    font=("Arial", 20, "bold"),
    padx=0,  # Padding nach rechts
    pady=10    # Padding nach unten
)
button_3.place(
    x=101.7,
    y=577.5,
    width=301.7,
    height=50.0
)

# Button für Clash Test durchführen
button_4 = Button(
    window,
    text="   Clash Test durchführen",  # Einzug mit Leerzeichen
    borderwidth=0,
    highlightthickness=0,
    command=on_perform_clash_test,
    relief="flat",
    fg="#FFFFFF",
    bg="#404040",
    font=("Arial", 20, "bold"),
    padx=0,  # Padding nach rechts
    pady=10    # Padding nach unten
)
button_4.place(
    x=476.7,
    y=577.5,
    width=301.7,
    height=50.0
)

window.resizable(False, False)
window.mainloop()
