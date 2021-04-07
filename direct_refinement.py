import sys
import time
from heapq import heapify, heappop

import startin

import numpy as np

from math import floor
from multiprocessing import cpu_count, Process
from scipy.spatial import KDTree

COARSE_THRESHOLD = 3
FINE_THRESHOLD = 0.3

# 37EN1 - 2m - 0.2m (6 threads)
# START TIME: 2021-04-06T09:34:35
# END TIME:   2021-04-06T18:06:22

# 37EN1 - Ground Only Decimation - 3m - 0.3m (10 threads)
# START TIME: 2021-04-07T14:44:16
# END TIME:   2021-04-07T17:35:27

# 37EN2 - 3m - 0.3m (6 threads)
# START TIME: 2021-04-06T22:00:00
# END TIME:   2021-04-07T05:27:13

# 37AN1 - 3m - 0.3m (2 threads)
# START TIME: 2021-04-06T22:28:21
# END TIME:   2021-04-06T23:56:15


def is_almost(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


class Triangulation:
    def __init__(self):
        self.total_points = None

        self.cell_size = None

        self.grid_dimensions = None
        self.grid_points = None
        self.initial_points = None

        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None

        self.vertices = {}
        self.vertex_id = 1

    def set_bbox(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def initialize_grid(self, grid_size):
        self.grid_dimensions = grid_size
        self.grid_points = np.empty(shape=(grid_size, grid_size), dtype=object)
        self.initial_points = np.empty(shape=(grid_size, grid_size), dtype=object)

    def insert_point(self, x, y, z, grid_x, grid_y):
        if type(self.grid_points[grid_x][grid_y]) == list:
            self.grid_points[grid_x][grid_y].append([x, y, z])
        else:
            self.grid_points[grid_x][grid_y] = [[x, y, z]]

    def insert_point_in_grid(self, x, y, z):
        grid_x, grid_y = self.get_cell(x, y)

        self.insert_point(x, y, z, grid_x, grid_y)

    def insert_vertex(self, x, y, z):
        self.vertices[self.vertex_id] = [x, y, z]
        self.vertex_id += 1

    def get_cell(self, x, y):
        return floor((x - self.min_x) / self.cell_size), floor((y - self.min_y) / self.cell_size)

    def finalize(self, input_line, grid_x, grid_y, vertices):

        if len(vertices) > 0:

            triangulation = startin.DT()

            x_vals = []
            y_vals = []
            z_vals = []

            for vertex_id, point in vertices.items():
                x_vals.append(point[0])
                y_vals.append(point[1])
                z_vals.append(point[2])

            tree = KDTree(np.c_[x_vals, y_vals])

            corner_points = [
                [self.min_x + (self.cell_size * grid_x), self.min_y + (self.cell_size * grid_y)],
                [self.min_x + (self.cell_size * grid_x) + self.cell_size - 1E-5, self.min_y + (self.cell_size * grid_y)],
                [self.min_x + (self.cell_size * grid_x), self.min_y + (self.cell_size * grid_y) + self.cell_size - 1E-5],
                [self.min_x + (self.cell_size * grid_x) + self.cell_size - 1E-5, self.min_y + (self.cell_size * grid_y) + self.cell_size - 1E-5]
            ]

            near_corner_points = []

            for corner_point in corner_points:
                # Get nearest point to corner
                distances, indexes = tree.query(corner_point, k=10)

                queried_z_vals = [z_vals[index] for index in indexes if index < len(z_vals)]

                # add a corner point with average z value of 10 nearest
                near_corner_points.append([corner_point[0], corner_point[1], sum(queried_z_vals) / len(queried_z_vals)])

            triangulation.insert(near_corner_points)

            to_delete = []

            # First coarse loop

            for key, vertex in vertices.items():
                x = vertex[0]
                y = vertex[1]
                z = vertex[2]

                try:
                    interpolated_value = triangulation.interpolate_tin_linear(x, y)

                    if abs(interpolated_value - z) > COARSE_THRESHOLD:
                        triangulation.insert_one_pt(x, y, z, 0)
                        to_delete.append(key)

                # In rare cases we get a point outside CH due to ----00.0 being counted as wrong cell
                # FIXME: Adjust get_cell function to return correct cell for ----00.0 points
                except OSError:
                    pass

            for key in reversed(to_delete):
                del vertices[key]

            # Fine loop

            for key, vertex in vertices.items():
                x = vertex[0]
                y = vertex[1]
                z = vertex[2]

                try:
                    interpolated_value = triangulation.interpolate_tin_linear(x, y)

                    if abs(interpolated_value - z) > FINE_THRESHOLD:
                        triangulation.insert_one_pt(x, y, z, 0)

                # In rare cases we get a point outside CH due to ----00.0 being counted as wrong cell
                # FIXME: Adjust get_cell function to return correct cell for ----00.0 points
                except OSError:
                    pass

            # Decimation step with fine threshold
            heap = []

            vertex_id = 0

            for vertex in triangulation.all_vertices():
                x = vertex[0]
                y = vertex[1]
                z = vertex[2]

                # Skip infinite vertex
                if triangulation.can_vertex_be_removed(vertex_id):
                    try:
                        interpolated_value = triangulation.interpolate_tin_linear(x, y)

                        # Only append delta's that are less than fine threshold
                        if abs(interpolated_value - z) < FINE_THRESHOLD:
                            heap.append((abs(interpolated_value - z) * -1, vertex_id, x, y, z))

                    # In rare cases we get a point outside CH due to ----00.0 being counted as wrong cell
                    # FIXME: Adjust get_cell function to return correct cell for ----00.0 points
                    except OSError:
                        pass

                vertex_id += 1

            heapify(heap)

            while heap:
                lowest_delta = heappop(heap)

                vertex_id = lowest_delta[1]
                x = lowest_delta[2]
                y = lowest_delta[3]
                z = lowest_delta[4]

                try:
                    interpolated_value = triangulation.interpolate_tin_linear(x, y)

                    if abs(interpolated_value - z) < FINE_THRESHOLD:
                        triangulation.remove(vertex_id)

                # In rare cases we get a point outside CH due to ----00.0 being counted as wrong cell
                # FIXME: Adjust get_cell function to return correct cell for ----00.0 points
                except OSError:
                    pass

            for vertex in triangulation.all_vertices():
                # Don't print infinite vertex
                if vertex[0] > 0:
                    sys.stdout.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")

        sys.stdout.write(input_line)
        sys.stdout.flush()


class Processor:
    def __init__(self, dt):
        self.triangulation = dt
        self.sprinkling = True

        self.processes = []

    def process_line(self, input_line):
        split_line = input_line.rstrip("\n").split(" ")

        identifier = split_line[0]
        data = split_line[1:]

        if identifier == "#" or identifier == "":
            if data[0] == "endsprinkle":
                self.sprinkling = False
                sys.stderr.write("Sprinkling done!\n")

        elif identifier == "n":
            # Total number of points
            self.triangulation.total_points = int(data[0])
            sys.stdout.write(input_line)

        elif identifier == "c":
            # Grid dimensions (cXc)
            # self.triangulation.initialize_grid(int(data[0]))
            sys.stdout.write(input_line)

        elif identifier == "s":
            # Cell size
            self.triangulation.cell_size = int(data[0])
            sys.stdout.write(input_line)

        elif identifier == "b":
            # bbox
            self.triangulation.set_bbox(float(data[0]), float(data[1]), float(data[2]), float(data[3]))
            sys.stdout.write(input_line)

        elif identifier == "v":
            # vertex
            # self.triangulation.insert_point_in_grid(float(data[0]), float(data[1]), float(data[2]))

            # All sprinkle points get passed to output directly
            if not self.sprinkling:
                self.triangulation.insert_vertex(float(data[0]), float(data[1]), float(data[2]))

            else:
                sys.stdout.write(input_line)

        elif identifier == "x":
            # cell finalizer

            # sys.stderr.write("Finalizing: {}\n".format(data))
            # self.triangulation.finalize(input_line, int(data[0]), int(data[1]))

            if self.sprinkling:
                sys.stdout.write(input_line)
                return

            sys.stderr.write("Starting new process to finalize cell: {}, {}. Processing currently running: {}\n".format(data[0], data[1], len(self.processes)))
            sys.stderr.flush()

            sleep_time = 1

            # Ensure total number of processes never exceeds capacity
            while len(self.processes) >= cpu_count() / 2:
                for i in reversed(range(len(self.processes))):
                    if not self.processes[i].is_alive():
                        del self.processes[i]

                time.sleep(sleep_time)

            process = Process(target=self.triangulation.finalize, args=(input_line, int(data[0]), int(data[1]), self.triangulation.vertices))
            self.triangulation.vertices = {}
            self.triangulation.vertex_id = 1
            self.processes.append(process)
            process.start()

        else:
            # Unknown identifier in stream
            pass

        sys.stdout.flush()


if __name__ == "__main__":
    triangulation = Triangulation()
    processor = Processor(triangulation)

    for stdin_line in sys.stdin:
        processor.process_line(stdin_line)

    for process in processor.processes:
        process.join()
