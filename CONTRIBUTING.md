# Contributing

Thanks for helping out! This is a single, dependency-free Python script, so contributing is quick.

## Ground rules

- **Never attach a real export.** Bitwarden exports and `chrome_import.csv` contain your passwords in plain text. Use fake data like `tests/fixtures/sample_export.csv` in issues and PRs.
- Keep `convert.py` standard-library only, working on Python 3.9+.

## Setup and tests

```
git clone https://github.com/MehdiMamas/bitwarden-to-apple-keychain-converter-script.git
cd bitwarden-to-apple-keychain-converter-script
python3 -m unittest discover -s tests -v
```

CI runs the same tests on Linux, macOS and Windows.

## Pull requests

1. Fork and branch from `master`.
2. Add or update a test in `tests/` for the behaviour you change.
3. Update `README.md` if the usage or import steps change.
4. Open the PR and describe what changed and why.
