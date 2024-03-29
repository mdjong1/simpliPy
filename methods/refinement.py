import random
import sys
import time

import startin

import numpy as np

from multiprocessing import cpu_count, Process
from scipy.spatial import KDTree

TRIANGULATION_THRESHOLD = 0.2
DELTA_PRECISION = 1E4


class Vertex:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.delta_z = 0

    def __str__(self):
        return "{} {} {} - {}\n".format(self.x, self.y, self.z, self.delta_z)

class Triangulation:
    def __init__(self):
        self.cell_size = None

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

    def insert_vertex(self, x, y, z):
        self.vertices[self.vertex_id] = Vertex(x, y, z)
        self.vertex_id += 1

    def finalize(self, input_line, grid_x, grid_y, vertices):
        if len(vertices) > 0:
            triangulation = startin.DT()

            x_vals = []
            y_vals = []
            z_vals = []

            for vertex_id, vertex in vertices.items():
                x_vals.append(vertex.x)
                y_vals.append(vertex.y)
                z_vals.append(vertex.z)

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

            worst_point_index = 1

            for vertex_id, vertex in vertices.items():
                try:
                    interpolated_value = triangulation.interpolate_tin_linear(vertex.x, vertex.y)

                    vertex.delta_z = round(abs(interpolated_value - vertex.z) * DELTA_PRECISION) / DELTA_PRECISION

                    if vertex.delta_z > vertices[worst_point_index].delta_z:
                        worst_point_index = vertex_id

                # If outside CH, always insert
                except OSError:
                    triangulation.insert_one_pt(vertex[0], vertex[1], vertex[2], 0)

            loop_time = time.time()

            largest_delta = vertices[worst_point_index]

            while True:
                if len(vertices) % 100 == 0:
                    sys.stderr.write("Vertices left: {}, time since last 100: {}\n".format(len(vertices), time.time() - loop_time))
                    sys.stderr.flush()
                    loop_time = time.time()

                try:
                    if largest_delta.delta_z > TRIANGULATION_THRESHOLD:
                        triangulation.insert_one_pt(largest_delta.x, largest_delta.y, largest_delta.z, 0)
                    else:
                        break

                # Somehow point is outside bbox, ignore
                except OSError:
                    pass

                for vertex_id, vertex in vertices.items():
                    interpolated_value = triangulation.interpolate_tin_linear(vertex.x, vertex.y)

                    vertex.delta_z = round(abs(interpolated_value - vertex.z) * DELTA_PRECISION) / DELTA_PRECISION

                    if vertex.delta_z > vertices[worst_point_index].delta_z:
                        worst_point_index = vertex_id

                largest_delta = vertices[worst_point_index]

                del vertices[worst_point_index]
                worst_point_index = random.choice(list(vertices.keys()))

            for vertex in triangulation.all_vertices():
                if vertex[0] > 0:  # Exclude infinite vertex
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
            # All sprinkle points get passed to output directly
            if not self.sprinkling:
                self.triangulation.insert_vertex(float(data[0]), float(data[1]), float(data[2]))

            else:
                sys.stdout.write(input_line)

        elif identifier == "x":
            # cell finalizer
            # While sprinkling, don't bother processing since all finalized cells now are still empty anyways
            if self.sprinkling:
                sys.stdout.write(input_line)
                return

            sys.stderr.write("Starting new process to finalize cell: {}, {}. Processing currently running: {}\n".format(data[0], data[1], len(self.processes)))
            sys.stderr.flush()

            sleep_time = 1

            # Ensure total number of processes never exceeds capacity
            while len(self.processes) >= cpu_count() - 4:
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
