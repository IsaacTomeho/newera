from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .core import DailyStore, add_note, add_task, build_review, list_tasks, mark_done, summarize_tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DayDrive: a daily command center for execution")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("start", help="Initialize today and print morning brief")

    add = sub.add_parser("add", help="Add a task for today")
    add.add_argument("text", help="Task text")

    note = sub.add_parser("note", help="Capture a quick note")
    note.add_argument("text", help="Note text")

    done = sub.add_parser("done", help="Mark a task done")
    done.add_argument("task_id", type=int, help="Task ID")

    sub.add_parser("list", help="List today's tasks")
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


def cmd_add(store: DailyStore, text: str) -> int:
    today = date.today()
    payload = store.load_or_create(today)
    payload = add_task(payload, text)
    store.save(today, payload)
    print(f"Added task #{payload['tasks'][-1]['id']}: {text}")
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
        return cmd_add(store, args.text)
    if args.command == "note":
        return cmd_note(store, args.text)
    if args.command == "done":
        return cmd_done(store, args.task_id)
    if args.command == "list":
        return cmd_list(store)
    if args.command == "review":
        return cmd_review(store)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
