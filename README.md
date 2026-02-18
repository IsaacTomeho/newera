# NewEra Experiments

This repository contains autonomous product experiments and implementation sprints.

## Current daily-driver product
**DayDrive**: a zero-dependency CLI for daily planning and execution. It is designed to be used every day with minimal setup.

## DayDrive features
- Start your day with a persistent daily workspace.
- Capture tasks quickly.
- Capture notes continuously during execution.
- Mark tasks done and track completion.
- Generate an end-of-day review report with task and git activity snapshot.

## Usage
```bash
python -m daydrive.cli start
python -m daydrive.cli add "Draft launch copy"
python -m daydrive.cli note "User interview: wants fewer setup steps"
python -m daydrive.cli done 1
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
