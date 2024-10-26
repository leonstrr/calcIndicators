# bodenaushub_debug.py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from stl import mesh

# Globale Variablen für STL-Dateien
zustand0_file = r"C:\Users\leons\iCloudDrive\Masterarbeit\IFC-Files\STL\gelaende auf 0.stl"  # Pfad zu deiner Mesh-Datei
zustand1_file = r"C:\Users\leons\iCloudDrive\Masterarbeit\IFC-Files\STL\gelaende auf 0 rotiert.stl"

# --- Funktionen zur Interpolation der Höhen und Berechnung der Volumendifferenzen --- #
def load_stl_files(file_0, file_1):
    """
    Lädt zwei STL-Dateien und gibt die Dreiecksarrays zurück.

    :param file_0: Pfad zur ersten STL-Datei
    :param file_1: Pfad zur zweiten STL-Datei
    :return: Dreiecksarrays von beiden STL-Dateien
    """
    mesh0 = mesh.Mesh.from_file(file_0)
    mesh1 = mesh.Mesh.from_file(file_1)

    triangles_0 = mesh0.vectors
    triangles_1 = mesh1.vectors

    print("STL-Dateien geladen:")
    print(f"Zustand 0: {file_0}, Anzahl Dreiecke: {len(triangles_0)}")
    print(f"Zustand 1: {file_1}, Anzahl Dreiecke: {len(triangles_1)}")

    return triangles_0, triangles_1
def calculate_overlapping_bounding_box(triangles_list):
    # Extrahiere alle x- und y-Werte aus den Dreiecksarrays
    all_x = [triangles[:, :, 0].flatten() for triangles in triangles_list]
    all_y = [triangles[:, :, 1].flatten() for triangles in triangles_list]

    # Berechne die Maxima und Minima für jedes Modell
    min_x_list = [np.min(x) for x in all_x]
    max_x_list = [np.max(x) for x in all_x]
    min_y_list = [np.min(y) for y in all_y]
    max_y_list = [np.max(y) for y in all_y]

    # Berechne die überlappende Bounding Box
    min_x = max(min_x_list)
    max_x = min(max_x_list)
    min_y = max(min_y_list)
    max_y = min(max_y_list)

    bounding_box = {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y
    }
    print("Überlappende Bounding Box:", bounding_box)
    return bounding_box
def create_raster(bounding_box, cell_size):
    min_x = bounding_box["min_x"]
    max_x = bounding_box["max_x"]
    min_y = bounding_box["min_y"]
    max_y = bounding_box["max_y"]

    # Berechne die Anzahl der Zellen pro Richtung
    num_cells_x = int(np.ceil((max_x - min_x) / cell_size))
    num_cells_y = int(np.ceil((max_y - min_y) / cell_size))

    # Anpassung des Maximalwerts, um die Rasterung abzudecken
    adjusted_max_x = min_x + num_cells_x * cell_size
    adjusted_max_y = min_y + num_cells_y * cell_size

    x_coords = np.linspace(min_x + cell_size / 2, adjusted_max_x - cell_size / 2, num_cells_x)
    y_coords = np.linspace(min_y + cell_size / 2, adjusted_max_y - cell_size / 2, num_cells_y)

    xv, yv = np.meshgrid(x_coords, y_coords)
    raster_points = np.column_stack([xv.ravel(), yv.ravel()])

    return raster_points
def interpolate_height_for_point(point, triangles, epsilon=1e-6):
    """
    Prüft für den Punkt (x, y), ob er in einem der Dreiecke liegt,
    und berechnet dann die Höhe (z-Wert) mittels baryzentrischer Interpolation.

    :param point: Ein Tupel (x, y) des Punkts, für den die Höhe interpoliert werden soll
    :param triangles: Liste von Dreiecken, die jedes aus drei Punkten besteht (jeder Punkt hat (x, y, z))
    :param epsilon: Toleranzwert für numerische Stabilität
    :return: Interpolierter z-Wert, falls der Punkt in einem Dreieck liegt, ansonsten None
    """
    x, y = point

    # Schleife über alle Dreiecke
    for triangle in triangles:
        a, b, c = triangle[0], triangle[1], triangle[2]

        # Vektoren berechnen
        v0 = (c[0] - a[0], c[1] - a[1])
        v1 = (b[0] - a[0], b[1] - a[1])
        v2 = (x - a[0], y - a[1])

        # Skalarprodukte berechnen
        dot00 = v0[0] * v0[0] + v0[1] * v0[1]
        dot01 = v0[0] * v1[0] + v0[1] * v1[1]
        dot02 = v0[0] * v2[0] + v0[1] * v2[1]
        dot11 = v1[0] * v1[0] + v1[1] * v1[1]
        dot12 = v1[0] * v2[0] + v1[1] * v2[1]

        # Determinante und Inverser der Determinante
        denom = dot00 * dot11 - dot01 * dot01
        if abs(denom) < epsilon:
            continue  # Das Dreieck ist degeneriert, also überspringen

        inv_denom = 1 / denom

        # Baryzentrische Koordinaten berechnen
        u = (dot11 * dot02 - dot01 * dot12) * inv_denom
        v = (dot00 * dot12 - dot01 * dot02) * inv_denom

        # Prüfen, ob der Punkt im Dreieck liegt
        if (u >= -epsilon) and (v >= -epsilon) and (u + v <= 1 + epsilon):
            # Interpolation der Höhe (z-Werte)
            z = a[2] + u * (b[2] - a[2]) + v * (c[2] - a[2])
            return z  # Interpolierte Höhe

    return None  # Kein passendes Dreieck gefunden
def calculate_and_classify_volume_difference(mesh_0_triangles, mesh_1_triangles, raster_points, cell_size_x, cell_size_y):
    volume_data = []
    for point in raster_points:
        z_0 = interpolate_height_for_point(point, mesh_0_triangles)
        z_1 = interpolate_height_for_point(point, mesh_1_triangles)

        if z_0 is not None and z_1 is not None:
            # Berechne die Volumendifferenz
            volume_diff = (z_1 - z_0) * cell_size_x * cell_size_y
            volume_data.append({
                'x': point[0],
                'y': point[1],
                'z_0': z_0,
                'z_1': z_1,
                'volumen_diff': volume_diff
            })

    volume_df = pd.DataFrame(volume_data)

    # Klassifizierung und Summierung der Volumina
    total_volume_diff = volume_df['volumen_diff'].sum()
    excess_points = volume_df[volume_df['volumen_diff'] > 0]
    deficit_points = volume_df[volume_df['volumen_diff'] < 0]

    print(f"Gesamte Volumendifferenz: {total_volume_diff} m³")
    return volume_df, total_volume_diff, excess_points, deficit_points

# --- Funktionen zum Visualisieren --- #
def plot_interpolated_heights(volume_df, z_column='z_0'):
    """
    Erstellt einen 3D-Scatterplot der interpolierten Höhen basierend auf dem volume_df DataFrame.

    :param volume_df: Pandas DataFrame mit den Spalten ['x', 'y', 'z_0', 'z_1', 'volumen_diff']
    :param z_column: Gibt an, welche z-Spalte geplottet werden soll. Optionen sind 'z_0', 'z_1'.
    """
    # Überprüfen, ob die notwendigen Spalten vorhanden sind
    required_columns = ['x', 'y', z_column]
    for col in required_columns:
        if col not in volume_df.columns:
            raise ValueError(f"Das DataFrame muss die Spalte '{col}' enthalten.")

    # Extrahieren der x, y, z Koordinaten
    x = volume_df['x'].values
    y = volume_df['y'].values
    z = volume_df[z_column].values

    # Erstellen der 3D-Darstellung
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    # 3D-Scatterplot
    scatter = ax.scatter(x, y, z, c=z, cmap='viridis', s=50)

    # Achsenbeschriftungen setzen
    ax.set_xlabel('X-Koordinate')
    ax.set_ylabel('Y-Koordinate')
    ax.set_zlabel(f'Interpolierte Höhe ({z_column})')
    ax.set_title(f'3D-Darstellung der interpolierten Punkte ({z_column})')

    # Farblegende hinzufügen
    cbar = fig.colorbar(scatter, ax=ax, shrink=0.5, aspect=10)
    cbar.set_label(f'Interpolierte Höhe ({z_column})')

    # Entfernen der Hintergrundflächen (optional)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False

    # Entfernen der Gitternetzlinien (optional)
    ax.grid(False)

    plt.show()
def visualize_mesh_and_raster(triangles, raster_points):
    """
    Visualisiert die Dreiecke und Rasterpunkte zusammen, um zu prüfen, ob die Punkte korrekt abgedeckt werden.
    """
    fig, ax = plt.subplots()

    # Zeichne die Dreiecke
    for triangle in triangles:
        a, b, c = triangle[0], triangle[1], triangle[2]
        polygon = plt.Polygon([a[:2], b[:2], c[:2]], fill=None, edgecolor='r', linewidth=1)
        ax.add_patch(polygon)

    # Zeichne die Rasterpunkte
    plt.scatter(raster_points[:, 0], raster_points[:, 1], color='green', s=5)
    plt.xlabel('x [m]')
    plt.ylabel('y [m]')
    plt.title('Dreiecke und Rasterpunkte')
    plt.grid(True)
    plt.show()

def main():
    # STL-Dateien laden
    triangles_0, triangles_1 = load_stl_files(zustand0_file, zustand1_file)

    # Überlappende Bounding Box berechnen
    bounding_box = calculate_overlapping_bounding_box([triangles_0, triangles_1])

    # Zellgröße festlegen
    cell_size = 1.0  # Wählen Sie die gewünschte Zellgröße

    # Raster erstellen
    raster_points = create_raster(bounding_box, cell_size)

    #total_area = (bounding_box["max_x"] - bounding_box["min_x"]) * (bounding_box["max_y"] - bounding_box["min_y"])
    #print(f"Gesamte Rasterfläche: {total_area} m²")

    # Diskrete Volumen, Volumendifferenzen und Gesamtvolumendifferenz berechnen
    #volume_df, total_volume_diff, excess_points, deficit_points = calculate_and_classify_volume_difference(
       # triangles_0, triangles_1, raster_points, cell_size_x, cell_size_y)

    # Validierung der Gesamtvolumina
    #total_excess = excess_points['volumen_diff'].sum()
    #total_deficit = deficit_points['volumen_diff'].sum()
    #print(f"Gesamtes Aufschüttvolumen: {total_excess} m³")
    #print(f"Gesamtes Aushubvolumen: {total_deficit} m³")

    #plot_interpolated_heights(volume_df,'z_1')

    visualize_mesh_and_raster(triangles_0,raster_points)



if __name__ == "__main__":
    main()
