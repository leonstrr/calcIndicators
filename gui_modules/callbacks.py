# gui_modules/callbacks.py

import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import ast

from gui_modules.gui_helpers import (
    open_in_blender,
    open_stl_in_blender,
    generate_output_file_path
)
from modules.bodenaushub import perform_bodenaushub, visualize_results
from modules.lichtraumprofil import create_lrp_and_perform_clash_detection

def on_open_input_in_blender(input_ifc_file, blender_executable, open_ifc_script):
    """Öffnet eine IFC-Datei in Blender."""
    print(f"on_open_input_in_blender aufgerufen mit: {input_ifc_file}, {blender_executable}, {open_ifc_script}")
    if not input_ifc_file:
        messagebox.showwarning("Warnung", "Bitte zuerst eine Input IFC-Datei auswählen.")
        return
    open_in_blender(input_ifc_file, blender_executable, open_ifc_script)

def select_input_file(button_input_file, input_ifc_file_var, zustand0_file_var, zustand1_file_var):
    """Öffnet einen Dateidialog zum Auswählen der IFC-Datei."""
    print("select_input_file aufgerufen")
    file_path = filedialog.askopenfilename(
        filetypes=[("IFC Files", "*.ifc")],
        title="Input IFC-Datei auswählen"
    )
    if file_path:
        input_ifc_file_var.set(file_path)
        button_input_file.config(text=f"   Input IFC: {Path(file_path).name}")
        print(f"Input IFC-Datei ausgewählt: {file_path}")

def on_create_lrp_and_clash_detection(entry_1, input_ifc_file, blender_executable, open_ifc_script):
    """Erstellt das Lichtraumprofil und führt Clash Detection durch."""
    print("on_create_lrp_and_clash_detection aufgerufen")
    if not input_ifc_file:
        messagebox.showwarning("Warnung", "Bitte eine Input IFC-Datei auswählen.")
        return

    lrp_text = entry_1.get("1.0", "end-1c")
    print(f"LRP-Koordinaten eingegeben: {lrp_text}")
    try:
        lrp_data = ast.literal_eval(lrp_text)
        if not isinstance(lrp_data, list):
            raise ValueError("Die Koordinaten müssen eine Liste sein.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Bitte gültige Koordinaten für das Lichtraumprofil eingeben.\n{e}")
        return

    # Generiere automatisch einen Output-Dateipfad
    output_ifc_file = generate_output_file_path(input_ifc_file)
    print(f"Generierter Output IFC-Dateipfad: {output_ifc_file}")

    # Lichtraumprofil erstellen und Clash Detection durchführen
    try:
        create_lrp_and_perform_clash_detection(input_ifc_file, output_ifc_file, lrp_data)
        print(f"Lichtraumprofil erstellt und Clash Detection durchgeführt: {output_ifc_file}")
        open_in_blender(output_ifc_file, blender_executable, open_ifc_script)  # Öffne die neue IFC-Datei in Blender
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler bei der Verarbeitung: {e}")

def select_stl_file(button, var_name, zustand0_file_var, zustand1_file_var):
    """Öffnet einen Dateidialog zum Auswählen der STL-Datei."""
    print(f"select_stl_file aufgerufen für: {var_name}")
    file_path = filedialog.askopenfilename(
        filetypes=[("STL Files", "*.stl")],
        title="STL-Datei auswählen"
    )
    if file_path:
        if var_name == "zustand0_file":
            zustand0_file_var.set(file_path)
            button.config(text=f"   STL-Zustand 0: {Path(file_path).name}")
            print(f"STL-Zustand 0 ausgewählt: {file_path}")
        elif var_name == "zustand1_file":
            zustand1_file_var.set(file_path)
            button.config(text=f"   STL-Zustand 1: {Path(file_path).name}")
            print(f"STL-Zustand 1 ausgewählt: {file_path}")

def open_specific_stl_in_blender(stl_file_var, blender_executable, open_stl_script):
    """Öffnet eine spezifische STL-Datei in Blender."""
    stl_file = stl_file_var.get()
    print(f"open_specific_stl_in_blender aufgerufen mit: {stl_file}")
    if not stl_file:
        messagebox.showwarning("Warnung", "Bitte zuerst eine STL-Datei auswählen.")
        return
    open_stl_in_blender([stl_file], blender_executable, open_stl_script)

def start_bodenaushub(zustand0_file_var, zustand1_file_var, blender_executable, open_stl_script, label_min_work):
    """Startet die Bodenaushub-Berechnung."""
    print("start_bodenaushub aufgerufen")
    if not zustand0_file_var.get() or not zustand1_file_var.get():
        messagebox.showwarning("Warnung", "Bitte beide STL-Dateien auswählen.")
        return
    try:
        # Führe die Bodenaushub-Berechnung durch
        results = perform_bodenaushub(zustand0_file_var.get(), zustand1_file_var.get())
        min_work = results['min_work']
        print(f"Bodenaushub-Berechnung abgeschlossen. Minimale Arbeit: {min_work}")

        # Anzeige des minimalen Arbeitsergebnisses
        label_min_work.config(text=f"Minimale Arbeit: {min_work:.2f} m³·m")
        print(f"Minimale Arbeit angezeigt: {min_work:.2f} m³·m")

        # Visualisierungen extern anzeigen
        visualize_results(
            bounding_box=results['bounding_box'],
            triangles_mesh0=results['triangles_mesh0'],
            volume_df=results['volume_df'],
            middle_point=results['middle_point']
        )
        print("Visualisierungen erstellt.")

        # Importiere die ausgewählten STL-Dateien in Blender
        open_stl_in_blender(
            [zustand0_file_var.get(), zustand1_file_var.get()],
            blender_executable,
            open_stl_script
        )
        print("STL-Dateien in Blender importiert.")

        messagebox.showinfo("Erfolg",
                            "Bodenaushub-Berechnung erfolgreich abgeschlossen und STL-Dateien in Blender importiert.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler bei der Bodenaushub-Berechnung:\n{e}")
