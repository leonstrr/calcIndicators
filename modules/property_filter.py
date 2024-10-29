import ifcopenshell
from ifcopenshell.util.element import get_psets
import os
from utils.helpers import generate_output_file_path, create_colour_assignment, compare_values

def open_model(ifc_file):
    """
    Öffnet die IFC-Datei und gibt das Modell zurück.

    :param ifc_file: Pfad zur IFC-Datei.
    :return: Geöffnetes IFC-Modell.
    """
    if not os.path.isfile(ifc_file):
        raise FileNotFoundError(f"Die IFC-Datei wurde nicht gefunden: {ifc_file}")

    print(f"Öffne IFC-Datei: {ifc_file}")

    # Öffne die Original-IFC-Datei
    model = ifcopenshell.open(ifc_file)
    return model
def filter_elements_in_model(model, property_conditions, epsilon=1e-4):
    """
    Filtert Elemente im gegebenen Modell basierend auf den angegebenen Property-Bedingungen.

    :param model: Geöffnetes IFC-Modell.
    :param property_conditions: Liste von Dictionaries mit Schlüsseln 'property_set', 'property', 'value'.
    :param epsilon: Toleranz für numerische Vergleiche.
    :return: Liste der Elemente, die die Bedingungen erfüllen.
    """
    matching_elements = []

    for element in model.by_type("IfcBuiltElement"):
        element_id = element.id()
        element_name = element.Name if hasattr(element, 'Name') else 'N/A'
        # Debugging-Ausgabe
        # print(f"\nVerarbeite Element ID: {element_id}, Name: {element_name}")

        # Hole alle Property Sets
        psets = ifcopenshell.util.element.get_psets(element)
        # Debugging-Ausgabe
        # print(f"Verfügbare Property Sets für Element {element_id}: {list(psets.keys())}")

        # Flag, um zu bestimmen, ob das Element gefiltert werden soll
        element_matches = False

        # Überprüfe jede Bedingung
        for condition in property_conditions:
            pset_name = condition.get('property_set')
            prop_name = condition.get('property')
            value = condition.get('value')

            # Debugging-Ausgabe
            # print(f"Prüfe Bedingung: Property Set='{pset_name}', Property='{prop_name}', Wert='{value}'")

            # Überprüfe, ob das Property Set existiert
            if pset_name and pset_name in psets:
                properties = psets[pset_name]
                # Überprüfe, ob die Property existiert
                if prop_name and prop_name in properties:
                    prop_value = properties[prop_name]
                    # Vergleiche den Wert (mit Toleranz)
                    if value is not None:
                        if compare_values(prop_value, value, epsilon):
                            element_matches = True
                            break
                    else:
                        # Wenn kein Wert angegeben ist, reicht das Vorhandensein der Property
                        element_matches = True
                        break
            elif not pset_name:
                # Wenn kein Property Set angegeben ist, durchsuchen wir alle Property Sets
                for properties in psets.values():
                    if prop_name and prop_name in properties:
                        prop_value = properties[prop_name]
                        # Vergleiche den Wert (mit Toleranz)
                        if value is not None:
                            if compare_values(prop_value, value, epsilon):
                                element_matches = True
                                break
                        else:
                            # Wenn kein Wert angegeben ist, reicht das Vorhandensein der Property
                            element_matches = True
                            break
                if element_matches:
                    break  # Wenn Element passt, weitere Prüfung abbrechen

        if element_matches:
            # Debugging-Ausgabe
            # print(f"Element {element_id} erfüllt die Bedingungen und wird hinzugefügt.")
            matching_elements.append(element)
        else:
            # Debugging-Ausgabe
            # print(f"Element {element_id} erfüllt die Bedingungen NICHT.")
            pass

    return matching_elements
def color_elements(model, elements, colour_rgb, transparency):
    """
    Fügt Farbzuweisungen zu den angegebenen Elementen im Modell hinzu.

    :param model: Geöffnetes IFC-Modell.
    :param elements: Liste der zu färbenden Elemente.
    :param colour_rgb: RGB-Farbwert als Tupel.
    :param transparency: Transparenzwert.
    """
    for element in elements:
        if element.Representation:
            for rep in element.Representation.Representations:
                if hasattr(rep, "Items"):
                    for item in rep.Items:
                        if isinstance(item, ifcopenshell.entity_instance):
                            # Füge die Farbzuweisung hinzu
                            create_colour_assignment(model, element, item, colour_rgb, transparency)
def main():
    # Pfad zur IFC-Datei
    ifc_file = "path/to/your/file.ifc"

    # Definieren Sie die Bedingungen
    property_conditions = [
        {'property_set': 'Pset_ConcreteElementGeneral', 'property': 'ConcreteCover', 'value': 0.06}
    ]

    # Öffne das Modell
    model = open_model(ifc_file)

    # Filtere die Elemente
    matching_elements = filter_elements_in_model(model, property_conditions)

    # Optional: Färben der Elemente
    color_elements(model, matching_elements, colour_rgb=(162, 34, 35), transparency=0.1)

    # Optional: Speichern des Modells
    filtered_ifc_path = generate_output_file_path(ifc_file)
    model.write(str(filtered_ifc_path))
    print(f"Modell gespeichert unter: {filtered_ifc_path}")

