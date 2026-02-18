# DayDrive

DayDrive is now an execution CLI, not just a tracker.

## Core behavior
- Manual tasks for planning and tracking.
- Command tasks that can run automatically.
- Persistent day logs and review reports.

## Commands
- `python -m daydrive.cli start`
- `python -m daydrive.cli add "Write release note"`
- `python -m daydrive.cli add "Run tests" --kind command --cmd "python -m unittest discover -s tests -p 'test_*.py'"`
- `python -m daydrive.cli run`
- `python -m daydrive.cli run --all`
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
