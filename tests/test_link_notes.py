import unittest
import sys
import os

# Import modules from scripts directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from link_notes import (
    clean_components, 
    strip_component_links,
    update_marked_section, 
    remove_marked_section,
    get_field_val, 
    has_field, 
    link_text_characters,
    build_links_plan
)

class TestLinkNotes(unittest.TestCase):
    def test_clean_components(self):
        # Test basic splitting
        self.assertEqual(clean_components("日, 月"), ["日", "月"])
        # Test Chinese comma splitting
        self.assertEqual(clean_components("日，月"), ["日", "月"])
        # Test space splitting
        self.assertEqual(clean_components("日 月"), ["日", "月"])
        # Test mixed splitting
        self.assertEqual(clean_components("日， 月 ,   空"), ["日", "月", "空"])
        # Test HTML tag cleanup
        self.assertEqual(clean_components("<div>日</div>, <span>月</span>"), ["日", "月"])
        # Test empty input
        self.assertEqual(clean_components(""), [])
        self.assertEqual(clean_components(None), [])

    def test_strip_component_links(self):
        self.assertEqual(strip_component_links("[日|nid12345], [月|nid67890]"), "日, 月")
        self.assertEqual(strip_component_links("日, 月"), "日, 月")
        self.assertEqual(strip_component_links(""), "")

    def test_get_field_val(self):
        note = {
            'fields': {
                'Hanzi': {'value': ' 明 '},
                'Pinyin': {'value': 'míng'},
                'Components': {'value': ' 日, 月 '}
            }
        }
        # Test exact match
        self.assertEqual(get_field_val(note, 'Hanzi'), '明')
        # Test case insensitivity
        self.assertEqual(get_field_val(note, 'pinyin'), 'míng')
        # Test missing field
        self.assertEqual(get_field_val(note, 'Notes'), '')

    def test_has_field(self):
        note = {
            'fields': {
                'Hanzi': {'value': '明'},
                'Notes': {'value': 'Some notes'}
            }
        }
        # Test exact match
        self.assertTrue(has_field(note, 'Hanzi'))
        # Test case insensitivity
        self.assertTrue(has_field(note, 'notes'))
        # Test missing field
        self.assertFalse(has_field(note, 'Components'))

    def test_update_marked_section(self):
        start_tag = "<!-- ANKI_LINKER_START -->"
        end_tag = "<!-- ANKI_LINKER_END -->"
        
        # Test initial append
        content = "My initial note text."
        section_html = "<div>Linked character count: 3</div>"
        result = update_marked_section(content, section_html)
        
        expected = f"{content}\n\n{start_tag}\n{section_html}\n{end_tag}"
        self.assertEqual(result, expected)
        
        # Test append on empty content
        result_empty = update_marked_section("", section_html)
        expected_empty = f"{start_tag}\n{section_html}\n{end_tag}"
        self.assertEqual(result_empty, expected_empty)
        
        # Test replacement/idempotency
        existing_notes_with_section = (
            "My initial note text.\n\n"
            f"{start_tag}\n"
            "<div>Old html content</div>\n"
            f"{end_tag}\n"
            "Some footer text."
        )
        new_section_html = "<div>New resolved content!</div>"
        
        result_updated = update_marked_section(existing_notes_with_section, new_section_html)
        
        expected_updated = (
            "My initial note text.\n\n"
            f"{start_tag}\n"
            f"{new_section_html}\n"
            f"{end_tag}\n"
            "Some footer text."
        )
        self.assertEqual(result_updated, expected_updated)

    def test_remove_marked_section(self):
        start_tag = "<!-- ANKI_LINKER_START -->"
        end_tag = "<!-- ANKI_LINKER_END -->"
        
        content = f"User note.\n\n{start_tag}\n<div>Old section</div>\n{end_tag}"
        self.assertEqual(remove_marked_section(content), "User note.")
        
        content_only = f"{start_tag}\n<div>Old section</div>\n{end_tag}"
        self.assertEqual(remove_marked_section(content_only), "")

    def test_link_text_characters(self):
        char_to_nid = {
            "高": 1768474724490,
            "兴": 1768474724491,
            "的": 1768474724455,
            "确": 1768474724456
        }
        
        # Test basic characters linking
        self.assertEqual(
            link_text_characters("高兴", char_to_nid),
            "[高|nid1768474724490][兴|nid1768474724491]"
        )
        
        # Test preserving commas, spaces, punctuation
        self.assertEqual(
            link_text_characters("的确, 熟悉", char_to_nid),
            "[的|nid1768474724455][确|nid1768474724456], 熟悉"
        )
        
        # Test existing links are preserved
        self.assertEqual(
            link_text_characters("[高|nid1768474724490]兴", char_to_nid),
            "[高|nid1768474724490][兴|nid1768474724491]"
        )
        
        # Test empty input
        self.assertEqual(link_text_characters("", char_to_nid), "")

    def test_build_links_plan(self):
        char_notes = [
            {
                'id': 101,
                'fields': {
                    'Hanzi': {'value': '高'},
                    'Simplified': {'value': '高'},
                    'Components': {'value': '高'},
                    'Notes': {'value': '<!-- ANKI_LINKER_START -->\n<b>Derived characters:</b> [亮|nid102]\n<!-- ANKI_LINKER_END -->'}
                }
            },
            {
                'id': 102,
                'fields': {
                    'Hanzi': {'value': '兴'},
                    'Simplified': {'value': '兴'},
                    'Components': {'value': '兴'},
                    'Notes': {'value': ''}
                }
            }
        ]
        word_notes = [
            {
                'id': 201,
                'fields': {
                    'Word': {'value': '高兴'},
                    'Characters': {'value': ''},
                    'Notes': {'value': 'Word notes.'}
                }
            }
        ]
        
        char_updates, word_updates, nids_to_tag = build_links_plan(char_notes, word_notes)
        
        # Check word updates
        self.assertEqual(len(word_updates), 1)
        self.assertEqual(word_updates[0]['fields']['Characters'], '[高|nid101][兴|nid102]')
        self.assertIn('<b>Characters in word:</b> [高|nid101] [兴|nid102]', word_updates[0]['fields']['Notes'])
        
        # Check char updates: both 高 and 兴 should link to 高兴, and 'Derived characters' must be removed
        self.assertEqual(len(char_updates), 2)
        for cu in char_updates:
            self.assertIn('<b>Words containing', cu['fields']['Notes'])
            self.assertNotIn('Derived characters', cu['fields']['Notes'])

if __name__ == "__main__":
    unittest.main()
