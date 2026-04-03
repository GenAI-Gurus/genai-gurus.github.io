import importlib.util
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


if __name__ == "__main__":
    unittest.main()
