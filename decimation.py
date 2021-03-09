import sys
import startin

from ast import literal_eval


TRIANGULATION_THRESHOLD = 0.001
PROCESSING_THRESHOLD = 75000


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
        # self.vertices[self.vertex_id] = [x, y, z]

        self.triangulation.insert_vertex(self.vertex_id, x, y, z)

        self.vertex_id += 1

    def simplify_triangulation(self):

        not_done = True

        total_vertices = self.triangulation.number_of_vertices()

        print("Processing {} vertices!".format(total_vertices))

        # self.triangulation.write_geojson_triangles("data\\pre_simplifying_triangles.json")

        while not_done:
            min_delta = 1E9
            max_index = -1

            for vertex_id in self.triangulation.all_vertex_ids(True):
                # Not infinite vertex or vertex on CH or vertex previously removed
                if not self.triangulation.can_vertex_be_removed(vertex_id):
                    continue

                vertex = self.triangulation.get_point(vertex_id)

                # print(vertex_id)

                # print("Doing 'fake' remove of:", vertex_id, vertex[0], vertex[1], vertex[2])
                self.triangulation.remove(vertex_id)

                # print("Interpolating: x=" + str(vertex[0]) + ", y=" + str(vertex[1]))
                end_value = self.triangulation.interpolate_tin_linear(vertex[0], vertex[1])

                # print("Inserting " + str(vertex_id))
                self.triangulation.insert_one_pt(vertex[0], vertex[1], vertex[2], vertex_id)

                delta = abs(end_value - vertex[2])

                if delta < min_delta:
                    min_delta = delta
                    max_index = vertex_id

            # print(max_index, min_delta)

            if max_index != -1 and min_delta < TRIANGULATION_THRESHOLD:
                # print("Removing:", max_index, min_delta)
                self.triangulation.remove(max_index)

            else:
                not_done = False

        # self.triangulation.write_geojson_triangles("data\\simplified_" + str(self.processing_index) + ".json")

        for vertex in self.triangulation.all_vertices():
            if vertex[0] >= 0:
                sys.stdout.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")

        for edge in self.triangulation.all_triangles():
            sys.stdout.write("f " + str(edge[0]) + " " + str(edge[1]) + " " + str(edge[2]) + "\n")

        self.triangulation.cleanup_complete_stars()

        # Reset triangulation for next set of points
        # self.triangulation = startin.DT()
        # self.triangulation.set_is_init(True)

    def new_star(self, index, neighbors):
        # self.finalized[index] = (True, len(neighbors))
        if neighbors:
            self.triangulation.define_star(index, neighbors)

        if self.vertex_id / self.processing_id >= PROCESSING_THRESHOLD:
            self.simplify_triangulation()
            self.processing_id += 1
            self.processing_index += PROCESSING_THRESHOLD

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

    # Finalize remaining points
    triangulation.simplify_triangulation()

    # for vertex in triangulation.triangulation.all_vertices():
    #     if vertex[0] >= 0:
    #         sys.stdout.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")
    #
    # for edge in triangulation.triangulation.all_triangles():
    #     sys.stdout.write("f " + str(edge[0]) + " " + str(edge[1]) + " " + str(edge[2]) + "\n")
