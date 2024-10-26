import ifcopenshell
from ifcopenshell.util.element import get_psets
import os
from utils.helpers import (generate_output_file_path, create_colour_assignment)

def filter_properties(ifc_file, property_conditions, colour_rgb=(162, 34, 35), transparency=0.1):
    """
    Filtert die IFC-Datei basierend auf den angegebenen Property Sets, Properties und Werten.
    Färbt die zutreffenden Elemente ein und speichert eine neue IFC-Datei mit einem Zeitstempel.

    :param ifc_file: Pfad zur Original-IFC-Datei
    :param property_conditions: Liste von Dictionaries mit Schlüsseln 'property_set', 'property', 'value'
    :param colour_rgb: Farbe für die Farbzuweisung (default: Rot)
    :param transparency: Transparenzwert (default: 0.0)
    :return: Pfad zur gefilterten IFC-Datei
    """
    # Überprüfe, ob die IFC-Datei existiert
    if not os.path.isfile(ifc_file):
        raise FileNotFoundError(f"Die IFC-Datei wurde nicht gefunden: {ifc_file}")

    # Öffne die Original-IFC-Datei
    model = ifcopenshell.open(ifc_file)

    # Generiere einen Zeitstempel für den Dateinamen mithilfe der Helper-Funktion
    filtered_ifc_path = generate_output_file_path(ifc_file)

    # Füge alle relevanten Elemente basierend auf den Filtern hinzu
    for element in model.by_type("IfcBuiltElement"):
        # Hole alle Property Sets
        psets = ifcopenshell.util.element.get_psets(element)

        # Flag, um zu bestimmen, ob das Element gefiltert werden soll
        element_matches = False

        # Überprüfe jede Bedingung
        for condition in property_conditions:
            pset_name = condition.get('property_set')
            prop_name = condition.get('property')
            value = condition.get('value')

            # Überprüfe, ob das Property Set existiert
            if pset_name and pset_name in psets:
                # Wenn nur das Property Set angegeben ist
                if not prop_name and not value:
                    element_matches = True
                    break  # Keine weitere Prüfung nötig
                properties = psets[pset_name]
                # Überprüfe, ob die Property existiert
                if prop_name and prop_name in properties:
                    # Wenn nur Property Set und Property angegeben sind
                    if not value:
                        element_matches = True
                        break
                    prop_value = properties[prop_name]
                    # Vergleiche den Wert (als String, um Typunterschiede zu vermeiden)
                    if str(prop_value) == str(value):
                        element_matches = True
                        break
            elif not pset_name:
                # Wenn kein Property Set angegeben ist, durchsuchen wir alle Property Sets
                for pset, properties in psets.items():
                    # Überprüfe, ob die Property existiert
                    if prop_name and prop_name in properties:
                        # Wenn nur Property angegeben ist
                        if not value:
                            element_matches = True
                            break
                        prop_value = properties[prop_name]
                        # Vergleiche den Wert
                        if str(prop_value) == str(value):
                            element_matches = True
                            break
                if element_matches:
                    break  # Wenn Element passt, weitere Prüfung abbrechen

        # Wenn das Element die Bedingungen erfüllt, färbe es ein
        if element_matches:
            if element.Representation:
                for rep in element.Representation.Representations:
                    if hasattr(rep, "Items"):
                        for item in rep.Items:
                            if isinstance(item, ifcopenshell.entity_instance):
                                # Füge die Farbzuweisung hinzu
                                create_colour_assignment(model, element, item, colour_rgb, transparency)

    # Speichere die gefilterte IFC-Datei
    model.write(str(filtered_ifc_path))
    print(f"Gefilterte IFC-Datei gespeichert unter: {filtered_ifc_path}")
    return str(filtered_ifc_path)
