import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/all_113_analysis.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

for item in items:
    eng = item['english']
    issues = []
    
    # Check 1: Unclosed parenthesis
    open_count = eng.count('(') + eng.count('（')
    close_count = eng.count(')') + eng.count('）')
    if open_count != close_count:
        issues.append(f"Unclosed paren ({open_count} open vs {close_count} close)")
        
    # Check 2: HTML entities
    if '&nbsp;' in eng or '<' in eng:
        issues.append("Contains HTML entity or tag")
        
    # Check 3: Missing space before '('
    if re.search(r'[A-Za-z0-9]\(', eng):
        issues.append("Missing space before '('")
        
    # Check 4: Bare (Surname)
    if re.search(r'^\s*\(Surname\)\s*$', eng, re.I) or re.search(r'/\s*\(Surname\)\s*$', eng, re.I):
        issues.append("Incomplete surname (missing actual name)")
        
    # Check 5: Dictionary artifacts like (Bound form), (sb), (etc)
    if any(k in eng.lower() for k in ['bound form', '(sb)', 'etc)', '(of a woman)', 'indicating', 'interjection', 'onomatopoeia', 'e.g.']):
        issues.append("Dictionary-style gloss artifact")
        
    # Check 6: Inconsistent measure word or classifier
    if any(k in eng.lower() for k in ['measure word for', 'classifier for', '(classifier']):
        issues.append("Inconsistent measure word formatting")
        
    # Check 7: Weird capitalization like (measure Word...) or (sound Of...)
    if re.search(r'\([a-z]', eng) or re.search(r'\([A-Z][a-z]+ [A-Z]', eng):
        issues.append("Weird title-casing or lowercasing inside parens")
        
    # Check 8: Trailing period
    if eng.strip().endswith('.'):
        issues.append("Trailing punctuation")
        
    # Check 9: Extremely verbose (> 35 chars)
    if len(eng) > 35:
        issues.append("Very verbose definition for a character card")
        
    item['issues'] = issues

has_issues = [it for it in items if it['issues']]
no_issues = [it for it in items if not it['issues']]

print(f"Total analyzed: {len(items)}")
print(f"Items with identified potential improvements: {len(has_issues)}")
print(f"Items already well-formed: {len(no_issues)}")

print("\n--- SAMPLE OF ITEMS WITH ISSUES ---")
for it in has_issues[:35]:
    print(f"{it['hanzi']} [{it['pinyin']}]: \"{it['english']}\" -> {', '.join(it['issues'])}")
