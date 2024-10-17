import numpy as np
import pandas as pd
from stl import mesh
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from mpl_toolkits.mplot3d import Axes3D
from scipy.optimize import linear_sum_assignment
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import pulp
import argparse
import sys

def calculate_bounding_box(triangles, padding=0.0):
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
def perform_bodenaushub(zustand0_file, zustand1_file, depot_distance=50):
    # Lade die STL-Dateien
    mesh0 = mesh.Mesh.from_file(zustand0_file)
    mesh1 = mesh.Mesh.from_file(zustand1_file)

    # Konvertiere die Meshes zu Dreiecksarrays
    triangles_0 = mesh0.vectors
    triangles_1 = mesh1.vectors

    # Berechne die Bounding Box und erstelle das Raster
    bounding_box = calculate_bounding_box(triangles_0, padding=1.0)
    raster_points = create_raster(bounding_box, cell_size=1.0)

    # Führe die Hauptberechnungen durch
    volume_df, excess_points, deficit_points, distance_matrix, transport_plan, to_depot, from_depot, prob = main(
        triangles_0, triangles_1, raster_points, depot_distance, cell_size=1.0
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
        'middle_point': (
            (bounding_box['min_x'] + bounding_box['max_x']) / 2,
            (bounding_box['min_y'] + bounding_box['max_y']) / 2,
            (bounding_box['min_z'] + bounding_box['max_z']) / 2
        )
    }
def visualize_mesh(triangles_mesh0, middle_point, bounding_box):
    # Implementiere hier deinen Visualisierungscode
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.add_collection3d(Poly3DCollection(triangles_mesh0))
    ax.set_xlim(bounding_box['min_x'], bounding_box['max_x'])
    ax.set_ylim(bounding_box['min_y'], bounding_box['max_y'])
    ax.set_zlim(bounding_box['min_z'], bounding_box['max_z'])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Mesh Visualisierung')

    # Achsenverhältnis einstellen
    ax.set_box_aspect([
        bounding_box['max_x'] - bounding_box['min_x'],
        bounding_box['max_y'] - bounding_box['min_y'],
        bounding_box['max_z'] - bounding_box['min_z']
    ])

    return fig
def visualize_volume_distribution_2d(volume_df):
    # Implementiere hier deinen Visualisierungscode
    fig, ax = plt.subplots()
    scatter = ax.scatter(volume_df['x'], volume_df['y'], c=volume_df['volumen_diff'], cmap='viridis')
    fig.colorbar(scatter, ax=ax, label='Volumendifferenz')
    return fig
def visualize_volume_bars_3d(volume_df):
    # Positive und negative Volumendifferenzen trennen
    positive_volumes = volume_df[volume_df['volumen_diff'] >= 0]
    negative_volumes = volume_df[volume_df['volumen_diff'] < 0]

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Positive Volumina plotten
    if not positive_volumes.empty:
        ax.bar3d(
            positive_volumes['x'], positive_volumes['y'], 0,
            dx=1, dy=1, dz=positive_volumes['volumen_diff'],
            color='blue', shade=True, label='Überschuss'
        )

    # Negative Volumina plotten (als positive Höhe nach unten)
    if not negative_volumes.empty:
        ax.bar3d(
            negative_volumes['x'], negative_volumes['y'], 0,
            dx=1, dy=1, dz=-negative_volumes['volumen_diff'],
            color='red', shade=True, label='Defizit'
        )

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Volumendifferenz')
    ax.legend()
    ax.set_title('3D Volumenbalken')

    # Achsenverhältnis einstellen
    ax.set_box_aspect([1, 1, 0.5])  # Seitenverhältnis anpassen

    return fig
def visualize_results(bounding_box, triangles_mesh0, volume_df, middle_point):
    fig_mesh = visualize_mesh(triangles_mesh0, middle_point, bounding_box)
    fig_mesh.show()

    fig_dist2d = visualize_volume_distribution_2d(volume_df)
    fig_dist2d.show()

    fig_dist3d = visualize_volume_bars_3d(volume_df)
    fig_dist3d.show()
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
