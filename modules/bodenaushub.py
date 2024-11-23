# bodenaushub.py
import numpy as np
import pandas as pd
import pulp
from scipy.spatial.distance import cdist
from stl import mesh
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
from matplotlib.colors import LinearSegmentedColormap

import tkinter as tk

# --- Funktionen zur Berechnung der Volumen (-differenzen) des Rasters --- #
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

    triangles_set = [triangles_0, triangles_1]

    print("STL-Dateien geladen:")
    print(f"Zustand 0: {file_0}, Anzahl Dreiecke: {len(triangles_0)}")
    print(f"Zustand 1: {file_1}, Anzahl Dreiecke: {len(triangles_1)}")

    return triangles_set
def calculate_bounding_box(triangles_set):
    # Extrahiere alle x- und y-Werte aus den Dreiecksarrays
    all_x = [triangles[:, :, 0].flatten() for triangles in triangles_set]
    all_y = [triangles[:, :, 1].flatten() for triangles in triangles_set]

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
def interpolate_height_for_points(raster_points, triangles_set, epsilon=1e-6):
    """
    Prüft für eine Liste von Punkten (x, y), ob diese in einem der Dreiecke eines jeden Dreieckssatzes liegt,
    und berechnet dann die Höhen (z0, z1, ...) mittels baryzentrischer Interpolation.

    :param raster_points: Liste von Tupeln (x, y) für die Interpolation
    :param triangles_set: Liste von Dreieckssätzen (jeder Dreieckssatz ist eine Liste von Dreiecken)
    :param epsilon: Toleranzwert für numerische Stabilität
    :return: Pandas-DataFrame mit x, y und z-Werten für jeden Dreieckssatz
    """
    point_data = []
    for p in raster_points:
        point_entry = {'x': p[0], 'y': p[1]}
        for idx, triangles in enumerate(triangles_set):
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

                # Prüfen, ob der Punkt innerhalb des Dreiecks liegt
                if (w1 >= -epsilon) and (w2 >= -epsilon) and (w3 >= -epsilon) and (w1 + w2 + w3 <= 1 + epsilon):
                    # Interpolation der Höhe
                    z = a[2] + w2 * (b[2] - a[2]) + w3 * (c[2] - a[2])
                    break  # Höhenwert gefunden
            point_entry[f'z{idx}'] = z
        point_data.append(point_entry)
    return pd.DataFrame(point_data)
def calculate_discrete_volume_difference(point_df, cell_size):
    """
    Berechnet die Volumendifferenz zwischen zwei Höhenmodellen anhand der interpolierten Höhenwerte in point_df.
    Fügt eine Spalte hinzu, die angibt, ob der Punkt ein Überschuss oder ein Defizit ist.

    :param point_df: Pandas DataFrame mit x, y, z0, z1 (interpolierte Höhen)
    :param cell_size: Größe der Zelle (Standard: 1.0)
    :return: Das gleiche DataFrame mit zusätzlichen Spalten 'volumen_diff' und 'status'
    """
    if 'z0' in point_df.columns and 'z1' in point_df.columns:
        # Berechnung der Volumendifferenz
        point_df['volumen_diff'] = (point_df['z1'] - point_df['z0']) * (cell_size ** 2)

        # Klassifizierung des Punkts als Überschuss, Defizit oder neutral
        point_df['status'] = np.where(
            point_df['volumen_diff'] > 0, 'excess',
            np.where(point_df['volumen_diff'] < 0, 'deficit', 'neutral')
        )
    else:
        print("Fehlende z0 oder z1 Spalte in DataFrame")
    return point_df

# --- Funktionen zum Lösen des Transportproblems --- #
def calculate_distance_matrix(point_df):
    """
    Berechnet die Distanzmatrix zwischen Punkten mit Überschuss und Punkten mit Defizit.

    :param point_df: Pandas DataFrame mit Spalten 'x', 'y', 'volumen_diff', 'status'
    :return: Distanzmatrix als 2D-NumPy-Array, Überschusspunkte, Defizitpunkte
    """
    # Extrahieren der Überschuss- und Defizitpunkte
    excess_df = point_df[point_df['status'] == 'excess'][['x', 'y', 'volumen_diff']]
    deficit_df = point_df[point_df['status'] == 'deficit'][['x', 'y', 'volumen_diff']]

    excess_points = excess_df[['x', 'y']].values
    deficit_points = deficit_df[['x', 'y']].values

    # Berechnen der Distanzen mit cdist für Effizienz
    distance_matrix = cdist(excess_points, deficit_points, metric='euclidean')

    return distance_matrix, excess_df, deficit_df
def solve_unbalanced_transport_problem(excess_points_df, deficit_points_df, distance_matrix, depot_distance):
    """
    Löst ein unbalanciertes Transportproblem mit PuLP, wobei die Deponie nur als Gesamttransportpunkt genutzt wird.

    :param excess_points_df: Pandas DataFrame mit Überschusspunkten (x, y, volumen_diff).
    :param deficit_points_df: Pandas DataFrame mit Defizitpunkten (x, y, volumen_diff).
    :param distance_matrix: Distanzmatrix zwischen Überschusspunkten und Defizitpunkten.
    :param depot_distance: Distanz zur Deponie (z.B. 50 km).
    :return: Transportplan, Transport zur/von der Deponie, interne Kosten, Depotkosten, LP Problem
    """
    # Berechnung der Summen für Überschuss und Defizit
    total_excess = excess_points_df['volumen_diff'].sum()
    total_deficit = -deficit_points_df['volumen_diff'].sum()
    total_difference = total_excess + total_deficit

    # Initialisierung des LP-Problems
    prob = pulp.LpProblem("Unbalanced_Transport_Problem", pulp.LpMinimize)

    # Anzahl der Überschuss- und Defizitpunkte
    num_excess = len(excess_points_df)
    num_deficit = len(deficit_points_df)

    # Entscheidungsvariablen: Transport von Überschusspunkt i zu Defizitpunkt j
    transport_vars = pulp.LpVariable.dicts(
        "Transport",
        ((i, j) for i in range(num_excess) for j in range(num_deficit)),
        lowBound=0, cat='Continuous'
    )

    # Variablen für Gesamtmengen zur/von Deponie
    to_depot = pulp.LpVariable("ToDepot", lowBound=0, cat='Continuous')
    from_depot = pulp.LpVariable("FromDepot", lowBound=0, cat='Continuous')

    # **Zielfunktion:** Minimierung der Transportkosten
    prob += (
        pulp.lpSum([transport_vars[i, j] * distance_matrix[i, j]
                    for i in range(num_excess) for j in range(num_deficit)]) +
        to_depot * depot_distance + from_depot * depot_distance
    ), "Total_Transport_Cost"

    # **Nebenbedingungen für Überschusspunkte**
    for i in range(num_excess):
        prob += (
            pulp.lpSum([transport_vars[i, j] for j in range(num_deficit)]) + to_depot == excess_points_df.iloc[i]['volumen_diff'],
            f"ExcessSupply_{i}"
        )

    # **Nebenbedingungen für Defizitpunkte**
    for j in range(num_deficit):
        prob += (
            pulp.lpSum([transport_vars[i, j] for i in range(num_excess)]) + from_depot == -deficit_points_df.iloc[j]['volumen_diff'],
            f"DeficitDemand_{j}"
        )

    # **Deponie-Balancing-Bedingungen:** nur wenn Überschuss oder Defizit bleibt
    prob += to_depot <= max(0, total_excess - total_deficit), "DepotSupplyCondition"
    prob += from_depot <= max(0, total_deficit - total_excess), "DepotDemandCondition"

    # **Lösen des Problems**
    prob.solve()

    # **Transportplan** extrahieren
    transport_plan = np.zeros((num_excess, num_deficit))
    for i in range(num_excess):
        for j in range(num_deficit):
            transport_plan[i, j] = pulp.value(transport_vars[i, j])

    # **Debugging-Ausgaben** zur Kostenverifizierung
    to_depot_value = pulp.value(to_depot)
    from_depot_value = pulp.value(from_depot)
    depot_costs = to_depot_value * depot_distance + from_depot_value * depot_distance
    internal_costs = pulp.value(prob.objective) - depot_costs
    total_costs = pulp.value(prob.objective)

    print(f"Gesamtkosten der Zielfunktion: {total_costs:.2f}")
    print(f"Kosten für Transport zur Deponie: {to_depot_value * depot_distance:.2f}")
    print(f"Kosten für Transport von der Deponie: {from_depot_value * depot_distance:.2f}")
    print(f"Berechnete interne Transportkosten: {internal_costs:.2f}")

    return transport_plan, to_depot_value, from_depot_value, total_excess,total_deficit, total_difference, depot_costs, internal_costs, total_costs, prob

# --- Grundfunktionen zur Visualisierung --- #
def visualize_interpolated_points(point_df):
    """
    Visualisiert die interpolierten Punkte (z0 und z1) in einem 3D-Scatterplot.

    :param point_df: Pandas-DataFrame mit Spalten 'x', 'y', 'z0', 'z1'
    :return: Matplotlib Figure Objekt
    """
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    # Zustand 0
    ax.scatter(point_df['x'], point_df['y'], point_df['z0'], c='#009682', label='Zustand 0', s=20)

    # Zustand 1
    ax.scatter(point_df['x'], point_df['y'], point_df['z1'], c='#4664AA', label='Zustand 1', s=20)

    ax.set_xlabel('x [m]', fontsize=18, fontweight='bold')
    ax.set_ylabel('y [m]', fontsize=18, fontweight='bold')
    ax.set_zlabel('z (interpoliert)', fontsize=18, fontweight='bold')
    ax.set_title('3D-Darstellung der interpolierten Punkte für Zustand 0 und Zustand 1', fontsize=22, fontweight='bold', pad=20)
    # Legende vergrößern
    legend = ax.legend(loc='center left', bbox_to_anchor=(-0.15, 0.5), fontsize=14, markerscale=2)
    legend.get_frame().set_linewidth(1.5)  # Optional: Rahmen der Legende verstärke

    # Optional: Entfernen der Hintergrundflächen und Gitternetzlinien
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    # ax.grid(False)

    return fig
def visualize_meshes_and_raster_points(triangles_set, raster_points):
    """
    Visualisiert zwei Meshes nebeneinander, jedes mit denselben Rasterpunkten.

    :param triangles_set: Liste von zwei Meshes, wobei jedes Mesh eine Liste von Dreiecken ist.
    :param raster_points: NumPy-Array von Rasterpunkten (x, y).
    """

    fig, axes = plt.subplots(1, 2, figsize=(12, 6))

    for idx, triangles in enumerate(triangles_set):
        ax = axes[idx]

        # Zeichne die Dreiecke des aktuellen Meshes
        for triangle in triangles:
            a, b, c = triangle
            polygon = Polygon([a[:2], b[:2], c[:2]], closed=True, fill=None, edgecolor='r', linewidth=1)
            ax.add_patch(polygon)

        # Zeichne die Rasterpunkte
        ax.scatter(raster_points[:, 0], raster_points[:, 1], color='green', s=5)

        ax.set_xlabel('x [m]', fontsize=18, fontweight='bold')
        ax.set_ylabel('y [m]', fontsize=18, fontweight='bold')
        ax.set_title(f'Mesh {idx + 1} und Rasterpunkte', fontsize=22, fontweight='bold', pad=20)
        ax.grid(True)
        ax.set_aspect('equal')  # Gleiche Skalierung auf beiden Achsen

    fig.tight_layout()
    return fig
def visualize_volume_distribution_2d(point_df):
    fig = Figure(figsize=(12, 8))
    ax = fig.add_subplot(1, 1, 1)

    # Farbskala von (0, 150, 130) über Weiß nach (70, 100, 170)
    color_list = ((162/255, 34/255, 35/255), (1.0, 1.0, 1.0), (70/255, 100/255, 170/255))
    custom_cmap = LinearSegmentedColormap.from_list('custom_cmap', colors=color_list)

    # Werte unterhalb des Schwellenwerts auf 0 setzen (oder maskieren)
    volumen_diff_rounded = np.round(point_df['volumen_diff'] / 0.1) * 0.1

    # Scatterplot mit angepassten Volumendifferenzen
    scatter = ax.scatter(
        point_df['x'], point_df['y'],
        c=volumen_diff_rounded, cmap=custom_cmap, edgecolor='k'
    )

    # Colorbar
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label('Volumendifferenz (m³)', fontsize=18, fontweight='bold')
    cbar.ax.tick_params(labelsize=12)

    # Achsenbeschriftung und Titel
    ax.set_xlabel('x [m]', fontsize=18, fontweight='bold')
    ax.set_ylabel('y [m]', fontsize=18, fontweight='bold')
    ax.set_title('Verteilung Volumendifferenz 2D', fontsize=22, fontweight='bold', pad=20)
    ax.set_aspect('equal')

    return fig
def visualize_volume_bars_3d(point_df, bounding_box, cell_size=1.0):
    # Positive und negative Volumendifferenzen trennen
    positive_volumes = point_df[point_df['volumen_diff'] > 0]
    negative_volumes = point_df[point_df['volumen_diff'] < 0]

    fig = Figure(figsize=(14, 10))
    ax = fig.add_subplot(1, 1, 1, projection='3d')

    # Plotten der positiven Volumina (Überschuss)
    if not positive_volumes.empty:
        ax.bar3d(
            positive_volumes['x'],
            positive_volumes['y'],
            np.zeros(len(positive_volumes)),  # Start bei z=0
            dx=cell_size,
            dy=cell_size,
            dz=positive_volumes['volumen_diff'],
            color='#4664AA',
            shade=True,
            alpha=0.7,
            label='Überschuss'
        )

    # Plotten der negativen Volumina (Defizit)
    if not negative_volumes.empty:
        ax.bar3d(
            negative_volumes['x'],
            negative_volumes['y'],
            np.zeros(len(negative_volumes)),  # Start bei z=0
            dx=cell_size,
            dy=cell_size,
            dz=negative_volumes['volumen_diff'],
            color='#A22223',
            shade=True,
            alpha=0.7,
            label='Defizit'
        )

    # Berechnung der Z-Achsenlimits
    min_vol_diff = point_df['volumen_diff'].min()
    max_vol_diff = point_df['volumen_diff'].max()
    z_min = min(0, min_vol_diff)
    z_max = max(0, max_vol_diff)
    z_range = z_max - z_min
    if z_range == 0:
        z_range = 1
    padding = z_range * 0.1
    ax.set_zlim(z_min - padding, z_max + padding)

    # Anpassung des Blickwinkels
    ax.view_init(elev=20, azim=30)

    # Einstellung des Seitenverhältnisses
    ax.set_box_aspect([1, 1, 0.5])

    # Achsenbeschriftungen und Titel
    ax.set_xlabel('x [m]', fontsize=18, fontweight='bold')
    ax.set_ylabel('y [m]', fontsize=18, fontweight='bold')
    ax.set_zlabel('Volumendifferenz [m³]', fontsize=18, fontweight='bold')
    ax.set_title('Verteilung Volumendifferenz 3D', fontsize=22, fontweight='bold', pad=20)

    # Gitterlinien auf der XY-Ebene
    x_min, x_max = bounding_box['min_x'], bounding_box['max_x']
    y_min, y_max = bounding_box['min_y'], bounding_box['max_y']
    for x in np.arange(x_min, x_max + cell_size, cell_size):
        ax.plot([x, x], [y_min, y_max], [0, 0], color='gray', linewidth=0.5)
    for y in np.arange(y_min, y_max + cell_size, cell_size):
        ax.plot([x_min, x_max], [y, y], [0, 0], color='gray', linewidth=0.5)

    # Entfernen der Hintergrundebenen und Achsenflächen
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('white')
    ax.yaxis.pane.set_edgecolor('white')
    ax.zaxis.pane.set_edgecolor('white')
    ax.xaxis.line.set_color((1.0, 1.0, 1.0, 1.0))
    ax.yaxis.line.set_color((1.0, 1.0, 1.0, 1.0))
    ax.zaxis.line.set_color((1.0, 1.0, 1.0, 1.0))

    # Legende hinzufügen
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(
        unique.values(),
        unique.keys(),
        fontsize=14,
        title_fontsize=16,
        loc='center left',
        bbox_to_anchor=(-0.2, 0.5)
    )
    return fig

# --- Finale Funktion zur Visualisierung aller Grafiken --- #
def visualize_results(bounding_box, raster_points, triangles_set, point_df):
    """
    Visualisiert die Ergebnisse der Bodenaushub-Berechnung.

    :param bounding_box: Dictionary mit min_x, max_x, min_y, max_y
    :param raster_points: Array mit den Rasterpunkten
    :param triangles_set: Numpy Array der Netze für Zustand 0 und Zustand 1
    :param point_df: Pandas DataFrame mit den interpolierten Höhen und Volumendifferenzen
    """
    print("Visualize Results aufgerufen")

    # Interpolierte z-Koordinaten plotten --> To Do
    fig_interpolated_points = visualize_interpolated_points(point_df)
    show_plot_in_new_window(fig_interpolated_points, "Interpolierte Punkte")

    # 2D Mesh Visualisierung
    fig_mesh = visualize_meshes_and_raster_points(triangles_set, raster_points)
    show_plot_in_new_window(fig_mesh, "2D Mesh Visualisierung")

    # 2D Volumendifferenz Visualisierung --> das brauche ich nicht unbedingt
    fig_dist2d = visualize_volume_distribution_2d(point_df)
    show_plot_in_new_window(fig_dist2d, "2D Volumendifferenzverteilung")

    # 3D Volumendifferenz Balkendiagramm
    fig_dist3d = visualize_volume_bars_3d(point_df, bounding_box)
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

# --- Funktion zum Export des Transport-Plans --- #
def export_transport_plan_to_csv(transport_plan, excess_points_df, deficit_points_df, to_depot_value, from_depot_value, depot_distance, filename='transport_plan.csv'):
    """
    Exportiert den Transportplan als CSV-Datei, inklusive Transport zur/von der Deponie.

    :param transport_plan: NumPy-Array mit den Transportmengen von Überschusspunkten zu Defizitpunkten.
    :param excess_points_df: DataFrame mit den Überschusspunkten (x, y, volumen_diff).
    :param deficit_points_df: DataFrame mit den Defizitpunkten (x, y, volumen_diff).
    :param to_depot_value: Gesamtmenge, die zur Deponie transportiert wird.
    :param from_depot_value: Gesamtmenge, die von der Deponie abgeholt wird.
    :param depot_distance: Distanz zur Deponie.
    :param filename: Name der Ausgabedatei.
    """
    data = []
    num_excess, num_deficit = transport_plan.shape
    for i in range(num_excess):
        for j in range(num_deficit):
            amount = transport_plan[i, j]
            if amount > 0:
                source = excess_points_df.iloc[i]
                destination = deficit_points_df.iloc[j]
                data.append({
                    'source_x': source['x'],
                    'source_y': source['y'],
                    'source_volumen_diff': source['volumen_diff'],
                    'destination_x': destination['x'],
                    'destination_y': destination['y'],
                    'destination_volumen_diff': destination['volumen_diff'],
                    'amount': amount,
                    'to_depot': 0,
                    'from_depot': 0
                })
    # Hinzufügen des Transports zur/von der Deponie
    if to_depot_value > 0:
        data.append({
            'source_x': 'Various',
            'source_y': 'Various',
            'source_volumen_diff': 'Various',
            'destination_x': 'Depot',
            'destination_y': 'Depot',
            'destination_volumen_diff': 'N/A',
            'amount': to_depot_value,
            'to_depot': 1,
            'from_depot': 0
        })
    if from_depot_value > 0:
        data.append({
            'source_x': 'Depot',
            'source_y': 'Depot',
            'source_volumen_diff': 'N/A',
            'destination_x': 'Various',
            'destination_y': 'Various',
            'destination_volumen_diff': 'Various',
            'amount': from_depot_value,
            'to_depot': 0,
            'from_depot': 1
        })
    transport_df = pd.DataFrame(data)
    transport_df.to_csv(filename, index=False)
    print(f"Transportplan wurde als '{filename}' gespeichert.")
def perform_bodenaushub(zustand0_file, zustand1_file, depot_distance, cell_size):

    # 1. Lade Netze
    triangles_set = load_stl_files(zustand0_file, zustand1_file)

    # 2. Berechne Bounding Box
    bounding_box = calculate_bounding_box(triangles_set)

    # 3. Erstelle das Raster
    raster_points = create_raster(bounding_box, cell_size)

    # 4. Interpoliere die Höhe der Rasterpunkte für Zustand 0 und Zustand 1
    point_df = interpolate_height_for_points(raster_points, triangles_set)

    # 5. Berechne die diskreten Volumendifferenzen und klassifiziere Überschuss- und Defizitpunkte
    point_df = calculate_discrete_volume_difference(point_df, cell_size)

    # 6. Berechne die Distanzmatrix
    distance_matrix, excess_points, deficit_points = calculate_distance_matrix(point_df)

    # 7. Löse das Transportproblem
    transport_plan, to_depot_value, from_depot_value, total_excess, total_deficit, total_difference, depot_costs, internal_costs, total_costs, prob = solve_unbalanced_transport_problem(excess_points, deficit_points, distance_matrix, depot_distance)

    return {
        'bounding_box': bounding_box,
        'raster_points': raster_points,
        'triangles_set': triangles_set,
        'point_df': point_df,
        'transport_plan': transport_plan,
        'excess_points': excess_points,
        'deficit_points': deficit_points,
        'to_depot_value': to_depot_value,
        'from_depot_value': from_depot_value,
        'total_excess': total_excess,
        'total_deficit': total_deficit,
        'total_difference': total_difference,
        'depot_costs': depot_costs,
        'internal_costs': internal_costs,
        'total_costs': total_costs,
        'prob': prob
    }

