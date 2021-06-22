import sys

for stdin_line in sys.stdin:
    identifier = stdin_line.split(" ")[0]

    if identifier == "x":
        continue

    sys.stdout.write(stdin_line)
