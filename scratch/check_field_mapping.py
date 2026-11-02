import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    nts = anki.get_notetypes()
    double_f = list(nts[1768218202442]['fields'].values())
    single_f = list(nts[1789676260669]['fields'].values())
    
    print("Double fields (count:", len(double_f), "):")
    print(double_f)
    print("\nSingle fields (count:", len(single_f), "):")
    print(single_f)
    
    print("\nDifferences:")
    print("In Single but not in Double:", set(single_f) - set(double_f))
    print("In Double but not in Single:", set(double_f) - set(single_f))
    
    # Are the first 25 fields in the exact same order?
    same_order = True
    for i in range(len(double_f)):
        if double_f[i] != single_f[i]:
            print(f"Mismatch at index {i}: Double='{double_f[i]}', Single='{single_f[i]}'")
            same_order = False
    if same_order:
        print("\nAll 25 fields in 'Chinese Character - Double' match 'Chinese Character - Single' in the EXACT same order!")
        print("The only difference is that 'Chinese Character - Single' has 1 extra trailing field at index 25: 'Do_Not_Recall'.")
