import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from csv_to_table import __version__
from csv_to_table.cli import EXIT_ERROR, EXIT_OK, EXIT_USAGE, main

SRC_DIR = Path(__file__).resolve().parent.parent / "src"


class FakeTty(io.StringIO):
    def isatty(self):
        return True


class BadBytesStdin(io.StringIO):
    def read(self, *args):
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")


def run(text, argv=None, stdin=None):
    out, err = io.StringIO(), io.StringIO()
    code = main(argv or [], stdin=stdin or io.StringIO(text), stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def test_csv_to_table(self):
        code, out, err = run("a,b\n1,2\n")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, "+---+---+\n| a | b |\n+---+---+\n| 1 | 2 |\n+---+---+\n")
        self.assertEqual(err, "")

    def test_table_to_csv(self):
        code, out, err = run("+---+\n| a |\n+---+\n| 1 |\n+---+\n")
        self.assertEqual((code, out, err), (EXIT_OK, "a\n1\n", ""))

    def test_conversion_error_reported(self):
        code, out, err = run("a,b\n1\n")
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("csv-to-table: error: CSV record 2"))

    def test_empty_input(self):
        code, out, err = run("")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("input is empty", err)

    def test_tty_stdin_rejected(self):
        code, out, err = run("", stdin=FakeTty())
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("no input", err)

    def test_undecodable_input(self):
        code, out, err = run("", stdin=BadBytesStdin())
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("not valid text", err)

    def test_unknown_argument(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            code, out, _ = run("a\n", argv=["--bogus"])
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("unrecognized arguments: --bogus", buf.getvalue())
        self.assertEqual(out, "")

    def test_help(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code, _, _ = run("", argv=["--help"])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("usage: csv-to-table", buf.getvalue())

    def test_version(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code, _, _ = run("", argv=["--version"])
        self.assertEqual(code, EXIT_OK)
        self.assertIn(__version__, buf.getvalue())


class ModuleInvocationTests(unittest.TestCase):
    """End-to-end checks through a real subprocess and real pipes."""

    def invoke(self, data: bytes, *args):
        env = dict(os.environ, PYTHONPATH=str(SRC_DIR))
        return subprocess.run(
            [sys.executable, "-m", "csv_to_table", *args],
            input=data, capture_output=True, env=env, timeout=30,
        )

    def test_success(self):
        proc = self.invoke(b"a,b\n1,2\n")
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(proc.stdout.startswith(b"+---+---+"))
        self.assertEqual(proc.stderr, b"")

    def test_failure_has_no_traceback(self):
        proc = self.invoke(b"+---+\nnope\n")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, b"")
        self.assertIn(b"csv-to-table: error:", proc.stderr)
        self.assertNotIn(b"Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
