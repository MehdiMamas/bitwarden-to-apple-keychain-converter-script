import csv
import os
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
        for p in [self.tmp / "chrome_import.csv", self.tmp / "multi_site_entries.txt"]:
            if p.exists():
                p.unlink()

        subprocess.run([sys.executable, str(ROOT / "convert.py"), str(export)],
                        capture_output=True, text=True, check=True)
        with open(self.tmp / "chrome_import.csv", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[1:], [["bob", "aaa", "aaa"]])

    def test_summary_output(self):
        self.assertIn("3 passwords written", self.result.stdout)
        self.assertIn("Found 1 multi-site entry — see", self.result.stdout)
        self.assertIn("Skipped 2 non-login entries (notes, cards, etc.)", self.result.stdout)

    def test_empty_login_skipped_and_pluralization(self):
        export = self.tmp / "skips.csv"
        export.write_text(
            "folder,favorite,type,name,notes,fields,reprompt,login_uri,login_username,login_password,login_totp\n"
            ",,login,Valid,,,0,https://example.com,user,pass,\n"
            ",,login,Empty 1,,,0,,,,\n"
            ",,note,Note 1,,,0,,,,\n",
            encoding="utf-8-sig",
        )
        res = subprocess.run([sys.executable, str(ROOT / "convert.py"), str(export), "--force"],
                             capture_output=True, text=True, check=True)
        self.assertIn("Skipped 1 empty login", res.stdout)
        self.assertIn("Skipped 1 non-login entry (notes, cards, etc.)", res.stdout)

        export_plural = self.tmp / "skips_plural.csv"
        export_plural.write_text(
            "folder,favorite,type,name,notes,fields,reprompt,login_uri,login_username,login_password,login_totp\n"
            ",,login,Valid,,,0,https://example.com,user,pass,\n"
            ",,login,Empty 1,,,0,,,,\n"
            ",,login,Empty 2,,,0,,,,\n",
            encoding="utf-8-sig",
        )
        res_plural = subprocess.run([sys.executable, str(ROOT / "convert.py"), str(export_plural), "--force"],
                                    capture_output=True, text=True, check=True)
        self.assertIn("Skipped 2 empty logins", res_plural.stdout)

    def test_missing_file(self):
        r = subprocess.run([sys.executable, str(ROOT / "convert.py"), str(self.tmp / "nope.csv")],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)

    
    def test_refuses_to_overwrite_existing_files(self):
        r = subprocess.run(
            [sys.executable, str(ROOT / "convert.py"), str(self.export)],
            capture_output=True, text=True
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Warning: Output files already exist", r.stderr + r.stdout)

    def test_force_overwrites_existing_files(self):
        (self.tmp / "chrome_import.csv").write_text("stale\n", encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(ROOT / "convert.py"), str(self.export), "--force"],
            capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("stale", (self.tmp / "chrome_import.csv").read_text(encoding="utf-8"))

    def test_force_before_path(self):
        r = subprocess.run(
            [sys.executable, str(ROOT / "convert.py"), "--force", str(self.export)],
            capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_refuses_input_named_like_output(self):
        src = self.tmp / "chrome_import.csv"
        original = self.export.read_bytes()
        src.write_bytes(original)
        r = subprocess.run(
            [sys.executable, str(ROOT / "convert.py"), str(src), "--force"],
            capture_output=True, text=True
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(src.read_bytes(), original)


class OutputOptionTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.tmp = Path(temporary.name)
        self.source = self.tmp / "source"
        self.source.mkdir()
        self.export = self.source / "export.csv"
        shutil.copy(FIXTURE, self.export)

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "convert.py"), *map(str, args)],
            cwd=self.tmp, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

    def test_custom_path_keeps_companion_report_next_to_input(self):
        destination = self.tmp / "輸出 folder"
        destination.mkdir()
        output = destination / "chosen.csv"
        result = self.run_cli("--output", output, self.export)
        self.assertEqual(result.returncode, 0, result.stderr)
        with output.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        self.assertEqual(rows[0], ["username", "password", "url"])
        self.assertEqual(rows[1], ["alice@example.com", "correct-horse-1", "https://mail.example.com"])
        self.assertEqual(len(rows), 4)
        self.assertFalse((self.source / "chrome_import.csv").exists())
        self.assertTrue((self.source / "multi_site_entries.txt").exists())
        self.assertFalse((destination / "multi_site_entries.txt").exists())

    def test_relative_output_is_relative_to_working_directory(self):
        result = self.run_cli(self.export, "--output", "chosen.csv")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.tmp / "chosen.csv").is_file())
        self.assertFalse((self.source / "chosen.csv").exists())

    def test_existing_custom_output_requires_force(self):
        output = self.tmp / "chosen.csv"
        output.write_text("keep this\n", encoding="utf-8")
        result = self.run_cli(self.export, "--output", output)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(encoding="utf-8"), "keep this\n")
        self.assertFalse((self.source / "multi_site_entries.txt").exists())
        original = self.export.read_bytes()
        result = self.run_cli("--force", self.export, "--output", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(output.read_text(encoding="utf-8").startswith("username,password,url"))
        self.assertEqual(self.export.read_bytes(), original)

    def test_force_cannot_overwrite_input_or_companion_report_with_csv(self):
        original = self.export.read_bytes()
        for output in (self.export, self.source / "multi_site_entries.txt"):
            with self.subTest(output=output.name):
                result = self.run_cli(self.export, "--output", output, "--force")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.export.read_bytes(), original)
                self.assertFalse((self.source / "multi_site_entries.txt").exists())

    def test_hardlinked_input_is_protected_even_with_force(self):
        output = self.tmp / "linked.csv"
        try:
            os.link(self.export, output)
        except OSError as error:
            self.skipTest(f"hardlinks unavailable: {error}")
        original = self.export.read_bytes()
        result = self.run_cli(self.export, "--output", output, "--force")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.export.read_bytes(), original)

    def test_missing_output_value_is_usage_error(self):
        result = self.run_cli(self.export, "--output")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.source / "chrome_import.csv").exists())


if __name__ == "__main__":
    unittest.main()
