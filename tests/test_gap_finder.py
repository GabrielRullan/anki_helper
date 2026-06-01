import unittest
import sys
import os

# Import modules from current directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from gap_finder import clean_sentence_hanzi, analyze_gap_and_synergy

import shutil

class TestGapFinder(unittest.TestCase):
    def setUp(self):
        import gap_finder
        self.known_words_path = os.path.join(os.path.dirname(gap_finder.__file__), "..", "data", "known_words.csv")
        self.known_chars_path = os.path.join(os.path.dirname(gap_finder.__file__), "..", "data", "known_characters.csv")
        
        self.words_bak = self.known_words_path + ".bak"
        self.chars_bak = self.known_chars_path + ".bak"
        
        # Backup existing
        if os.path.exists(self.known_words_path):
            if os.path.exists(self.words_bak):
                os.remove(self.words_bak)
            shutil.move(self.known_words_path, self.words_bak)
        if os.path.exists(self.known_chars_path):
            if os.path.exists(self.chars_bak):
                os.remove(self.chars_bak)
            shutil.move(self.known_chars_path, self.chars_bak)
            
        # Create empty sandboxes
        with open(self.known_words_path, 'w', encoding='utf-8', newline='') as f:
            f.write("Word\n")
        with open(self.known_chars_path, 'w', encoding='utf-8', newline='') as f:
            f.write("Character\n")
            
    def tearDown(self):
        # Remove sandboxes
        if os.path.exists(self.known_words_path):
            os.remove(self.known_words_path)
        if os.path.exists(self.known_chars_path):
            os.remove(self.known_chars_path)
            
        # Restore backups
        if os.path.exists(self.words_bak):
            shutil.move(self.words_bak, self.known_words_path)
        if os.path.exists(self.chars_bak):
            shutil.move(self.chars_bak, self.known_chars_path)
            
    def test_clean_sentence_hanzi(self):
        # Mixed HTML, English, punctuation, and Hanzi
        test_str = "她已经是这么多人里面最好的一个了<br>! She is the best. 123"
        expected = list("她已经是这么多人里面最好的一个了")
        self.assertEqual(clean_sentence_hanzi(test_str), expected)
        
        # English only
        self.assertEqual(clean_sentence_hanzi("Hello World! 123"), [])
        
        # HTML tag cleanup
        self.assertEqual(clean_sentence_hanzi("<div>你好</div>"), list("你好"))
        
    def test_analyze_gap_and_synergy(self):
        # Mock characters (Learned: 一, 二, 三, 人)
        char_notes = [
            {'fields': {'Hanzi': '一'}},
            {'fields': {'Hanzi': '二'}},
            {'fields': {'Hanzi': '三'}},
            {'fields': {'Hanzi': '人'}},
        ]
        
        # Mock immersion cards
        # Sentence 1 has: 个人 (人 is learned, 个 is gap)
        # Sentence 2 has: 三个人 (三, 个, 人 - 个 is gap)
        # Sentence 3 has: 从一而终 (从, 而, 终 are gaps; 一 is learned)
        migaku_notes = [
            {'fields': {'Sentence': '个人', 'Word': ''}},
            {'fields': {'Sentence': '三个人', 'Word': ''}},
            {'fields': {'Sentence': '从一而终', 'Word': ''}}
        ]
        
        # Mock HSK words
        # Word 1: 三人 (Synergy: 三 and 人 are learned)
        # Word 2: 个人 (One char away: 人 is learned, 个 is missing)
        # Word 3: 从小 (Not synergy: 从 and 小 are missing, so needs 2 characters)
        hsk_words = [
            {
                's': '三人',
                'f': [{'i': {'y': 'sān rén'}, 'm': ['three people']}]
            },
            {
                's': '个人',
                'f': [{'i': {'y': 'gè rén'}, 'm': ['individual']}]
            },
            {
                's': '从小',
                'f': [{'i': {'y': 'cóng xiǎo'}, 'm': ['from childhood']}]
            }
        ]
        
        results = analyze_gap_and_synergy(char_notes, migaku_notes, hsk_words)
        
        # Verify learned characters count
        self.assertEqual(results['learned_chars_count'], 4)
        
        # Verify immersion cards count
        self.assertEqual(results['total_immersion_cards'], 3)
        
        # Gaps: '个' (seen 2 times), '从' (seen 1 time), '而' (seen 1 time), '终' (seen 1 time)
        # Total unique gaps = 4 ('个', '从', '而', '终')
        self.assertEqual(results['total_gaps_count'], 4)
        
        # Top gaps should have '个' first since it has 2 occurrences
        self.assertEqual(results['top_gaps'][0], ('个', 2))
        
        # Synergy words: '三人' should be in synergy (composed of 三 and 人, both learned)
        self.assertEqual(len(results['synergy_words']), 1)
        self.assertEqual(results['synergy_words'][0]['word'], '三人')
        
        # Unlocked characters:
        # '个' should unlock '个人' (since 人 is learned, and only '个' is missing)
        # Check if '个' is in the unlocked chars list
        unlocked_chars = {item['character']: item for item in results['unlocked_chars']}
        self.assertIn('个', unlocked_chars)
        self.assertEqual(unlocked_chars['个']['unlock_count'], 1)
        self.assertEqual(unlocked_chars['个']['unlocked_words'][0]['word'], '个人')
        
        # '从' should NOT be a 1-character unlock for '从小' because both '从' and '小' are missing (2 characters missing)
        if '从' in unlocked_chars:
            unlocked_words = [w['word'] for w in unlocked_chars['从']['unlocked_words']]
            self.assertNotIn('从小', unlocked_words)

    def test_n1_sentence_finder(self):
        from n1_sentence_finder import find_n1_sentences
        # Mock characters (Learned: 一, 二)
        char_notes = [
            {'fields': {'Hanzi': '一'}},
            {'fields': {'Hanzi': '二'}},
        ]
        # Mock immersion notes
        # Sentence 1: "一" -> N+0 (since '一' is learned)
        # Sentence 2: "一三" -> N+1 (since '一' is learned, '三' is missing)
        # Sentence 3: "一三四" -> N+2 (since '一' is learned, '三' and '四' are missing)
        migaku_notes = [
            {'fields': {'Sentence': '一', 'Word': '', 'Translated Sentence': 'One'}},
            {'fields': {'Sentence': '一三', 'Word': '', 'Translated Sentence': 'One Three'}},
            {'fields': {'Sentence': '一三四', 'Word': '', 'Translated Sentence': 'One Three Four'}}
        ]
        
        n0, n1, n2 = find_n1_sentences(char_notes, migaku_notes)
        self.assertEqual(len(n0), 1)
        self.assertEqual(len(n1), 1)
        self.assertEqual(len(n2), 1)
        self.assertEqual(n1[0]['missing_char'], '三')
        self.assertEqual(n1[0]['char_freq'], 2) # '三' appears in 'one three' and 'one three four'
        
        # Verify low-context checks
        self.assertTrue(n1[0]['low_context'])
        self.assertEqual(n1[0]['low_context_reason'], 'Too short (< 5 characters)')

    def test_mbp_profiler(self):
        from mbp_profiler import profile_mbp_palace, split_pinyin
        # Test split_pinyin helper
        self.assertEqual(split_pinyin('bàn'), ('b', 'an'))
        self.assertEqual(split_pinyin('zhōng'), ('zh', 'ong'))
        self.assertEqual(split_pinyin('yī'), ('y', 'i'))
        self.assertEqual(split_pinyin('ān'), ('', 'an'))
        
        # Test profiler
        char_notes = [
            {
                'id': 101,
                'fields': {
                    'Hanzi': '一', 'Pinyin': 'yī', 'Tone': '1', 'Tone-Location': 'In Front [1]',
                    'Actor': 'Yelena', 'Set': '-(Null)', 'Components': '一'
                },
                'lapses': 1, 'ease': 2500, 'reps': 10, 'tags': []
            },
            {
                'id': 102,
                'fields': {
                    'Hanzi': '三', 'Pinyin': 'sān', 'Tone': '1', 'Tone-Location': 'In Front [1]',
                    'Actor': 'Samuel L Jackson', 'Set': '-an', 'Components': '一 , 二'
                },
                'lapses': 5, 'ease': 1800, 'reps': 15, 'tags': ['leech']
            },
            {
                'id': 103,
                'fields': {
                    'Hanzi': '干', 'Pinyin': 'gān', 'Tone': '1', 'Tone-Location': 'In Front [1]',
                    'Actor': 'Chef Gordon', 'Set': '-an', 'Components': '一 , 十'
                },
                'lapses': 0, 'ease': 2500, 'reps': 5, 'tags': []
            }
        ]
        
        profile = profile_mbp_palace(char_notes)
        
        # Verify leech detection
        leeches = [l['hanzi'] for l in profile['leeches']]
        self.assertIn('三', leeches)
        
        # Verify codebook extraction
        # Actor for 's' should be 'Samuel L Jackson'
        self.assertEqual(profile['codebook']['actors'].get('s'), 'Samuel L Jackson')

    def test_known_words_csv_and_missing_hsk_words(self):
        # Create a mock known_words.csv file
        import csv
        import gap_finder
        known_csv = os.path.join(os.path.dirname(gap_finder.__file__), "..", "data", "known_words.csv")
        # Backup if it exists
        existed = os.path.exists(known_csv)
        backup_lines = []
        if existed:
            with open(known_csv, 'r', encoding='utf-8') as f:
                backup_lines = f.readlines()
                
        # Write test data: personal known words
        with open(known_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Word'])
            writer.writerow(['个人']) # mark '个人' as known
            
        char_notes = [{'fields': {'Hanzi': '人'}}]
        migaku_notes = []
        hsk_words = [
            {
                's': '个人',
                'f': [{'i': {'y': 'gè rén'}, 'm': ['individual']}]
            },
            {
                's': '从小',
                'f': [{'i': {'y': 'cóng xiǎo'}, 'm': ['from childhood']}]
            }
        ]
        
        try:
            results = analyze_gap_and_synergy(char_notes, migaku_notes, hsk_words)
            
            # Since '个人' is in known_words.csv, it should be in learned_words.
            # Thus, the only missing HSK word in Migaku should be '从小'
            missing_words = [item['word'] for item in results['missing_hsk_words_in_migaku']]
            self.assertNotIn('个人', missing_words)
            self.assertIn('从小', missing_words)
            
        finally:
            # Cleanup known_words.csv
            if existed:
                with open(known_csv, 'w', encoding='utf-8', newline='') as f:
                    f.writelines(backup_lines)
            elif os.path.exists(known_csv):
                os.remove(known_csv)

    def test_known_characters_csv_and_missing_hsk_chars(self):
        # Create a mock known_characters.csv file
        import csv
        import gap_finder
        known_chars_csv = os.path.join(os.path.dirname(gap_finder.__file__), "..", "data", "known_characters.csv")
        # Backup if it exists
        existed = os.path.exists(known_chars_csv)
        backup_lines = []
        if existed:
            with open(known_chars_csv, 'r', encoding='utf-8') as f:
                backup_lines = f.readlines()
                
        # Write test data: mark '个' as known
        with open(known_chars_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Character'])
            writer.writerow(['个'])
            
        char_notes = [{'fields': {'Hanzi': '人'}}]
        migaku_notes = []
        # '个' and '人' are required for HSK word '个人'
        hsk_words = [
            {
                's': '个人',
                'f': [{'i': {'y': 'gè rén'}, 'm': ['individual']}]
            }
        ]
        
        try:
            results = analyze_gap_and_synergy(char_notes, migaku_notes, hsk_words)
            
            # Since '个' is in known_characters.csv, and '人' is in char_notes,
            # '个' should be in learned_chars. So missing_chars_hsk should be empty!
            self.assertEqual(len(results['missing_chars_hsk']), 0)
            
            # '个人' should now be a synergy word because both '个' and '人' are known/learned!
            synergy_words = [item['word'] for item in results['synergy_words']]
            self.assertIn('个人', synergy_words)
            
        finally:
            # Cleanup known_characters.csv
            if existed:
                with open(known_chars_csv, 'w', encoding='utf-8', newline='') as f:
                    f.writelines(backup_lines)
            elif os.path.exists(known_chars_csv):
                os.remove(known_chars_csv)

if __name__ == "__main__":
    unittest.main()
