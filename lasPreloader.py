import subprocess
import sys

# input_file = "H:\\LAZ\\c_37en1_big_delft.laz"
input_file = "data\\crop.laz"


lasinfo = subprocess.check_output(["thirdparty\\lastools\\lasinfo", "-i", input_file, "-stdout"])

min_x = min_y = min_z = None
max_x = max_y = max_z = None
num_points = None

for line in lasinfo.splitlines():
    if b"min x y z:" in line:
        min_data = line.split()
        min_x = float(min_data[4])
        min_y = float(min_data[5])
        min_z = float(min_data[6])

    if b"max x y z:" in line:
        max_data = line.split()
        max_x = float(max_data[4])
        max_y = float(max_data[5])
        max_z = float(max_data[6])

    if b"number of point records:" in line:
        num_points = int(line.split()[4])

offset = {
    0: min_x + (max_x - min_x) / 2,
    1: min_y + (max_y - min_y) / 2,
    2: min_z + (max_z - min_z) / 2
}


sys.stdout.write("offset {} {} {}\n".format(offset[0], offset[1], offset[2]))


las2txt = subprocess.Popen(["thirdparty\\lastools\\las2txt", "-drop_class", "3", "4", "5", "-i", input_file, "-stdout"], stdout=subprocess.PIPE)

for line in las2txt.stdout:
    stripped_line = str(line.rstrip(), "utf-8")
    split_line = stripped_line.split()
    split_line = [float(val) for val in split_line]

    x = round(split_line[0] - offset[0], 4)
    y = round(split_line[1] - offset[1], 4)
    z = round(split_line[2] - offset[2], 4)

    sys.stdout.write("{} {} {}\n".format(x, y, z))

