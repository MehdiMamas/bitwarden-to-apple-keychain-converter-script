#!/usr/bin/env python3
"""
Bitwarden CSV → Chrome/Safari Password Import Converter

Converts a Bitwarden CSV export into a CSV that Chrome can import,
which you can then import from Chrome into Safari → Keychain.

Usage:
    python3 convert.py <bitwarden_export.csv>

Output:
    chrome_import.csv (in the same directory as the input file)

Steps after running this script:
    1. Open Google Chrome
    2. Go to chrome://flags/#password-import-export → Enable import
    3. Go to chrome://settings/passwords
    4. Click the 3 dots → "Import passwords" → select chrome_import.csv
    5. Restart Chrome, verify passwords are there
    6. Open Safari → File → Import From → Google Chrome → select Passwords
    7. Passwords will sync to iCloud Keychain
"""

import csv
import sys
from pathlib import Path

PLACEHOLDER = "aaa"


def convert(input_path: str) -> None:
    input_file = Path(input_path)
    if not input_file.exists():
        sys.exit(f"File not found: {input_file}")

    output_file = input_file.parent / "chrome_import.csv"
    multi_site_file = input_file.parent / "multi_site_entries.txt"
    kept = 0
    skipped = 0
    multi_site_entries = []

    with open(input_file, newline="", encoding="utf-8-sig") as fin, \
         open(output_file, "w", newline="", encoding="utf-8") as fout:

        reader = csv.DictReader(fin)
        writer = csv.writer(fout)
        writer.writerow(["username", "password", "url"])

        for row in reader:
            if row.get("type") != "login":
                skipped += 1
                continue

            raw_uri = (row.get("login_uri") or "").strip()
            username = (row.get("login_username") or "").strip()
            password = (row.get("login_password") or "").strip()
            name = (row.get("name") or "").strip()

            if not raw_uri and not username and not password:
                skipped += 1
                continue

            uris = [u.strip() for u in raw_uri.split(",") if u.strip()] if raw_uri else [""]

            writer.writerow([
                username or PLACEHOLDER,
                password or PLACEHOLDER,
                uris[0] or PLACEHOLDER,
            ])
            kept += 1

            if len(uris) > 1:
                multi_site_entries.append((name, username, uris))

    with open(multi_site_file, "w", encoding="utf-8") as mf:
        mf.write("MULTI-SITE ENTRIES\n")
        mf.write("=" * 60 + "\n")
        mf.write("These entries had multiple websites in Bitwarden.\n")
        mf.write("The FIRST url was imported. Open Apple Passwords,\n")
        mf.write("search for the entry, and add the EXTRA urls.\n")
        mf.write("=" * 60 + "\n\n")
        for name, username, uris in multi_site_entries:
            mf.write(f"Entry:      {name}\n")
            mf.write(f"Username:   {username}\n")
            mf.write(f"Imported:   {uris[0]}\n")
            mf.write(f"Add these:\n")
            for uri in uris[1:]:
                mf.write(f"  - {uri}\n")
            mf.write("\n" + "-" * 60 + "\n\n")

    print(f"Done — {kept} passwords written to {output_file}")
    if multi_site_entries:
        print(f"Found {len(multi_site_entries)} multi-site entries — see {multi_site_file}")
    if skipped:
        print(f"Skipped {skipped} non-login entries (notes, cards, etc.)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"Usage: python3 {sys.argv[0]} <bitwarden_export.csv>")
    convert(sys.argv[1])
