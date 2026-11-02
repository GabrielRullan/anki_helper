import os
import glob
import shutil
import sqlite3
import json

class AnkiConnection:
    def __init__(self, profile_name="Main"):
        self.profile_name = profile_name
        self.db_path = self._find_db_path()
        self.temp_db_path = None
        self.conn = None
        
    def _find_db_path(self):
        appdata = os.getenv('APPDATA')
        if not appdata:
            raise EnvironmentError("APPDATA environment variable not found.")
        
        # 1. Allow environment variable override
        env_profile = os.getenv("ANKI_PROFILE")
        profile = env_profile if env_profile else self.profile_name

        path = os.path.join(appdata, "Anki2", profile, "collection.anki2")
        if os.path.exists(path):
            return path

        # 2. Check if folder exists for "Gabriel"
        if profile != "Gabriel":
            gabriel_path = os.path.join(appdata, "Anki2", "Gabriel", "collection.anki2")
            if os.path.exists(gabriel_path):
                print(f"Profile '{profile}' not found. Falling back to active profile 'Gabriel'.")
                return gabriel_path

        # 3. Dynamic auto-detection of available profiles
        anki2_dir = os.path.join(appdata, "Anki2")
        if os.path.exists(anki2_dir):
            profiles = [d for d in os.listdir(anki2_dir) 
                        if os.path.isdir(os.path.join(anki2_dir, d)) 
                        and d not in ["addons21", "logs", "templates"]]
            if len(profiles) == 1:
                auto_path = os.path.join(anki2_dir, profiles[0], "collection.anki2")
                if os.path.exists(auto_path):
                    print(f"Profile '{profile}' not found. Auto-detected and using single profile '{profiles[0]}'.")
                    return auto_path
            raise FileNotFoundError(f"Database not found for profile '{profile}'. Available profiles: {profiles}")
        else:
            raise FileNotFoundError(f"Anki2 folder not found in AppData/Roaming.")
        return path

    def connect(self):
        """Creates a copy of the database to avoid locks and connects to it."""
        # Use workspace or scratch directory for temp file
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        self.temp_db_path = os.path.join(temp_dir, f"collection_temp_{self.profile_name}.anki2")
        
        shutil.copy2(self.db_path, self.temp_db_path)
        
        # Also copy WAL file if it exists (crucial for WAL mode SQLite sync)
        wal_path = self.db_path + "-wal"
        if os.path.exists(wal_path):
            try:
                shutil.copy2(wal_path, self.temp_db_path + "-wal")
            except OSError:
                pass
                
        # Also copy SHM file if it exists
        shm_path = self.db_path + "-shm"
        if os.path.exists(shm_path):
            try:
                shutil.copy2(shm_path, self.temp_db_path + "-shm")
            except OSError:
                pass
                
        self.conn = sqlite3.connect(self.temp_db_path)
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
        if self.temp_db_path:
            for suffix in ['', '-wal', '-shm']:
                path = self.temp_db_path + suffix
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass # ignore errors deleting temp file

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_decks(self):
        """Returns dict of did -> name"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM decks")
        return {row[0]: row[1] for row in cursor.fetchall()}

    def best_match_deck(self, candidates):
        """Returns the first candidate deck that exists in the database, or the last one as fallback."""
        decks = self.get_decks()
        def normalize(name):
            return name.replace('::', '\x1f').replace('/', '\x1f').replace('\\', '\x1f').lower().strip()
        
        normalized_decks = {normalize(name) for name in decks.values()}
        for cand in candidates:
            if normalize(cand) in normalized_decks:
                # Find the actual name
                for name in decks.values():
                    if normalize(name) == normalize(cand):
                        return name
        return candidates[-1]

    def get_notetypes(self):
        """Returns dict of ntid -> {name, fields: {ord: name}}"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM notetypes")
        notetypes = {row[0]: {'name': row[1], 'fields': {}} for row in cursor.fetchall()}
        
        cursor.execute("SELECT ntid, ord, name FROM fields")
        for ntid, ord_val, f_name in cursor.fetchall():
            if ntid in notetypes:
                notetypes[ntid]['fields'][ord_val] = f_name
        return notetypes

    def get_notes_in_deck(self, deck_name):
        """Retrieves all notes in a specific deck with card stats (lapses, ease, reps, queue)."""
        cursor = self.conn.cursor()
        decks = self.get_decks()
        
        # Normalize and find deck ID (case and separator agnostic)
        def normalize(name):
            return name.replace('::', '\x1f').replace('/', '\x1f').replace('\\', '\x1f').lower().strip()
            
        target = normalize(deck_name)
        did = None
        for d_id, name in decks.items():
            if normalize(name) == target:
                did = d_id
                break
                
        if did is None:
            raise ValueError(f"Deck '{deck_name}' not found. Available decks: {list(decks.values())}")
            
        notetypes = self.get_notetypes()
        
        # Query cards in this deck or original deck (if in filtered deck) and get stats
        cursor.execute("""
            SELECT n.id, n.mid, n.flds, n.tags, c.lapses, c.factor, c.reps, c.queue
            FROM cards c
            JOIN notes n ON c.nid = n.id
            WHERE c.did = ? OR c.odid = ?
        """, (did, did))
        
        raw_data = cursor.fetchall()
        
        # Aggregate by note id since notes can have multiple cards
        notes_agg = {}
        for n_id, mid, flds, tags, lapses, factor, reps, queue in raw_data:
            if n_id not in notes_agg:
                notes_agg[n_id] = {
                    'mid': mid,
                    'flds': flds,
                    'tags': tags,
                    'lapses': [],
                    'factors': [],
                    'reps': [],
                    'queues': []
                }
            notes_agg[n_id]['lapses'].append(lapses or 0)
            notes_agg[n_id]['factors'].append(factor or 2500)
            notes_agg[n_id]['reps'].append(reps or 0)
            notes_agg[n_id]['queues'].append(queue or 0)
            
        notes = []
        for n_id, data in notes_agg.items():
            nt_info = notetypes.get(data['mid'], {'name': 'Unknown', 'fields': {}})
            field_values = data['flds'].split('\x1f')
            fields_dict = nt_info['fields']
            
            # Map field names to values
            note_fields = {}
            for ord_val, name in fields_dict.items():
                note_fields[name] = field_values[ord_val] if ord_val < len(field_values) else ""
                
            tags_list = [t for t in data['tags'].split(' ') if t]
            
            # Summarize stats across cards of this note
            notes.append({
                'id': n_id,
                'notetype': nt_info['name'],
                'tags': tags_list,
                'fields': note_fields,
                'lapses': max(data['lapses']) if data['lapses'] else 0,
                'ease': min(data['factors']) if data['factors'] else 2500,
                'reps': sum(data['reps']) if data['reps'] else 0,
                'suspended': any(q < 0 for q in data['queues']) if data['queues'] else False
            })
        return notes
