import ifcopenshell
import os
from ifcopenshell.util.element import get_pset, get_property

ifc_file_path = 'C:/Users/leons/Desktop/IFC-Files/wuerfel_mit_property_set.ifc'

# Checken, ob Datei existiert
if not os.path.exists(ifc_file_path):
    raise FileNotFoundError(f"IFC-Datei wurde nicht gefunden unter: {ifc_file_path}")

model = ifcopenshell.open(ifc_file_path)

def property_filer(model):
    products = model.by_type("IfcBuiltElement")
    product = products[0]
    print(product)
    properties_of_product = ifcopenshell.util.element.get_psets(product)
    print(properties_of_product)
    print(properties_of_product)

