import random
import sys

# 1 / 10 points kept (on average)
THINNING_FACTOR = 10


class Processor:
    def process_line(self, input_line):
        split_line = input_line.rstrip("\n").split(" ")

        identifier = split_line[0]

        if identifier == "#" or identifier == "":
            pass

        elif identifier == "n":
            # Total number of points
            sys.stdout.write(input_line)

        elif identifier == "c":
            # Grid dimensions (cXc)
            sys.stdout.write(input_line)

        elif identifier == "s":
            # Cell size
            sys.stdout.write(input_line)

        elif identifier == "b":
            # bbox
            sys.stdout.write(input_line)

        elif identifier == "v":
            # vertex
            if random.randint(0, THINNING_FACTOR) == 1:
                sys.stdout.write(input_line)

        elif identifier == "x":
            # cell finalizer
            sys.stdout.write(input_line)

        else:
            # Unknown identifier in stream
            pass

        sys.stdout.flush()


if __name__ == "__main__":
    processor = Processor()

    for stdin_line in sys.stdin.readlines():
        processor.process_line(stdin_line)

