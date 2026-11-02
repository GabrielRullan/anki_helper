import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    c.execute("SELECT ntid, ord, name, config FROM templates WHERE ntid IN (1768218202442, 1789676260669)")
    for ntid, ord_v, name, config in c.fetchall():
        print(f"=== ntid: {ntid}, ord: {ord_v}, name: {name} ===")
        # In sqlite, config is a serialized protobuf message CardTemplateConfig:
        # field 1: qfmt (string)
        # field 2: afmt (string)
        # field 3: bqfmt (string)
        # field 4: bafmt (string)
        # Let's decode protobuf roughly or search for strings
        # Protobuf wire format: tag (field_number << 3 | wire_type)
        # For strings (wire_type = 2): tag byte, then varint length, then utf-8 bytes
        idx = 0
        while idx < len(config):
            tag = config[idx]
            wire_type = tag & 7
            field_num = tag >> 3
            idx += 1
            if wire_type == 2: # length-delimited
                # read varint length
                length = 0
                shift = 0
                while True:
                    b = config[idx]
                    idx += 1
                    length |= (b & 0x7f) << shift
                    if not (b & 0x80):
                        break
                    shift += 7
                val_bytes = config[idx:idx+length]
                idx += length
                val_str = val_bytes.decode('utf-8', errors='replace')
                field_names = {1: 'qfmt (Front)', 2: 'afmt (Back)', 3: 'bqfmt', 4: 'bafmt'}
                print(f"[{field_names.get(field_num, f'Field {field_num}')}]:")
                print(val_str)
                print("~"*40)
            elif wire_type == 0: # varint
                while config[idx] & 0x80:
                    idx += 1
                idx += 1
            else:
                break
