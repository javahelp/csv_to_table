import unittest

from csv_to_table.converter import (
    ConversionError,
    convert,
    csv_to_table,
    is_table,
    table_to_csv,
)

SAMPLE_CSV = "id,name\n1,Alice\n2,Bob\n"

SAMPLE_TABLE = (
    "+----+-------+\n"
    "| id | name  |\n"
    "+----+-------+\n"
    "| 1  | Alice |\n"
    "| 2  | Bob   |\n"
    "+----+-------+\n"
)


class DetectionTests(unittest.TestCase):
    def test_table_detected(self):
        self.assertTrue(is_table(SAMPLE_TABLE))

    def test_table_detected_after_leading_whitespace(self):
        self.assertTrue(is_table("\n\n   \t" + SAMPLE_TABLE))

    def test_csv_not_detected_as_table(self):
        self.assertFalse(is_table(SAMPLE_CSV))

    def test_short_marker_is_csv(self):
        self.assertFalse(is_table("+--,x\n"))


class CsvToTableTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(csv_to_table(SAMPLE_CSV), SAMPLE_TABLE)

    def test_header_only(self):
        self.assertEqual(
            csv_to_table("a,bb\n"),
            "+---+----+\n| a | bb |\n+---+----+\n+---+----+\n",
        )

    def test_empty_cells_have_minimum_width(self):
        out = csv_to_table(",x\n,y\n")
        self.assertTrue(out.startswith("+---+---+\n"))
        self.assertIn("|   | x |", out)

    def test_quoted_fields_with_commas_and_quotes(self):
        out = csv_to_table('k,v\n"a,b","say ""hi"""\n')
        self.assertIn('| a,b | say "hi" |', out)

    def test_blank_lines_skipped(self):
        self.assertEqual(csv_to_table("id,name\n\n1,Alice\n\n2,Bob\n\n"), SAMPLE_TABLE)

    def test_crlf_input(self):
        self.assertEqual(csv_to_table(SAMPLE_CSV.replace("\n", "\r\n")), SAMPLE_TABLE)

    def test_ragged_row_rejected(self):
        with self.assertRaisesRegex(ConversionError, r"record 3: expected 2 fields .* found 3"):
            csv_to_table("a,b\n1,2\n1,2,3\n")

    def test_embedded_newline_rejected(self):
        with self.assertRaisesRegex(ConversionError, "line breaks"):
            csv_to_table('a,b\n"x\ny",2\n')

    def test_unterminated_quote_rejected(self):
        with self.assertRaisesRegex(ConversionError, "CSV line"):
            csv_to_table('a,b\n"oops,2\n')

    def test_stray_quote_rejected(self):
        with self.assertRaisesRegex(ConversionError, "CSV line 2"):
            csv_to_table('a,b\n"x"y,2\n')

    def test_empty_rejected(self):
        with self.assertRaisesRegex(ConversionError, "empty"):
            csv_to_table("\n\n")


class TableToCsvTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(table_to_csv(SAMPLE_TABLE), SAMPLE_CSV)

    def test_indented_table_and_trailing_whitespace(self):
        indented = "\n".join("    " + line + "  " for line in SAMPLE_TABLE.splitlines())
        self.assertEqual(table_to_csv("\n" + indented + "\n\n"), SAMPLE_CSV)

    def test_header_only(self):
        self.assertEqual(table_to_csv("+---+\n| a |\n+---+\n+---+\n"), "a\n")

    def test_pipe_inside_cell(self):
        table = "+-----+\n| x   |\n+-----+\n| a|b |\n+-----+\n"
        self.assertEqual(table_to_csv(table), "x\na|b\n")

    def test_special_characters_are_quoted(self):
        table = csv_to_table('k,v\n"a,b","say ""hi"""\n')
        self.assertEqual(table_to_csv(table), 'k,v\n"a,b","say ""hi"""\n')

    def test_malformed_first_border(self):
        with self.assertRaisesRegex(ConversionError, "line 1: malformed table border"):
            table_to_csv("+---x\n| a |\n+---+\n+---+\n")

    def test_too_short(self):
        with self.assertRaisesRegex(ConversionError, "incomplete table"):
            table_to_csv("+---+\n| a |\n")

    def test_missing_header_separator(self):
        with self.assertRaisesRegex(ConversionError, "line 3: expected a border line after the header"):
            table_to_csv("+---+\n| a |\n| b |\n+---+\n")

    def test_missing_closing_border(self):
        with self.assertRaisesRegex(ConversionError, "line 5: expected the table to end"):
            table_to_csv("+---+\n| a |\n+---+\n| b |\n| c |\n")

    def test_misaligned_row(self):
        with self.assertRaisesRegex(ConversionError, "line 4: row does not line up"):
            table_to_csv("+---+\n| a |\n+---+\n| bb |\n+---+\n")

    def test_wrong_column_count(self):
        with self.assertRaisesRegex(ConversionError, "line 4: row does not line up"):
            table_to_csv("+---+---+\n| a | b |\n+---+---+\n| 1     |\n+---+---+\n")

    def test_unexpected_border_in_body(self):
        with self.assertRaisesRegex(ConversionError, "line 5: unexpected border"):
            table_to_csv("+---+\n| a |\n+---+\n| 1 |\n+---+\n| 2 |\n+---+\n")


class ConvertTests(unittest.TestCase):
    def test_dispatches_csv(self):
        self.assertEqual(convert(SAMPLE_CSV), SAMPLE_TABLE)

    def test_dispatches_table(self):
        self.assertEqual(convert(SAMPLE_TABLE), SAMPLE_CSV)

    def test_round_trip(self):
        csv_text = 'name,notes\nAnn,"x, y"\n,empty first\nZoë,"a ""q"""\n'
        self.assertEqual(convert(convert(csv_text)), csv_text)

    def test_empty_input(self):
        for text in ("", "   \n\t\n"):
            with self.subTest(text=text):
                with self.assertRaisesRegex(ConversionError, "empty"):
                    convert(text)


if __name__ == "__main__":
    unittest.main()
