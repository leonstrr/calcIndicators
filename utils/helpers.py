from pathlib import Path
import datetime

def generate_output_file_path(input_path):
    """Generiert einen automatischen Output-Dateipfad basierend auf dem Input."""
    input_path = Path(input_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{input_path.stem}_filtered_{timestamp}{input_path.suffix}"
    return input_path.parent / output_filename
def create_colour_assignment(model,element, representation_item, color_rgb, transparency=0.0):
    """
    Weist einem Element eine bestimmte Farbe und Transparenz zu.

    :param model: Das IFC-Modell
    :param element: Das Element, dem die Farbe zugewiesen werden soll
    :param representation_item: Das Representation-Item des Elements
    :param color_rgb: Tupel mit RGB-Werten im Bereich 0-255, z.B. (0, 150, 130)
    :param transparency: Transparenzwert zwischen 0.0 (undurchsichtig) und 1.0 (vollständig transparent)
    :return: Das erstellte IfcStyledItem
    """
    # RGB-Werte von 0-255 auf 0-1 skalieren
    red = color_rgb[0] / 255.0
    green = color_rgb[1] / 255.0
    blue = color_rgb[2] / 255.0

    # Erstelle die Farbe
    surface_colour = model.create_entity(
        "IfcColourRgb",
        Name=None,
        Red=red,
        Green=green,
        Blue=blue
    )

    # Erstelle die SurfaceStyleShading mit Transparenz
    surface_style_shading = model.create_entity(
        "IfcSurfaceStyleShading",
        SurfaceColour=surface_colour,
        Transparency=transparency
    )

    # Erstelle die SurfaceStyle
    surface_style = model.create_entity(
        "IfcSurfaceStyle",
        Name="Custom Colour",
        Side="BOTH",
        Styles=[surface_style_shading]
    )

    # Erstelle das IfcStyledItem
    styled_item = model.create_entity(
        "IfcStyledItem",
        Item=representation_item,
        Styles=[surface_style],
        Name="Custom Colour"
    )

    return styled_item
def compare_values(prop_value, value, epsilon=1e-5):
    """
    Vergleicht zwei Werte und berücksichtigt dabei numerische Toleranzen.
    Unterstützt auch Listen von Werten.
    """
    # Wenn der Eigenschaftswert eine Liste ist
    if isinstance(prop_value, (list, tuple)):
        # Vergleiche jedes Element der Liste mit dem gewünschten Wert
        return any(compare_values(item, value, epsilon) for item in prop_value)
    else:
        # Einzelwertvergleich
        try:
            # Versuche, beide Werte in float umzuwandeln
            prop_value_float = float(prop_value)
            value_float = float(value)
            # Vergleich mit Toleranz
            return abs(prop_value_float - value_float) < epsilon
        except (ValueError, TypeError):
            # Wenn Umwandlung fehlschlägt, prüfe auf boolesche Werte
            bool_values = {'true': True, 'false': False}
            prop_value_str = str(prop_value).strip().lower()
            value_str = str(value).strip().lower()
            if prop_value_str in bool_values and value_str in bool_values:
                return bool_values[prop_value_str] == bool_values[value_str]
            # String-Vergleich
            return prop_value_str == value_str
def parse_property_conditions(conditions_input):
    """
    Parst die Eingabe der Property-Bedingungen und gibt eine Liste von Dictionaries zurück.

    :param conditions_input: String der Bedingungen (z.B. aus einem Textfeld)
    :return: Liste von Dictionaries mit Schlüsseln 'property_set', 'property', 'value'
    :raises ValueError: Wenn das Bedingungsformat ungültig ist
    """
    conditions = [cond.strip() for cond in conditions_input.strip().split('\n') if cond.strip()]
    property_conditions = []
    for condition_str in conditions:
        condition = {'property_set': None, 'property': None, 'value': None}
        try:
            # Zuerst nach '=' aufteilen, um den Wert zu extrahieren
            if '=' in condition_str:
                lhs, value = condition_str.split('=', 1)
                condition['value'] = value.strip()
            else:
                lhs = condition_str
            lhs = lhs.strip()
            # Jetzt prüfen, ob ein '.' vorhanden ist
            if '.' in lhs:
                pset_name, prop_name = lhs.split('.', 1)
                condition['property_set'] = pset_name.strip()
                condition['property'] = prop_name.strip()
            else:
                condition['property'] = lhs.strip()
            # Typkonvertierung des Wertes hier durchführen
            if condition['value'] is not None:
                value_str = condition['value']
                # Versuchen, den Wert in eine Zahl umzuwandeln
                try:
                    if '.' in value_str or 'e' in value_str.lower():
                        condition['value'] = float(value_str)
                    else:
                        condition['value'] = int(value_str)
                except ValueError:
                    # Wert bleibt ein String (z.B. 'True', 'False', 'ABC')
                    condition['value'] = value_str.strip()
            # Überprüfen, ob mindestens die Property vorhanden ist
            if not condition['property']:
                raise ValueError("Keine gültige Property angegeben.")
            property_conditions.append(condition)
        except ValueError as ve:
            raise ValueError(
                f"Ungültiges Bedingungsformat: {condition_str}\n{ve}\n"
                "Verwenden Sie das Format 'PropertySet.Property=Value', 'Property=Value' oder 'Property'."
            )
    return property_conditions


