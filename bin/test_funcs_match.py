import argparse
import pathlib
import sys


def parse_representations(path: pathlib.Path) -> list[str]:
    """Parse representations from a file."""
    start, *lines = path.read_text().splitlines()
    if start != "start":
        raise ValueError("File does not have a valid representation.")
    indent = " " * next(i for i, c in enumerate(lines[0]) if c != " ")
    lines = [l.removeprefix(indent) for l in lines] + ["END"]
    blocks = []
    block = []
    for line in lines:
        if line.startswith(indent):
            block.append(line)
        elif block:
            blocks.append("\n".join(block))
            block = []
    return blocks


def check_matches(representations) -> bool:
    """Check if representations are all the same."""
    if len(representations) < 2:
        raise ValueError("Need at least two representations to compare.")
    first, *rest = representations
    for i, representation in enumerate(rest, 2):
        if representation != first:
            print(f"Representations 1 and {i} differ.")
            print(f"Representation 1:\n{first}")
            print()
            print(f"Representation {i}:\n{representation}")
            return False
    return True


def arg_parser() -> argparse.ArgumentParser:
    """Return an ArgumentParser."""
    parser = argparse.ArgumentParser()
    parser.add_argument("representation")
    return parser


def main() -> None:
    """Generate a representation."""
    args = arg_parser().parse_args()
    representation = pathlib.Path(args.representation)

    print(f"== Checking all representations match for {representation} ==")
    result = check_matches(parse_representations(representation))
    print(f"== Done with {representation} ==")
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
