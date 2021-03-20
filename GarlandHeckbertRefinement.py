import collections
import random
import sys
from heapq import _siftup, _siftdown

import startin

import numpy as np

from math import floor

from heapq import *

from scipy.spatial import KDTree

TRIANGULATION_THRESHOLD = 0.2


def shift_right(input_list):
    collection = collections.deque(input_list)
    collection.rotate(1)
    return list(collection)


class Triangle:
    def __init__(self):
        self.vertices = {}
        self.points = []

        self.point_index = -1
        self.max_error = 0

    def __lt__(self, other):
        return self.max_error < other.max_error

    def __str__(self):
        return str(self.point_index) + " " + str(self.max_error)


class Triangulation:
    def __init__(self):
        self.total_points = None

        self.cell_size = None

        self.grid_dimensions = None
        self.grid_points = None

        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None

        self.heap = []

    def set_bbox(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def initialize_grid(self, grid_size):
        self.grid_dimensions = grid_size
        self.grid_points = np.empty(shape=(grid_size, grid_size), dtype=object)

    def insert_point_in_grid(self, x, y, z):
        grid_cell = self.get_cell(x, y)

        if type(self.grid_points[grid_cell[0]][grid_cell[1]]) == list:
            self.grid_points[grid_cell[0]][grid_cell[1]].append([x, y, z])
        else:
            self.grid_points[grid_cell[0]][grid_cell[1]] = [[x, y, z]]

    def get_cell(self, x, y):
        return floor((x - self.min_x) / self.cell_size), floor((y - self.min_y) / self.cell_size)

    def get_corner_points(self, grid_x, grid_y):
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

        return near_corner_points

    def heap_update(self, max_error, local_index, triangle):
        if max_error == self.heap[local_index].max_error:
            return

        old_val, self.heap[local_index] = self.heap[local_index], triangle

        if max_error > old_val[0]:
            _siftup(self.heap, local_index)
        else:
            _siftdown(self.heap, 0, local_index)

    def heap_change(self, triangle):
        heappush(self.heap, triangle)

    def scan_triangle(self, triangulation, input_triangle, points):

        best = None
        max_error = 0

        output_triangle = Triangle()
        output_triangle.points = input_triangle

        for i in points:
            point = points[i]

            in_triangle = triangulation.locate(point[0], point[1])

            is_inside_triangle = all(item in input_triangle for item in in_triangle)

            if is_inside_triangle:
                output_triangle.vertices[i] = point

                error = abs(point[2] - triangulation.interpolate_tin_linear(point[0], point[1]))

                if error > max_error:
                    max_error = error
                    best = i

        if best is not None:
            del output_triangle.vertices[best]

            output_triangle.max_error = max_error * -1
            output_triangle.point_index = best

            self.heap_change(output_triangle)

    def insert(self, triangulation, all_points, max_abs):
        index = max_abs.point_index

        triangulation.insert_one_pt(all_points[index][0], all_points[index][1], all_points[index][2], 0)

        nearest_vertex = triangulation.closest_point(all_points[index][0], all_points[index][1])

        adjacent_triangles = triangulation.incident_triangles_to_vertex(nearest_vertex)

        if adjacent_triangles is not None:
            for triangle in adjacent_triangles:
                self.scan_triangle(triangulation, triangle, max_abs.vertices)

    def finalize(self, grid_x, grid_y, input_line):
        all_points = {}
        points_in_cell = self.grid_points[grid_x][grid_y]

        if points_in_cell is None or len(points_in_cell) == 0:
            sys.stdout.write(input_line)
            return

        for i in range(len(points_in_cell)):
            all_points[i] = points_in_cell[i]

        corner_points = self.get_corner_points(grid_x, grid_y)

        triangulation = startin.DT()

        # Insert 4 corner points into triangulation
        triangulation.insert(corner_points)

        for triangle in triangulation.all_triangles():
            self.scan_triangle(triangulation, triangle, all_points)

        while True:
            max_abs = heappop(self.heap)

            if max_abs.max_error * -1 < TRIANGULATION_THRESHOLD:
                break

            self.insert(triangulation, all_points, max_abs)

        self.heap = []

        for vertex in triangulation.all_vertices():
            if vertex[0] > 0:
                sys.stdout.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")

        sys.stdout.write(input_line)

        triangulation.write_geojson_triangles("3-19-21\\after_refinement" + str(random.randint(0, 10000)) + ".json")


class Processor:
    def __init__(self, dt):
        self._triangulation = dt

    def process_line(self, input_line):
        split_line = input_line.rstrip("\n").split(" ")

        identifier = split_line[0]
        data = split_line[1:]

        if identifier == "#" or identifier == "":
            pass

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
            self._triangulation.finalize(int(data[0]), int(data[1]), input_line)

        else:
            # Unknown identifier in stream
            pass


if __name__ == "__main__":
    tr = Triangulation()
    processor = Processor(tr)

    for stdin_line in sys.stdin.readlines():
        processor.process_line(stdin_line)

