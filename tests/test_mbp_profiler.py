import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from mbp_profiler import clean_components, split_pinyin, profile_mbp_palace

class TestMbpProfiler(unittest.TestCase):
    def test_clean_components(self):
        self.assertEqual(clean_components("日, 月"), ["日", "月"])
        self.assertEqual(clean_components("日，月"), ["日", "月"])
        self.assertEqual(clean_components("日 月"), ["日", "月"])
        self.assertEqual(clean_components("日， 月 ,   空"), ["日", "月", "空"])
        self.assertEqual(clean_components(""), [])
        self.assertEqual(clean_components(None), [])

    def test_split_pinyin(self):
        self.assertEqual(split_pinyin("hǎo"), ("h", "ao"))
        self.assertEqual(split_pinyin("zhōng"), ("zh", "ong"))
        self.assertEqual(split_pinyin("ài"), ("", "ai"))
        self.assertEqual(split_pinyin("míng"), ("m", "ing"))

    def test_profile_mbp_palace_empty(self):
        res = profile_mbp_palace([])
        self.assertIn("codebook", res)
        self.assertIn("actors", res["codebook"])
        self.assertIn("sets", res["codebook"])
        self.assertIn("locations", res["codebook"])
        self.assertIn("leeches", res)
        self.assertIn("vacant_actors", res)

    def test_profile_mbp_palace_sample(self):
        sample_notes = [
            {
                "id": 1001,
                "fields": {
                    "Hanzi": "好",
                    "Pinyin": "hǎo",
                    "Actor": "Hulk",
                    "Set": "Outhouse (-ao)",
                    "Tone-Location": "Kitchen [3]",
                    "Components": "女, 子"
                },
                "lapses": 5,
                "reps": 12,
                "ease": 1900,
                "tags": ["leech"]
            }
        ]
        res = profile_mbp_palace(sample_notes)
        self.assertEqual(len(res["characters"]), 1)
        self.assertEqual(res["characters"][0]["hanzi"], "好")
        self.assertEqual(len(res["leeches"]), 1)
        self.assertEqual(res["leeches"][0]["hanzi"], "好")
        self.assertEqual(res["codebook"]["actors"]["h"], "Hulk")

if __name__ == "__main__":
    unittest.main()
