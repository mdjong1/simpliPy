import sys
import time

import startin

import numpy as np

from math import floor
from multiprocessing import cpu_count, Process
from scipy.spatial import KDTree

COARSE_THRESHOLD = 1
FINE_THRESHOLD = 0.2


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

    def set_bbox(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def initialize_grid(self, grid_size):
        self.grid_dimensions = grid_size
        self.grid_points = np.empty(shape=(grid_size, grid_size), dtype=object)
        self.initial_points = np.empty(shape=(grid_size, grid_size), dtype=object)

    def insert_point(self, x, y, z, grid_cell):
        if type(self.grid_points[grid_cell[0]][grid_cell[1]]) == list:
            self.grid_points[grid_cell[0]][grid_cell[1]].append([x, y, z])
        else:
            self.grid_points[grid_cell[0]][grid_cell[1]] = [[x, y, z]]

    def insert_point_in_grid(self, x, y, z):
        grid_cell = self.get_cell(x, y)

        self.insert_point(x, y, z, grid_cell)

    def get_cell(self, x, y):
        return floor((x - self.min_x) / self.cell_size), floor((y - self.min_y) / self.cell_size)

    def finalize(self, grid_x, grid_y, input_line):

        if self.grid_points[grid_x][grid_y] is not None:

            triangulation = startin.DT()

            x_vals = []
            y_vals = []

            for point in self.grid_points[grid_x][grid_y]:
                x_vals.append(point[0])
                y_vals.append(point[1])

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

                z_vals = [self.grid_points[grid_x][grid_y][index][2] for index in indexes]

                # add a corner point with average z value of 10 nearest
                near_corner_points.append([corner_point[0], corner_point[1], sum(z_vals) / len(z_vals)])

            triangulation.insert(near_corner_points)

            for vertex in self.grid_points[grid_x][grid_y]:
                    x = vertex[0]
                    y = vertex[1]
                    z = vertex[2]

                    try:
                        interpolated_value = triangulation.interpolate_tin_linear(x, y)

                        if abs(interpolated_value - z) > COARSE_THRESHOLD:
                            triangulation.insert_one_pt(x, y, z, 0)

                    except OSError:
                        pass

            for vertex in triangulation.all_vertices():
                # Don't print infinite vertex
                if vertex[0] > 0:
                    sys.stdout.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")

            self.grid_points[grid_x][grid_y] = None

        sys.stdout.write(input_line)
        sys.stdout.flush()


class Processor:
    def __init__(self, dt):
        self.triangulation = dt

        self.processes = []

    def process_line(self, input_line):
        split_line = input_line.rstrip("\n").split(" ")

        identifier = split_line[0]
        data = split_line[1:]

        if identifier == "#" or identifier == "":
            pass

        elif identifier == "n":
            # Total number of points
            self.triangulation.total_points = int(data[0])
            sys.stdout.write(input_line)

        elif identifier == "c":
            # Grid dimensions (cXc)
            self.triangulation.initialize_grid(int(data[0]))
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
            self.triangulation.insert_point_in_grid(float(data[0]), float(data[1]), float(data[2]))

        elif identifier == "x":
            # cell finalizer

            sys.stderr.write("Starting new process to finalize: {}. Processing currently running: {}\n".format(data, len(self.processes)))
            sys.stderr.flush()

            sleep_time = 0.01

            # Ensure total number of processes never exceeds capacity
            while len(self.processes) >= cpu_count() - 4:
                for i in reversed(range(len(self.processes))):
                    if not self.processes[i].is_alive():
                        del self.processes[i]

                # Incremental sleep timer
                time.sleep(sleep_time)
                sleep_time *= 1.5

            process = Process(target=self.triangulation.finalize, args=(int(data[0]), int(data[1]), input_line,))
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
