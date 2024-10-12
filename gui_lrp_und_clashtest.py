from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, filedialog

import sys
import os
import multiprocessing
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.api
import ifcopenshell.util.element
from ifcopenshell.util.element import get_psets

# Hier kommen deine Hilfsfunktionen und die neu definierten Funktionen
# wie create_lichtraumprofil und perform_clash_test
# ... (die Funktionen aus deinem Hauptprogramm hier einfügen)

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path("assets/frame0")

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

# Globale Variablen für die Datei-Pfade
input_ifc_file = None
output_ifc_file = None

def select_input_file():
    global input_ifc_file
    file_path = filedialog.askopenfilename(
        filetypes=[("IFC Files", "*.ifc")],
        title="Input IFC-File auswählen"
    )
    if file_path:
        button_input_file.config(text=file_path)
        input_ifc_file = file_path

def select_output_file():
    global output_ifc_file
    file_path = filedialog.asksaveasfilename(
        defaultextension=".ifc",
        filetypes=[("IFC Files", "*.ifc")],
        title="Output IFC-File auswählen"
    )
    if file_path:
        button_output_file.config(text=file_path)
        output_ifc_file = file_path

def on_create_lichtraumprofil():
    if not input_ifc_file or not output_ifc_file:
        print("Bitte Input und Output IFC-Datei auswählen.")
        return
    lrp_text = entry_1.get("1.0", "end-1c")
    try:
        lrp_data = eval(lrp_text)
        if not isinstance(lrp_data, list):
            raise ValueError
    except:
        print("Bitte gültige Koordinaten für das Lichtraumprofil eingeben.")
        return
    create_lrp_profile(input_ifc_file, lrp_data, output_ifc_file)

def on_perform_clash_test():
    if not input_ifc_file or not output_ifc_file:
        print("Bitte Input und Output IFC-Datei auswählen.")
        return
    perform_clash_test(input_ifc_file, output_ifc_file)

window = Tk()

window.geometry("600x400")
window.configure(bg = "#FFFFFF")

canvas = Canvas(
    window,
    bg = "#FFFFFF",
    height = 400,
    width = 600,
    bd = 0,
    highlightthickness = 0,
    relief = "ridge"
)

canvas.place(x = 0, y = 0)
canvas.create_rectangle(
    0.0,
    0.0,
    600.0,
    400.0,
    fill="#009682",
    outline=""
)

canvas.create_text(
    132.0,
    42.0,
    anchor="nw",
    text="Lichtraumprofil und Clash Testing",
    fill="#FFFFFF",
    font=("Inter Bold", 20 * -1)
)

canvas.create_text(
    61.0,
    98.0,
    anchor="nw",
    text="Input IFC-File:",
    fill="#FFFFFF",
    font=("Inter", 16 * -1)
)

canvas.create_text(
    61.0,
    161.0,
    anchor="nw",
    text="Output IFC-File:",
    fill="#FFFFFF",
    font=("Inter", 16 * -1)
)

# Passe die Buttons an
button_image_1 = PhotoImage(
    file=relative_to_assets("button_1.png"))
button_input_file = Button(
    image=button_image_1,
    borderwidth=0,
    highlightthickness=0,
    command=select_input_file,
    relief="flat",
    text="Input IFC-Datei auswählen",
    compound="center",
    fg="#FFFFFF",
    bg="#009682"
)
button_input_file.place(
    x=61.0,
    y=128.0,
    width=477.0,
    height=18.0
)

button_image_2 = PhotoImage(
    file=relative_to_assets("button_2.png"))
button_output_file = Button(
    image=button_image_2,
    borderwidth=0,
    highlightthickness=0,
    command=select_output_file,
    relief="flat",
    text="Output IFC-Datei auswählen",
    compound="center",
    fg="#FFFFFF",
    bg="#009682"
)
button_output_file.place(
    x=61.0,
    y=190.0,
    width=477.0,
    height=18.0
)

canvas.create_text(
    60.0,
    223.0,
    anchor="nw",
    text="Koordinaten des LRPs bezogen auf den Nullpunkt:",
    fill="#FFFFFF",
    font=("Inter", 16 * -1)
)

entry_image_1 = PhotoImage(
    file=relative_to_assets("entry_1.png"))
entry_bg_1 = canvas.create_image(
    299.5,
    262.0,
    image=entry_image_1
)
entry_1 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    highlightthickness=0
)
entry_1.place(
    x=61.0,
    y=253.0,
    width=477.0,
    height=16.0
)
# Setze einen Standardwert für die Koordinaten
entry_1.insert("1.0", "[(-14.5, 0.0), (14.5, 0.0), (14.5, 7.5), (-14.5, 7.5)]")

button_image_3 = PhotoImage(
    file=relative_to_assets("button_3.png"))
button_3 = Button(
    image=button_image_3,
    borderwidth=0,
    highlightthickness=0,
    command=on_create_lichtraumprofil,
    relief="flat",
    text="Lichtraumprofil erstellen",
    compound="center",
    fg="#FFFFFF",
    bg="#009682"
)
button_3.place(
    x=61.0,
    y=299.0,
    width=181.0,
    height=37.0
)

button_image_4 = PhotoImage(
    file=relative_to_assets("button_4.png"))
button_4 = Button(
    image=button_image_4,
    borderwidth=0,
    highlightthickness=0,
    command=on_perform_clash_test,
    relief="flat",
    text="Clash Test durchführen",
    compound="center",
    fg="#FFFFFF",
    bg="#009682"
)
button_4.place(
    x=286.0,
    y=299.0,
    width=181.0,
    height=37.0
)

window.resizable(False, False)
window.mainloop()
