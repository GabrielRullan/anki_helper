import os
import re
import json
import sys
from collections import Counter, defaultdict
from gap_finder import load_data_from_live_db, load_data_from_backup_json

# Reconfigure stdout to use UTF-8 on Windows console
sys.stdout.reconfigure(encoding='utf-8')

def split_pinyin(pinyin):
    """Splits a pinyin syllable into (initial, final)."""
    pinyin = pinyin.lower().strip()
    # Clean HTML first
    pinyin = re.sub(r'<[^>]+>', '', pinyin)
    
    # Mapping of vowels with tone marks to normal vowels
    vowel_map = {
        'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
        'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
        'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
        'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
        'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
        'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v',
        'ü': 'v'
    }
    
    clean_p = ""
    for char in pinyin:
        clean_p += vowel_map.get(char, char)
        
    # Clean non-alphabetic characters
    clean_p = re.sub(r'[^a-z]', '', clean_p)
    
    if not clean_p:
        return "", ""
        
    # Check double initials first
    for double_init in ['zh', 'ch', 'sh']:
        if clean_p.startswith(double_init):
            return double_init, clean_p[2:]
            
    # Check single initials
    for init in 'bpmfdtnlgkhjqxrzcsyw':
        if clean_p.startswith(init):
            return init, clean_p[1:]
            
    return "", clean_p

def clean_components(comp_str):
    """Parses visual components list."""
    if not comp_str:
        return []
    # Split by comma or space
    parts = re.split(r'[,，\s]+', comp_str)
    return [p.strip() for p in parts if p.strip()]

def profile_mbp_palace(char_notes):
    """
    Analyzes Character notes to build the MBP codebook and diagnose conflicts and leeches.
    """
    # 1. Compile all characters and parse their fields
    characters = []
    
    # Frequency maps to find the "standard" mappings
    initial_actors = defaultdict(list)
    final_sets = defaultdict(list)
    tone_locations = defaultdict(list)
    
    for note in char_notes:
        f = note['fields']
        # Depending on whether data is from sqlite dict or json, keys might be different casing
        hanzi = f.get('Hanzi', f.get('hanzi', '')).strip()
        if not hanzi:
            continue
            
        pinyin_raw = f.get('Pinyin', f.get('pinyin', '')).strip()
        initial, final = split_pinyin(pinyin_raw)
        
        actor = f.get('Actor', f.get('actor', '')).strip()
        c_set = f.get('Set', f.get('set', '')).strip()
        
        # Tone
        tone = f.get('Tone', f.get('tone', '')).strip()
        # Clean tone to just digits if it's mixed
        tone = re.sub(r'\D', '', tone)
        if not tone:
            # Try to get tone from tone_location
            loc_temp = f.get('Tone-Location', f.get('tone_location', ''))
            match = re.search(r'\[(\d)\]', loc_temp)
            if match:
                tone = match.group(1)
            else:
                tone = "Unknown"
                
        loc = f.get('Tone-Location', f.get('tone_location', '')).strip()
        # Clean HTML out of fields
        actor = re.sub(r'<[^>]+>', '', actor).strip()
        c_set = re.sub(r'<[^>]+>', '', c_set).strip()
        loc = re.sub(r'<[^>]+>', '', loc).strip()
        
        comp_raw = f.get('Components', f.get('components', ''))
        components = clean_components(comp_raw)
        
        # Card performance
        lapses = note.get('lapses', 0)
        ease = note.get('ease', 2500)
        reps = note.get('reps', 0)
        suspended = note.get('suspended', False)
        tags = note.get('tags', [])
        
        char_data = {
            'note_id': note.get('id', note.get('note_id', 0)),
            'hanzi': hanzi,
            'pinyin': pinyin_raw,
            'initial': initial,
            'final': final,
            'tone': tone,
            'actor': actor,
            'set': c_set,
            'location': loc,
            'components': components,
            'lapses': lapses,
            'ease': ease,
            'reps': reps,
            'suspended': suspended,
            'tags': tags
        }
        characters.append(char_data)
        
        # Add to frequency lists if valid
        if initial and actor:
            initial_actors[initial].append(actor)
        if final and c_set:
            final_sets[final].append(c_set)
        if tone != "Unknown" and loc:
            tone_locations[tone].append(loc)
            
    # 2. Determine "Standard Codebook" based on majority vote
    codebook = {
        'actors': {},
        'sets': {},
        'locations': {}
    }
    
    for init, actors in initial_actors.items():
        if actors:
            codebook['actors'][init] = Counter(actors).most_common(1)[0][0]
    for fin, sets in final_sets.items():
        if sets:
            codebook['sets'][fin] = Counter(sets).most_common(1)[0][0]
    for tone, locs in tone_locations.items():
        if locs:
            codebook['locations'][tone] = Counter(locs).most_common(1)[0][0]
            
    # 3. Detect Inconsistencies
    inconsistencies = []
    for c in characters:
        issues = []
        
        # Check Actor
        std_actor = codebook['actors'].get(c['initial'])
        if c['initial'] and std_actor and c['actor'] and c['actor'] != std_actor:
            issues.append(f"Actor mismatch: '{c['actor']}' (standard for initial '{c['initial']}' is '{std_actor}')")
            
        # Check Set
        std_set = codebook['sets'].get(c['final'])
        if c['final'] and std_set and c['set'] and c['set'] != std_set:
            issues.append(f"Set mismatch: '{c['set']}' (standard for final '{c['final']}' is '{std_set}')")
            
        # Check Location
        std_loc = codebook['locations'].get(c['tone'])
        # Strip numbers/branding from locations for a softer match (e.g. "Backyard [4]" vs "Backyard")
        if c['tone'] != "Unknown" and std_loc and c['location']:
            c_loc_clean = re.sub(r'\[\d\]', '', c['location']).strip().lower()
            std_loc_clean = re.sub(r'\[\d\]', '', std_loc).strip().lower()
            if c_loc_clean != std_loc_clean:
                issues.append(f"Location mismatch: '{c['location']}' (standard for tone '{c['tone']}' is '{std_loc}')")
                
        if issues:
            inconsistencies.append({
                'hanzi': c['hanzi'],
                'pinyin': c['pinyin'],
                'note_id': c['note_id'],
                'issues': issues
            })
            
    # 4. Leech and Hard Character diagnostics
    # A card is a leech if it has lapses >= 4 or ease factor < 2000 or the 'leech' tag
    leeches = []
    for c in characters:
        is_leech = "leech" in c['tags'] or c['lapses'] >= 4 or c['ease'] < 2000
        if is_leech and c['reps'] > 0: # Ignore new cards
            leeches.append(c)
            
    # Sort leeches by severity (lapses descending, ease ascending)
    leeches.sort(key=lambda x: (x['lapses'], -x['ease']), reverse=True)
    
    # 5. Component Conflicts & Audio Collisions among hard characters
    conflicts = []
    hard_chars_set = leeches[:30] # Top 30 hard characters to check
    
    for i in range(len(hard_chars_set)):
        c1 = hard_chars_set[i]
        for j in range(i + 1, len(hard_chars_set)):
            c2 = hard_chars_set[j]
            conflict_reasons = []
            
            # Sound collision: Same initial, final, and tone (homophones!)
            if c1['initial'] == c2['initial'] and c1['final'] == c2['final'] and c1['tone'] == c2['tone']:
                conflict_reasons.append(f"Homophone collision: both pronounced '{c1['pinyin']}' (Actor: '{c1['actor']}', Set: '{c1['set']}', Location: '{c1['location']}')")
                
            # Visual component overlap: share 1 or more components
            shared_comps = set(c1['components']) & set(c2['components'])
            # Filter out generic components like '一' or '口' if they are too small, or keep them if they are meaningful
            # Let's show shared components if any are found
            if shared_comps:
                conflict_reasons.append(f"Visual component overlap: both share component(s) {list(shared_comps)}")
                
            if conflict_reasons:
                conflicts.append({
                    'char1': c1['hanzi'],
                    'char1_pinyin': c1['pinyin'],
                    'char1_lapses': c1['lapses'],
                    'char2': c2['hanzi'],
                    'char2_pinyin': c2['pinyin'],
                    'char2_lapses': c2['lapses'],
                    'reasons': conflict_reasons
                })
                
    # 6. Vacant slots in palace
    all_possible_initials = ['b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x', 'zh', 'ch', 'sh', 'r', 'z', 'c', 's', 'y', 'w']
    vacant_actors = [init for init in all_possible_initials if init not in codebook['actors']]
    
    all_possible_finals = ['a', 'o', 'e', 'i', 'u', 'v', 'ai', 'ei', 'ui', 'ao', 'ou', 'iu', 'ie', 've', 'er', 'an', 'en', 'in', 'un', 'vn', 'ang', 'eng', 'ing', 'ong']
    vacant_sets = [fin for fin in all_possible_finals if fin not in codebook['sets']]
    
    return {
        'codebook': codebook,
        'inconsistencies': inconsistencies,
        'leeches': leeches,
        'conflicts': conflicts,
        'vacant_actors': vacant_actors,
        'vacant_sets': vacant_sets,
        'characters': characters
    }

def main():
    # 1. Load Character data
    char_notes, _ = load_data_from_live_db()
    if char_notes is None:
        char_notes, _ = load_data_from_backup_json()
        
    if not char_notes:
        print("Error: Could not retrieve characters.")
        return
        
    print(f"Loaded {len(char_notes)} character notes.")
    
    # 2. Analyze
    profile = profile_mbp_palace(char_notes)
    
    print("\n=== MANDARIN BLUEPRINT CODEBOOK ===")
    print("Detected Standard Actors:")
    for init in sorted(profile['codebook']['actors'].keys()):
        print(f"  - [{init.upper()}]: {profile['codebook']['actors'][init]}")
        
    print("\nDetected Standard Sets:")
    for fin in sorted(profile['codebook']['sets'].keys()):
        print(f"  - [-{fin}]: {profile['codebook']['sets'][fin]}")
        
    print("\nDetected Standard Tone-Locations:")
    for tone in sorted(profile['codebook']['locations'].keys()):
        print(f"  - [Tone {tone}]: {profile['codebook']['locations'][tone]}")
        
    print(f"\n=== PALACE INCONSISTENCIES ({len(profile['inconsistencies'])}) ===")
    for item in profile['inconsistencies'][:10]:
        print(f"Character: {item['hanzi']} ({item['pinyin']})")
        for issue in item['issues']:
            print(f"  * {issue}")
    if len(profile['inconsistencies']) > 10:
        print(f"  ...and {len(profile['inconsistencies']) - 10} more inconsistencies.")
        
    print(f"\n=== TOP LEECHES / HARD CHARACTERS ({len(profile['leeches'])}) ===")
    for i, leech in enumerate(profile['leeches'][:10]):
        print(f" {i+1}. {leech['hanzi']} ({leech['pinyin']}) - Lapses: {leech['lapses']}, Ease: {leech['ease']}, Reps: {leech['reps']}")
        
    print(f"\n=== HARD CHARACTER CONFLICTS ({len(profile['conflicts'])}) ===")
    for item in profile['conflicts'][:10]:
        print(f"Between {item['char1']} ({item['char1_pinyin']}, Lapses: {item['char1_lapses']}) and {item['char2']} ({item['char2_pinyin']}, Lapses: {item['char2_lapses']})")
        for reason in item['reasons']:
            print(f"  * {reason}")
            
    print("\n=== VACANT SLOTS ===")
    print(f"Vacant Actors (Initials): {profile['vacant_actors']}")
    print(f"Vacant Sets (Finals):     {profile['vacant_sets']}")

if __name__ == "__main__":
    main()
