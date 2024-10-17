# gui_modules/gui_helpers.py

import tkinter as tk
from tkinter import messagebox, PhotoImage
import os
import subprocess
from pathlib import Path
import datetime

from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # Falls verwendet

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
        messagebox.showinfo("Erfolg", "IFC-Datei wurde in Blender geöffnet.")
        print(f"Blender gestartet mit: {blender_executable}, {open_ifc_script}, {file_path}")
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
            "--background",  # Blender im Hintergrund starten
            "--python", open_stl_script,
            "--"
        ] + stl_files)  # Übergibt alle STL-Dateien nach '--'
        messagebox.showinfo("Erfolg", "STL-Dateien wurden in Blender importiert.")
        print("Blender erfolgreich gestartet mit den STL-Dateien.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Öffnen von Blender: {e}")
        print(f"Fehler beim Öffnen von Blender: {e}")

def generate_output_file_path(input_path):
    """Generiert einen automatischen Output-Dateipfad basierend auf dem Input."""
    input_path = Path(input_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{input_path.stem}_output_{timestamp}{input_path.suffix}"
    return input_path.parent / output_filename

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


