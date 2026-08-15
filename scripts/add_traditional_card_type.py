import os
import sys
import json
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'

def request_anki(action, **params):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    req = urllib.request.Request(
        ANKICONNECT_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                print(f"AnkiConnect Error [{action}]: {res.get('error')}", flush=True)
                return None
            return res.get('result')
    except Exception as e:
        print(f"AnkiConnect Request Failed [{action}]: {e}", flush=True)
        return None

REC_FRONT = """<div class="meta-info">
    Phase {{Tags}} • HSK {{HSK_2}} • {{Frequency}}
    {{#Do_Not_Recall}}<span class="badge-recognition-only">📖 Recognition Only</span>{{/Do_Not_Recall}}
</div>

<div class="header-row">
   <div class="character-box">
        <ruby class="hanzi">
           {{Hanzi}}
           <rt class="pinyin"></rt>
        </ruby>
    </div>
    <div class="translation-box">
        <span class="meaning"></span>
    </div>
</div>
"""

REC_BACK = """<div class="meta-info">
    Phase {{Tags}} • HSK {{HSK_2}} • {{Frequency}}
    {{#Do_Not_Recall}}<span class="badge-recognition-only">📖 Recognition Only</span>{{/Do_Not_Recall}}
</div>

<div class="header-row">
    <div class="character-box">
        <ruby class="hanzi-{{Tone}}">
           {{Hanzi}}
           <rt class="pinyin-{{Tone}}">{{Pinyin}}</rt>
        </ruby>
    </div>
    <div class="translation-box">
        <span class="meaning">{{English}}</span>
    </div>
    <div class="sound-wrapper">{{Sound}}</div>
</div>

<div class="vocab-container">
    <div class="vocab-header">Common Words</div>
    <div class="vocab-zh">{{Common Words}}</div>
    <div class="vocab-en">{{Translation of Words}}</div>
    <div class="sound-wrapper">
        {{Words_Sound}}
        {{Words_English_Sound}}
    </div>
</div>

<div id="trad-display" class="traditional-container" style="display:none;">
    Traditional: {{Traditional}}
</div>

<script>
   var simplified = "{{Hanzi}}";
   var traditional = "{{Traditional}}";
   if (traditional && traditional !== simplified) {
       document.getElementById("trad-display").style.display = "block";
   }
</script>

{{#Image}} <div class="mnemonic-image">{{Image}}</div> {{/Image}}

<div class="movie-container">
    <div class="scene-header">🎬 The Movie Scene</div>
    
    <div class="grid">
        <div class="label">Actor:</div>
        <div class="data">[{{Initial}}] - {{Actor}}</div>
        
        <div class="label">Set:</div>
        <div class="data">{{Set}}</div>
      
        <div class="label">Tone:</div>
        <div class="data">{{Tone-Location}}</div>

        <div class="label">Props:</div>
        <div class="data">{{Components}}</div>

        <div class="label">Scene:</div>
        <div class="data">{{Scene}}</div>
    </div>
</div>

<div class="vocab-container">
    <div class="vocab-header">Notes</div>
    {{Notes}}
    <br>
    <a href="https://hanzicraft.com/character/{{Hanzi}}" target="_blank">HanziCraft: {{Hanzi}}</a>
</div>
"""

RECALL_FRONT = """{{^Do_Not_Recall}}
<div class="meta-info">Phase {{Tags}} • HSK {{HSK_2}} • {{Frequency}}</div>

<div class="header-row">
    <div class="character-box">
        <ruby class="hanzi-{{Tone}}">
           <rt class="pinyin">{{Pinyin}}</rt>
        </ruby>
    </div>
    <div class="translation-box">
        <span class="meaning">{{English}}</span>
    </div>
</div>
{{/Do_Not_Recall}}
"""

RECALL_BACK = """<div class="meta-info">Phase {{Tags}} • HSK {{HSK_2}} • {{Frequency}}</div>

<div class="header-row">
    <div class="character-box">
        <ruby class="hanzi-{{Tone}}">
           {{Hanzi}}
           <rt class="pinyin-{{Tone}}">{{Pinyin}}</rt>
        </ruby>
    </div>
    <div class="translation-box">
        <span class="meaning">{{English}}</span>
    </div>
    <div class="sound-wrapper">{{Sound}}</div>
</div>

<div class="movie-container">
    <div class="scene-header">🎬 The Movie Scene</div>
    
    <div class="grid">
        <div class="label">Actor:</div>
        <div class="data">[{{Initial}}] - {{Actor}}</div>
        
        <div class="label">Set:</div>
        <div class="data">{{Set}}</div>
      
        <div class="label">Tone:</div>
        <div class="data">{{Tone-Location}}</div>

        <div class="label">Props:</div>
        <div class="data">{{Components}}</div>

        <div class="label">Scene:</div>
        <div class="data">{{Scene}}</div>
    </div>
</div>
"""

TRAD_FRONT = """{{#has_traditional_variant}}
<div class="meta-info">
    Phase {{Tags}} • HSK {{HSK_2}} • {{Frequency}}
    <span class="badge-traditional">🇹🇼 Traditional Variant</span>
</div>

<div class="header-row">
   <div class="character-box">
        <ruby class="hanzi-trad">
           {{Traditional}}
           <rt class="pinyin"></rt>
        </ruby>
    </div>
</div>
{{/has_traditional_variant}}
"""

TRAD_BACK = """<div class="meta-info">
    Phase {{Tags}} • HSK {{HSK_2}} • {{Frequency}}
    <span class="badge-traditional">🇹🇼 Traditional Variant</span>
</div>

<div class="header-row">
    <div class="character-box">
        <ruby class="hanzi-{{Tone}}">
           {{Traditional}}
           <rt class="pinyin-{{Tone}}">{{Pinyin}}</rt>
        </ruby>
    </div>
    <div class="translation-box">
        <div class="simplified-ref">Simplified: <span class="hanzi-simpl">{{Hanzi}}</span></div>
        <span class="meaning">{{English}}</span>
    </div>
    <div class="sound-wrapper">{{Sound}}</div>
</div>

<div class="vocab-container">
    <div class="vocab-header">Common Words</div>
    <div class="vocab-zh">{{Common Words}}</div>
    <div class="vocab-en">{{Translation of Words}}</div>
    <div class="sound-wrapper">
        {{Words_Sound}}
        {{Words_English_Sound}}
    </div>
</div>

{{#Image}} <div class="mnemonic-image">{{Image}}</div> {{/Image}}

<div class="movie-container">
    <div class="scene-header">🎬 The Movie Scene</div>
    
    <div class="grid">
        <div class="label">Actor:</div>
        <div class="data">[{{Initial}}] - {{Actor}}</div>
        
        <div class="label">Set:</div>
        <div class="data">{{Set}}</div>
      
        <div class="label">Tone:</div>
        <div class="data">{{Tone-Location}}</div>

        <div class="label">Props:</div>
        <div class="data">{{Components}}</div>

        <div class="label">Scene:</div>
        <div class="data">{{Scene}}</div>
    </div>
</div>

<div class="vocab-container">
    <div class="vocab-header">Notes</div>
    {{Notes}}
    <br>
    <a href="https://hanzicraft.com/character/{{Traditional}}" target="_blank">HanziCraft (Traditional): {{Traditional}}</a>
</div>
"""

ENHANCED_CSS = """/* ===========================
   DEFAULT (LIGHT MODE)
   =========================== */

.card {
    font-family: system-ui, -apple-system, sans-serif;
    font-size: 20px;
    text-align: center;
    color: #333;
    background-color: #f9f9f9;
    padding: 15px;
}

/* Meta Info */
.meta-info {
    font-size: 13px; 
    color: #888; 
    margin-bottom: 12px; 
    text-transform: uppercase; 
    letter-spacing: 0.8px;
}

.badge-recognition-only {
    display: inline-block;
    background-color: #f3e8ff;
    color: #7e22ce;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 12px;
    margin-left: 6px;
    letter-spacing: 0.5px;
}

.badge-traditional {
    display: inline-block;
    background-color: #e0f2fe;
    color: #0369a1;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 12px;
    margin-left: 6px;
    letter-spacing: 0.5px;
}

.simplified-ref {
    font-size: 16px;
    color: #718096;
    margin-bottom: 6px;
}

.hanzi-simpl {
    font-weight: bold;
    color: #2b6cb0;
    font-size: 22px;
}

.hanzi-trad {
    font-size: 80px;
    font-family: "KaiTi", "STKaiti", "SimSun", serif;
    font-weight: normal;
    color: #0369a1;
}

/* Main Hanzi */
.hanzi, .hanzi-1, .hanzi-2, .hanzi-3, .hanzi-4, .hanzi-5 { 
    font-size: 80px; 
    font-family: "KaiTi", "STKaiti", "SimSun", serif;
    font-weight: normal;
    color: #222;
}

.hanzi-1, .pinyin-1 { color: #e53e3e; } /* Tone 1: Red */
.hanzi-2, .pinyin-2 { color: #38a169; } /* Tone 2: Green */
.hanzi-3, .pinyin-3 { color: #3182ce; } /* Tone 3: Blue */
.hanzi-4, .pinyin-4 { color: #805ad5; } /* Tone 4: Purple */
.hanzi-5, .pinyin-5 { color: #718096; } /* Tone 5: Gray */

.meaning { 
    font-size: 26px; 
    font-weight: bold; 
    color: #2d3748; 
    margin-top: 10px; 
    margin-bottom: 5px;
}

.pinyin, .pinyin-1, .pinyin-2, .pinyin-3, .pinyin-4, .pinyin-5 { 
    font-size: 24px; 
    font-weight: 500;
    font-family: "Segoe UI", Arial, sans-serif; 
    margin-bottom: 15px;
}

.vocab-container {
    margin-top: 20px;
    padding: 12px 16px;
    background-color: #ffffff;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.vocab-header {
    font-size: 14px;
    font-weight: bold;
    color: #a0aec0;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.vocab-zh { font-size: 24px; color: #2d3748; margin-bottom: 4px; font-weight: bold; }
.vocab-en { font-size: 18px; color: #4a5568; font-style: italic; }

.movie-container {
    margin-top: 20px;
    padding: 16px;
    background-color: #ffffff;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    text-align: left;
}

.scene-header {
    font-size: 16px;
    font-weight: bold;
    color: #2b6cb0;
    margin-bottom: 12px;
}

.grid {
    display: grid;
    grid-template-columns: 80px 1fr;
    row-gap: 8px;
    font-size: 16px;
}

.label { font-weight: bold; color: #718096; }
.data { color: #2d3748; }

/* Dark Mode Support */
.night_mode .card {
    background-color: #1a202c;
    color: #e2e8f0;
}

.night_mode .vocab-container, .night_mode .movie-container {
    background-color: #2d3748;
    color: #e2e8f0;
}

.night_mode .data { color: #edf2f7; }
.night_mode .vocab-zh { color: #ffffff; }
.night_mode .vocab-en { color: #cbd5e0; }
.night_mode .badge-recognition-only {
    background-color: #4c1d95;
    color: #e9d5ff;
}
.night_mode .badge-traditional {
    background-color: #0c4a6e;
    color: #bae6fd;
}
.night_mode .hanzi-simpl {
    color: #63b3ed;
}
"""

def main():
    print("=" * 70, flush=True)
    print("   ADDING 3RD CARD TYPE: TRADITIONAL RECOGNITION")
    print("=" * 70, flush=True)

    current_templates = request_anki("modelTemplates", modelName="Chinese Character")
    if not current_templates:
        print("Error: Could not fetch templates for 'Chinese Character'", flush=True)
        return

    print("Existing model templates:", list(current_templates.keys()), flush=True)

    if "Traditional Recognition" not in current_templates:
        print("Adding template 'Traditional Recognition' via addModelTemplate...", flush=True)
        tmpl_payload = {
            "model": {"name": "Chinese Character"},
            "template": {
                "Name": "Traditional Recognition",
                "Front": TRAD_FRONT,
                "Back": TRAD_BACK
            }
        }
        res_add = request_anki("addModelTemplate", **tmpl_payload)
        print("addModelTemplate result:", res_add, flush=True)
    else:
        print("Template 'Traditional Recognition' already exists. Updating...", flush=True)

    templates_payload = {
        "model": {
            "name": "Chinese Character",
            "templates": {
                "Recognition": {
                    "Front": REC_FRONT,
                    "Back": REC_BACK
                },
                "Recall": {
                    "Front": RECALL_FRONT,
                    "Back": RECALL_BACK
                },
                "Traditional Recognition": {
                    "Front": TRAD_FRONT,
                    "Back": TRAD_BACK
                }
            }
        }
    }

    print("Updating card templates...", flush=True)
    res_tmpl = request_anki("updateModelTemplates", **templates_payload)
    print("Templates update result:", res_tmpl, flush=True)

    styling_payload = {
        "model": {
            "name": "Chinese Character",
            "css": ENHANCED_CSS
        }
    }

    print("\nUpdating model CSS styling...", flush=True)
    res_style = request_anki("updateModelStyling", **styling_payload)
    print("Styling update result:", res_style, flush=True)

    # Check generated cards
    cids = request_anki("findCards", query='deck:Chinese::Char card:"Traditional Recognition"')
    if cids:
        print(f"\nSuccessfully generated {len(cids):,} 'Traditional Recognition' cards in Anki!", flush=True)
    else:
        print("\nNote: Template added. Anki will generate cards for notes with tag 'has_traditional_variant'.", flush=True)

    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
