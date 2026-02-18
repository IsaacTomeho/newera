from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .core import (
    DailyStore,
    add_note,
    add_task,
    build_review,
    execute_pending_commands,
    list_tasks,
    mark_done,
    summarize_tasks,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DayDrive: a daily command center for execution")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("start", help="Initialize today and print morning brief")

    add = sub.add_parser("add", help="Add a task for today")
    add.add_argument("text", help="Task text")
    add.add_argument(
        "--kind",
        choices=["manual", "command"],
        default="manual",
        help="Task type: manual tracking or executable command",
    )
    add.add_argument("--cmd", default="", help="Shell command to run for command tasks")

    note = sub.add_parser("note", help="Capture a quick note")
    note.add_argument("text", help="Note text")

    done = sub.add_parser("done", help="Mark a task done")
    done.add_argument("task_id", type=int, help="Task ID")

    sub.add_parser("list", help="List today's tasks")

    run = sub.add_parser("run", help="Execute pending command tasks")
    run.add_argument("--all", action="store_true", help="Run all pending command tasks")
    run.add_argument("--limit", type=int, default=1, help="Max pending command tasks to run")
    run.add_argument("--timeout", type=int, default=600, help="Command timeout in seconds")

    sub.add_parser("review", help="Generate end-of-day review markdown")

    return parser.parse_args()


def cmd_start(store: DailyStore) -> int:
    today = date.today()
    payload = store.load_or_create(today)
    done, total = summarize_tasks(payload)
    print(f"DayDrive ready for {today.isoformat()}")
    print(f"Tasks complete: {done}/{total}")
    print(list_tasks(payload))
    return 0


def cmd_add(store: DailyStore, text: str, kind: str, cmd: str) -> int:
    today = date.today()
    payload = store.load_or_create(today)
    payload = add_task(payload, text, kind=kind, command=cmd)
    store.save(today, payload)
    task = payload["tasks"][-1]
    print(f"Added task #{task['id']}: {text}")
    if task.get("kind") == "command":
        print(f"Command: {task.get('command')}")
    return 0


def cmd_note(store: DailyStore, text: str) -> int:
    today = date.today()
    payload = store.load_or_create(today)
    payload = add_note(payload, text)
    store.save(today, payload)
    print("Note captured")
    return 0


def cmd_done(store: DailyStore, task_id: int) -> int:
    today = date.today()
    payload = store.load_or_create(today)
    payload, found = mark_done(payload, task_id)
    if not found:
        print(f"Task {task_id} not found")
        return 1
    store.save(today, payload)
    print(f"Task {task_id} marked done")
    return 0


def cmd_list(store: DailyStore) -> int:
    payload = store.load_or_create(date.today())
    print(list_tasks(payload))
    return 0


def cmd_run(store: DailyStore, run_all: bool, limit: int, timeout: int) -> int:
    today = date.today()
    payload = store.load_or_create(today)
    payload, results = execute_pending_commands(
        payload,
        cwd=Path.cwd(),
        run_all=run_all,
        limit=max(limit, 1),
        timeout_seconds=max(timeout, 1),
    )
    store.save(today, payload)

    if not results:
        print("No pending command tasks to run")
        return 0

    failures = 0
    for result in results:
        print(
            f"Task {result['id']}: {result['status']} (rc={result['returncode']}) - {result['text']}"
        )
        if result["status"] != "done":
            failures += 1

    return 1 if failures else 0


def cmd_review(store: DailyStore) -> int:
    today = date.today()
    payload = store.load_or_create(today)
    report = build_review(payload, Path.cwd())
    output = store.reports_dir() / f"{today.isoformat()}-review.md"
    output.write_text(report, encoding="utf-8")
    print(f"Review saved: {output}")
    print(report)
    return 0


def main() -> int:
    args = parse_args()
    store = DailyStore.from_env()

    if args.command == "start":
        return cmd_start(store)
    if args.command == "add":
        return cmd_add(store, args.text, args.kind, args.cmd)
    if args.command == "note":
        return cmd_note(store, args.text)
    if args.command == "done":
        return cmd_done(store, args.task_id)
    if args.command == "list":
        return cmd_list(store)
    if args.command == "run":
        return cmd_run(store, args.all, args.limit, args.timeout)
    if args.command == "review":
        return cmd_review(store)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
