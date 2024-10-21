# gui_modules/gui_helpers.py
import tkinter as tk
from tkinter import messagebox, PhotoImage, colorchooser, END
import os
import subprocess

def open_in_blender(file_path, blender_executable, open_ifc_script):
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
            "--",  # Trennt Blender-Argumente von Skript-Argumenten
            file_path
        ])
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Öffnen von Blender: {e}")
        print(f"Fehler beim Öffnen von Blender: {e}")
def open_stl_in_blender(stl_files, blender_executable, open_stl_script):
    """Öffnet mehrere STL-Dateien in Blender."""
    print(f"open_stl_in_blender aufgerufen mit: {stl_files}, {blender_executable}, {open_stl_script}")
    if not os.path.isfile(blender_executable):
        messagebox.showerror("Fehler", f"Blender wurde nicht gefunden unter:\n{blender_executable}")
        return
    if not os.path.isfile(open_stl_script):
        messagebox.showerror("Fehler", f"Blender-Skript wurde nicht gefunden unter:\n{open_stl_script}")
        return
    for file_path in stl_files:
        if not os.path.isfile(file_path):
            messagebox.showerror("Fehler", f"Die Datei wurde nicht gefunden:\n{file_path}")
            return
    try:
        # Starte Blender im Hintergrund und importiere die STL-Dateien
        print(f"Starte Blender mit Skript: {open_stl_script} und Dateien: {stl_files}")
        subprocess.Popen([
            blender_executable,
            "--python", open_stl_script,
            "--"
        ] + stl_files)  # Übergibt alle STL-Dateien nach '--'
        print("Blender erfolgreich gestartet mit den STL-Dateien.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Öffnen von Blender: {e}")
        print(f"Fehler beim Öffnen von Blender: {e}")
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
def load_blender_icon():
    """Lädt das Blender-Icon und das Hover-Icon."""
    try:
        blender_icon = PhotoImage(file=os.path.join("assets", "blender_icon.png"))
        blender_icon_hover = PhotoImage(file=os.path.join("assets", "blender_icon_hover.png"))
        print("Blender-Icons erfolgreich geladen.")
        return blender_icon, blender_icon_hover
    except Exception as e:
        messagebox.showerror("Fehler", f"Blender-Icon konnte nicht geladen werden:\n{e}")
        print(f"Fehler beim Laden der Blender-Icons: {e}")
        raise e
def choose_colour(entry_colour):
    """
    Öffnet einen Farb-Dialog und setzt die ausgewählte Farbe in das übergebene Entry-Widget.

    :param entry_colour: Das Entry-Widget, in das die Farbe eingefügt wird
    """
    colour_code = colorchooser.askcolor(title="Farbe auswählen")
    if colour_code and colour_code[0]:
        # Rundung der RGB-Werte und Umwandlung in int
        rgb = ','.join(map(str, map(int, colour_code[0])))
        entry_colour.delete(0, tk.END)
        entry_colour.insert(0, rgb)
def update_transparency_entry(entry_transparency, val):
    """
    Aktualisiert das Transparenz-Eingabefeld basierend auf dem Slider-Wert.

    :param entry_transparency: Das Entry-Widget, das den Transparenzwert enthält
    :param val: Aktueller Wert des Sliders
    """
    try:
        transparency_val = float(val)
        transparency_val = max(0.0,
                               min(1.0, transparency_val))  # Sicherstellen, dass der Wert zwischen 0.0 und 1.0 liegt
        entry_transparency.delete(0, tk.END)
        entry_transparency.insert(0, f"{transparency_val:.1f}")
    except ValueError:
        pass  # Ungültigen Wert ignorieren
