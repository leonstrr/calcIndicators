import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.api
import ifcopenshell.util.element
import multiprocessing
from utils.helpers import create_colour_assignment
from modules.property_filter import filter_elements_in_model

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
def create_lrp_profile(model, lrp_data):
    # --- Find the needed data --- #
    # Find street element to copy Representation Context and Object Placement
    built_element = model.by_type('IfcBuiltElement')[0]  # TODO: Filter konkretisieren
    # Find the curve of the alignment
    alignment = model.by_type('IfcAlignment')[0]  # TODO: Filter konkretisieren
    alignment_curve = alignment.Representation.Representations[0].Items[0]  # TODO: Filter konkretisieren

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

    # Lichtraumprofil färben (grün, leicht transparent)
    try:
        lrp_representation_items = lrp_built_element.Representation.Representations[0].Items
        for item in lrp_representation_items:
            create_colour_assignment(
                model,
                lrp_built_element,
                item,
                color_rgb=(0, 150, 130),  # KIT-Grün
                transparency=0.1          # Leicht transparent
            )
        print("Lichtraumprofil wurde erfolgreich gefärbt.")
    except Exception as e:
        print(f"Fehler beim Färben des Lichtraumprofils: {e}")

    return lrp_built_element
def perform_clash_detection(model, lrp_element, property_conditions):
    # --- Vorbereitung Clash Testing --- #
    # Alle IfcBuiltElemente abrufen, um das erstellte Lichtraumprofil einzuschließen
    all_built_elements = model.by_type("IfcBuiltElement")

    # -- Gruppe A -- #
    # Lichtraumprofil ist bereits bekannt (lrp_element)
    group_a_elements = [lrp_element]

    # -- Gruppe B -- #
    # Anwendung der Filterfunktion für Load Bearing
    filtered_elements = filter_elements_in_model(model, property_conditions)
    print(f"Anzahl der gefundenen Elemente: {len(filtered_elements)}")
    for el in filtered_elements:
        print(f"Element ID: {el.GlobalId}, Name: {el.Name}")

    group_b_elements = filtered_elements

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
    # Liste der kollidierenden Elemente sammeln
    clashing_elements_info = []
    for clash in clashes:
        element2 = clash.b
        guid = element2.get_argument(0)
        element = model.by_guid(guid)
        element_info = f"Element ID: #{element.id()}, Name: {element.Name}"
        print(element_info)
        clashing_elements_info.append(element_info)

        # Clashing Elemente färben (rot, undurchsichtig)
        try:
            representation_item = element.Representation.Representations[1].Items[0]
            create_colour_assignment(
                model,
                element,
                representation_item,
                color_rgb=(162, 34, 35),  # KIT-Rot
                transparency=0.0          # Undurchsichtig
            )
        except Exception as e:
            print(f"Fehler beim Färben des Elements mit GUID {guid}: {e}")

    # Anzahl der kollidierenden Elemente ausgeben
    print(f"Anzahl der kollidierenden Elemente: {len(clashing_elements_info)}")

    return model, clashing_elements_info  # Geändertes Modell und Liste der kollidierenden Elemente zurückgeben
def save_ifc_file(model, output_ifc_file):
    """Speichert das IFC-Modell."""
    model.write(output_ifc_file)
    print(f"IFC-Datei wurde erfolgreich geschrieben: {output_ifc_file}")
def create_lrp_and_perform_clash_detection(input_ifc_file, output_ifc_file, lrp_data, property_conditions):
    """
    Kombinierte Funktion zum Erstellen des Lichtraumprofils und Durchführen der Clash Detection.
    """
    # IFC-Datei laden
    model = ifcopenshell.open(input_ifc_file)

    # Lichtraumprofil erstellen
    lrp_element = create_lrp_profile(model, lrp_data)

    # Clash Detection durchführen
    model, clashing_elements_info = perform_clash_detection(model, lrp_element, property_conditions)

    # IFC-Datei speichern
    save_ifc_file(model, output_ifc_file)

    return model, clashing_elements_info
