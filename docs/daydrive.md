# DayDrive

DayDrive is now an execution CLI, not just a tracker.

## Core behavior
- All new tasks are command tasks.
- Tasks can run automatically.
- Persistent day logs and review reports.

## Commands
- `python -m daydrive.cli start`
- `python -m daydrive.cli add "python -m unittest discover -s tests -p 'test_*.py'" --name "Run tests"`
- `python -m daydrive.cli add "npm run build"`
- `python -m daydrive.cli run`
- `python -m daydrive.cli run --limit 1`
- `python -m daydrive.cli done 2`
- `python -m daydrive.cli review`

## What `run` does
- Finds pending command tasks.
- Executes each command in current working directory.
- Records return code and output tail.
- Marks task `done` on success or `failed` on non-zero exit.

## Storage
By default DayDrive writes to `~/.daydrive`:
- `days/YYYY-MM-DD.json`
- `reports/YYYY-MM-DD-review.md`

Set a custom location with `DAYDRIVE_HOME`.
