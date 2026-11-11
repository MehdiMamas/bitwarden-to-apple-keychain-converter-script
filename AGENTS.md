# AGENTS.md

## What it is
A single Python 3 script (`convert.py`, no dependencies) that turns a Bitwarden CSV export into a Chrome-importable CSV, as a bridge into Safari and iCloud Keychain. README.md has the import steps.

## Run
`python3 convert.py <your_bitwarden_export.csv>` writes `chrome_import.csv` (website logins only) and `multi_site_entries.txt` (entries that had several URLs; only the first is imported). It refuses to overwrite existing outputs unless `--force` is passed.

## Gotchas
- Inputs and outputs contain credentials. `*.csv` and `multi_site_entries.txt` are gitignored; never commit them or paste their contents anywhere.
- Passkeys cannot be converted via CSV.
- Tests: `python3 -m unittest discover -s tests -v` (stdlib only, fake data in `tests/fixtures/`, the one CSV allowed in git). CI runs them on Linux, macOS and Windows.
- `docs/images/demo.png` and `.github/social-preview.png` are rendered from HTML with headless Chromium; the social preview is uploaded by hand in Settings > Social preview.
