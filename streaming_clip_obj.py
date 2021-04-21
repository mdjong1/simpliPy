import sys


input_file = "H:\\LAZ\\C_37EN1_CROP_DECIMATED_v2.obj"

# 37EN1
clip_box = [
    83974.0646,
    446127.1660,
    84967.6011,
    447077.8905
]

# 37EN2
# clip_box = [
#     85010.2044,
#     446050.8249,
#     86245.8417,
#     447235.2819
# ]

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

