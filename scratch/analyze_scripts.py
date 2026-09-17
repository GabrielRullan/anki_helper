import os
import glob
import sys

sys.stdout.reconfigure(encoding="utf-8")
scripts = sorted([os.path.basename(f) for f in glob.glob("scripts/*.py")])

for s in scripts:
    path = os.path.join("scripts", s)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        # search for docstring or first non-import comments
        doc = []
        for l in lines[:25]:
            if l.startswith("#") and not l.startswith("#!/") and "utf-8" not in l.lower():
                doc.append(l.lstrip("#").strip())
            elif '"""' in l or "'''" in l:
                doc.append(l.replace('"""', '').replace("'''", '').strip())
        summary = " ".join(doc)[:120] if doc else "Utility/One-off script"
        print(f"{s:35} | {summary}")
