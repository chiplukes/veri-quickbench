import argparse
import importlib.metadata

from .tb_creator import create_testbench

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Optional argument flag which defaults to False
    parser.add_argument("-d", "--debug", action="store_true", default=False)

    # Optional argument flag which defaults to False
    parser.add_argument("-c", "--create", action="store_true", default=False)

    # Optional verbosity counter (eg. -v, -vv, -vvv, etc.)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Verbosity (-v, -vv, etc)",
    )

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=importlib.metadata.version("veri_quickbench")),
    )

    args = parser.parse_args()

    if args.verbose > 0:
        print(f"Verbose: {args.verbose}")
        print(f"{__file__}:__main__")

    if args.create:
        print("Creating a new testbench")
        # Call the function to create a new example application
        create_testbench()
