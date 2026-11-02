path = 'scripts/generate_dashboard.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Replace lines 2728 to 2748 (0-indexed: 2728 to 2748)
start_idx = 2728 # '    # Fetch props notes\n'
end_idx = 2748   # '    if not char_notes:\n' is at 2749

new_lines = lines[:start_idx] + [
    "    # Props have been removed per user instruction\n",
    "    prop_notes = []\n",
    "    \n"
] + lines[end_idx:]

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("generate_dashboard.py successfully patched.")
