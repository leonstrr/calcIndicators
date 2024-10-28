import ifcopenshell
from ifcopenshell.util.element import get_psets
import os
from utils.helpers import generate_output_file_path, create_colour_assignment, compare_values

file_path = r"C:\Users\leons\iCloudDrive\Masterarbeit\IFC-Files\selbst erstellte files\bruecke mit trasse\bruecke und trasse 24-10-06.ifc"
conditions = [{'property_set': None, 'property':'ConcreteCover', 'value':0.06 }]

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

    print(f"Öffne IFC-Datei: {ifc_file}")

    # Öffne die Original-IFC-Datei
    model = ifcopenshell.open(ifc_file)

    # Anzahl der Elemente im Modell ausgeben
    num_elements = len(model.by_type("IfcBuiltElement"))
    print(f"Anzahl der IfcBuiltElement-Entitäten im Modell: {num_elements}")

    # Generiere einen Zeitstempel für den Dateinamen mithilfe der Helper-Funktion
    filtered_ifc_path = generate_output_file_path(ifc_file)
    print(f"Gefilterte IFC-Datei wird gespeichert unter: {filtered_ifc_path}")

    epsilon = 1e-4  # Toleranz für numerische Vergleiche
    print(f"Verwendete Toleranz für numerische Vergleiche: {epsilon}")

    # Füge alle relevanten Elemente basierend auf den Filtern hinzu
    for element in model.by_type("IfcBuiltElement"):
        element_id = element.id()
        element_name = element.Name if hasattr(element, 'Name') else 'N/A'
        print(f"\nVerarbeite Element ID: {element_id}, Name: {element_name}")

        # Hole alle Property Sets
        psets = ifcopenshell.util.element.get_psets(element)
        print(f"Verfügbare Property Sets für Element {element_id}: {list(psets.keys())}")

        # Flag, um zu bestimmen, ob das Element gefiltert werden soll
        element_matches = False

        # Überprüfe jede Bedingung
        for condition in property_conditions:
            pset_name = condition.get('property_set')
            prop_name = condition.get('property')
            value = condition.get('value')

            print(f"Prüfe Bedingung: Property Set='{pset_name}', Property='{prop_name}', Wert='{value}'")

            # Überprüfe, ob das Property Set existiert
            if pset_name and pset_name in psets:
                print(f"Property Set '{pset_name}' gefunden im Element {element_id}")
                properties = psets[pset_name]
                # Überprüfe, ob die Property existiert
                if prop_name and prop_name in properties:
                    prop_value = properties[prop_name]
                    print(f"Property '{prop_name}' gefunden mit Wert '{prop_value}'")
                    # Vergleiche den Wert (mit Toleranz)
                    if value is not None:
                        if compare_values(prop_value, value, epsilon):
                            print(f"Wert '{prop_value}' entspricht der Bedingung '{value}' (mit Toleranz)")
                            element_matches = True
                            break
                        else:
                            print(f"Wert '{prop_value}' entspricht NICHT der Bedingung '{value}' (mit Toleranz)")
                    else:
                        # Wenn kein Wert angegeben ist, reicht das Vorhandensein der Property
                        print(f"Property '{prop_name}' vorhanden, kein Wert zum Vergleichen angegeben")
                        element_matches = True
                        break
                else:
                    print(f"Property '{prop_name}' nicht gefunden im Property Set '{pset_name}'")
            elif not pset_name:
                # Wenn kein Property Set angegeben ist, durchsuchen wir alle Property Sets
                print("Kein Property Set angegeben, durchsuchen alle Property Sets")
                for current_pset_name, properties in psets.items():
                    if prop_name and prop_name in properties:
                        prop_value = properties[prop_name]
                        print(f"Property '{prop_name}' gefunden in Property Set '{current_pset_name}' mit Wert '{prop_value}'")
                        # Vergleiche den Wert (mit Toleranz)
                        if value is not None:
                            if compare_values(prop_value, value, epsilon):
                                print(f"Wert '{prop_value}' entspricht der Bedingung '{value}' (mit Toleranz)")
                                element_matches = True
                                break
                            else:
                                print(f"Wert '{prop_value}' entspricht NICHT der Bedingung '{value}' (mit Toleranz)")
                        else:
                            # Wenn kein Wert angegeben ist, reicht das Vorhandensein der Property
                            print(f"Property '{prop_name}' vorhanden, kein Wert zum Vergleichen angegeben")
                            element_matches = True
                            break
                if element_matches:
                    break  # Wenn Element passt, weitere Prüfung abbrechen
            else:
                print(f"Property Set '{pset_name}' nicht gefunden im Element {element_id}")

        # Wenn das Element die Bedingungen erfüllt, färbe es ein
        if element_matches:
            print(f"Element {element_id} erfüllt die Bedingungen und wird eingefärbt.")
            if element.Representation:
                for rep in element.Representation.Representations:
                    if hasattr(rep, "Items"):
                        for item in rep.Items:
                            if isinstance(item, ifcopenshell.entity_instance):
                                # Füge die Farbzuweisung hinzu
                                create_colour_assignment(model, element, item, colour_rgb, transparency)
        else:
            print(f"Element {element_id} erfüllt die Bedingungen NICHT.")

    # Speichere die gefilterte IFC-Datei
    model.write(str(filtered_ifc_path))
    print(f"\nGefilterte IFC-Datei gespeichert unter: {filtered_ifc_path}")
    return str(filtered_ifc_path)

def main():
    filter_properties(file_path, conditions)

if __name__ == '__main__':
    main()
