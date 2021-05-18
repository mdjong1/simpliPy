simplified_dt = "F:\\LAZ\\twotiles_full.obj"

vertex_count = 0
face_count = 0

print("Starting vertex counting")

for line in open(simplified_dt, "r"):
    split_line = line.split(" ")
    identifier = split_line[0]
    data = split_line[1:]

    if identifier == "v":
        vertex_count += 1

    elif identifier == "f":
        face_count += 1


print("Number of vertices: {}".format(vertex_count))

print("Number of triangles: {}".format(face_count))

