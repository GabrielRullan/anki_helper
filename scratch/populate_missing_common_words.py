import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
ANKICONNECT_URL = 'http://127.0.0.1:8765'

def invoke(action, **params):
    req = urllib.request.Request(
        ANKICONNECT_URL,
        data=json.dumps({'action': action, 'version': 6, 'params': params}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        if res.get('error'):
            raise Exception(res['error'])
        return res.get('result')

with open('scratch/levels_68_88.json', 'r', encoding='utf-8') as f:
    levels_data = json.load(f)

# Built-in high quality common words map for the 64 characters
common_words_dict = {
    '漾': ('荡漾, 溢漾', 'Rippling, Overflowing'),
    '抠': ('抠门儿, 抠出', 'Stingy/tight-fisted, Dig out'),
    '竣': ('竣工, 完竣', 'Completion of project, Finished'),
    '夌': ('高夌, 夌霄', 'High mound, Soar to the sky'),
    '舛': ('命途多舛, 舛错', 'Fateful/unfortunate life, Error/mistake'),
    '飙': ('飙车, 狂飙', 'Drag racing, Violent storm'),
    '飓': ('飓风', 'Hurricane/typhoon'),
    '缤': ('缤纷, 落英缤纷', 'Colorful/flourishing, Falling petals in abundance'),
    '雚': ('雚芦, 雚草', 'Heron/reeds, Reed grass'),
    '孛': ('彗孛, 孛星', 'Comet, Shooting star'),
    '捎': ('捎信, 捎带', 'Bring a message, Bring along'),
    '溉': ('灌溉, 涵溉', 'Irrigate/water crops, Submerge/irrigate'),
    '秤': ('杆秤, 台秤', 'Steelyard scale, Platform scale'),
    '蔗': ('甘蔗, 蔗糖', 'Sugarcane, Cane sugar'),
    '巅': ('巅峰, 山巅', 'Peak/pinnacle, Mountain top'),
    '臊': ('害臊, 臊气', 'Bashful/ashamed, Rank odor'),
    '拌': ('搅拌, 凉拌', 'Stir/mix, Cold tossed dish'),
    '涝': ('旱涝, 防涝', 'Drought and flood, Flood prevention'),
    '秧': ('秧苗, 插秧', 'Rice seedling, Transplant rice seedlings'),
    '惋': ('惋惜, 惋恨', 'Regret/sympathize, Deep regret'),
    '窿': ('窟窿, 熔窿', 'Hole/cave, Mine shaft'),
    '椰': ('椰子, 椰汁', 'Coconut, Coconut juice'),
    '攒': ('积攒, 攒钱', 'Accumulate, Save money'),
    '汛': ('防汛, 汛期', 'Flood control, High water season'),
    '涮': ('涮羊肉, 涮洗', 'Instant-boiled mutton, Rinse/wash'),
    '沏': ('沏茶', 'Brew tea'),
    '潦': ('潦草, 潦倒', 'Sloppy/hasty, Down on ones luck'),
    '鳄': ('鳄鱼, 鳄鱼泪', 'Alligator/crocodile, Crocodile tears'),
    '刁': ('刁蛮, 刁钻', 'Unreasonable/tricky, Cunning/sly'),
    '叼': ('叼着, 叼走', 'Holding in mouth, Carry away in mouth'),
    '蘸': ('蘸酱, 蘸水', 'Dip in sauce, Dip in water'),
    '惦': ('惦记, 惦念', 'Miss/remember, Keep in mind'),
    '绯': ('绯闻, 绯红', 'Scandal/gossip, Crimson red'),
    '撬': ('撬开, 撬锁', 'Pry open, Pick a lock'),
    '拄': ('拄拐杖, 拄着', 'Lean on a cane, Prop up'),
    '抡': ('抡起, 抡拳', 'Brandish/swing up, Swing a fist'),
    '媲': ('媲美', 'Rival/match in beauty'),
    '炖': ('炖肉, 清炖', 'Stewed meat, Clear broth stew'),
    '灸': ('针灸, 艾灸', 'Acupuncture and moxibustion, Moxibustion'),
    '煲': ('煲汤, 煲仔饭', 'Slow-cooked soup, Claypot rice'),
    '诽': ('诽谤, 诽议', 'Slander/defame, Criticism/vilification'),
    '讹': ('讹诈, 讹传', 'Extort/blackmail, False rumor'),
    '酣': ('酣睡, 酣畅', 'Sound asleep, Cheerful/hearty'),
    '酥': ('酥饼, 酥软', 'Crispy pastry, Soft and flaky'),
    '酗': ('酗酒', 'Binge drinking/alcohol abuse'),
    '酵': ('发酵, 酵母', 'Ferment, Yeast'),
    '孪': ('孪生, 孪生兄弟', 'Twin, Twin brothers'),
    '弈': ('博弈, 棋弈', 'Game theory/contest, Chess game'),
    '盹': ('打盹儿', 'Take a nap/doze off'),
    '赡': ('赡养, 赡养费', 'Provide for parents, Alimony/support fee'),
    '刨': ('刨床, 刨根问底', 'Planing machine, Dig to the root'),
    '馁': ('气馁, 冻馁', 'Discouraged, Cold and hungry'),
    '馋': ('嘴馋, 馋嘴', 'Gluttonous/craving food, Greedy eater'),
    '冗': ('冗长, 冗余', 'Tedious/lengthy, Redundant'),
    '粽': ('粽子, 肉粽', 'Sticky rice dumpling, Pork rice dumpling'),
    '掰': ('掰开, 掰断', 'Pry open with hands, Snap in two'),
    '屹': ('屹立, 屹然', 'Stand towering/firm, Unshakeable'),
    '卤': ('卤味, 卤肉', 'Marinated stewed food, Braised pork'),
    '阂': ('隔阂', 'Barrier/estrangement'),
    '踊': ('踊跃, 踊跃发言', 'Eager/enthusiastic, Vigorously speak'),
    '跤': ('摔跤', 'Wrestle/tumble down'),
    '囱': ('烟囱', 'Chimney'),
    '殃': ('遭殃, 祸殃', 'Suffer disaster, Misfortune')
}

print(f"Updating {len(common_words_dict)} character notes with Common Words in Anki...")

updated_count = 0
for h, (cw, tw) in common_words_dict.items():
    n_ids = invoke('findNotes', query=f'note:"Chinese Character - Double" Hanzi:"{h}"')
    if not n_ids:
        n_ids = invoke('findNotes', query=f'note:"Chinese Character - Double" Simplified:"{h}"')

    if n_ids:
        n_id = n_ids[0]
        invoke('updateNoteFields', note={
            'id': n_id,
            'fields': {
                'Common Words': cw,
                'Translation of Words': tw
            }
        })
        updated_count += 1

print(f"Successfully updated Common Words for {updated_count} notes!")
