import sys
import os
import multiprocessing
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.api
import ifcopenshell.util.element
from ifcopenshell.util.element import get_psets

def process_elements(elements, name_filter="Alignment"):
    """
    Filtert IfcAlignment basierend auf dem Namen.

    :param elements: Liste der IfcAlignment's
    :param name_filter: Name oder Teilname zum Filtern der Elemente
    :return: Gefiltertes Element oder eine Ausnahme bei Fehlern
    """
    if len(elements) == 0:
        raise ValueError("Kein Element gefunden. Das Programm wird abgebrochen.")
    elif len(elements) == 1:
        element = elements[0]
        print(f"Element gefunden: \n{element}")
        return element
    else:
        print(f"Es wird nach dem Namen des Objekts gesucht: {name_filter}")
        filtered_elements = [
            element for element in elements
            if hasattr(element, "Name") and element.Name and name_filter in element.Name
        ]

        if len(filtered_elements) == 0:
            raise ValueError(f"Kein Element nach dem Filtern mit dem Namen '{name_filter}' gefunden.")
        elif len(filtered_elements) == 1:
            element = filtered_elements[0]
            print(f"Ein Element nach dem Filtern gefunden: \n{element}")
            return element
        else:
            print(f"Mehrere Elemente nach dem Filtern mit dem Namen {name_filter} gefunden:")
            for element in filtered_elements:
                print(f"#{element.id()} = {element.is_a()}(Name = {element.Name})")
            raise ValueError("Mehrere Elemente gefunden. Das Programm wird abgebrochen.")
    pass
def create_lrp_profile(model, lrp_data):
    # --- Find the needed data --- #
    # Find street element to copy Representation Context and Object Placement
    built_element = model.by_type('IfcBuiltElement')[0]  # filter to do
    # Find the curve of the alignment
    alignment = model.by_type('IfcAlignment')[0]  # filter to do
    alignment_curve = alignment.Representation.Representations[0].Items[0]  # filter to do

    # --- Create the profile --- #
    lrp_cartesianpointlist = model.create_entity(
        "IfcCartesianPointList2D",
        CoordList=lrp_data
    )

    lrp_listoflineindices = [
        model.createIfcLineIndex([1, 2]),
        model.createIfcLineIndex([2, 3]),
        model.createIfcLineIndex([3, 4]),
        model.createIfcLineIndex([4, 1])
    ]

    lrp_indexedpolycurve = model.create_entity(
        "IfcIndexedPolyCurve",
        Points=lrp_cartesianpointlist,
        Segments=lrp_listoflineindices
    )

    lrp_arbitraryclosedprofile = model.create_entity(
        "IfcArbitraryClosedProfileDef",
        ProfileType="AREA",
        ProfileName="Ausgang Profil Lichtraumprofil",
        OuterCurve=lrp_indexedpolycurve
    )

    lrp_profile_operator = model.create_entity(
        "IfcCartesianTransformationOperator2D",
        Axis1=model.createIfcDirection([0., -1.]),
        Axis2=model.createIfcDirection([1., 0.]),
        LocalOrigin=model.createIfcCartesianPoint([0., 0.])
    )

    lrp_derivedprofiledef = model.create_entity(
        "IfcDerivedProfileDef",
        ProfileType="AREA",
        ProfileName="Transformiertes Profil Lichtraumprofil",
        ParentProfile=lrp_arbitraryclosedprofile,
        Operator=lrp_profile_operator
    )
    lrp_fixedreferencesweptareasolid = model.create_entity(
        "IfcFixedReferenceSweptAreaSolid",
        SweptArea=lrp_derivedprofiledef,
        Position=None,
        Directrix=alignment_curve,
        StartParam=None,
        EndParam=None,
        FixedReference=model.createIfcDirection((0., 0., 1.))
    )

    # Create Shape Representation
    lrp_shape_representation = model.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=built_element.Representation.Representations[0].ContextOfItems,
        Items=[lrp_fixedreferencesweptareasolid]
    )

    lrp_product_representation = model.create_entity(
        "IfcProductRepresentation",
        Representations=[lrp_shape_representation]
    )

    lrp_built_element = model.create_entity(
        "IfcBuiltElement",
        GlobalId=ifcopenshell.guid.new(),
        Name="Lichtraumprofil",
        ObjectPlacement=built_element.ObjectPlacement,
        Representation=lrp_product_representation
    )
    return lrp_built_element
    pass
def filter_elements_by_properties(elements, pset_name, property_name, expected_value=True):
    """
    Filtert IfcBuiltElemente basierend auf einem Property Set und einer spezifischen Eigenschaft.

    :param elements: Liste der Elemente
    :param pset_name: Name des Property Sets, in dem die Eigenschaft definiert ist
    :param property_name: Name der Eigenschaft innerhalb des Property Sets
    :param expected_value: Erwarteter Wert der Eigenschaft
    :return: Gefilterte Liste von Elementen
    """
    filtered = []
    for element in elements:
        psets = get_psets(element)
        if pset_name in psets:
            pset = psets[pset_name]
            if property_name in pset:
                value = pset[property_name]
                if isinstance(value, list):
                    # Falls der Wert eine Liste ist, nimm das erste Element
                    value = value[0]
                if value == expected_value:
                    filtered.append(element)
    return filtered
    pass
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
    detection_colour = model.create_entity(
        "IfcColourRgb",
        Name=None,
        Red=red,
        Green=green,
        Blue=blue
    )

    # Erstelle die SurfaceStyleShading mit Transparenz
    surfacestyleshading = model.create_entity(
        "IfcSurfaceStyleShading",
        SurfaceColour=detection_colour,
        Transparency=transparency
    )

    # Erstelle die SurfaceStyle
    surfacestyle = model.create_entity(
        "IfcSurfaceStyle",
        Name="Custom Colour",
        Side="BOTH",
        Styles=[surfacestyleshading]
    )

    # Erstelle das IfcStyledItem
    styled_item = model.create_entity(
        "IfcStyledItem",
        Item=representation_item,
        Styles=[surfacestyle],
        Name="Custom Colour"
    )

    return styled_item
    pass
def print_element_psets(elements, max_elements=5):
    """
    Gibt die verfügbaren Property Sets und deren Eigenschaften für die ersten `max_elements` Elemente aus.

    :param elements: Liste der Elemente
    :param max_elements: Maximale Anzahl der Elemente, die ausgegeben werden
    """
    for el in elements[:max_elements]:
        psets = get_psets(el)
        print(f"Element ID: {el.GlobalId}, Name: {el.Name}")
        for pset_name, properties in psets.items():
            print(f"  Property Set: {pset_name}")
            for prop, value in properties.items():
                print(f"    {prop}: {value}")
        print("\n")
    pass

if __name__ == "__main__":
    # Abmessungen des gewünschten Lichtraumprofils
    lrp_data = [(-14.5, 0.0), (14.5, 0.0), (14.5, 7.5), (-14.5, 7.5)]

    # IFC-Dateipfad
    ifc_file_path = 'C:/Users/leons/iCloudDrive/Masterarbeit/IFC-Files/selbst erstellte files/bruecke mit trasse/selbst erstellte bruecke mit trasse 24-10-06.ifc'

    # Checken, ob Datei existiert
    if not os.path.exists(ifc_file_path):
        raise FileNotFoundError(f"IFC-Datei wurde nicht gefunden unter: {ifc_file_path}")

    # IFC-Datei laden
    model = ifcopenshell.open(ifc_file_path)

    # Alle Alignments finden
    alignment_elements = model.by_type("IfcAlignment")
    print(f"Anzahl der IfcAlignment Elemente: {len(alignment_elements)}")

    # Alignment finden
    try:
        alignment_element = process_elements(alignment_elements, name_filter="Alignment")
    except ValueError as e:
        print(e)
        sys.exit(1)

    # Lichtraumprofil erstellen
    try:
        lrp_element = create_lrp_profile(model, lrp_data)
    except Exception as e:
        print(f"Fehler beim Erstellen des Lichtraumprofils: {e}")
        sys.exit(1)

    # --- Vorbereitung Clash testing --- #
    # Alle IfcBuiltElemente abrufen, um das erstellte Lichtraumprofil einzuschließen
    all_built_elements = model.by_type("IfcBuiltElement")

    # -- Gruppe A -- #
    # Lichtraumprofil finden
    try:
        lrp_element = process_elements(all_built_elements, name_filter="Lichtraumprofil")
    except ValueError as e:
        print(f"Fehler beim Finden des Lichtraumprofils: {e}")
        sys.exit(1)

    group_a_elements = [lrp_element]  # In Liste packen, da die Funktion später eine Liste erwartet

    # -- Gruppe B -- #
    # Anwendung der Filterfunktion für Load Bearing
    load_bearing_elements = filter_elements_by_properties(
        all_built_elements,
        pset_name="Pset_BeamCommon",
        property_name="LoadBearing",
        expected_value=True
    )
    print(f"Anzahl der geundenen Elemente: {len(load_bearing_elements)}")
    for el in load_bearing_elements:
        print(f"Element ID: {el.GlobalId}, Name: {el.Name}")

    group_b_elements = load_bearing_elements

    # -- Clash Detection -- #
    # Geometrie Setup
    tree = ifcopenshell.geom.tree()
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)  # Sicherstellen, dass Weltkoordinaten verwendet werden
    iterator = ifcopenshell.geom.iterator(settings, model, multiprocessing.cpu_count())

    if iterator.initialize():
        while True:
            element = iterator.get()
            tree.add_element(element)
            if not iterator.next():
                break

    # Clash Detection durchführen
    clashes = tree.clash_intersection_many(
        group_a_elements,  # Lichtraumprofil
        group_b_elements,  # Elemente, die gefiltert wurden (hier: LoadBearing)
        tolerance=0.002,    # Toleranz von 2 mm
        check_all=True      # Alle möglichen Kollisionen überprüfen
    )

    # -- Post Processing -- #
    # Liste der clashing Elemente GUIDs sammeln
    list_of_clashing_elements_guid = []
    for clash in clashes:
        element2 = clash.b
        list_of_clashing_elements_guid.append(element2.get_argument(0))

    # Clashing Elemente färben (rot, undurchsichtig)
    for guid in list_of_clashing_elements_guid:
        try:
            element = model.by_guid(guid)
            representation_item = element.Representation.Representations[1].Items[0]
            create_colour_assignment(
                model,
                element,
                representation_item,
                color_rgb=(162, 34, 35),  # KIT-Rot: (162, 34, 35)
                transparency=0.0          # Undurchsichtig
            )
        except Exception as e:
            print(f"Fehler beim Färben des Elements mit GUID {guid}: {e}")

    # Lichtraumprofil färben (grün, leicht transparent)
    try:
        lrp_representation_items = lrp_element.Representation.Representations[0].Items
        for item in lrp_representation_items:
            create_colour_assignment(
                model,
                lrp_element,
                item,
                color_rgb=(0, 150, 130),  # KIT-Blau: (0, 150, 130)
                transparency=0.1          # Leicht transparent
            )
        print("Lichtraumprofil wurde erfolgreich gefärbt.")
    except Exception as e:
        print(f"Fehler beim Färben des Lichtraumprofils: {e}")

    # IFC-Datei schreiben
    output_ifc_file = 'C:/Users/leons/iCloudDrive/Masterarbeit/IFC-Files/selbst erstellte files/bruecke mit trasse/selbst erstellte bruecke mit trasse lrp und farben 24-10-12.ifc'
    model.write(output_ifc_file)
    print(f"IFC-Datei wurde erfolgreich geschrieben: {output_ifc_file}")


