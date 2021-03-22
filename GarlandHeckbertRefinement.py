import collections
import sys
import threading

import startin

import numpy as np

from math import floor
from scipy.spatial import KDTree
from heapq import *


TRIANGULATION_THRESHOLD = 0.2


def shift_left(input_list):
    collection = collections.deque(input_list)
    collection.rotate(-1)
    return list(collection)


class Triangle:
    def __init__(self):
        self.vertices = {}
        self.triangle_vertex_ids = []

        self.point_index = -1
        self.max_error = 0

    def __lt__(self, other):
        return self.max_error < other.max_error

    def __str__(self):
        return str("max index: " + str(self.point_index) + ", error: " + str(-self.max_error) + ", len vertices: " + str(len(self.vertices)))


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

        # Determine 4 corner points for this grid cell to initialize triangulation
        corner_points = [
            [self.min_x + (self.cell_size * grid_x), self.min_y + (self.cell_size * grid_y)],
            [self.min_x + (self.cell_size * grid_x) + self.cell_size - 1E-5, self.min_y + (self.cell_size * grid_y)],
            [self.min_x + (self.cell_size * grid_x), self.min_y + (self.cell_size * grid_y) + self.cell_size - 1E-5],
            [self.min_x + (self.cell_size * grid_x) + self.cell_size - 1E-5, self.min_y + (self.cell_size * grid_y) + self.cell_size - 1E-5]
        ]

        near_corner_points = []

        for corner_point in corner_points:
            # Get nearest k points to corner points
            distances, indexes = tree.query(corner_point, k=10)

            z_vals = [self.grid_points[grid_x][grid_y][index][2] for index in indexes]

            # Add a corner point with average z value of k nearest
            near_corner_points.append([corner_point[0], corner_point[1], sum(z_vals) / len(z_vals)])

        del tree
        del x_vals
        del y_vals
        del z_vals

        return near_corner_points

    def scan_triangle(self, triangulation, heap, input_triangle, points):
        best = None
        max_error = 0

        # Create a new Triangle for in the heap and set the vertex indexes that define this triangle
        output_triangle = Triangle()
        output_triangle.triangle_vertex_ids = input_triangle

        # Adjacent triangles may also include relevant points because of flipping
        adjacent_triangles = triangulation.adjacent_triangles_to_triangle(input_triangle)

        # The points we have are from the old triangle, after inserting a point we need to find which are in the new one
        # and determine the point of maximum error within this triangle
        for i in points:
            point = points[i]

            in_triangle = triangulation.locate(point[0], point[1])

            # Triangle ordering may be different;
            # check if all points are in both lists [1, 2, 3] == [3, 1, 2] == [2, 3, 1]
            is_inside_triangle = all(vertex in input_triangle for vertex in in_triangle)

            # Assign each point that is within the new triangle to the new triangle and check if its error is largest
            if is_inside_triangle:
                output_triangle.vertices[i] = point

                error = abs(point[2] - triangulation.interpolate_tin_linear(point[0], point[1]))

                if error > max_error:
                    max_error = error
                    best = i
            else:
                # Check if a point exists in an adjacent triangle as this point may be relevant after a flip operation
                for adjacent_triangle in adjacent_triangles:

                    is_inside_triangle = all(vertex in adjacent_triangle for vertex in in_triangle)

                    if is_inside_triangle:
                        output_triangle.vertices[i] = point
                        break

        if best is not None:
            # Push worst abs vertex to triangle & heap
            output_triangle.max_error = -max_error
            output_triangle.point_index = best

            heappush(heap, output_triangle)

    def insert(self, triangulation, heap, index, vertices):
        vertex_id = triangulation.insert_one_pt(vertices[index][0], vertices[index][1], vertices[index][2], 0)

        incident_triangles = triangulation.incident_triangles_to_vertex(vertex_id)

        # Inserted this point, no need to keep it in our list of vertices for later triangles
        del vertices[index]

        # If there is only 1 point in this triangle, then no need to continue search as max granularity is reached
        if incident_triangles is not None and len(vertices) > 1:
            for triangle in incident_triangles:
                self.scan_triangle(triangulation, heap, triangle, vertices)

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

        heap = []

        # Insert 4 corner points into triangulation
        triangulation.insert(corner_points)

        # Get largest delta for initial 2 triangles and push to heap
        for triangle in triangulation.all_triangles():
            self.scan_triangle(triangulation, heap, triangle, all_points)

        while heap:
            # Get largest delta from heap
            max_abs = heappop(heap)

            sys.stdout.write(str(max_abs) + "\n")
            sys.stdout.flush()

            # If below threshold, we're done!
            if -max_abs.max_error < TRIANGULATION_THRESHOLD:
                break

            # If not below threshold, insert it and add delta's for each incident triangle to heap
            self.insert(triangulation, heap, max_abs.point_index, max_abs.vertices)

        for vertex in triangulation.all_vertices():
            if vertex[0] > 0:
                sys.stdout.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")

        sys.stdout.write(input_line)


class Processor:
    def __init__(self, dt):
        self.triangulation = dt
        self.threads = []

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
            # self.triangulation.finalize(int(data[0]), int(data[1]), input_line)

            thread = threading.Thread(target=self.triangulation.finalize, args=(int(data[0]), int(data[1]), input_line,), daemon=True)
            self.threads.append(thread)
            thread.start()

        else:
            # Unknown identifier in stream
            pass


if __name__ == "__main__":
    tr = Triangulation()
    processor = Processor(tr)

    for stdin_line in sys.stdin.readlines():
        processor.process_line(stdin_line)

    for thread in processor.threads:
        thread.join()

