import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from daydrive.core import DailyStore, add_note, add_task, build_review, list_tasks, mark_done


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
            self.assertTrue(saved["tasks"][0]["done"])
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
            "tasks": [{"id": 1, "text": "Prepare brief", "done": False}],
            "notes": [{"text": "Need simpler setup"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            report = build_review(payload, Path(tmp))
        self.assertIn("# DayDrive Review", report)
        self.assertIn("## Task Completion", report)
        self.assertIn("Prepare brief", report)


if __name__ == "__main__":
    unittest.main()
