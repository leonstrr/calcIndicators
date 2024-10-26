# utils/helpers.py
from pathlib import Path
import datetime

def generate_output_file_path(input_path):
    """Generiert einen automatischen Output-Dateipfad basierend auf dem Input."""
    input_path = Path(input_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{input_path.stem}_filtered_{timestamp}{input_path.suffix}"
    return input_path.parent / output_filename
def create_colour_assignment(model, element, representation_item, color_rgb, transparency=0.0):
    """
    Weist einem Element eine bestimmte Farbe und Transparenz zu.

    :param model: Das IFC-Modell
    :param element: Das Element, dem die Farbe zugewiesen werden soll
    :param representation_item: Das Repräsentations-Item des Elements
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
