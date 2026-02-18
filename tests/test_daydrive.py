import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from daydrive.core import (
    DailyStore,
    add_note,
    add_task,
    build_review,
    execute_pending_commands,
    list_tasks,
    mark_done,
    normalize_payload,
)


class DayDriveCoreTests(unittest.TestCase):
    def test_store_create_add_and_complete_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = DailyStore(Path(tmp))
            today = date.today()
            payload = store.load_or_create(today)

            payload = add_task(payload, "Ship feature")
            payload = add_note(payload, "Customer asked for simpler UX")
            payload, found = mark_done(payload, 1)
            self.assertTrue(found)

            store.save(today, payload)
            saved = json.loads(store.day_path(today).read_text(encoding="utf-8"))
            self.assertEqual(len(saved["tasks"]), 1)
            self.assertEqual(saved["tasks"][0]["status"], "done")
            self.assertEqual(len(saved["notes"]), 1)

    def test_mark_done_not_found(self) -> None:
        payload = {"tasks": []}
        _, found = mark_done(payload, 99)
        self.assertFalse(found)

    def test_list_tasks_empty_message(self) -> None:
        payload = {"tasks": []}
        msg = list_tasks(payload)
        self.assertIn("No tasks yet", msg)

    def test_build_review_contains_sections(self) -> None:
        payload = {
            "date": date.today().isoformat(),
            "tasks": [{"id": 1, "text": "Prepare brief", "status": "pending", "done": False}],
            "notes": [{"text": "Need simpler setup"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            report = build_review(payload, Path(tmp))
        self.assertIn("# DayDrive Review", report)
        self.assertIn("## Task Completion", report)
        self.assertIn("Prepare brief", report)

    def test_execute_pending_commands_success(self) -> None:
        payload = {"tasks": [], "notes": [], "date": date.today().isoformat()}
        payload = add_task(payload, "Print ok", command="echo ok")

        with tempfile.TemporaryDirectory() as tmp:
            payload, results = execute_pending_commands(payload, Path(tmp), run_all=True)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "done")
        self.assertEqual(payload["tasks"][0]["status"], "done")
        self.assertEqual(payload["tasks"][0]["last_run"]["returncode"], 0)

    def test_execute_pending_commands_failure(self) -> None:
        payload = {"tasks": [], "notes": [], "date": date.today().isoformat()}
        payload = add_task(payload, "Fail command", command="exit 2")

        with tempfile.TemporaryDirectory() as tmp:
            payload, results = execute_pending_commands(payload, Path(tmp), run_all=True)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "failed")
        self.assertEqual(payload["tasks"][0]["status"], "failed")
        self.assertEqual(payload["tasks"][0]["last_run"]["returncode"], 2)

    def test_normalize_payload_backfills_old_tasks(self) -> None:
        payload = {
            "tasks": [{"id": 1, "text": "Legacy", "done": True}],
            "notes": [],
            "date": date.today().isoformat(),
        }
        normalize_payload(payload)
        self.assertEqual(payload["tasks"][0]["status"], "done")
        self.assertEqual(payload["tasks"][0]["kind"], "manual")

    def test_add_task_defaults_to_command_task(self) -> None:
        payload = {"tasks": [], "notes": [], "date": date.today().isoformat()}
        payload = add_task(payload, "echo hello")
        self.assertEqual(payload["tasks"][0]["kind"], "command")
        self.assertEqual(payload["tasks"][0]["command"], "echo hello")


if __name__ == "__main__":
    unittest.main()
