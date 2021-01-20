import sys
import startin

import numpy as np

from math import floor

TRIANGULATION_THRESHOLD = 2
PROCESSING_THRESHOLD = 1000


class Triangulation:
    def __init__(self):
        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None

        self.vertices = {}
        self.vertex_id = 1

        self.triangulation = None

    def set_bbox(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def add_vertex(self, x, y, z):
        self.vertices[self.vertex_id] = [x, y, z]
        self.vertex_id += 1

        if len(self.vertices) > PROCESSING_THRESHOLD:
            self.simplify_triangulation()

    def simplify_triangulation(self):
        output_triangulation = startin.DT()

        not_done = True

        while not_done:
            max_delta = 0
            max_index = -1

            for i in range(1, len(self.vertices) + 1):
                x = self.vertices[i][0]
                y = self.vertices[i][1]
                z = self.vertices[i][2]

                try:
                    interpolated_value = output_triangulation.interpolate_nn(x, y)

                    if abs(interpolated_value - z) > max_delta:
                        max_index = i
                        max_delta = abs(interpolated_value - z)
                except:
                    output_triangulation.insert_one_pt(x, y, z)

            if max_delta > TRIANGULATION_THRESHOLD and max_index != -1:
                output_triangulation.insert_one_pt(self.vertices[max_index][0], self.vertices[max_index][1], self.vertices[max_index][2])

            else:
                not_done = False

        for vertex in output_triangulation.all_vertices():
            sys.stdout.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")

        for edge in output_triangulation.all_triangles():
            sys.stdout.write("f " + str(edge[0] + 1) + " " + str(edge[1] + 1) + " " + str(edge[2] + 1) + "\n")

    def delete_vertex(self, index):
        pass
        # del self.vertices[index]
        # self.triangulation.remove(index)


class Processor:
    def __init__(self, dt):
        self._triangulation = dt

    def process_line(self, input_line):
        split_line = input_line.rstrip("\n").split(" ")

        identifier = split_line[0]
        data = split_line[1:]

        if identifier == "#" or identifier == "":
            pass

        elif identifier == "b":
            # bbox
            self._triangulation.set_bbox(float(data[0]), float(data[1]), float(data[2]), float(data[3]))

        elif identifier == "v":
            # vertex
            self._triangulation.add_vertex(float(data[0]), float(data[1]), float(data[2]))

        elif identifier == "f":
            # face
            pass

        elif identifier == "x":
            # vertex finalizer
            self._triangulation.delete_vertex(int(data[0]))

        else:
            # Unknown identifier in stream
            pass


if __name__ == "__main__":
    triangulation = Triangulation()
    processor = Processor(triangulation)

    for stdin_line in sys.stdin.readlines():
        processor.process_line(stdin_line)
