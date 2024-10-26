import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from stl import mesh

# Globale Variablen für STL-Dateien
zustand0_file = r"C:\Users\leons\iCloudDrive\Masterarbeit\IFC-Files\STL\gelaende auf 0.stl"
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
def interpolate_height_for_points(points, triangle_sets, epsilon=1e-6):
    """
    Prüft für eine Liste von Punkten (x, y), ob diese in einem der Dreiecke eines jeden Dreieckssatzes liegt,
    und berechnet dann die Höhen (z0, z1, ...) mittels baryzentrischer Interpolation.

    :param points: Liste von Tupeln (x, y) für die Interpolation
    :param triangle_sets: Liste von Dreieckssätzen (jede Dreieckssatz ist eine Liste von Dreiecken)
    :param epsilon: Toleranzwert für numerische Stabilität
    :return: Pandas-DataFrame mit x, y und z-Werten für jeden Dreieckssatz
    """
    point_data = []
    for p in points:
        point_entry = {'x': p[0], 'y': p[1]}
        for idx, triangles in enumerate(triangle_sets):
            z = None
            for triangle in triangles:
                a, b, c = triangle
                ab = (b[0] - a[0], b[1] - a[1])
                ac = (c[0] - a[0], c[1] - a[1])

                A_ges = 0.5 * abs(ab[0] * ac[1] - ab[1] * ac[0])
                if A_ges == 0:
                    continue  # Degeneriertes Dreieck

                A1 = 0.5 * abs((b[0] - p[0]) * (c[1] - p[1]) - (b[1] - p[1]) * (c[0] - p[0]))
                A2 = 0.5 * abs((a[0] - p[0]) * (c[1] - p[1]) - (a[1] - p[1]) * (c[0] - p[0]))
                A3 = 0.5 * abs((a[0] - p[0]) * (b[1] - p[1]) - (a[1] - p[1]) * (b[0] - p[0]))

                w1 = A1 / A_ges
                w2 = A2 / A_ges
                w3 = A3 / A_ges

                if (w1 >= -epsilon) and (w2 >= -epsilon) and (w1 + w2 + w3 <= 1 + epsilon):
                    z = a[2] + w2 * (b[2] - a[2]) + w3 * (c[2] - a[2])
                    break  # Höhenwert gefunden

            point_entry[f'z{idx}'] = z
        point_data.append(point_entry)
    return pd.DataFrame(point_data)

# Visualisierung
def visualize_interpolated_points(point_df):
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    for col in point_df.columns:
        if col.startswith('z'):
            ax.scatter(point_df['x'], point_df['y'], point_df[col], label=col, s=20)

    ax.set_xlabel('X-Koordinate')
    ax.set_ylabel('Y-Koordinate')
    ax.set_zlabel('Z (interpoliert)')
    ax.set_title('3D-Darstellung der interpolierten Punkte')
    ax.legend()

    # Entfernen der Hintergrundflächen (optional)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False

    # Entfernen der Gitternetzlinien (optional)
    # ax.grid(False)

    plt.show()


def main():
    triangles_0 , triangles_1 = load_stl_files(zustand0_file, zustand1_file)
    bounding_box = calculate_overlapping_bounding_box([triangles_0, triangles_1])
    raster_points = create_raster(bounding_box, cell_size=1.0)
    point_df = interpolate_height_for_points(raster_points, [triangles_0, triangles_1])
    visualize_interpolated_points(point_df)
    print(raster_points)



if __name__ == "__main__":
    main()