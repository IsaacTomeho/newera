from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass
class DailyStore:
    base_dir: Path

    @classmethod
    def from_env(cls) -> "DailyStore":
        root = os.environ.get("DAYDRIVE_HOME", "")
        if root:
            return cls(Path(root).expanduser())
        return cls(Path.home() / ".daydrive")

    def day_path(self, day: date) -> Path:
        return self.base_dir / "days" / f"{day.isoformat()}.json"

    def reports_dir(self) -> Path:
        return self.base_dir / "reports"

    def ensure(self) -> None:
        (self.base_dir / "days").mkdir(parents=True, exist_ok=True)
        self.reports_dir().mkdir(parents=True, exist_ok=True)

    def load_or_create(self, day: date) -> dict:
        self.ensure()
        path = self.day_path(day)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))

        payload = {
            "date": day.isoformat(),
            "tasks": [],
            "notes": [],
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.save(day, payload)
        return payload

    def save(self, day: date, payload: dict) -> None:
        payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.day_path(day).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def add_task(payload: dict, text: str) -> dict:
    next_id = max((task["id"] for task in payload["tasks"]), default=0) + 1
    payload["tasks"].append(
        {
            "id": next_id,
            "text": text.strip(),
            "done": False,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    return payload


def add_note(payload: dict, text: str) -> dict:
    payload["notes"].append(
        {
            "text": text.strip(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    return payload


def mark_done(payload: dict, task_id: int) -> tuple[dict, bool]:
    for task in payload["tasks"]:
        if task["id"] == task_id:
            task["done"] = True
            task["done_at"] = datetime.now().isoformat(timespec="seconds")
            return payload, True
    return payload, False


def summarize_tasks(payload: dict) -> tuple[int, int]:
    total = len(payload["tasks"])
    done = len([task for task in payload["tasks"] if task["done"]])
    return done, total


def list_tasks(payload: dict) -> str:
    if not payload["tasks"]:
        return "No tasks yet. Add one with: daydrive add \"task\""

    lines = []
    for task in payload["tasks"]:
        status = "x" if task["done"] else " "
        lines.append(f"[{status}] {task['id']}. {task['text']}")
    return "\n".join(lines)


def _run_git(cwd: Path, args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def git_snapshot(cwd: Path) -> dict:
    branch = _run_git(cwd, ["branch", "--show-current"])
    status = _run_git(cwd, ["status", "--porcelain"])
    commit_lines = _run_git(cwd, ["log", "--since=midnight", "--oneline", "--max-count", "5"])
    return {
        "branch": branch or "n/a",
        "dirty_files": len([line for line in status.splitlines() if line.strip()]),
        "today_commits": [line for line in commit_lines.splitlines() if line.strip()],
    }


def build_review(payload: dict, cwd: Path) -> str:
    done, total = summarize_tasks(payload)
    open_tasks = [task for task in payload["tasks"] if not task["done"]]
    notes = payload["notes"]
    git = git_snapshot(cwd)

    lines = [
        f"# DayDrive Review - {payload['date']}",
        "",
        "## Task Completion",
        f"- Completed: {done}/{total}",
        f"- Remaining: {max(total - done, 0)}",
        "",
        "## Remaining Tasks",
    ]

    if open_tasks:
        lines.extend([f"- {task['id']}. {task['text']}" for task in open_tasks])
    else:
        lines.append("- None")

    lines.extend(["", "## Notes Captured"])
    if notes:
        lines.extend([f"- {note['text']}" for note in notes[-8:]])
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Git Snapshot",
        f"- Branch: {git['branch']}",
        f"- Dirty files: {git['dirty_files']}",
        f"- Commits since midnight: {len(git['today_commits'])}",
    ])

    if git["today_commits"]:
        lines.append("- Recent commits:")
        lines.extend([f"  - {line}" for line in git["today_commits"]])

    return "\n".join(lines) + "\n"
