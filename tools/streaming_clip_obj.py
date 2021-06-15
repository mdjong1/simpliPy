import sys

if __name__ == "__main__":
    arguments = sys.argv
    if len(arguments) != 6:
        print("Invalid number of arguments used!")
        print("Usage: streaming_clip_obj.py <input OBJ file> <minX> <minY> <maxX> <maxY> > <output OBJ file>")
        sys.exit()

    input_file = sys.argv[1]
    clip_box = [
        float(sys.argv[2]),
        float(sys.argv[3]),
        float(sys.argv[4]),
        float(sys.argv[5]),
    ]

    input_vertex_id = 1
    output_vertex_id = 1
    vertices = {}

    sys.stdout.write("b {} {} {} {}\n".format(clip_box[0], clip_box[1], clip_box[2], clip_box[3]))

    for line in open(input_file, "r"):
        split_line = line.split(" ")

        identifier = split_line[0]
        data = split_line[1:]

        if identifier == "v":

            x = float(data[0])
            y = float(data[1])

            if clip_box[0] < x < clip_box[2] and clip_box[1] < y < clip_box[3]:
                vertices[input_vertex_id] = output_vertex_id
                output_vertex_id += 1

                sys.stdout.write(line)

            input_vertex_id += 1

        elif identifier == "f":
            data = [int(val) for val in data]

            in_bbox = all([key in vertices for key in data])

            if in_bbox:
                output_vertices = [vertices[vertex_id] for vertex_id in data]

                sys.stdout.write("f {} {} {}\n".format(output_vertices[0], output_vertices[1], output_vertices[2]))

