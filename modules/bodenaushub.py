import numpy as np
import pandas as pd
from stl import mesh
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from mpl_toolkits.mplot3d import Axes3D
from scipy.optimize import linear_sum_assignment

def create_raster(bounding_box, cell_size=1.0):
    """
    Erzeugt ein Raster von Punkten innerhalb der definierten Bounding Box.
    """
    x_coords = np.arange(bounding_box["min_x"], bounding_box["max_x"], cell_size)
    y_coords = np.arange(bounding_box["min_y"], bounding_box["max_y"], cell_size)
    raster_points = np.array([(x, y) for x in x_coords for y in y_coords])
    return raster_points

def point_in_triangle(x, y, triangle, epsilon=1e-6):
    """
    Überprüft, ob ein gegebener Punkt (x, y) innerhalb eines Dreiecks liegt.
    """
    a, b, c = triangle[0], triangle[1], triangle[2]
    v0 = (c[0] - a[0], c[1] - a[1])
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (x - a[0], y - a[1])
    dot00 = v0[0] * v0[0] + v0[1] * v0[1]
    dot01 = v0[0] * v1[0] + v0[1] * v1[1]
    dot02 = v0[0] * v2[0] + v0[1] * v2[1]
    dot11 = v1[0] * v1[0] + v1[1] * v1[1]
    dot12 = v1[0] * v2[0] + v1[1] * v2[1]
    inv_denom = 1 / (dot00 * dot11 - dot01 * dot01)
    u = (dot11 * dot02 - dot01 * dot12) * inv_denom
    v = (dot00 * dot12 - dot01 * dot02) * inv_denom

    return (u >= -epsilon) and (v >= -epsilon) and (u + v <= 1 + epsilon)

def barycentric_interpolation(x, y, triangle):
    """
    Berechnet die Höhe (z-Koordinate) eines Punktes (x, y) innerhalb eines Dreiecks mithilfe baryzentrischer Interpolation.
    """
    a, b, c = triangle[0], triangle[1], triangle[2]
    v0 = (c[0] - a[0], c[1] - a[1])
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (x - a[0], y - a[1])
    dot00 = v0[0] * v0[0] + v0[1] * v0[1]
    dot01 = v0[0] * v1[0] + v0[1] * v1[1]
    dot02 = v0[0] * v2[0] + v0[1] * v2[1]
    dot11 = v1[0] * v1[0] + v1[1] * v1[1]
    dot12 = v1[0] * v2[0] + v1[1] * v2[1]
    inv_denom = 1 / (dot00 * dot11 - dot01 * dot01)
    u = (dot11 * dot02 - dot01 * dot12) * inv_denom
    v = (dot00 * dot12 - dot01 * dot02) * inv_denom
    z = a[2] + u * (b[2] - a[2]) + v * (c[2] - a[2])
    return z

def interpolate_height(point, triangles):
    """
    Interpoliert die Höhe (z-Wert) eines Punktes, falls er in einem der Dreiecke liegt.
    """
    x, y = point
    for triangle in triangles:
        if point_in_triangle(x, y, triangle):
            return barycentric_interpolation(x, y, triangle)
    return None

def calculate_bounding_box(triangles, padding=0.0):
    """
    Berechnet die Bounding Box, die alle Dreiecke umschließt.
    """
    min_x = np.min(triangles[:, :, 0]) - padding
    max_x = np.max(triangles[:, :, 0]) + padding
    min_y = np.min(triangles[:, :, 1]) - padding
    max_y = np.max(triangles[:, :, 1]) + padding
    min_z = np.min(triangles[:, :, 2])
    max_z = np.max(triangles[:, :, 2])

    return {
        "min_x": float(min_x),
        "max_x": float(max_x),
        "min_y": float(min_y),
        "max_y": float(max_y),
        "min_z": float(min_z),
        "max_z": float(max_z)
    }

def create_raster(bounding_box, cell_size=1.0):
    """
    Erzeugt ein Raster von Punkten innerhalb der definierten Bounding Box.
    """
    x_coords = np.arange(bounding_box["min_x"], bounding_box["max_x"], cell_size)
    y_coords = np.arange(bounding_box["min_y"], bounding_box["max_y"], cell_size)
    raster_points = np.array([(x, y) for x in x_coords for y in y_coords])
    return raster_points

def calculate_discrete_volume(triangles_0, triangles_1, raster_points, cell_size=1.0):
    """
    Berechnet die Volumendifferenzen zwischen zwei Zuständen (vor und nach dem Bau) für jeden Punkt im Raster.
    """
    volume_data = []

    for point in raster_points:
        z_0 = interpolate_height(point, triangles_0)
        z_1 = interpolate_height(point, triangles_1)

        if z_0 is not None and z_1 is not None:
            volume_difference = (z_1 - z_0) * (cell_size ** 2)
            volume_data.append({'x': point[0], 'y': point[1], 'volumen_diff': volume_difference})

    return pd.DataFrame(volume_data)

def visualize_mesh(triangles, test_point, bounding_box):
    """
    Visualisiert das Dreiecksnetz und einen ausgewählten Punkt in der XY-Ebene.
    """
    fig, ax = plt.subplots()

    for triangle in triangles:
        polygon = Polygon(triangle[:, :2], closed=True, edgecolor='r', facecolor='cyan', alpha=0.5)
        ax.add_patch(polygon)

    ax.plot(test_point[0], test_point[1], 'bo', label='Testpunkt')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Mesh und Testpunkt in der XY-Ebene')

    ax.set_xlim([bounding_box['min_x'], bounding_box['max_x']])
    ax.set_ylim([bounding_box['min_y'], bounding_box['max_y']])

    plt.legend()
    plt.grid(True)

    return fig

def visualize_volume_distribution_2d(volume_df):
    """
    Visualisiert die Volumendifferenz in einem 2D-Streudiagramm mit Farbkodierung.
    """
    x = volume_df['x'].values
    y = volume_df['y'].values
    z = volume_df['volumen_diff'].values

    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(x, y, c=z, cmap='coolwarm', s=100, edgecolor='k', alpha=0.75)
    plt.colorbar(scatter, label='Volumendifferenz (m³)')
    ax.set_xlabel('X-Position (m)')
    ax.set_ylabel('Y-Position (m)')
    ax.set_title('Verteilung der Volumendifferenz')
    ax.grid(True)

    return fig

def visualize_volume_bars_3d(volume_df, scale_factor=10):
    """
    Visualisiert die Volumendifferenz in einem 3D-Balkendiagramm.
    """
    x = volume_df['x'].values
    y = volume_df['y'].values
    z = volume_df['volumen_diff'].values

    z_scaled = z * scale_factor

    dx = (np.max(x) - np.min(x)) / len(np.unique(x)) * 0.8
    dy = (np.max(y) - np.min(y)) / len(np.unique(y)) * 0.8

    z_base = np.zeros_like(z)

    colors = np.where(z >= 0, 'r', 'b')

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    ax.bar3d(x, y, z_base, dx, dy, z_scaled, color=colors, shade=True)

    ax.set_xlabel('X-Position (m)')
    ax.set_ylabel('Y-Position (m)')
    ax.set_zlabel(f'Volumendifferenz (m³, skaliert um {scale_factor}x)')
    ax.set_title('3D-Balkenplot der Volumendifferenz (skaliert)')

    return fig

def calculate_distance_matrix(excess_points, deficit_points):
    """
    Berechnet die Distanzmatrix zwischen Überschuss- und Defizitpunkten.
    """
    distance_matrix = np.zeros((len(excess_points), len(deficit_points)))

    for i, excess in enumerate(excess_points):
        for j, deficit in enumerate(deficit_points):
            distance_matrix[i, j] = np.sqrt((excess[0] - deficit[0]) ** 2 + (excess[1] - deficit[1]) ** 2)

    return distance_matrix

def calculate_transport_work(volume_excess, volume_deficit, distance_matrix):
    """
    Berechnet die Transportarbeit basierend auf der Volumendifferenz und der Distanz.
    """
    work_matrix = np.zeros_like(distance_matrix)

    for i, excess in enumerate(volume_excess['volumen_diff']):
        for j, deficit in enumerate(volume_deficit['volumen_diff']):
            work_matrix[i, j] = abs(excess) * abs(deficit) * distance_matrix[i, j]

    return work_matrix

def optimize_transport(work_matrix):
    """
    Optimiert den Transport mittels des ungarischen Algorithmus.
    """
    row_ind, col_ind = linear_sum_assignment(work_matrix)
    return row_ind, col_ind

def calculate_minimum_work(row_ind, col_ind, work_matrix):
    """
    Berechnet die minimale Transportarbeit basierend auf der optimierten Zuordnung.
    """
    total_work = 0
    for i, j in zip(row_ind, col_ind):
        total_work += work_matrix[i, j]
    return total_work

def perform_bodenaushub(zustand0_file, zustand1_file):
    """
    Führt die gesamte Bodenaushub-Berechnung durch und gibt die Ergebnisse zurück.
    """
    # STL-Dateien laden (Zustand 0 und Zustand 1)
    mesh0 = mesh.Mesh.from_file(zustand0_file)
    mesh1 = mesh.Mesh.from_file(zustand1_file)

    # Alle Koordinaten der Dreiecke der Datei
    triangles_mesh0 = mesh0.vectors
    triangles_mesh1 = mesh1.vectors

    # Bounding Box berechnen
    bounding_box = calculate_bounding_box(triangles_mesh0, padding=0.5)

    # Raster erstellen
    raster_points = create_raster(bounding_box, cell_size=0.5)

    # Test Punkt zur Visualisierung
    mid_x = (bounding_box['min_x'] + bounding_box['max_x']) / 2
    mid_y = (bounding_box['min_y'] + bounding_box['max_y']) / 2
    middle_point = (mid_x, mid_y)

    # Berechne diskrete Volumendifferenzen
    volume_df = calculate_discrete_volume(triangles_mesh0, triangles_mesh1, raster_points, cell_size=1.0)

    # --- Optimierung --- #
    # Separiere Überschüsse (positive Volumendifferenz) und Defizite (negative Volumendifferenz)
    volume_excess = volume_df[volume_df['volumen_diff'] > 0]
    volume_deficit = volume_df[volume_df['volumen_diff'] < 0]

    if volume_excess.empty or volume_deficit.empty:
        raise ValueError("Keine Überschüsse oder Defizite gefunden für die Optimierung.")

    # Berechne die minimale Arbeit
    distance_matrix = calculate_distance_matrix(volume_excess[['x', 'y']].values, volume_deficit[['x', 'y']].values)
    work_matrix = calculate_transport_work(volume_excess, volume_deficit, distance_matrix)
    row_ind, col_ind = optimize_transport(work_matrix)
    min_work = calculate_minimum_work(row_ind, col_ind, work_matrix)

    return {
        "bounding_box": bounding_box,
        "volume_df": volume_df,
        "min_work": min_work,
        "middle_point": middle_point
    }

def visualize_results(bounding_box, triangles_mesh0, volume_df, middle_point):
    """
    Erstellt alle benötigten Visualisierungen und gibt die Figures zurück.
    """
    figures = {}
    figures['mesh'] = visualize_mesh(triangles_mesh0, middle_point, bounding_box)
    figures['distribution_2d'] = visualize_volume_distribution_2d(volume_df)
    figures['distribution_3d'] = visualize_volume_bars_3d(volume_df)
    return figures
