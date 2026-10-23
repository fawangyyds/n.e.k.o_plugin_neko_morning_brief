from __future__ import annotations

import json
import unittest

import _loader
from nmb.fetch import interpret_text
from nmb.sources.http import FetchError

_loader.setup()


WEATHER = {
    "latitude": 30.29,
    "longitude": 120.16,
    "daily": {
        "time": ["2026-10-23"],
        "weather_code": [61],
        "temperature_2m_max": [21.4],
        "temperature_2m_min": [15.2],
        "precipitation_probability_max": [80],
    },
}

NEWS = {
    "data": {
        "items": [
            {"title": "A", "summary": "ea", "url": "https://x.test/a"},
            {"title": "B", "summary": "eb", "url": "https://x.test/b"},
        ]
    }
}


class WeatherTests(unittest.TestCase):
    def test_open_meteo_becomes_readable_weather(self):
        result = interpret_text(json.dumps(WEATHER), url="https://api.test/w", label="杭州")
        self.assertEqual(result["kind"], "weather")
        item = result["items"][0]
        self.assertIn("杭州", item["title"])
        self.assertIn("15~21℃", item["title"])
        self.assertIn("小雨", item["title"])
        self.assertIn("降水概率 80%", item["summary"])
        self.assertNotIn("weather_code", json.dumps(result))

    def test_without_label(self):
        result = interpret_text(json.dumps(WEATHER))
        self.assertEqual(result["kind"], "weather")
        self.assertFalse(result["items"][0]["title"].startswith(" "))


class JsonTests(unittest.TestCase):
    def test_list_payload_becomes_items(self):
        result = interpret_text(json.dumps(NEWS))
        self.assertEqual(result["kind"], "items")
        self.assertEqual([item["title"] for item in result["items"]], ["A", "B"])

    def test_scalar_payload_is_passed_as_raw_json(self):
        payload = {"bitcoin": {"cny": 512300}, "ok": True}
        result = interpret_text(json.dumps(payload))
        self.assertEqual(result["kind"], "json")
        self.assertIn("512300", result["text"])
        self.assertIn("bitcoin", result["text"])

    def test_broken_json_raises(self):
        with self.assertRaises(FetchError):
            interpret_text("{broken")


class HtmlTests(unittest.TestCase):
    def test_html_title(self):
        result = interpret_text("<html><head><title>Hello</title></head></html>")
        self.assertEqual(result["kind"], "items")
        self.assertEqual(result["items"][0]["title"], "Hello")


if __name__ == "__main__":
    unittest.main()
