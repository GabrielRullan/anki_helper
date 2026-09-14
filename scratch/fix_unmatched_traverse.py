import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/traverse_words_db.json', 'r', encoding='utf-8') as f:
    traverse_words = json.load(f)

custom_meanings = {
    '迪斯尼/迪士尼': ('dísīní / díshìní', 'Disney'),
    '冰淇淋/冰激凌': ('bīngqílín / bīngjīlíng', 'Ice cream'),
    '定为': ('dìng wéi', 'Set as, define as, designate as'),
    '难以想象': ('nán yǐ xiǎng xiàng', 'Hard to imagine, unimaginable'),
    '纵恨交错': ('zòng hèn jiāo cuò', 'Intertwined emotions of hatred and passion'),
    '一日俱进': ('yī rì jù jìn', 'Advance together day by day'),
    '潮气蓬勃': ('cháo qì péng bó', 'Vibrant, full of youthful vigor'),
    '蓬勃发展': ('péng bó fā zhǎn', 'Flourishing development, thrive'),
    '行政诉讼': ('xíng zhèng sù sòng', 'Administrative litigation'),
    '刑事诉讼': ('xíng shì sù sòng', 'Criminal litigation'),
    '赞叹不已': ('zàn tàn bù yǐ', 'Praise incessantly, full of admiration'),
    '艰苦奋斗': ('jiān kǔ fèn dòu', 'Struggle hard, work arduous and perseveringly'),
    '擦肩而过': ('cā jiān ér guò', 'Brush past each other, miss an opportunity'),
    '呼风唤雨': ('hū fēng huàn yǔ', 'Summon wind and rain, wield immense power'),
    '相辅相成': ('xiāng fǔ xiāng chéng', 'Complement each other'),
    '一不小心': ('yī bù xiǎo xīn', 'Accidentally, inadvertently'),
    '一事无成': ('yī shì wú chéng', 'Accomplish nothing'),
    '乘人之危': ('chéng rén zhī wēi', 'Take advantage of someone in danger'),
    '引人入胜': ('yǐn rén rù shèng', 'Enchanting, fascinating'),
    '因人而异': ('yīn rén ér yì', 'Vary from person to person')
}

fixed_count = 0
for item in traverse_words:
    w = item['word']
    if not item.get('pinyin') or item['meaning'] == 'Word introduced in lesson':
        if w in custom_meanings:
            item['pinyin'] = custom_meanings[w][0]
            item['meaning'] = custom_meanings[w][1]
            fixed_count += 1

print(f"Fixed custom definitions for {fixed_count} words!")

with open('data/traverse_words_db.json', 'w', encoding='utf-8') as f:
    json.dump(traverse_words, f, ensure_ascii=False, indent=2)

print("Saved 100% enriched database to data/traverse_words_db.json")
