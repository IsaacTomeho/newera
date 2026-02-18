# NewEra Experiments

This repository tracks autonomous product-discovery experiments.

## Current focus: MergeGuard
MergeGuard is a v0 AI code verification engine for pull requests. It inspects changed code files, scores risk, and outputs a report with gates and test suggestions.

## Implemented in this repo
- Landing page MVP: `landing/index.html`
- Pricing experiment and waitlist capture: `landing/script.js`
- Verification engine: `mergeguard/analyzer.py`
- CLI entrypoint: `mergeguard/cli.py`
- CI workflow for PR report generation: `.github/workflows/mergeguard.yml`
- Pilot ops docs:
  - `docs/pilot-outreach-email.md`
  - `docs/verification-report-template.md`

## Run MergeGuard locally
```bash
python -m mergeguard.cli --repo . --base HEAD~1 --head HEAD
```

JSON output:
```bash
python -m mergeguard.cli --repo . --base HEAD~1 --head HEAD --format json
```

Custom output file:
```bash
python -m mergeguard.cli --repo . --base HEAD~1 --head HEAD --output reports/mergeguard-report.md
```

## Run tests
```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Landing page
Open `landing/index.html` in a browser. Use `?variant=a` or `?variant=b` to force pricing variants.
