import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from n1_sentence_finder import check_descriptive_context, find_n1_sentences

class TestN1SentenceFinder(unittest.TestCase):
    def test_check_descriptive_context(self):
        # Good sentence
        is_low, reason = check_descriptive_context("今天天气非常晴朗。", "Today the weather is very sunny.")
        self.assertFalse(is_low)
        self.assertEqual(reason, "")

        # Too short
        is_low, reason = check_descriptive_context("你好！", "Hello!")
        self.assertTrue(is_low)
        self.assertIn("Too short", reason)

        # Missing translation
        is_low, reason = check_descriptive_context("我们明天一起去北京。", "")
        self.assertTrue(is_low)
        self.assertIn("Missing or very short translation", reason)

    def test_find_n1_sentences_classification(self):
        char_notes = [
            {"fields": {"Hanzi": "我"}},
            {"fields": {"Hanzi": "是"}},
            {"fields": {"Hanzi": "学"}},
            {"fields": {"Hanzi": "生"}},
        ]
        # Sentence with all known characters: 我是学生 (N+0)
        # Sentence with 1 unknown character: 我爱学生 (爱 is unknown) (N+1)
        # Sentence with 2 unknown characters: 他在北京 (他, 在, 京 are unknown) (N+2+)
        migaku_notes = [
            {
                "id": 1,
                "fields": {
                    "Sentence": "我是学生。",
                    "Word": "学生",
                    "Translated Sentence": "I am a student."
                }
            },
            {
                "id": 2,
                "fields": {
                    "Sentence": "我爱学生。",
                    "Word": "爱",
                    "Translated Sentence": "I love students."
                }
            },
            {
                "id": 3,
                "fields": {
                    "Sentence": "他在北京。",
                    "Word": "北京",
                    "Translated Sentence": "He is in Beijing."
                }
            }
        ]
        n0, n1, n2 = find_n1_sentences(char_notes, migaku_notes)
        self.assertEqual(len(n0), 1)
        self.assertEqual(n0[0]["sentence"], "我是学生。")
        self.assertEqual(len(n1), 1)
        self.assertEqual(n1[0]["missing_char"], "爱")
        self.assertEqual(len(n2), 1)
        self.assertIn("他", n2[0]["missing_chars"])

if __name__ == "__main__":
    unittest.main()
