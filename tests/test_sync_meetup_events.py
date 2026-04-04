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
    def test_extract_image_from_event_html_prefers_meetup_event_photo_from_srcset(self):
        html = """
        <meta property="og:image" content="https://images.meetupstatic.com/group-logo.jpeg" />
        <img
          alt="OpenClaw - How It Works"
          srcset="
            https://secure.meetupstatic.com/photos/event/8/c/a/5/highres_533436005.webp?w=640 640w,
            https://secure.meetupstatic.com/photos/event/8/c/a/5/highres_533436005.webp?w=1920 1920w
          "
          src="https://secure.meetupstatic.com/photos/event/8/c/a/5/highres_533436005.webp?w=3840"
        />
        """
        image_url = mod.extract_image_from_event_html(html)
        self.assertEqual(
            image_url,
            "https://secure.meetupstatic.com/photos/event/8/c/a/5/highres_533436005.webp?w=1920",
        )

    def test_extract_image_from_event_html_prefers_og_image(self):
        html = """
        <meta property="og:image" content="https://images.meetupstatic.com/event.jpg" />
        <script type="application/ld+json">
          {"@type":"Event","image":"https://images.meetupstatic.com/other.jpg"}
        </script>
        """
        image_url = mod.extract_image_from_event_html(html)
        self.assertEqual(image_url, "https://images.meetupstatic.com/event.jpg")

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

    def test_parse_ld_json_events_keeps_image_url(self):
        html = '''
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Event",
          "name": "Upcoming Meetup Event",
          "startDate": "2026-04-15T19:00:00+02:00",
          "url": "https://www.meetup.com/genai-gurus/events/313946334/",
          "location": {"name": "Online"},
          "description": "Speaker: Jane Doe",
          "image": "https://secure.meetupstatic.com/photos/event/8/c/a/5/600_533436005.jpeg"
        }
        </script>
        '''
        events = mod.parse_ld_json_events(html)
        self.assertEqual(len(events), 1)
        self.assertEqual(
            events[0]["image"],
            "https://secure.meetupstatic.com/photos/event/8/c/a/5/600_533436005.jpeg",
        )

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

    def test_fill_event_images_uses_event_page_image(self):
        events = [
            {
                "title": "OpenClaw",
                "date": "2026-04-15T19:00:00Z",
                "event_status": "upcoming",
                "speaker_name": "",
                "location_label": "Online",
                "meetup_url": "https://www.meetup.com/genai-gurus/events/313946334/",
                "youtube_url": "",
                "image": "",
                "summary": "",
            }
        ]

        original_fetch_url = mod.fetch_url
        try:
            mod.fetch_url = lambda *_args, **_kwargs: (
                '<meta property="og:image" content="https://images.meetupstatic.com/correct-image.jpg" />'
            )
            updated = mod.fill_event_images(events, headers={})
        finally:
            mod.fetch_url = original_fetch_url

        self.assertEqual(updated[0]["image"], "https://images.meetupstatic.com/correct-image.jpg")

    def test_hydrate_events_from_links_prefers_cover_image_from_event_html(self):
        fallback_events = {
            "https://www.meetup.com/genai-gurus/events/313946334": {
                "title": "OpenClaw",
                "date": "2026-04-15T17:00:00Z",
                "event_status": "upcoming",
                "speaker_name": "",
                "location_label": "Online",
                "meetup_url": "https://www.meetup.com/genai-gurus/events/313946334/",
                "youtube_url": "",
                "image": "https://secure-content.meetupstatic.com/images/classic-events/533436005/676x676.jpg",
                "summary": "",
            }
        }

        event_html = """
        <meta property="og:image" content="https://secure.meetupstatic.com/photos/event/8/c/a/5/600_533436005.jpeg" />
        <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": "OpenClaw",
            "startDate": "2026-04-15T19:00:00+02:00",
            "url": "https://www.meetup.com/genai-gurus/events/313946334/",
            "location": {"name": "Online"},
            "description": "Speaker: Jane Doe",
            "image": "https://secure-content.meetupstatic.com/images/classic-events/533436005/676x676.jpg"
          }
        </script>
        """

        original_fetch_url = mod.fetch_url
        try:
            mod.fetch_url = lambda *_args, **_kwargs: event_html
            hydrated = mod.hydrate_events_from_links(
                ["https://www.meetup.com/genai-gurus/events/313946334"],
                headers={},
                fallback_events_by_url=fallback_events,
            )
        finally:
            mod.fetch_url = original_fetch_url

        self.assertEqual(len(hydrated), 1)
        self.assertEqual(
            hydrated[0]["image"],
            "https://secure.meetupstatic.com/photos/event/8/c/a/5/600_533436005.jpeg",
        )


if __name__ == "__main__":
    unittest.main()
