import sys
import fileinput
import startin

import numpy as np

from math import floor


TRIANGULATION_THRESHOLD = 1


class Vertex:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class Triangulation:
    def __init__(self):
        self.total_points = None

        self.cell_size = None

        self.grid_dimensions = None
        self.grid_points = None
        self.triangulations = None

        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None

        self.vertices = {}

    def set_bbox(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def initialize_grid(self, grid_size):
        self.grid_dimensions = grid_size
        self.grid_points = np.empty(shape=(grid_size, grid_size), dtype=object)
        self.triangulations = np.empty(shape=(grid_size, grid_size), dtype=object)

    def insert_point_in_grid(self, x, y, z):
        grid_cell = self.get_cell(x, y)

        if self.triangulations[grid_cell[0]][grid_cell[1]] is None:

            if type(self.grid_points[grid_cell[0]][grid_cell[1]]) == list:
                self.grid_points[grid_cell[0]][grid_cell[1]].append([x, y, z])

            else:
                self.grid_points[grid_cell[0]][grid_cell[1]] = [[x, y, z]]

            if len(self.grid_points[grid_cell[0]][grid_cell[1]]) == 5:
                dt = startin.DT()
                dt.insert(self.grid_points[grid_cell[0]][grid_cell[1]])
                self.triangulations[grid_cell[0]][grid_cell[1]] = dt

        else:
            try:
                interpolated_value = self.triangulations[grid_cell[0]][grid_cell[1]].interpolate_laplace(x, y)

                if abs(interpolated_value - z) > TRIANGULATION_THRESHOLD:
                    self.grid_points[grid_cell[0]][grid_cell[1]].append([x, y, z])
                    self.triangulations[grid_cell[0]][grid_cell[1]].insert_one_pt(x, y, z)

            except OSError:  # Outside convex hull (CH)
                self.grid_points[grid_cell[0]][grid_cell[1]].append([x, y, z])
                self.triangulations[grid_cell[0]][grid_cell[1]].insert_one_pt(x, y, z)

    def get_cell(self, x, y):
        return floor((x - self.min_x) / self.cell_size), floor((y - self.min_y) / self.cell_size)

    def finalize(self, grid_x, grid_y):
        if self.grid_points[grid_x][grid_y] is not None:
            for vertex in self.grid_points[grid_x][grid_y]:
                sys.stdout.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")

        self.triangulations[grid_x][grid_y] = None
        self.grid_points[grid_x][grid_y] = None


class Processor:
    def __init__(self, dt):
        self._triangulation = dt

    def process_line(self, input_line):
        split_line = input_line.rstrip("\n").split(" ")

        identifier = split_line[0]
        data = split_line[1:]

        if identifier == "#":
            return

        elif identifier == "n":
            # Total number of points
            self._triangulation.total_points = int(data[0])
            sys.stdout.write(input_line)

        elif identifier == "c":
            # Grid dimensions (cXc)
            self._triangulation.initialize_grid(int(data[0]))
            sys.stdout.write(input_line)

        elif identifier == "s":
            # Cell size
            self._triangulation.cell_size = int(data[0])
            sys.stdout.write(input_line)

        elif identifier == "b":
            # bbox
            self._triangulation.set_bbox(float(data[0]), float(data[1]), float(data[2]), float(data[3]))
            sys.stdout.write(input_line)

        elif identifier == "v":
            # vertex
            self._triangulation.insert_point_in_grid(float(data[0]), float(data[1]), float(data[2]))

        elif identifier == "x":
            # cell finalizer
            self._triangulation.finalize(int(data[0]), int(data[1]))
            sys.stdout.write(input_line)

        else:
            # Unknown identifier in stream
            pass


if __name__ == "__main__":
    triangulation = Triangulation()
    processor = Processor(triangulation)

    for stdin_line in fileinput.input():
        if stdin_line == "":
            continue

        processor.process_line(stdin_line)
