"""Command-line entry point: read stdin, convert, write stdout."""

import argparse
import os
import sys
from typing import List, Optional, TextIO

from csv_to_table import __version__
from csv_to_table.converter import ConversionError, convert

PROG = "csv-to-table"

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_INTERRUPTED = 130


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=(
            "Convert CSV on stdin to a MySQL-style ASCII table on stdout, or "
            "convert such a table back to CSV. Input whose first non-blank "
            "characters are '+---' is treated as a table; anything else is "
            "treated as CSV, with the first row as the header."
        ),
        epilog=f"example: {PROG} < data.csv > data.txt",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(
    argv: Optional[List[str]] = None,
    stdin: Optional[TextIO] = None,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
) -> int:
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr

    try:
        build_parser().parse_args(argv)
    except SystemExit as exc:  # argparse has already printed help/usage
        return exc.code if isinstance(exc.code, int) else EXIT_USAGE

    if stdin.isatty():
        print(
            f"{PROG}: error: no input; pipe CSV or a table into stdin "
            f"(try '{PROG} --help')",
            file=stderr,
        )
        return EXIT_USAGE

    try:
        text = stdin.read()
        result = convert(text)
        stdout.write(result)
        stdout.flush()
    except ConversionError as exc:
        print(f"{PROG}: error: {exc}", file=stderr)
        return EXIT_ERROR
    except UnicodeDecodeError as exc:
        print(f"{PROG}: error: input is not valid text: {exc}", file=stderr)
        return EXIT_ERROR
    except BrokenPipeError:
        # Downstream closed early (e.g. `| head`); not worth a traceback.
        # Point stdout at devnull so the interpreter's final flush is silent.
        if stdout is sys.stdout:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
        return EXIT_ERROR
    except KeyboardInterrupt:
        return EXIT_INTERRUPTED
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
