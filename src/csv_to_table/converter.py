"""Core conversion logic between CSV text and MySQL-style ASCII tables.

A table looks like this::

    +----+-------+
    | id | name  |
    +----+-------+
    | 1  | Alice |
    | 2  | Bob   |
    +----+-------+

The first CSV row is treated as the header row.
"""

import csv
import io
import re
from typing import List

TABLE_MARKER = "+---"

_BORDER_RE = re.compile(r"^\+(?:-+\+)+$")


class ConversionError(ValueError):
    """Raised when input cannot be converted."""


def is_table(text: str) -> bool:
    """Return True if ``text`` looks like an ASCII-art table rather than CSV."""
    return text.lstrip().startswith(TABLE_MARKER)


def convert(text: str) -> str:
    """Convert ``text`` in whichever direction its format implies."""
    if not text.strip():
        raise ConversionError("input is empty")
    if is_table(text):
        return table_to_csv(text)
    return csv_to_table(text)


def csv_to_table(text: str) -> str:
    """Render CSV ``text`` as a MySQL-style ASCII table."""
    rows = _parse_csv(text)

    for line_no, row in rows:
        for cell in row:
            if "\n" in cell or "\r" in cell:
                raise ConversionError(
                    f"CSV record {line_no}: cells containing line breaks "
                    "cannot be shown in a table"
                )

    header_len = len(rows[0][1])
    for line_no, row in rows[1:]:
        if len(row) != header_len:
            raise ConversionError(
                f"CSV record {line_no}: expected {header_len} fields "
                f"(to match the header) but found {len(row)}"
            )

    cells = [row for _, row in rows]
    # A minimum width of 1 keeps every border starting with "+---", so the
    # output is always detected as a table when fed back in.
    widths = [max(1, *(len(row[i]) for row in cells)) for i in range(header_len)]

    border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def render(row: List[str]) -> str:
        return "|" + "|".join(f" {cell.ljust(w)} " for cell, w in zip(row, widths)) + "|"

    lines = [border, render(cells[0]), border]
    lines.extend(render(row) for row in cells[1:])
    lines.append(border)
    return "\n".join(lines) + "\n"


def table_to_csv(text: str) -> str:
    """Convert a MySQL-style ASCII table back to CSV text."""
    lines = [
        (line_no, line.strip())
        for line_no, line in enumerate(text.splitlines(), start=1)
        if line.strip()
    ]
    if not lines:
        raise ConversionError("input is empty")

    first_no, border = lines[0]
    if not _BORDER_RE.match(border):
        raise ConversionError(f"line {first_no}: malformed table border")

    # Column boundaries are the positions of '+' in the border line; slicing
    # by position (rather than splitting on '|') lets cells contain '|'.
    separators = [i for i, ch in enumerate(border) if ch == "+"]

    if len(lines) < 4:
        raise ConversionError(
            "incomplete table: expected a border, a header row, a border "
            "and a closing border"
        )

    header_no, header = lines[1]
    if lines[2][1] != border:
        raise ConversionError(
            f"line {lines[2][0]}: expected a border line after the header row"
        )
    last_no, last = lines[-1]
    if last != border:
        raise ConversionError(
            f"line {last_no}: expected the table to end with a border line"
        )

    records = [_split_row(header_no, header, border, separators)]
    for line_no, line in lines[3:-1]:
        if _BORDER_RE.match(line):
            raise ConversionError(f"line {line_no}: unexpected border line")
        records.append(_split_row(line_no, line, border, separators))

    out = io.StringIO()
    csv.writer(out, lineterminator="\n").writerows(records)
    return out.getvalue()


def _parse_csv(text: str):
    """Return a list of (record_number, row) pairs, skipping blank lines."""
    reader = csv.reader(io.StringIO(text), strict=True)
    rows = []
    try:
        for row in reader:
            if row:
                rows.append((reader.line_num, row))
    except csv.Error as exc:
        raise ConversionError(f"CSV line {reader.line_num}: {exc}") from exc
    if not rows:
        raise ConversionError("input is empty")
    return rows


def _split_row(line_no: int, line: str, border: str, separators: List[int]) -> List[str]:
    if len(line) != len(border) or any(line[i] != "|" for i in separators):
        raise ConversionError(
            f"line {line_no}: row does not line up with the table border"
        )
    return [
        line[start + 1 : end].strip()
        for start, end in zip(separators, separators[1:])
    ]
