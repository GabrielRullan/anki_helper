import unittest
import os
import sys
import csv
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from import_grammar import parse_semana_md, generate_csv

class TestGrammarParser(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.md_path = os.path.join(self.base_dir, "..", "lessons", "semana.md")
        self.csv_path = os.path.join(self.base_dir, "test_grammar_import.csv")
        
    def tearDown(self):
        if os.path.exists(self.csv_path):
            os.remove(self.csv_path)
        
    def test_parse_semana_md(self):
        self.assertTrue(os.path.exists(self.md_path), "semana.md must exist in the workspace")
        
        items = parse_semana_md(self.md_path)
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0, "Should extract at least some grammar items")
        
        # Test keys in the parsed dicts
        required_keys = {'id', 'grammar_pattern', 'grammar_meaning', 'sub_label', 'spanish', 'english', 'chinese', 'notes'}
        for item in items:
            self.assertEqual(set(item.keys()), required_keys)
            self.assertTrue(item['id'].isdigit(), f"ID should be a digit: {item['id']}")
            self.assertTrue(item['grammar_pattern'], "Grammar pattern should not be empty")
            self.assertTrue(item['spanish'], "Spanish text should not be empty")
            self.assertTrue(item['english'], "English text should not be empty")
            self.assertTrue(item['chinese'], "Chinese text should not be empty")
            
        # Test specific lesson parsing details
        # Lesson 1: 不仅……而且/还/也
        lesson_1_items = [x for x in items if x['id'] == '1']
        self.assertEqual(len(lesson_1_items), 1)
        self.assertEqual(lesson_1_items[0]['grammar_pattern'], '不仅……而且/还/也')
        self.assertEqual(lesson_1_items[0]['grammar_meaning'], 'Not only... but also')
        self.assertIn('攀岩', lesson_1_items[0]['chinese'])
        self.assertEqual(lesson_1_items[0]['notes'], '"攀岩" (pānyán) means rock climbing.')
        
        # Lesson 3: 刚 / 刚才 (contains sub-labels "刚" and "刚才")
        lesson_3_items = [x for x in items if x['id'] == '3']
        self.assertEqual(len(lesson_3_items), 2)
        self.assertEqual(lesson_3_items[0]['sub_label'], '刚')
        self.assertEqual(lesson_3_items[1]['sub_label'], '刚才')
        # Both should share the note at the end of the section
        expected_note = '"刚" is an adverb and must go after the subject. "刚才" is a time noun and can go before or after the subject.'
        self.assertIn(expected_note, lesson_3_items[0]['notes'])
        self.assertIn(expected_note, lesson_3_items[1]['notes'])

        # Lesson 19: 原来 / 本来 (contains multiple sub-labels/usages)
        lesson_19_items = [x for x in items if x['id'] == '19']
        self.assertEqual(len(lesson_19_items), 3)
        self.assertEqual(lesson_19_items[0]['sub_label'], '本来 - Original plan/logic')
        self.assertEqual(lesson_19_items[1]['sub_label'], '原来 - Discovery')
        self.assertEqual(lesson_19_items[2]['sub_label'], '原来/本来 - Adjective + 的')

    def test_generate_csv(self):
        items = parse_semana_md(self.md_path)
        generate_csv(items, self.csv_path)
        self.assertTrue(os.path.exists(self.csv_path))
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            self.assertEqual(headers, ['Word', 'Grammar Point', 'Sentence', 'Translated Sentence', 'Definitions', 'Notes'])
            
            rows = list(reader)
            self.assertEqual(len(rows), len(items))
            
            # Check mapped fields of first row (Lesson 1)
            first_row = rows[0]
            self.assertEqual(first_row['Word'], '')
            self.assertEqual(first_row['Grammar Point'], '不仅……而且/还/也')
            self.assertEqual(first_row['Sentence'], '我**不仅**带孩子们去攀岩了，**还**跟女儿一起涂了彩色的指甲油。')
            self.assertEqual(first_row['Translated Sentence'], 'I not only took the kids climbing, but also painted my nails in many colors with my daughter.')
            self.assertEqual(first_row['Definitions'], 'Not only... but also')
            
            # Notes should not contain Spanish, only explanation/usage
            self.assertNotIn('Spanish:', first_row['Notes'])
            self.assertIn('Explanation: "攀岩" (pānyán) means rock climbing.', first_row['Notes'])

if __name__ == '__main__':
    unittest.main()
