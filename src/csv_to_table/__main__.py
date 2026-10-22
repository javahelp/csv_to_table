"""Allow running as ``python -m csv_to_table``."""

import sys

from csv_to_table.cli import main

sys.exit(main())
