import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
dashboard_script_path = os.path.abspath('scripts/generate_dashboard.py')

with open(dashboard_script_path, 'r', encoding='utf-8') as f:
    code = f.read()

new_func = '''        function exportIgnoredHskWords() {
            const ignored = getIgnoredHskMissingWords();
            if (ignored.length === 0) {
                showToast('No ignored HSK words to export.');
                return;
            }
            const csvContent = `Word\\n` + ignored.join(`\\n`);
            copyToClipboard(csvContent);
            showToast('Ignored HSK words CSV copied to clipboard!');
        }'''

# Replace in code
code = re.sub(r'function exportIgnoredHskWords\(\).*?showToast\(\'Ignored HSK words CSV copied to clipboard!\'\);\s*\}', new_func, code, flags=re.DOTALL)

with open(dashboard_script_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Fixed syntax in generate_dashboard.py!")
