with open('scripts/generate_dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(2725, min(2752, len(lines))):
    print(f"{i+1}: {repr(lines[i])}")
