import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "sample_export.csv"


class ConvertTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.export = self.tmp / "export.csv"
        shutil.copy(FIXTURE, self.export)
        self.result = subprocess.run(
            [sys.executable, str(ROOT / "convert.py"), str(self.export)],
            capture_output=True, text=True, check=True,
        )

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_keeps_only_logins(self):
        with open(self.tmp / "chrome_import.csv", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[0], ["username", "password", "url"])
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[1], ["alice@example.com", "correct-horse-1", "https://mail.example.com"])

    def test_first_url_imported_and_extra_listed(self):
        with open(self.tmp / "chrome_import.csv", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[2][2], "https://shop.example.com")
        multi = (self.tmp / "multi_site_entries.txt").read_text(encoding="utf-8")
        self.assertIn("https://store.example.com", multi)

    def test_empty_username_gets_placeholder(self):
        with open(self.tmp / "chrome_import.csv", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[3][0], "aaa")

    def test_empty_password_and_url_get_placeholder(self):
        export = self.tmp / "bom.csv"
        export.write_text(
            "folder,favorite,type,name,notes,fields,reprompt,login_uri,login_username,login_password,login_totp\n"
            ",,login,No pass,,,0,,bob,,\n"
            ",,login,Empty,,,0,,,,\n",
            encoding="utf-8-sig",
        )
        subprocess.run([sys.executable, str(ROOT / "convert.py"), str(export)],
                       capture_output=True, text=True, check=True)
        with open(self.tmp / "chrome_import.csv", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[1:], [["bob", "aaa", "aaa"]])

    def test_summary_output(self):
        self.assertIn("3 passwords written", self.result.stdout)
        self.assertIn("Skipped 2", self.result.stdout)

    def test_missing_file(self):
        r = subprocess.run([sys.executable, str(ROOT / "convert.py"), str(self.tmp / "nope.csv")],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
