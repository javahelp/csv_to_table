# csv-to-table

A small command-line filter that converts CSV into a MySQL-style ASCII table,
and converts such a table back into CSV.

```
$ printf 'id,name\n1,Alice\n2,Bob\n' | csv-to-table
+----+-------+
| id | name  |
+----+-------+
| 1  | Alice |
| 2  | Bob   |
+----+-------+
```

## Usage

```
csv-to-table < input > output
python -m csv_to_table < input > output
```

Input is read from **stdin** and the result is written to **stdout**. The tool
works out which way to convert by itself:

* If the input begins with `+---` (ignoring leading whitespace), it is treated
  as an ASCII table and converted to **CSV**.
* Otherwise it is treated as **CSV** and converted to an ASCII table. The first
  CSV record is used as the header row.

So it is its own inverse:

```
$ csv-to-table < data.csv | csv-to-table   # gives back the CSV
```

Options:

| Option      | Meaning                     |
|-------------|-----------------------------|
| `-h/--help` | Show help and exit          |
| `--version` | Show the version and exit   |

### Exit status and errors

Errors go to stderr as one line, `csv-to-table: error: <message>`, with a line
or record number where that helps. Nothing is written to stdout on failure.

| Code | Meaning                                                         |
|------|-----------------------------------------------------------------|
| 0    | Success                                                         |
| 1    | The input could not be converted (malformed, empty, not text)   |
| 2    | Misuse: unknown arguments, or stdin is a terminal (nothing piped in) |
| 130  | Interrupted with Ctrl-C                                         |

Rejected input includes:

* CSV rows whose field count differs from the header row
* CSV with bad quoting (for example, an unterminated quoted field)
* CSV fields containing line breaks (a table can't show them)
* Tables with a malformed border, a missing header separator or closing border,
  extra border lines in the body, or rows that don't line up with the border

### Behaviour notes

* All cells are left-aligned. (MySQL right-aligns numbers; this tool doesn't.)
* Blank lines in CSV are skipped. Output CSV uses `\n` line endings and quotes
  fields only when needed.
* Leading and trailing spaces inside a cell are lost when converting a table
  back to CSV.
* A cell may contain `|`. Columns are found from the `+` positions in the
  border, not by splitting on `|`.
* Column widths count characters. East Asian wide characters or emoji may
  therefore look misaligned in a terminal, but they still convert back
  correctly.

## Build and development

Requires Python 3.8 or newer. There are no runtime dependencies.

```
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'      # editable install plus pytest
pytest                       # run the tests
```

The tests also run with the standard library alone:

```
PYTHONPATH=src python3 -m unittest discover -s tests
```

To build a wheel and sdist:

```
pip install build
python -m build              # results go in dist/
pip install dist/csv_to_table-*.whl
```

## Project layout

```
pyproject.toml
src/csv_to_table/
    converter.py   # pure conversion functions + ConversionError
    cli.py         # argparse, stdin/stdout, error reporting, exit codes
    __main__.py    # `python -m csv_to_table`
tests/
    test_converter.py
    test_cli.py
```

## License

MIT. See [LICENSE](LICENSE).
