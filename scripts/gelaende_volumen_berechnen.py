import numpy as np
import pandas as pd
from stl import mesh
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from mpl_toolkits.mplot3d import Axes3D
# --- Packages fuer Optimierung --- #
from scipy.optimize import linear_sum_assignment

def create_raster(bounding_box, cell_size=1.0):
    """
    Erzeugt ein Raster von Punkten innerhalb der definierten Bounding Box.

    Parameters:
    bounding_box (dict): Die Bounding Box, die die minimalen und maximalen x- und y-Koordinaten enthält.
    cell_size (float): Die Größe der Zellen im Raster, standardmäßig 1.0.

    Returns:
    numpy.ndarray: Ein Array von (x, y)-Punkten, das das Raster darstellt.
    """
    x_coords = np.arange(bounding_box["min_x"], bounding_box["max_x"], cell_size)
    y_coords = np.arange(bounding_box["min_y"], bounding_box["max_y"], cell_size)
    raster_points = np.array([(x, y) for x in x_coords for y in y_coords])
    return raster_points
def point_in_triangle(x, y, triangle, epsilon=1e-6):
    """
    Überprüft, ob ein gegebener Punkt (x, y) innerhalb eines Dreiecks liegt.

    Parameters:
    x (float): Die x-Koordinate des Punktes.
    y (float): Die y-Koordinate des Punktes.
    triangle (numpy.ndarray): Ein 2D-Dreieck, das durch drei Punkte definiert ist.
    epsilon (float): Toleranzwert für numerische Berechnungen, standardmäßig 1e-6.

    Returns:
    bool: True, wenn der Punkt im Dreieck liegt, sonst False.
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

    if (u >= -epsilon) and (v >= -epsilon) and (u + v <= 1 + epsilon):
        return True
    return False
def barycentric_interpolation(x, y, triangle):
    """
    Berechnet die Höhe (z-Koordinate) eines Punktes (x, y) innerhalb eines Dreiecks
    mithilfe baryzentrischer Interpolation.

    Parameters:
    x (float): Die x-Koordinate des Punktes.
    y (float): Die y-Koordinate des Punktes.
    triangle (numpy.ndarray): Ein 2D-Dreieck, das durch drei Punkte mit z-Koordinaten definiert ist.

    Returns:
    float: Die interpolierte z-Koordinate des Punktes.
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

    Parameters:
    point (tuple): Ein Tupel (x, y), das den Punkt darstellt, dessen Höhe interpoliert werden soll.
    triangles (numpy.ndarray): Eine Liste von Dreiecken, in denen die Höhe interpoliert werden soll.

    Returns:
    float or None: Die interpolierte Höhe, wenn der Punkt in einem Dreieck liegt, ansonsten None.
    """
    x, y = point
    # Gehe durch alle Dreiecke und überprüfe, ob der Punkt in einem Dreieck liegt
    for triangle in triangles:
        if point_in_triangle(x, y, triangle):
            # Falls der Punkt im Dreieck liegt, berechne die Höhe (Z-Wert)
            return barycentric_interpolation(x, y, triangle)

    # Falls der Punkt in keinem Dreieck liegt, gib None zurück (ignoriere diesen Punkt)
    return None
def calculate_bounding_box(triangles, padding=0.0):
    """
    Berechnet die Bounding Box, die alle Dreiecke umschließt.

    Parameters:
    triangles (numpy.ndarray): Eine Liste von Dreiecken, die die zu umschließende Geometrie definieren.
    padding (float): Ein optionaler Puffer, der zur Bounding Box hinzugefügt wird, standardmäßig 0.0.

    Returns:
    dict: Eine Bounding Box als Dictionary mit min_x, max_x, min_y, max_y, min_z, max_z.
    """
    # Berechne die minimalen und maximalen Koordinaten für x, y und z
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
def visualize_mesh(triangles, test_point):
    """
    Visualisiert das Dreiecksnetz und einen ausgewählten Punkt in der XY-Ebene.

    Parameters:
    triangles (numpy.ndarray): Die Liste von Dreiecken, die das Netz bilden.
    test_point (tuple): Der Punkt, der im Plot hervorgehoben werden soll.

    Returns:
    None
    """
    fig, ax = plt.subplots()

    # Zeichne jedes Dreieck
    for triangle in triangles:
        polygon = Polygon(triangle[:, :2], closed=True, edgecolor='r', facecolor='cyan', alpha=0.5)
        ax.add_patch(polygon)

    # Zeichne den zu testenden Punkt
    ax.plot(test_point[0], test_point[1], 'bo', label='Testpunkt')

    # Achsenbeschriftungen
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Mesh und Testpunkt in der XY-Ebene')

    # Grenzen basierend auf der Bounding Box
    ax.set_xlim([bounding_box['min_x'], bounding_box['max_x']])
    ax.set_ylim([bounding_box['min_y'], bounding_box['max_y']])

    plt.legend()
    plt.grid(True)
    plt.show()
def calculate_discrete_volume(triangles_0, triangles_1, raster_points, cell_size=1.0):
    """
    Berechnet die Volumendifferenzen zwischen zwei Zuständen (vor und nach dem Bau)
    für jeden Punkt im Raster.

    Parameters:
    triangles_0 (numpy.ndarray): Die Dreiecksgeometrie des Ausgangszustands (vor dem Bau).
    triangles_1 (numpy.ndarray): Die Dreiecksgeometrie des Endzustands (nach dem Bau).
    raster_points (numpy.ndarray): Die Punkte, für die die Volumendifferenz berechnet wird.
    cell_size (float): Die Größe jeder Rasterzelle, standardmäßig 1.0.

    Returns:
    pandas.DataFrame: Ein DataFrame mit den x-, y-Koordinaten und der Volumendifferenz.
    """
    volume_data = []

    for point in raster_points:
        # Interpoliere Höhe für Zustand 0 (vor dem Bau)
        z_0 = interpolate_height(point, triangles_0)

        # Interpoliere Höhe für Zustand 1 (nach dem Bau)
        z_1 = interpolate_height(point, triangles_1)

        # Berechne die Volumendifferenz, falls beide Höhen vorhanden sind
        if z_0 is not None and z_1 is not None:
            volume_difference = (z_1 - z_0) * (cell_size ** 2)  # Volumen für diese Zelle
            volume_data.append({'x': point[0], 'y': point[1], 'volumen_diff': volume_difference})
        else:
            # Falls einer der Z-Werte None ist, ignoriere diesen Punkt
            continue

    return pd.DataFrame(volume_data)  # Rückgabe als DataFrame zur einfachen Weiterverarbeitung
def visualize_volume_distribution_2d(volume_df):
    """
    Visualisiert die Volumendifferenz in einem 2D-Streudiagramm mit Farbkodierung.

    Parameters:
    volume_df (pandas.DataFrame): Ein DataFrame mit den x-, y-Koordinaten und der Volumendifferenz.

    Returns:
    None
    """
    # Konvertiere den DataFrame in ein numpy Array für die Darstellung
    x = volume_df['x'].values
    y = volume_df['y'].values
    z = volume_df['volumen_diff'].values

    # Erstelle ein Streudiagramm mit Farbcodierung für die Volumendifferenz
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(x, y, c=z, cmap='coolwarm', s=100, edgecolor='k', alpha=0.75)
    plt.colorbar(scatter, label='Volumendifferenz (m³)')
    plt.xlabel('X-Position (m)')
    plt.ylabel('Y-Position (m)')
    plt.title('Verteilung der Volumendifferenz')
    plt.grid(True)
    plt.show()
def visualize_volume_bars_3d(volume_df, scale_factor=10):
    """
    Visualisiert die Volumendifferenz in einem 3D-Balkendiagramm.

    Parameters:
    volume_df (pandas.DataFrame): Ein DataFrame mit den x-, y-Koordinaten und der Volumendifferenz.
    scale_factor (float): Ein Skalierungsfaktor für die Höhe der Balken, standardmäßig 10.

    Returns:
    None
    """
    # Konvertiere den DataFrame in numpy Arrays für die Darstellung
    x = volume_df['x'].values
    y = volume_df['y'].values
    z = volume_df['volumen_diff'].values

    # Skaliere die Z-Werte, um sie deutlicher zu machen
    z_scaled = z * scale_factor  # Volumendifferenzen skalieren

    # Berechne den minimalen Abstand zwischen den Punkten, um Balkenbreite dynamisch zu bestimmen
    dx = (np.max(x) - np.min(x)) / len(np.unique(x)) * 0.8  # Balkenbreite in X-Richtung (80% des Abstands)
    dy = (np.max(y) - np.min(y)) / len(np.unique(y)) * 0.8  # Balkenbreite in Y-Richtung (80% des Abstands)

    # Definiere die Startpunkte der Balken in der XY-Ebene
    z_base = np.zeros_like(z)  # Start der Balken bei Z=0

    # Passe die Farben an: Positive Balken rot, negative blau
    colors = np.where(z >= 0, 'r', 'b')

    # Erstelle eine 3D-Darstellung
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Erstelle den 3D-Balkenplot mit den skalierten Z-Werten
    ax.bar3d(x, y, z_base, dx, dy, z_scaled, color=colors, shade=True)

    # Achsenbeschriftungen
    ax.set_xlabel('X-Position (m)')
    ax.set_ylabel('Y-Position (m)')
    ax.set_zlabel(f'Volumendifferenz (m³, skaliert um {scale_factor}x)')
    ax.set_title('3D-Balkenplot der Volumendifferenz (skaliert)')

    plt.show()
# --- Methoden zur Optimierung --- #
def calculate_distance_matrix(excess_points, deficit_points):
    distance_matrix = np.zeros((len(excess_points), len(deficit_points)))

    for i, excess in enumerate(excess_points):
        for j, deficit in enumerate(deficit_points):
            distance_matrix[i, j] = np.sqrt((excess[0] - deficit[0]) ** 2 + (excess[1] - deficit[1]) ** 2)

    return distance_matrix
def calculate_transport_work(volume_excess, volume_deficit, distance_matrix):
    work_matrix = np.zeros_like(distance_matrix)

    for i, excess in enumerate(volume_excess['volumen_diff']):
        for j, deficit in enumerate(volume_deficit['volumen_diff']):
            work_matrix[i, j] = abs(excess) * abs(deficit) * distance_matrix[i, j]  # Masse mal Entfernung

    return work_matrix
def optimize_transport(work_matrix):
    # Verwende den ungarischen Algorithmus, um die optimale Zuordnung zu berechnen
    row_ind, col_ind = linear_sum_assignment(work_matrix)

    # Gibt die optimierte Zuordnung zurück
    return row_ind, col_ind
def calculate_minimum_work(row_ind, col_ind, work_matrix):
    total_work = 0
    for i, j in zip(row_ind, col_ind):
        total_work += work_matrix[i, j]
    return total_work


# STL-Dateien laden (Zustand 0 und Zustand 1)
mesh0 = mesh.Mesh.from_file('C:/Users/leons/Desktop/IFC-Files/STL/generiertes_flaches_gelaende_auf_0.stl')
mesh1 = mesh.Mesh.from_file('C:/Users/leons/Desktop/IFC-Files/STL/generiertes_flaches_gelaende_auf_0_rotiert.stl')

# Alle Koordinaten der Dreiecke der Datei
triangles_mesh0 = mesh0.vectors
triangles_mesh1 = mesh1.vectors

# Bounding Box berechnen
bounding_box = calculate_bounding_box(triangles_mesh0,padding=0.5)

# Raster erstellen
raster_points = create_raster(bounding_box, cell_size=0.5)

# Test Punkt zur Visualisierung
    # Berechnung des Punktes in der Mitte der Bounding Box
mid_x = (bounding_box['min_x'] + bounding_box['max_x']) / 2
mid_y = (bounding_box['min_y'] + bounding_box['max_y']) / 2
    # Setze den Testpunkt auf die Mitte der Bounding Box
middle_point = (mid_x, mid_y)

# Visualisiere das Mesh und den Testpunkt
visualize_mesh(triangles_mesh0, middle_point)

# Berechne diskrete Volumendifferenzen
volume_df = calculate_discrete_volume(triangles_mesh0, triangles_mesh1, raster_points, cell_size=1.0)

# Visualisiere die Volumenverteilung 2d
visualize_volume_distribution_2d(volume_df)

# Visualisiere die Volumenverteilung 3d
visualize_volume_bars_3d(volume_df)

# Zugriff auf x, y, z und z_scaled aus dem volume_df DataFrame
x = volume_df['x'].values
y = volume_df['y'].values
z = volume_df['volumen_diff'].values
z_scaled = z * 10  # Skalierung der Z-Werte


# --- Optimierung --- #
# Separiere Überschüsse (positive Volumendifferenz) und Defizite (negative Volumendifferenz)
volume_excess = volume_df[volume_df['volumen_diff'] > 0]
volume_deficit = volume_df[volume_df['volumen_diff'] < 0]

#Berechne die minimale Arbeit
distance_matrix = calculate_distance_matrix(volume_excess[['x', 'y']].values, volume_deficit[['x', 'y']].values)
work_matrix = calculate_transport_work(volume_excess, volume_deficit, distance_matrix)
row_ind, col_ind = optimize_transport(work_matrix)
min_work = calculate_minimum_work(row_ind, col_ind, work_matrix)
print(f"Minimale Arbeit für den Bodentransport: {min_work}")



