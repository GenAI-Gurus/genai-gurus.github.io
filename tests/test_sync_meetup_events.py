import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sync_meetup_events.py"
spec = importlib.util.spec_from_file_location("sync_meetup_events", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class SyncMeetupEventsTests(unittest.TestCase):
    def test_extract_event_urls_handles_relative_and_absolute_links(self):
        html = '''
        <a href="/genai-gurus/events/312645423/">Past A</a>
        <a href="https://www.meetup.com/genai-gurus/events/313946334/?foo=bar">Past B</a>
        <a href="/genai-gurus/about/">About</a>
        '''
        urls = mod.extract_event_urls_from_html(html)
        self.assertIn("https://www.meetup.com/genai-gurus/events/312645423", urls)
        self.assertIn("https://www.meetup.com/genai-gurus/events/313946334", urls)
        self.assertEqual(len(urls), 2)

    def test_parse_ld_json_events_supports_graph_nodes(self):
        html = '''
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "Event",
              "name": "Past Meetup Event",
              "startDate": "2025-10-20T18:30:00+02:00",
              "url": "https://www.meetup.com/genai-gurus/events/312645423/",
              "location": {"name": "Online"},
              "description": "Speaker: Jane Doe"
            }
          ]
        }
        </script>
        '''
        events = mod.parse_ld_json_events(html)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Past Meetup Event")
        self.assertEqual(events[0]["event_status"], "past")

    def test_extract_event_urls_handles_json_escaped_urls(self):
        html = r'''
        <script>
          window.__DATA__ = {"links":["https:\/\/www.meetup.com\/genai-gurus\/events\/312645423\/?eventOrigin=group_past_events"]};
        </script>
        '''
        urls = mod.extract_event_urls_from_html(html)
        self.assertIn("https://www.meetup.com/genai-gurus/events/312645423", urls)

    def test_parse_api_events_handles_meetup_rest_payload(self):
        payload = """
        [
          {
            "name": "GenAI Past Session",
            "time": 1729445400000,
            "link": "https://www.meetup.com/genai-gurus/events/312645423/",
            "description": "Speaker: Jane Doe",
            "is_online": true,
            "venue": {"name": "Online"}
          }
        ]
        """
        events = mod.parse_api_events(payload)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "GenAI Past Session")
        self.assertEqual(events[0]["meetup_url"], "https://www.meetup.com/genai-gurus/events/312645423/")

    def test_preserve_existing_past_events_when_fetch_returns_only_upcoming(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_output = Path(tmpdir) / "events.json"
            temp_output.write_text(
                json.dumps(
                    [
                        {
                            "title": "Past Event",
                            "date": "2025-10-20T16:30:00Z",
                            "event_status": "past",
                            "meetup_url": "https://www.meetup.com/genai-gurus/events/312645423/",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            original_output = mod.OUTPUT_FILE
            mod.OUTPUT_FILE = temp_output
            try:
                merged = mod.preserve_existing_past_events(
                    [
                        {
                            "title": "Upcoming Event",
                            "date": "2026-04-15T19:00:00Z",
                            "event_status": "upcoming",
                            "meetup_url": "https://www.meetup.com/genai-gurus/events/313946334/",
                        }
                    ]
                )
            finally:
                mod.OUTPUT_FILE = original_output

        self.assertEqual(len(merged), 2)
        statuses = {event["event_status"] for event in merged}
        self.assertIn("past", statuses)
        self.assertIn("upcoming", statuses)

    def test_event_links_file_roundtrip_and_normalization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_links = Path(tmpdir) / "event_links.json"
            original_links_file = mod.EVENT_LINKS_FILE
            mod.EVENT_LINKS_FILE = temp_links
            try:
                changed = mod.write_event_links_if_changed(
                    [
                        "https://www.meetup.com/genai-gurus/events/313946334/?foo=1",
                        "https://www.meetup.com/genai-gurus/events/313946334/",
                    ]
                )
                links = mod.load_event_links()
            finally:
                mod.EVENT_LINKS_FILE = original_links_file

        self.assertTrue(changed)
        self.assertEqual(links, ["https://www.meetup.com/genai-gurus/events/313946334"])


if __name__ == "__main__":
    unittest.main()
