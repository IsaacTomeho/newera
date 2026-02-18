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
            payload = json.loads(path.read_text(encoding="utf-8"))
            normalize_payload(payload)
            return payload

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


def normalize_payload(payload: dict) -> dict:
    payload.setdefault("tasks", [])
    payload.setdefault("notes", [])

    for task in payload["tasks"]:
        task.setdefault("kind", "manual")
        task.setdefault("command", "")

        done_flag = bool(task.get("done", False))
        if "status" not in task:
            task["status"] = "done" if done_flag else "pending"

        # Keep backward-compatibility with old structure.
        task["done"] = task["status"] == "done"
        task.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))

    return payload


def add_task(payload: dict, text: str, command: str = "") -> dict:
    normalize_payload(payload)
    next_id = max((task["id"] for task in payload["tasks"]), default=0) + 1

    command_text = command.strip() or text.strip()

    payload["tasks"].append(
        {
            "id": next_id,
            "text": text.strip(),
            "kind": "command",
            "command": command_text,
            "status": "pending",
            "done": False,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    return payload


def add_note(payload: dict, text: str) -> dict:
    payload.setdefault("notes", [])
    payload["notes"].append(
        {
            "text": text.strip(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    return payload


def mark_done(payload: dict, task_id: int) -> tuple[dict, bool]:
    normalize_payload(payload)
    for task in payload["tasks"]:
        if task["id"] == task_id:
            task["status"] = "done"
            task["done"] = True
            task["done_at"] = datetime.now().isoformat(timespec="seconds")
            return payload, True
    return payload, False


def summarize_tasks(payload: dict) -> tuple[int, int]:
    normalize_payload(payload)
    total = len(payload["tasks"])
    done = len([task for task in payload["tasks"] if task["status"] == "done"])
    return done, total


def list_tasks(payload: dict) -> str:
    normalize_payload(payload)
    if not payload["tasks"]:
        return "No tasks yet. Add one with: daydrive add \"echo hello\""

    icons = {"pending": " ", "running": "~", "done": "x", "failed": "!"}
    lines = []
    for task in payload["tasks"]:
        status = task.get("status", "pending")
        icon = icons.get(status, " ")
        suffix = ""
        if task.get("kind") == "command":
            suffix = " [command]"
        lines.append(f"[{icon}] {task['id']}. {task['text']}{suffix}")
    return "\n".join(lines)


def execute_pending_commands(
    payload: dict,
    cwd: Path,
    run_all: bool = False,
    limit: int = 1,
    timeout_seconds: int = 600,
) -> tuple[dict, list[dict]]:
    normalize_payload(payload)
    results: list[dict] = []
    executed = 0

    for task in payload["tasks"]:
        if task.get("kind") != "command":
            continue
        if task.get("status") not in {"pending", "failed"}:
            continue
        if not task.get("command"):
            continue

        if not run_all and executed >= limit:
            break

        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat(timespec="seconds")

        try:
            proc = subprocess.run(
                task["command"],
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
            stdout_tail = "\n".join(proc.stdout.splitlines()[-20:]).strip()
            stderr_tail = "\n".join(proc.stderr.splitlines()[-20:]).strip()

            ok = proc.returncode == 0
            task["status"] = "done" if ok else "failed"
            task["done"] = ok
            if ok:
                task["done_at"] = datetime.now().isoformat(timespec="seconds")

            task["last_run"] = {
                "returncode": proc.returncode,
                "stdout_tail": stdout_tail,
                "stderr_tail": stderr_tail,
                "finished_at": datetime.now().isoformat(timespec="seconds"),
            }
            results.append(
                {
                    "id": task["id"],
                    "text": task["text"],
                    "returncode": proc.returncode,
                    "status": task["status"],
                }
            )
        except subprocess.TimeoutExpired:
            task["status"] = "failed"
            task["done"] = False
            task["last_run"] = {
                "returncode": -1,
                "stdout_tail": "",
                "stderr_tail": f"Command timed out after {timeout_seconds}s",
                "finished_at": datetime.now().isoformat(timespec="seconds"),
            }
            results.append(
                {
                    "id": task["id"],
                    "text": task["text"],
                    "returncode": -1,
                    "status": "failed",
                }
            )

        executed += 1

    return payload, results


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
    normalize_payload(payload)
    done, total = summarize_tasks(payload)
    open_tasks = [task for task in payload["tasks"] if task["status"] in {"pending", "running"}]
    failed_tasks = [task for task in payload["tasks"] if task["status"] == "failed"]
    notes = payload["notes"]
    git = git_snapshot(cwd)

    lines = [
        f"# DayDrive Review - {payload['date']}",
        "",
        "## Task Completion",
        f"- Completed: {done}/{total}",
        f"- Remaining: {max(total - done, 0)}",
        f"- Failed: {len(failed_tasks)}",
        "",
        "## Remaining Tasks",
    ]

    if open_tasks:
        lines.extend([f"- {task['id']}. {task['text']}" for task in open_tasks])
    else:
        lines.append("- None")

    lines.extend(["", "## Failed Task Runs"])
    if failed_tasks:
        for task in failed_tasks:
            error = task.get("last_run", {}).get("stderr_tail", "")
            lines.append(f"- {task['id']}. {task['text']} ({error or 'no stderr captured'})")
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
        for line in git["today_commits"]:
            lines.append(f"  - {line}")

    return "\n".join(lines) + "\n"
