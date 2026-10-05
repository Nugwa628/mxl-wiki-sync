"""Generate the prose/reference pages converted from the docs."""
import re, json
from bs4 import BeautifulSoup
from common import *
import settings
from conv import Conv, load, tidy, esc, norm_ws, PAGE_TITLES

def page_soup(path):
    soup = load(path)
    p = soup.select_one('.page')
    h = p.find('h2', recursive=False) or p.find('h2')
    if h and not h.find_parent(class_='changelog'):
        h.decompose()
    return soup, p

def drop_first_heading(text):
    return re.sub(r'^\s*(<span id="[^"]*"></span>)?== [^\n]* ==\n+', r'\1', text, count=1)

def convert(path, table_class='wikitable mxl-table', hb=2):
    soup, p = page_soup(path)
    return tidy(Conv(heading_base=hb, table_class=table_class).blocks(p))

def wrap(body, src, cats, lead_styles=True):
    return ('{{MXL styles}}\n' if lead_styles else '') + body.strip() + '\n' + footer(src, cats)

# ------------------------------------------------------------------ patch notes
def patch_notes():
    soup, p = page_soup('raw/index.html')
    toc = p.find(id='toc')
    if toc: toc.decompose()
    cl = p.select_one('.changelog')
    body = tidy(Conv(heading_base=2, table_class='wikitable mxl-table').blocks(cl))
    # docs h1 "Median XL - Σ 2.14" becomes a level-2 heading; make it the lead line instead
    body = re.sub(r'^== (Median XL - .*?) ==\n', r"This page reproduces the official version log for '''\1''' (current release).\n\n", body)
    body = ("{{Main|Patch Notes}}\n" if False else '') + body
    extra = ("\n== Item and skill histories ==\n"
             "Many item, skill and area pages on this wiki include a collapsible '''Version history''' table that lists every change to that "
             "entry across past patches (from 2.0.0 onward), for example [[Grim Fang#Version history|Grim Fang]] or [[Relics#Version history|Relics]].\n")
    add_page('Patch Notes', wrap(body + extra, '/', ['Patch notes']))
    for r in ('Version Log', 'Patch notes', 'Changelog', 'Version log', settings.VERSION, 'Sigma ' + settings.VERSION):
        add_redirect(r, 'Patch Notes')

# ------------------------------------------------------------------ classes
CLASSES = ['Amazon', 'Assassin', 'Barbarian', 'Druid', 'Necromancer', 'Paladin', 'Sorceress']

def extract_sections(text, names):
    """Return list of level-2 sections (by heading name) from existing wikitext, verbatim."""
    parts = re.split(r'(?m)^(==[^=].*?==)\s*$', text)
    out = []
    for i in range(1, len(parts), 2):
        h = parts[i].strip('= ').strip()
        if h.lower() in names:
            out.append(parts[i] + parts[i + 1].rstrip())
    return out

def class_infobox(soup_page, name):
    txt = soup_page.get_text('\n')
    def grab(stat):
        m = re.search(stat + r'\s*:\s*(\d+)', norm_ws(soup_page.get_text(' ')))
        return m.group(1) if m else ''
    plain = norm_ws(soup_page.get_text(' '))
    lvl = re.search(r'(\+[\d.]+ life, \+[\d.]+ mana per level)', plain)
    vit = re.search(r'Gains (\+[\d.]+ life) per point into vitality', plain)
    ene = re.search(r'Gains (\+[\d.]+ mana) per point into energy', plain)
    blacks = soup_page.select('div.black')
    weapons = armour = ''
    if blacks:
        weapons = Conv().inline(blacks[0]).strip()
    if len(blacks) > 1:
        armour = Conv().inline(blacks[1]).strip()
    return ('{{Infobox class\n'
            f'|name={name}\n|image={name}.gif\n|str={grab("Strength")}\n|dex={grab("Dexterity")}\n|vit={grab("Vitality")}\n|ene={grab("Energy")}\n'
            f'|perlevel={lvl.group(1) if lvl else ""}\n|vitality={vit.group(1) if vit else ""}\n|energy={ene.group(1) if ene else ""}\n'
            f'|weapons={weapons}\n|armour={armour}\n}}}}\n')

def class_pages():
    for c in CLASSES:
        path = f'raw/doc_class_{c.lower()}.html'
        soup, p = page_soup(path)
        ib = class_infobox(p, c)
        body = tidy(Conv().blocks(p))
        body = drop_first_heading(body)
        old = EXISTING.get(c, {}).get('text', '')
        kept = extract_sections(old, {'list of guides'})
        import gen_skills
        skills_txt, nskills = gen_skills.class_skills(c, {t.lower(): t for t in EXISTING if not EXISTING[t]['text'].lstrip().upper().startswith('#REDIRECT') or True}, {f['name'].replace('_', ' ').lower(): f['name'].replace('_', ' ') for f in EXPORT['files']})
        txt = '{{MXL styles}}\n' + ib + body.strip() + '\n\n' + skills_txt + '\n'
        if kept:
            for sec in kept:
                if sec.lower().startswith('==skills') or sec.lower().startswith('== skills'):
                    sec = re.sub(r'^(==\s*Skills\s*==)', r'\1\n<div class="mxl-note">This skill overview is maintained by wiki editors and is not part of the official game guide; some values may be from older versions.</div>', sec)
                sec = re.sub(r'\[\[Category:[^\]]*\]\]', '', sec).rstrip()
                txt += sec + '\n\n'
        txt += f"== Related pages ==\n* [[Base Items]] – class-specific weapons and armour\n* [[Sets#{c} Sets|{c} sets]]\n* [[Challenges#Ennead Challenge|Ennead Challenge]] – class charm\n* [[Mercenaries]]\n\n"
        txt += changelog(c)
        txt += footer(f'/doc/class/{c.lower()}', ['Classes'])
        add_page(c, txt)

def mercenaries():
    body = drop_first_heading(convert('raw/doc_class_hirelings.html'))
    add_page('Mercenaries', wrap(body, '/doc/class/hirelings', ['Mercenaries', 'Characters']))
    for r in ('Hirelings', 'Hireling', 'Mercenary', 'Mercs', 'Merc'):
        add_redirect(r, 'Mercenaries')

# ------------------------------------------------------------------ quests
def section_changelogs(text, level='==='):
    """Append version-history tables to sections whose title has an entry in the changelog data."""
    pat = re.compile(r'(?m)^%s ([^=\n]+) %s$' % (level, level))
    out = []
    pos = 0
    ms = list(pat.finditer(text))
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else None
        seg = text[m.start(): end]
        # stop at next higher heading
        nxt = re.search(r'(?m)^== [^=]', seg[len(m.group(0)):])
        name = m.group(1).strip()
        key = CL_LOWER.get(name.lower()) or CL_LOWER.get(re.sub(r'^The ', '', name).lower())
        if key:
            add = f"\n'''Version history''' (click to expand):\n{{{{Changelog|{key}|{settings.VERSION_FULL}}}}}\n"
            if nxt:
                cut = len(m.group(0)) + nxt.start()
                seg = seg[:cut].rstrip() + '\n' + add + '\n' + seg[cut:]
            else:
                seg = seg.rstrip() + '\n' + add + '\n'
        out.append((m.start(), end, seg))
    if not out:
        return text
    res = text[:out[0][0]]
    for s, e, seg in out:
        res += seg
    return res

def quest_page(path, title, src, cats, redirect_level=True):
    body = convert(path)
    body = drop_first_heading(body)
    body = body.replace('\n==== ', '\n=== ').replace(' ====\n', ' ===\n')
    body = section_changelogs(body)
    add_page(title, wrap(body, src, cats))
    names = re.findall(r'(?m)^=== ([^=\n]+) ===$', body)
    for n in names:
        add_redirect(n.strip(), f'{title}#{n.strip()}')
    return names

def quests():
    quest_page('raw/doc_quests_challenges.html', 'Challenges', '/doc/quests/challenges', ['Quests', 'Endgame'])
    quest_page('raw/doc_quests_dungeons.html', 'Dungeons', '/doc/quests/dungeons', ['Quests', 'Endgame', 'Dungeons'])
    quest_page('raw/doc_quests_rifts.html', 'Nephalem Rifts', '/doc/quests/rifts', ['Quests', 'Endgame', 'Rifts'])
    add_redirect('Rifts', 'Nephalem Rifts')
    add_redirect('Rift', 'Nephalem Rifts')
    add_redirect('Uberquests', 'Dungeons')
    add_redirect('Endgame Dungeons', 'Dungeons')
    add_redirect('Endgame Quests', 'Dungeons')

# ------------------------------------------------------------------ items (generic)
def cube():
    body = drop_first_heading(convert('raw/doc_items_cube.html'))
    add_page('Cube Recipes', wrap(body, '/doc/items/cube', ['Items', 'Crafting']))
    for r in ('Cube recipes', 'Cube', 'Horadric Cube Recipes', 'Crafting', 'Disenchanting', 'Shrine crafting', 'Jewelcrafting', 'Reagents'):
        add_redirect(r, 'Cube Recipes')

def socketables():
    body = drop_first_heading(convert('raw/doc_items_socketables.html'))
    # anchors for each gem / rune name cell
    names = []
    def anc(m):
        n = m.group(1).strip()
        names.append(n)
        return f'| <span id="{n.replace(" ", "_")}"></span><span class="mxl-rune">{m.group(1)}</span>'
    body = re.sub(r'\| <span class="mxl-rune">([^<]+)</span>\s*$', anc, body, flags=re.M)
    add_page('Gems and Runes', wrap(body, '/doc/items/socketables', ['Items', 'Socketables']))
    for r in ('Runes', 'Gems', 'Socketables', 'Rune', 'Gem', 'Gems and runes'):
        add_redirect(r, 'Gems and Runes')
    for n in names:
        add_redirect(n.strip(), f'Gems and Runes#{n.strip()}')
    return names

def simple(path, title, src, cats, redirects=(), merge_changelog=None, table_class='wikitable mxl-table'):
    body = drop_first_heading(convert(path, table_class=table_class))
    if merge_changelog:
        body += '\n\n' + changelog(merge_changelog)
    add_page(title, wrap(body, src, cats))
    for r in redirects:
        add_redirect(r, title)

def affixes():
    soup, p = page_soup('raw/doc_wiki_affixes.html')
    w = p.find(id='wait')
    if w: w.decompose()
    fs = p.find_all('fieldset')
    calc_rare = ('<div class="mxl-formula">affix level = ilvl − ⌊qlvl / 2⌋ &nbsp;&nbsp;(if ilvl &lt; 99 − ⌊qlvl / 2⌋)<br />'
                 'affix level = 2 × ilvl − 99 &nbsp;&nbsp;(otherwise)</div>\n'
                 "where ''ilvl'' is first capped at 99 and raised to at least ''qlvl'', and the result is capped at 99. "
                 "Use <code><nowiki>{{Affix level|item level|quality level}}</nowiki></code> to calculate it on any page, e.g. "
                 "an item level 85 item with quality level 80 has affix level {{Affix level|85|80}}.\n\n"
                 "'''Quick reference''' – affix level by item level (rows) and quality level (columns):\n"
                 "{{#invoke:Affix level|table}}\n")
    calc_craft = ("Crafted items use the same formula with the quality level clamped between 71 and 90. For '''jewels''', quality level is 1 and the "
                  "item level is first reduced to 95% (rounded down, minimum 1). The output item level is capped at 99.\n"
                  "Use <code><nowiki>{{Affix level|item level|quality level|type=craft}}</nowiki></code> or "
                  "<code><nowiki>{{Affix level|item level|type=craft|jewel=yes}}</nowiki></code>.\n")
    for i, f in enumerate(fs):
        f.replace_with(BeautifulSoup(f'<p>%%CALC{i}%%</p>', 'lxml').p)
    t = p.find('table', id='tablesorter')
    body = tidy(Conv(table_class='mxl-table sortable mxl-compact').blocks(p))
    body = drop_first_heading(body)
    body = body.replace('%%CALC0%%', calc_rare).replace('%%CALC1%%', calc_craft)
    body = re.sub(r'%%CALC\d+%%', '', body)
    body = body.replace('Sort the table by clicking a column name (+shift for multiple).', 'Sort the table by clicking a column name (shift-click to sort by several columns).')
    body = body.replace('Hover mouse over elements for help.', 'Hover over dotted column headers for help. Use your browser\'s find (Ctrl+F) to search the table.')
    add_page('Item Affixes', wrap(body, '/doc/wiki/affixes', ['Items', 'Crafting']))
    for r in ('Affixes', 'Prefixes', 'Suffixes', 'Affix level', 'Rare affixes', 'Item affixes'):
        add_redirect(r, 'Item Affixes')

def reference():
    simple('raw/doc_concepts_defense.html', 'Defense and Block', '/doc/concepts/defense', ['Game mechanics'],
           ('Defense', 'Block', 'Blocking', 'Chance to Block', 'Defense rating'))
    simple('raw/doc_concepts_experience.html', 'Experience', '/doc/concepts/experience', ['Game mechanics'],
           ('XP', 'Exp', 'Leveling', 'Level penalty'), merge_changelog='Experience')
    simple('raw/doc_concepts_spellfocus.html', 'Spell Focus', '/doc/concepts/spellfocus', ['Game mechanics'], ('Spellfocus', 'Spell focus'))
    simple('raw/doc_concepts_minion.html', 'Minion Mechanics', '/doc/concepts/minion', ['Game mechanics'],
           ('Minions', 'Summons', 'Minion', 'Summoning'))
    simple('raw/doc_wiki_cycles.html', 'Cycles', '/doc/wiki/cycles', ['Items', 'Charms'], ('Cycle', 'Corrupted Wormhole'), merge_changelog='Cycles')
    simple('raw/doc_wiki_umos.html', 'Unique Mystic Orbs', '/doc/wiki/umos', ['Items', 'Mystic Orbs'], ('UMO', 'UMOs', 'Unique Mystic Orb'))
    simple('raw/doc_wiki_shrines.html', 'Shrine Bonuses', '/doc/wiki/shrines', ['Items', 'Crafting'], ('Shrines', 'Shrine', 'Shrine bonuses'))
    simple('raw/doc_wiki_trophies.html', 'Trophy Bonuses', '/doc/wiki/trophies', ['Items', 'Charms'], ('Trophies', 'Trophy', 'Trophy bonuses'), merge_changelog='Trophies')
    simple('raw/doc_wiki_armorlooks.html', 'Armor Looks', '/doc/wiki/armorlooks', ['Items'], ('Armour Looks', 'Armor looks', 'Armour looks'))
    # Relics: replace short stub (which pointed to the docs) and keep its version-history call
    body = drop_first_heading(convert('raw/doc_wiki_relics.html'))
    old = EXISTING['Relics']['text']
    keep = [re.sub(r'^(\{\{Changelog\|[^|}]+)\|[0-9.]+\}\}$', lambda m: m.group(1) + '|' + settings.VERSION_FULL + '}}', k) for k in re.findall(r'\{\{Changelog\|[^}]*\}\}', old)]
    txt = body.strip() + '\n\n== Version history ==\n' + ('\n'.join(keep) if keep else '{{Changelog|Relics|' + settings.VERSION_FULL + '}}')
    add_page('Relics', wrap(txt, '/doc/wiki/relics', ['Items', 'Relics']))
    add_redirect('Relic', 'Relics')

def build():
    patch_notes()
    if settings.CLASS_PAGES:
        class_pages()
    mercenaries()
    quests()
    cube()
    socketables()
    affixes()
    reference()
