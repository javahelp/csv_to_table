# CLAUDE.md

This file guides Claude Code (claude.ai/code) when working in this repository.

## Project

`csv-to-table` is a stdin→stdout CLI that converts CSV into a MySQL-style ASCII
table, or a table back into CSV. It picks the direction by checking whether the
input, after stripping leading whitespace, starts with `+---`. It uses only the
standard library (Python ≥3.8, src layout, setuptools).

## Commands

```
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'   # setup
.venv/bin/pytest                                             # all tests
.venv/bin/pytest tests/test_converter.py::TableToCsvTests::test_basic   # one test
PYTHONPATH=src python3 -m unittest discover -s tests         # no pytest needed
printf 'a,b\n1,2\n' | .venv/bin/csv-to-table                 # manual check
```

## Architecture

- `src/csv_to_table/converter.py`: pure functions with no I/O. `convert()`
  chooses between `csv_to_table()` and `table_to_csv()` using `is_table()`.
  Every input problem raises `ConversionError` (a `ValueError` subclass). Its
  message includes a line or record number and has no "error:" prefix.
- `src/csv_to_table/cli.py`: `main(argv, stdin, stdout, stderr) -> int`. The
  streams can be injected, which lets tests avoid subprocesses. This is the only
  place exceptions are turned into `csv-to-table: error: ...` on stderr and
  exit codes (0 ok, 1 conversion error, 2 usage, 130 Ctrl-C). It also handles
  `BrokenPipeError` quietly by pointing stdout at devnull.
- `src/csv_to_table/__main__.py` runs `main()`. The console script
  `csv-to-table` is declared in `pyproject.toml`.

## Invariants and design decisions

- Column width has a minimum of 1, so every border starts with `+---`.
  Otherwise a table with empty columns would be read as CSV on round-trip.
- `table_to_csv` finds column boundaries from the `+` positions in the first
  border and slices each row at those positions. It does not split on `|`, so
  cells can contain `|`. Every row must be exactly as long as the border and
  have `|` at each boundary.
- The table must be: border, header row, border, zero or more data rows,
  border. Borders anywhere else are an error. Blank lines and indentation
  around lines are ignored.
- CSV is parsed with `csv.reader(strict=True)`. Rows must have the same field
  count as the header, and cells with newlines are rejected.
- Cells are left-aligned. Whitespace at the edges of a cell is lost when
  converting a table back to CSV. These limits are documented in the README.
  Update the README if behaviour changes.

## Tests

`tests/test_converter.py` covers the conversion logic and each error message.
`tests/test_cli.py` covers exit codes and stderr through injected streams, and
runs a couple of real subprocess runs of `python -m csv_to_table`. Add a
success test and a failure test for any new behaviour.
