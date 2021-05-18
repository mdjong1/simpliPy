import random
import sys

from math import floor

# 1 / THINNING_FACTOR points kept (on average)
THINNING_FACTOR = 8


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
            if random.randint(0, THINNING_FACTOR) == floor(THINNING_FACTOR / 2):
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

    for stdin_line in sys.stdin:
        processor.process_line(stdin_line)

