import numpy as np
import pandas as pd
from stl import mesh
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
import pulp
import tkinter as tk

def calculate_overall_bounding_box(triangles_list, padding=0.0):
    """
    Berechnet die Bounding Box, die alle gegebenen Dreiecksarrays umfasst.

    :param triangles_list: Liste von Dreiecksarrays (numpy.ndarray)
    :param padding: Optionales Padding, um die Bounding Box zu erweitern
    :return: Dictionary mit min_x, max_x, min_y, max_y
    """
    all_x = np.concatenate([triangles[:, :, 0].flatten() for triangles in triangles_list])
    all_y = np.concatenate([triangles[:, :, 1].flatten() for triangles in triangles_list])

    min_x = np.min(all_x) - padding
    max_x = np.max(all_x) + padding
    min_y = np.min(all_y) - padding
    max_y = np.max(all_y) + padding

    return {
        "min_x": float(min_x),
        "max_x": float(max_x),
        "min_y": float(min_y),
        "max_y": float(max_y)
    }
def create_raster(bounding_box, cell_size=1.0):
    x_coords = np.arange(bounding_box["min_x"], bounding_box["max_x"] + cell_size, cell_size)
    y_coords = np.arange(bounding_box["min_y"], bounding_box["max_y"] + cell_size, cell_size)
    raster_points = np.array([(x, y) for x in x_coords for y in y_coords])
    return raster_points
def point_in_triangle(x, y, triangle, epsilon=1e-6):
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
    x, y = point
    for triangle in triangles:
        if point_in_triangle(x, y, triangle):
            return barycentric_interpolation(x, y, triangle)
    return None
def calculate_discrete_volume_difference(triangles_0, triangles_1, raster_points, cell_size=1.0):
    volume_data = []
    for point in raster_points:
        z_0 = interpolate_height(point, triangles_0)
        z_1 = interpolate_height(point, triangles_1)
        if z_0 is not None and z_1 is not None:
            volume_difference = (z_1 - z_0) * (cell_size ** 2)
            volume_data.append({'x': point[0], 'y': point[1], 'volumen_diff': volume_difference})
    return pd.DataFrame(volume_data)
def classify_points(volume_data):
    excess_points = volume_data[volume_data['volumen_diff'] > 0]
    deficit_points = volume_data[volume_data['volumen_diff'] < 0]
    return excess_points[['x', 'y', 'volumen_diff']].values, deficit_points[['x', 'y', 'volumen_diff']].values
def calculate_distance_matrix(excess_points, deficit_points):
    distance_matrix = np.zeros((len(excess_points), len(deficit_points)))
    for i, excess in enumerate(excess_points):
        for j, deficit in enumerate(deficit_points):
            distance_matrix[i, j] = np.sqrt((excess[0] - deficit[0]) ** 2 + (excess[1] - deficit[1]) ** 2)
    return distance_matrix
def solve_unbalanced_transport_problem(excess_points, deficit_points, distance_matrix, depot_distance=50):
    """
    Löst ein unbalanciertes Transportproblem mit PuLP unter Berücksichtigung einer festen Distanz zur Deponie.
    - excess_points: Numpy-Array mit Überschusspunkten (x, y, volumen_diff).
    - deficit_points: Numpy-Array mit Defizitpunkten (x, y, volumen_diff).
    - distance_matrix: Distanzmatrix zwischen Überschusspunkten und Defizitpunkten.
    - depot_distance: Feste Distanz zur Deponie (z.B. 50 km).
    """
    total_excess = excess_points[:, 2].sum()
    total_deficit = -deficit_points[:, 2].sum()

    # Initialisiere das LP-Problem
    prob = pulp.LpProblem("Unbalanced_Transport_Problem", pulp.LpMinimize)

    num_excess = len(excess_points)
    num_deficit = len(deficit_points)

    # Entscheidungsvariablen: Menge, die von Überschusspunkt i zu Defizitpunkt j transportiert wird
    transport_vars = pulp.LpVariable.dicts("Transport",
                                           ((i, j) for i in range(num_excess) for j in range(num_deficit)),
                                           lowBound=0, cat='Continuous')

    # Entscheidungsvariablen für den Transport zum/zur Depot
    transport_to_depot = pulp.LpVariable.dicts("ToDepot",
                                               (i for i in range(num_excess)),
                                               lowBound=0, cat='Continuous')
    transport_from_depot = pulp.LpVariable.dicts("FromDepot",
                                                 (j for j in range(num_deficit)),
                                                 lowBound=0, cat='Continuous')

    # Zielfunktion: Minimierung der Transportkosten
    prob += (
            pulp.lpSum([transport_vars[i, j] * distance_matrix[i, j]
                        for i in range(num_excess) for j in range(num_deficit)]) +
            pulp.lpSum([transport_to_depot[i] * depot_distance for i in range(num_excess)]) +
            pulp.lpSum([transport_from_depot[j] * depot_distance for j in range(num_deficit)])
    ), "Total_Transport_Cost"

    # Nebenbedingungen: Überschüsse müssen transportiert werden
    for i in range(num_excess):
        prob += (
            pulp.lpSum([transport_vars[i, j] for j in range(num_deficit)]) +
            transport_to_depot[i] == excess_points[i, 2],
            f"ExcessSupply_{i}"
        )

    # Nebenbedingungen: Defizite müssen ausgeglichen werden
    for j in range(num_deficit):
        prob += (
            pulp.lpSum([transport_vars[i, j] for i in range(num_excess)]) +
            transport_from_depot[j] == -deficit_points[j, 2],
            f"DeficitDemand_{j}"
        )

    # Zielfunktion und Nebenbedingungen sind jetzt balanciert durch die Deponie
    # Es gibt keinen weiteren Balancing-Knoten

    # Lösen des Problems
    prob.solve()

    # Extrahiere den Transportplan
    transport_plan = np.zeros((num_excess, num_deficit))
    for i in range(num_excess):
        for j in range(num_deficit):
            transport_plan[i, j] = pulp.value(transport_vars[i, j])

    # Extrahiere den Transport zum Depot
    to_depot = np.array([pulp.value(transport_to_depot[i]) for i in range(num_excess)])
    from_depot = np.array([pulp.value(transport_from_depot[j]) for j in range(num_deficit)])

    return transport_plan, to_depot, from_depot, prob
def perform_bodenaushub(zustand0_file, zustand1_file, depot_distance=50, cell_size = 1.0):
    # Lade die STL-Dateien
    mesh0 = mesh.Mesh.from_file(zustand0_file)
    mesh1 = mesh.Mesh.from_file(zustand1_file)

    # Konvertiere die Meshes zu Dreiecksarrays
    triangles_0 = mesh0.vectors
    triangles_1 = mesh1.vectors

    # Berechne die Bounding Box für beide Meshes und erstelle das Raster
    bounding_box = calculate_overall_bounding_box([triangles_0, triangles_1], padding=1.0)
    raster_points = create_raster(bounding_box, cell_size=cell_size)

    # Führe die Hauptberechnungen durch
    volume_df, excess_points, deficit_points, distance_matrix, transport_plan, to_depot, from_depot, prob = main(
        triangles_0, triangles_1, raster_points, depot_distance, cell_size=cell_size
    )

    # Berechne die minimale Arbeit
    min_work = pulp.value(prob.objective)

    # Gib die Ergebnisse in einem Dictionary zurück
    return {
        'volume_df': volume_df,
        'excess_points': excess_points,
        'deficit_points': deficit_points,
        'distance_matrix': distance_matrix,
        'transport_plan': transport_plan,
        'to_depot': to_depot,
        'from_depot': from_depot,
        'min_work': min_work,
        'bounding_box': bounding_box,
        'triangles_mesh0': triangles_0,
        'triangles_mesh1': triangles_1,  # Füge Mesh1 hinzu
        'middle_point': (
            (bounding_box['min_x'] + bounding_box['max_x']) / 2,
            (bounding_box['min_y'] + bounding_box['max_y']) / 2
        )
    }
def visualize_mesh_2d(triangles_mesh0, triangles_mesh1, bounding_box):
    """
    Erstellt eine Matplotlib-Figur mit zwei nebeneinanderliegenden Subplots für die beiden Meshes.

    :param triangles_mesh0: Numpy Array der Dreiecke für Mesh Zustand 0
    :param triangles_mesh1: Numpy Array der Dreiecke für Mesh Zustand 1
    :param bounding_box: Dictionary mit min_x, max_x, min_y, max_y
    :return: Matplotlib Figure
    """
    fig = Figure(figsize=(24, 12))
    ax1 = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(1, 2, 2)

    # Zeichnen von Mesh0 auf ax1
    for triangle in triangles_mesh0:
        polygon = Polygon(triangle[:, :2], closed=True, edgecolor='black', facecolor='#009682', alpha=0.5)
        ax1.add_patch(polygon)

    ax1.set_xlim(bounding_box['min_x'], bounding_box['max_x'])
    ax1.set_ylim(bounding_box['min_y'], bounding_box['max_y'])
    ax1.set_xlabel('x [m]', fontsize=18, fontweight='bold')
    ax1.set_ylabel('y [m]', fontsize=18, fontweight='bold')
    ax1.set_title('Projektion in xy, Mesh Zustand 0', fontsize=22, fontweight='bold')
    ax1.set_aspect('equal')
    ax1.grid(False)

    # Zeichnen von Mesh1 auf ax2
    for triangle in triangles_mesh1:
        polygon = Polygon(triangle[:, :2], closed=True, edgecolor='black', facecolor='#4664aa', alpha=0.5)
        ax2.add_patch(polygon)

    ax2.set_xlim(bounding_box['min_x'], bounding_box['max_x'])
    ax2.set_ylim(bounding_box['min_y'], bounding_box['max_y'])
    ax2.set_xlabel('x [m]', fontsize=18, fontweight='bold')
    ax2.set_ylabel('y [m]', fontsize=18, fontweight='bold')
    ax2.set_title('Projektion in xy, Mesh Zustand 1', fontsize=22, fontweight='bold')
    ax2.set_aspect('equal')
    ax2.grid(False)

    fig.tight_layout()
    return fig
def visualize_volume_distribution_2d(volume_df):
    fig = Figure(figsize=(12, 8))
    ax = fig.add_subplot(1, 1, 1)
    scatter = ax.scatter(volume_df['x'], volume_df['y'], c=volume_df['volumen_diff'], cmap='bwr', edgecolor='k')

    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label('Volumendifferenz (m³)', fontsize=14)
    cbar.ax.tick_params(labelsize=12)

    ax.set_xlabel('x [m]', fontsize=18, fontweight='bold')
    ax.set_ylabel('y [m]', fontsize=18, fontweight='bold')
    ax.set_title('Verteilung Volumendifferenz 2D', fontsize=22, fontweight='bold')
    ax.set_aspect('equal')
    return fig
def visualize_volume_bars_3d(volume_df, bounding_box, cell_size=1.0):
    """
    Erstellt eine Matplotlib-Figur für das 3D Volumendifferenz Balkendiagramm.

    :param volume_df: Pandas DataFrame mit den Volumendifferenzen
    :param bounding_box: Dictionary mit min_x, max_x, min_y, max_y
    :param cell_size: Größe der Rasterzellen
    :return: Matplotlib Figure
    """
    # Positive und negative Volumendifferenzen trennen
    positive_volumes = volume_df[volume_df['volumen_diff'] >= 0]
    negative_volumes = volume_df[volume_df['volumen_diff'] < 0]

    fig = Figure(figsize=(12, 8))
    ax = fig.add_subplot(1,1,1, projection='3d')

    # Plotten der positiven Volumina (Überschuss)
    if not positive_volumes.empty:
        ax.bar3d(
            positive_volumes['x'],
            positive_volumes['y'],
            np.zeros(len(positive_volumes)),
            dx=cell_size,
            dy=cell_size,
            dz=positive_volumes['volumen_diff'],
            color='blue',
            shade=True,
            alpha=0.7,
            label='Überschuss'
        )

    # Plotten der negativen Volumina (Defizit)
    if not negative_volumes.empty:
        ax.bar3d(
            negative_volumes['x'],
            negative_volumes['y'],
            negative_volumes['volumen_diff'],  # Startposition z ist negativ
            dx=cell_size,
            dy=cell_size,
            dz=negative_volumes['volumen_diff'].abs(),  # Höhe ist positiv
            color='red',
            shade=True,
            alpha=0.7,
            label='Defizit'
        )

    # Achsenbeschriftungen und Titel
    ax.set_xlabel('x [m]', fontsize=18, fontweight='bold')  # Größere und fette Beschriftung
    ax.set_ylabel('y [m]', fontsize=18, fontweight='bold')  # Größere und fette Beschriftung
    ax.set_zlabel('Volumendifferenz [m³]', fontsize=18, fontweight='bold')  # Größere und fette Beschriftung
    ax.set_title('Verteilung Volumendifferenz 3D', fontsize=22, fontweight='bold')  # Größerer und fetter Titel

    # Festlegen der Z-Achsen-Skalierung unabhängig von der Rastergröße
    min_z = volume_df['volumen_diff'].min()
    max_z = volume_df['volumen_diff'].max()
    padding_z = max(abs(min_z), abs(max_z)) * 0.1  # 10% Padding basierend auf dem maximalen Absolutwert

    ax.set_zlim(min_z - padding_z, max_z + padding_z)

    # Deaktivieren des Standardgitternetzes
    ax.grid(False)

    # Manuelles Hinzufügen eines Gitternetzes nur auf der XY-Ebene (z=0)
    x_min, x_max = bounding_box['min_x'], bounding_box['max_x']
    y_min, y_max = bounding_box['min_y'], bounding_box['max_y']

    # Erstellen Sie eine Reihe von Linien entlang der X-Achse
    for x in np.arange(x_min, x_max + cell_size, cell_size):
        ax.plot([x, x], [y_min, y_max], [0, 0], color='gray', linewidth=0.5)

    # Erstellen Sie eine Reihe von Linien entlang der Y-Achse
    for y in np.arange(y_min, y_max + cell_size, cell_size):
        ax.plot([x_min, x_max], [y, y], [0, 0], color='gray', linewidth=0.5)

    # Entfernen Sie die Hintergrundebenen und Achsenflächen
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False

    ax.xaxis.pane.set_edgecolor('white')
    ax.yaxis.pane.set_edgecolor('white')
    ax.zaxis.pane.set_edgecolor('white')

    # Achsenlinien nur anzeigen
    ax.xaxis.line.set_color((1.0, 1.0, 1.0, 1.0))  # Weiß, vollständig sichtbar
    ax.yaxis.line.set_color((1.0, 1.0, 1.0, 1.0))
    ax.zaxis.line.set_color((1.0, 1.0, 1.0, 1.0))

    # Festlegen des Blickwinkels für bessere Sichtbarkeit
    ax.view_init(elev=30, azim=45)

    # Legende hinzufügen
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(
        unique.values(),
        unique.keys(),
        fontsize=14,
        title_fontsize=16,
        loc='upper left',
        bbox_to_anchor=(-1,1)
    )

    return fig
def visualize_results(bounding_box, triangles_mesh0, triangles_mesh1, volume_df, middle_point):
    """
    Visualisiert die Ergebnisse der Bodenaushub-Berechnung.

    :param bounding_box: Dictionary mit min_x, max_x, min_y, max_y
    :param triangles_mesh0: Numpy Array der Dreiecke für Mesh Zustand 0
    :param triangles_mesh1: Numpy Array der Dreiecke für Mesh Zustand 1
    :param volume_df: Pandas DataFrame mit den Volumendifferenzen
    :param middle_point: Tuple mit den Mittelpunkten der Bounding Box
    """
    print("Visualize Results aufgerufen")
    # 2D Mesh Visualisierung
    fig_mesh = visualize_mesh_2d(triangles_mesh0, triangles_mesh1, bounding_box)
    show_plot_in_new_window(fig_mesh, "2D Mesh Visualisierung")

    # 2D Volumendifferenz Visualisierung
    fig_dist2d = visualize_volume_distribution_2d(volume_df)
    show_plot_in_new_window(fig_dist2d, "2D Volumendifferenzverteilung")

    # 3D Volumendifferenz Balkendiagramm
    fig_dist3d = visualize_volume_bars_3d(volume_df, bounding_box)
    show_plot_in_new_window(fig_dist3d, "3D Volumendifferenz Balkendiagramm")
def show_plot_in_new_window(fig, window_title):
    """
    Erstellt ein neues Tkinter-Fenster und bettet die Matplotlib-Figur ein.

    :param fig: Matplotlib Figure
    :param window_title: Titel des neuen Fensters
    """
    print(f"Erstelle Fenster: {window_title}")
    # Erstellen eines neuen Tkinter-Fensters
    new_window = tk.Toplevel()
    new_window.title(window_title)
    # new_window.geometry("1200x800") erst später setzen

    # Erstellen eines Canvas und Einbetten der Figur
    canvas = FigureCanvasTkAgg(fig, master=new_window)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Zeichnen der Figur und Aktualisieren des Canvas
    canvas.draw()
    canvas.get_tk_widget().update_idletasks()

    # Aktualisieren des Fensters
    new_window.update_idletasks()
    new_window.update()

    new_window.geometry("1200x800")

def main(triangles_0, triangles_1, raster_points, depot_distance=50, cell_size=1.0):
    # 1. Berechne Volumendifferenzen
    volume_df = calculate_discrete_volume_difference(triangles_0, triangles_1, raster_points, cell_size)

    # 2. Klassifiziere die Punkte in Überschuss- und Defizitpunkte
    excess_points, deficit_points = classify_points(volume_df)

    # 3. Berechne die Distanzmatrix zwischen den Überschuss- und Defizitpunkten
    distance_matrix = calculate_distance_matrix(excess_points, deficit_points)

    # 4. Lösen des unbalancierten Transportproblems
    transport_plan, to_depot, from_depot, prob = solve_unbalanced_transport_problem(
        excess_points, deficit_points, distance_matrix, depot_distance
    )

    return volume_df, excess_points, deficit_points, distance_matrix, transport_plan, to_depot, from_depot, prob

