"""Convert CSV to MySQL-style ASCII tables and back again."""

from csv_to_table.converter import (
    ConversionError,
    convert,
    csv_to_table,
    is_table,
    table_to_csv,
)

__version__ = "0.1.0"

__all__ = [
    "ConversionError",
    "convert",
    "csv_to_table",
    "is_table",
    "table_to_csv",
    "__version__",
]
