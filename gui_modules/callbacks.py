from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import ast
import os

from gui_modules.gui_helpers import open_in_blender, open_stl_in_blender
from modules.bodenaushub import perform_bodenaushub, visualize_results, export_transport_plan_to_csv
from modules.lichtraumprofil import create_lrp_and_perform_clash_detection
from utils.helpers import generate_output_file_path, parse_property_conditions  # Allgemeine Funktionen importieren
from modules.property_filter import open_model, filter_elements_in_model, color_elements  # Importiere die filter_properties-Funktion

def on_open_input_in_blender(input_ifc_file, blender_executable, open_ifc_script):
    """Öffnet eine IFC-Datei in Blender."""
    print(f"on_open_input_in_blender aufgerufen mit: {input_ifc_file}, {blender_executable}, {open_ifc_script}")
    if not input_ifc_file:
        messagebox.showwarning("Warnung", "Bitte zuerst eine Input IFC-Datei auswählen.")
        return
    open_in_blender(input_ifc_file, blender_executable, open_ifc_script)
def select_input_file(button_input_file, input_ifc_file_var):
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
def on_create_lrp_and_clash_detection(entry_1, entry_conditions, input_ifc_file, blender_executable, open_ifc_script, listbox_clashing_elements):
    """Erstellt das Lichtraumprofil und führt Clash Detection durch."""
    print("on_create_lrp_and_clash_detection aufgerufen")
    if not input_ifc_file:
        messagebox.showwarning("Warnung", "Bitte eine Input IFC-Datei auswählen.")
        return

    # LRP-Koordinaten verarbeiten
    lrp_text = entry_1.get("1.0", "end-1c")
    print(f"LRP-Koordinaten eingegeben: {lrp_text}")
    try:
        lrp_data = ast.literal_eval(lrp_text)
        if not isinstance(lrp_data, list):
            raise ValueError("Die Koordinaten müssen eine Liste sein.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Bitte gültige Koordinaten für das Lichtraumprofil eingeben.\n{e}")
        return

    # Property-Bedingungen verarbeiten
    conditions_input = entry_conditions.get("1.0", "end-1c")
    print(f"Property-Bedingungen eingegeben: {conditions_input}")
    if not conditions_input.strip():
        messagebox.showwarning("Warnung", "Bitte mindestens eine gültige Filterbedingung eingeben.")
        return

    try:
        property_conditions = parse_property_conditions(conditions_input)
    except ValueError as ve:
        messagebox.showerror("Fehler", str(ve))
        return

    # Generiere Output-Dateipfad
    output_ifc_file = generate_output_file_path(input_ifc_file)
    print(f"Generierter Output IFC-Dateipfad: {output_ifc_file}")

    # Lichtraumprofil erstellen und Clash Detection durchführen
    try:
        model, clashing_elements_info = create_lrp_and_perform_clash_detection(
            input_ifc_file, output_ifc_file, lrp_data, property_conditions
        )
        print(f"Lichtraumprofil erstellt und Clash Detection durchgeführt: {output_ifc_file}")

        # Aktualisieren der Listbox mit den kollidierenden Elementen
        listbox_clashing_elements.delete(0, tk.END)  # Löschen der vorherigen Einträge
        if clashing_elements_info:
            for info in clashing_elements_info:
                listbox_clashing_elements.insert(tk.END, info)
        else:
            listbox_clashing_elements.insert(tk.END, "Keine Kollisionen gefunden.")

        # Öffne die neue IFC-Datei in Blender
        open_in_blender(output_ifc_file, blender_executable, open_ifc_script)
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
def start_bodenaushub(zustand0_file_var, zustand1_file_var, cell_size_var, depot_distance_var, label_volume, label_work):
    """
    Startet die Bodenaushub-Berechnung und aktualisiert die GUI entsprechend.

    :param zustand0_file_var: StringVar für Zustand 0 STL-Datei
    :param zustand1_file_var: StringVar für Zustand 1 STL-Datei
    :param cell_size_var: DoubleVar für die Rastergröße
    :param depot_distance_var: DoubleVar für die Deponie-Distanz
    :param label_volume: Label-Widget für das Ergebnis der minimalen Arbeit
    :param label_work: Label-Widget für die Mengen/Arbeit von/zur Deponie
    """

    zustand0_file = zustand0_file_var.get()
    zustand1_file = zustand1_file_var.get()
    cell_size = cell_size_var.get()
    depot_distance = depot_distance_var.get()

    if not zustand0_file or not zustand1_file:
        messagebox.showerror("Fehler", "Bitte beide STL-Dateien auswählen.")
        return

    try:
        # Berechnung durchführen
        results = perform_bodenaushub(
            zustand0_file,
            zustand1_file,
            depot_distance,
            cell_size
        )

        total_excess = results['total_excess']
        total_deficit = results['total_deficit']
        total_difference = total_excess - total_deficit
        total_difference_message = abs(total_difference)
        min_work = results['total_costs']
        min_work_external = results['depot_costs']

        # Depot-Transportwert ermitteln
        depot_transport_value = results['depot_transport_value']

        # Nachricht basierend auf dem Vorzeichen der Differenz erstellen
        if total_difference > 0:
            depot_message = f"zur Deponie"
        elif total_difference < 0:
            depot_message = f"von der Deponie"
        else:
            depot_message = f"Die Deponie wird nicht genutzt."

        # Label neu beschriften
        label_volume.config(
            text=f"Überschüsse: {total_excess:.2f} m³, Defizite: {total_deficit:.2f} m³, Differenz gesamt: {total_difference:.2f} m³."
        )
        label_work.config(
            text=f"Minimale Arbeit (gesamt): {min_work:.2f} m³·m, davon {min_work_external:.2f} m³·m {depot_message}"
        )

        # Verzeichnis der STL-Dateien ermitteln
        stl_directory = os.path.dirname(zustand0_file)

        # Dateiname für die CSV-Datei festlegen
        csv_filename = os.path.join(stl_directory, 'transport_plan.csv')

        # Bestimmen von to_depot_value und from_depot_value
        if total_difference > 0:
            to_depot_value = depot_transport_value
            from_depot_value = 0
        elif total_difference < 0:
            to_depot_value = 0
            from_depot_value = depot_transport_value
        else:
            to_depot_value = 0
            from_depot_value = 0

        # Transportplan als CSV exportieren
        export_transport_plan_to_csv(
            results['transport_plan'],
            results['excess_points'],
            results['deficit_points'],
            results['depot_transport_value'],
            results['total_difference'],
            depot_distance,
            filename=csv_filename
        )

        # Visualisiere die Ergebnisse
        visualize_results(
            results['bounding_box'],
            results['raster_points'],
            results['triangles_set'],
            results['point_df'],
        )

    except Exception as e:
        messagebox.showerror("Fehler", f"Bei der Berechnung ist ein Fehler aufgetreten:\n{e}")

def apply_property_filter(ifc_file, conditions_input, colour, transparency, blender_executable, open_ifc_script):
    """
    Führt den Property-Filter durch, färbt die passenden Elemente ein und öffnet das Ergebnis in Blender.

    :param ifc_file: Pfad zur IFC-Datei
    :param conditions_input: Eingabe aus dem Text-Widget (mehrzeiliger String)
    :param colour: Farbe im Format "R, G, B"
    :param transparency: Transparenz [0..1]
    :param blender_executable: Pfad zur Blender-Executable
    :param open_ifc_script: Pfad zum Blender-Skript zum Öffnen der IFC-Datei
    """
    print("apply_property_filter aufgerufen")
    if not ifc_file:
        messagebox.showerror("Fehler", "Bitte eine IFC-Datei auswählen.")
        return

    # Entfernen des Beispieltexts und Überprüfung der Eingabe
    conditions_input = conditions_input.strip()
    example_conditions = "Beispiel:\nPset_WallCommon.FireRating=30min\nPset_DoorCommon.IsExternal=True"
    if conditions_input == example_conditions or not conditions_input:
        messagebox.showwarning("Warnung", "Bitte mindestens eine gültige Filterbedingung eingeben.")
        return

    try:
        colour_rgb = tuple(map(int, colour.split(',')))
        if len(colour_rgb) != 3 or not all(0 <= val <= 255 for val in colour_rgb):
            raise ValueError
    except ValueError:
        messagebox.showerror("Fehler", "Die Farbe muss im Format R,G,B angegeben werden, wobei R, G und B Zahlen zwischen 0 und 255 sind.")
        return
    try:
        transparency_val = float(transparency)
        if not (0.0 <= transparency_val <= 1.0):
            raise ValueError
    except ValueError:
        messagebox.showerror("Fehler", "Der Transparenzwert muss eine Zahl zwischen 0.0 und 1.0 sein.")
        return

    # Verarbeite die Bedingungen in eine Liste von Dictionaries
    try:
        property_conditions = parse_property_conditions(conditions_input)
    except ValueError as ve:
        messagebox.showerror("Fehler", str(ve))
        return

    try:
        # Öffne das Modell
        model = open_model(ifc_file)

        # Filtere die Elemente
        matching_elements = filter_elements_in_model(model, property_conditions)

        # Färbe die Elemente ein
        color_elements(model, matching_elements, colour_rgb, transparency_val)

        # Speichere das Modell
        filtered_ifc_path = generate_output_file_path(ifc_file)
        model.write(str(filtered_ifc_path))
        print(f"Gefilterte IFC-Datei gespeichert unter: {filtered_ifc_path}")

        # Öffne die gefilterte IFC-Datei in Blender
        open_in_blender(filtered_ifc_path, blender_executable, open_ifc_script)

    except Exception as e:
        messagebox.showerror("Fehler", f"Beim Anwenden des Filters ist ein Fehler aufgetreten:\n{e}")






