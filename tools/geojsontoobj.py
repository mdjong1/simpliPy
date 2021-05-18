import sys

from geojson import load

if __name__ == "__main__":
    arguments = sys.argv
    if len(arguments) != 3:
        print("Invalid number of arguments used!")
        print("Usage: geojsontoobj.py <input GeoJSON file> <output OBJ file>")
        sys.exit()

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file) as f:
        gj = load(f)

    vertex_id = 1

    with open(output_file, "w") as f:
        for feature in gj["features"]:
            vertex_ids = []
            for vertices in feature["geometry"]["coordinates"]:
                for vertex in vertices:
                    f.write("v {} {} {}\n".format(vertex[0], vertex[1], vertex[2]))
                    vertex_ids.append(str(vertex_id))
                    vertex_id += 1

                f.write("f {}\n".format(" ".join(vertex_ids)))
