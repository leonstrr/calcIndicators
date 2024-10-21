import ifcopenshell
from ifcopenshell.util.element import get_psets
import os
from utils.helpers import (generate_output_file_path, create_colour_assignment)


def filter_properties(ifc_file, property_sets, single_properties=None, colour_rgb=(255, 0, 0), transparency=0.0):
    """
    Filtert die IFC-Datei basierend auf den angegebenen Property Sets und Properties.
    Färbt die zutreffenden Elemente ein und speichert eine neue IFC-Datei mit einem Zeitstempel.

    :param ifc_file: Pfad zur Original-IFC-Datei
    :param property_sets: Liste von Property Sets zum Filtern
    :param single_properties: Liste von einzelnen Properties zum Filtern (optional)
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

        # Flags zur Bestimmung, ob das Element gefiltert werden soll
        matches_property_set = False
        matches_single_property = False

        # Überprüfe Property Sets
        if property_sets:
            if any(ps in psets for ps in property_sets):
                matches_property_set = True

        # Überprüfe einzelne Properties
        if single_properties:
            properties = []
            if property_sets:
                for pset in property_sets:
                    properties.extend(psets.get(pset, {}).keys())
            else:
                for pset_props in psets.values():
                    properties.extend(pset_props.keys())
            if any(prop in properties for prop in single_properties):
                matches_single_property = True

        # Entscheide, ob das Element gefiltert werden soll
        if (property_sets and matches_property_set) or (single_properties and matches_single_property):
            # Färbe das Element ein
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
