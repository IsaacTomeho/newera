# DayDrive

DayDrive is a daily execution CLI designed for low-friction personal operation.

## Why this pivot
The previous concept was infrastructure-heavy. DayDrive is intentionally simple and immediately useful every day.

## Commands
- `python -m daydrive.cli start`
- `python -m daydrive.cli add "Finalize onboarding copy"`
- `python -m daydrive.cli note "Customer mentioned confusing setup screen"`
- `python -m daydrive.cli done 1`
- `python -m daydrive.cli list`
- `python -m daydrive.cli review`

## Storage
By default DayDrive writes to `~/.daydrive`:
- `days/YYYY-MM-DD.json`
- `reports/YYYY-MM-DD-review.md`

Set a custom location with `DAYDRIVE_HOME`.

## Daily workflow
1. Run `start` in the morning.
2. Capture tasks and notes all day (`add`, `note`).
3. Mark progress with `done`.
4. Run `review` at end of day to produce a compact daily report.
