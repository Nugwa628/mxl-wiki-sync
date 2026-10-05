import json, re, collections, os
from conv import esc
import settings

# Snapshot of the wiki taken before the first docs import. Used so page titles stay stable
# (e.g. "Athulua's Wrath (item)" because "Athulua's Wrath" was already a skill page).
EXPORT = json.load(open(settings.PRE_IMPORT, encoding='utf-8'))
EXISTING = EXPORT['pages']
EXIST_LOWER = {t.lower(): t for t in EXISTING}
# Pages that people created on the live wiki since then (not made by this tool) also block titles.
EXIST_LOWER.update({t.lower(): t for t in settings.LIVE_OTHER_TITLES})

# keys known to Module:Changelog/data (entity names with version history)
_cl = settings.CHANGELOG_DATA or EXISTING['Module:Changelog/data']['text']
CL_KEYS = set(re.findall(r'\n\t\t\["([^"]+)"\] = \{', _cl)) | set(re.findall(r'\n\t\t(\w+) = \{', _cl))
CL_LOWER = {k.lower(): k for k in sorted(CL_KEYS)}

PAGES = collections.OrderedDict()   # title -> text
REDIRECTS = collections.OrderedDict()  # title -> target
OVERWRITE_OK = {'Mercenaries', 'Experience', 'Relics',
                'Amazon', 'Assassin', 'Barbarian', 'Druid', 'Necromancer', 'Paladin', 'Sorceress'}
CLAIMED = set()

def exists_on_wiki(title):
    return title.lower() in EXIST_LOWER

def claim(title, fallback_suffix):
    """Return a free title for a new page (avoids existing wiki pages and our own pages)."""
    t = title
    if (exists_on_wiki(t) and t not in OVERWRITE_OK) or t.lower() in {c.lower() for c in CLAIMED}:
        t = f'{title} ({fallback_suffix})'
    n = 2
    while (exists_on_wiki(t) and t not in OVERWRITE_OK) or t.lower() in {c.lower() for c in CLAIMED}:
        t = f'{title} ({fallback_suffix} {n})'; n += 1
    CLAIMED.add(t)
    return t

def add_page(title, text):
    assert title not in PAGES, title
    PAGES[title] = text

SKILL_NAMES = {f['name'][:-9].replace('_', ' ').lower() for f in EXPORT['files'] if f['name'].endswith('_icon.gif')}

def add_redirect(src, target):
    if src.lower() in SKILL_NAMES:
        return
    if src == target.split('#')[0]:
        return
    low = src.lower()
    if exists_on_wiki(src) or low in {p.lower() for p in PAGES} or low in {r.lower() for r in REDIRECTS} or low in {c.lower() for c in CLAIMED}:
        return
    REDIRECTS[src] = target

CL_BROKEN = {'Barbarian', 'Black Razor'}  # nested data that Module:Changelog can't render

def changelog(name):
    k = CL_LOWER.get(name.lower())
    if k and k not in CL_BROKEN:
        return f'== Version history ==\nChanges to {esc(name)} in past patches (click to expand):\n{{{{Changelog|{k}|{settings.VERSION_FULL}}}}}\n'
    return ''

def anchor(text):
    return text.replace('[', '').replace(']', '').replace('|', '').replace('#', '')

NAV = '{{Navbox Median XL}}'

def footer(src_path, cats):
    c = '\n'.join(f'[[Category:{x}]]' for x in cats)
    return f'\n{NAV}\n{{{{Docs source|{src_path}}}}}\n{c}\n'

def plural_lower(cat):
    return cat.lower() if cat else cat

def rng(a, b):
    if a is None and b is None:
        return ''
    if a == b or b is None:
        return str(a)
    if a is None:
        return str(b)
    return f'{a} – {b}'
