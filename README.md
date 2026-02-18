# NewEra Experiments

This repository contains autonomous product experiments and implementation sprints.

## Current product: DayDrive
**DayDrive** is a daily execution CLI that can run your command tasks automatically.

## DayDrive features
- Start your day with a persistent workspace.
- Add manual tasks for planning.
- Add command tasks that actually execute.
- Run pending command tasks and capture outcomes.
- Generate end-of-day reviews with failures and git snapshot.

## Usage
```bash
python -m daydrive.cli start
python -m daydrive.cli add "Draft launch copy"
python -m daydrive.cli add "Run tests" --kind command --cmd "python -m unittest discover -s tests -p 'test_*.py'"
python -m daydrive.cli run
python -m daydrive.cli list
python -m daydrive.cli review
```

## Data location
- Default: `~/.daydrive`
- Override: set `DAYDRIVE_HOME`

## Validation
```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Other assets in repo
- MergeGuard prototype: `mergeguard/`
- Landing MVP: `landing/`
- Experiment reports: `reports/`
