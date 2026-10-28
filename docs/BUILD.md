# Build, test and release

Python 3.9+ runs the app source; the acceptance test suite ran on 3.13. Install development dependencies into a virtual environment. They are not runtime dependencies and must never be bundled into the app.

```bash
python -m venv .venv
# Activate .venv using your platform's normal activation command.
python -m pip install -r requirements-dev.txt
python tools/build_assets.py
python -m unittest discover -s tests -v
python tools/check_package.py
python tools/package.py
```

`build_assets.py` creates the six dashboards and two data models. Edit that generator when changing generated searches. `build_brand.py` regenerates the PNG assets from the original geometric eye/pulse mark; its font lookup supports Windows Segoe UI and Linux DejaVu Sans. Brand generation requires Pillow and is unnecessary for routine packaging because the rendered assets are committed.

The package contains only the `zabbix_vision` directory and excludes `local/`, bytecode and checkpoints. `tools/package.py` includes the public guide and release notes under the package README directory. The archive has deterministic timestamps and ownership; the adjacent SHA-256 file verifies the install artifact.

## Acceptance testing

Use `lab/compose.yaml` with an untracked `.env`, a generated DB password and separate Compose project names. Frontends bind to loopback. The agent configuration allows only the harmless test command; do not generalize it into a production execution policy.

Run a real profile/input against each supported Zabbix generation, inspect stream health, verify known authentication events, exercise custom CA/mTLS locally and dispatch every dashboard search on Splunk. An app rename changes its credential/checkpoint namespace; protocol tests do not replace a live installation acceptance test. See VALIDATION.md for the evidence actually collected.

## AppInspect and Splunkbase

Install Splunk AppInspect in its own supported validation environment and run it against the exact final archive:

```bash
splunk-appinspect inspect dist/zabbix_vision-1.0.0.tar.gz --mode precert --output-file dist/appinspect.json
```

Review failures, errors, warnings and manual checks. Do not convert a local result into a claim of Splunkbase approval or Splunk Cloud certification. The submission copy is in `SPLUNKBASE.md`. The first release still needs Splunk's marketplace review.

The GitHub validation workflow runs tests and static package checks for pull requests and pushes. A tagged source revision produces the install archive and checksum as workflow artifacts. Releases are published from a reviewed package with the release notes, not from the GitHub source ZIP.
