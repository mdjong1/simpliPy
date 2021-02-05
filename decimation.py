import sys
import startin

from ast import literal_eval


TRIANGULATION_THRESHOLD = 2
PROCESSING_THRESHOLD = 1E-9


class Triangulation:
    def __init__(self):
        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None

        self.vertices = {}
        self.vertex_id = 1

        self.triangulation = startin.DT()
        self.triangulation.set_is_init(True)

        self.processing_id = 1
        self.processing_index = 1

        self.finalized = {}

    def set_bbox(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def add_vertex(self, x, y, z):
        self.vertices[self.vertex_id] = [x, y, z]

        self.triangulation.insert_vertex(self.vertex_id, x, y, z)

        self.vertex_id += 1

    def simplify_triangulation(self):

        not_done = True

        total_vertices = self.triangulation.number_of_vertices()

        while not_done:
            min_delta = 1E9
            max_index = -1

            for vertex_id in range(total_vertices):
                # Not infinite vertex or vertex on CH or vertex previously removed
                if vertex_id == 0 or \
                        self.triangulation.is_vertex_convex_hull(vertex_id) or \
                        self.triangulation.is_vertex_removed(vertex_id):
                    continue

                vertex = self.triangulation.get_point(vertex_id)

                self.triangulation.remove(vertex_id)

                end_value = self.triangulation.interpolate_tin_linear(vertex[0], vertex[1])

                self.triangulation.insert_one_pt(vertex[0], vertex[1], vertex[2])

                delta = abs(end_value - vertex[2])

                if delta < min_delta:
                    min_delta = delta
                    max_index = vertex_id

            if max_index != -1 and min_delta < TRIANGULATION_THRESHOLD:
                self.triangulation.remove(max_index)

            else:
                not_done = False

        for vertex in self.triangulation.all_vertices():
            sys.stdout.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")

        for edge in self.triangulation.all_triangles():
            sys.stdout.write("f " + str(edge[0] + 1) + " " + str(edge[1] + 1) + " " + str(edge[2] + 1) + "\n")

    def new_star(self, index, neighbors):
        if neighbors:
            self.triangulation.define_star(index, neighbors)

        # if self.vertex_id / self.processing_id >= PROCESSING_THRESHOLD:
        #     self.simplify_triangulation()
        #     self.processing_id += 1
        #     self.processing_index += PROCESSING_THRESHOLD

    def delete_vertex(self, index):
        self.finalized[index] = True
        # del self.vertices[index]
        # self.triangulation.remove(index)


class Processor:
    def __init__(self, dt):
        self._triangulation = dt

    def simplify(self):
        self._triangulation.simplify_triangulation()

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
            # self._triangulation.delete_vertex(int(data[0]))
            self._triangulation.new_star(int(data[0]), literal_eval("".join(data[1:])))

        else:
            # Unknown identifier in stream
            pass


if __name__ == "__main__":
    triangulation = Triangulation()
    processor = Processor(triangulation)

    for stdin_line in sys.stdin.readlines():
        processor.process_line(stdin_line)
    processor.simplify()
