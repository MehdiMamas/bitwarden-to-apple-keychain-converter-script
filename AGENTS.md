# AGENTS.md

## What it is
A single Python 3 script (`convert.py`, no dependencies) that turns a Bitwarden CSV export into a Chrome-importable CSV, as a bridge into Safari and iCloud Keychain. README.md has the import steps.

## Run
`python3 convert.py <your_bitwarden_export.csv>` writes `chrome_import.csv` (website logins only) and `multi_site_entries.txt` (entries that had several URLs; only the first is imported).

## Gotchas
- Inputs and outputs contain credentials. `*.csv` and `multi_site_entries.txt` are gitignored; never commit them or paste their contents anywhere.
- Passkeys cannot be converted via CSV.
- No tests, build or CI in this repo.
