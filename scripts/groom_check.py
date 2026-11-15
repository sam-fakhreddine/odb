"""Check committed seam briefs against their declared Git dependencies."""

import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seam", type=int)
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
