import argparse
import sys
from .repl import start_repl
from .runner import run_file


def main() -> int:
    parser = argparse.ArgumentParser(prog="aegis", description="Aegis Language CLI")
    parser.add_argument("file", nargs="?", help="Path to .aeg script to execute")
    parser.add_argument("--", dest="script_args", nargs=argparse.REMAINDER, help="Arguments passed to script")
    args = parser.parse_args()

    if args.file:
        return run_file(args.file, args.script_args or [])

    start_repl()
    return 0


if __name__ == "__main__":
    sys.exit(main())


