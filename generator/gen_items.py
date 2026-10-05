"""Generate pages for uniques, sets, runewords and base items."""
import json, re, collections
from common import *
from conv import esc, Conv, load, tidy, norm_ws, IMAGES_USED
from tooltip import render_lines, line_text, tooltip_template

SKILLS = {f['name'][:-9].replace('_', ' ').lower() for f in EXPORT['files'] if f['name'].endswith('_icon.gif')}

U = json.load(open('data_uniques.json', encoding='utf-8'))
S = json.load(open('data_sets.json', encoding='utf-8'))
R = json.load(open('data_runewords.json', encoding='utf-8'))
B = json.load(open('data_bases.json', encoding='utf-8'))

BASE_TITLE = {}   # base name -> page title
UNIQ_TITLE = {}   # (kind, name) -> page title
SET_TITLE = {}
RW_TITLE = {}

def safe_changelog(name, allow_single=True):
    if name.lower() in SKILLS:
        return ''
    if not allow_single and ' ' not in name:
        return ''
    return changelog(name)

def cat_link(cat):
    return f'[[:Category:{cat}|{cat}]]'

def base_link(b):
    if not b:
        return ''
    t = BASE_TITLE.get(b)
    if t:
        return f'[[{t}|{esc(b)}]]' if t != b else f'[[{t}]]'
    return esc(b)

# ------------------------------------------------------------------ titles
def assign_titles():
    for b in B:
        BASE_TITLE[b['name']] = claim(b['name'], 'base item')
    seen = set()
    for kind in ('tiered', 'sacred'):
        for it in U[kind]:
            key = (kind, it['name'])
            if key in seen:
                continue
            seen.add(key)
            UNIQ_TITLE[key] = claim(it['name'], 'item')
    for s in S:
        SET_TITLE[s['name']] = claim(s['name'], 'set')
    for name in dict.fromkeys(r['name'] for r in R):
        RW_TITLE[name] = claim(name, 'runeword')

# ------------------------------------------------------------------ uniques
SACRED_DROP = {
    'SU': 'Hell difficulty, typically from area level 104 and beyond',
    'SSU': 'Hell difficulty, from area level 119 areas',
    'SSSU': 'Hell difficulty, from area level 130 areas',
}

def unique_pages():
    groups = collections.defaultdict(list)
    for kind in ('tiered', 'sacred'):
        for it in U[kind]:
            groups[(kind, it['category'])].append(it)
    byname = collections.defaultdict(list)
    for kind in ('tiered', 'sacred'):
        for it in U[kind]:
            byname[(kind, it['name'])].append(it)

    for (kind, name), its in byname.items():
        title = UNIQ_TITLE[(kind, name)]
        it = its[0]
        cat = it['category']
        quality = 'unique'
        variants = [(it2, v) for it2 in its for v in it2['variants']]
        req = [v['fields'].get('reqlevel') for _, v in variants if v['fields'].get('reqlevel') is not None]
        ilv = [v['fields'].get('ilvl') for _, v in variants if v['fields'].get('ilvl') is not None]
        cls = next((v['fields']['classonly'] for _, v in variants if v['fields'].get('classonly')), '')
        ib = ['{{Infobox unique', f'|name={esc(name)}', f'|image={it["image"] or ""}', f'|quality={quality}']
        if kind == 'tiered':
            ib.append('|type=[[Tiered Uniques|Tiered unique]]')
            if len(it['variants']) > 1:
                ib.append(f'|tiers={len(it["variants"])}')
        else:
            ib.append('|type=[[Sacred Uniques|Sacred unique]]')
            var = it.get('variation')
            if var:
                ib.append(f'|variation={var}')
                ib.append(f'|drops={SACRED_DROP[var]}')
            else:
                ib.append('|drops=Hell difficulty')
        if it.get('base'):
            ib.append(f'|base={base_link(it["base"])}')
        ib.append(f'|category={cat_link(cat)}')
        if cls:
            ib.append(f'|class=[[{cls}]]')
        if req:
            ib.append(f'|reqlevel={rng(min(req), max(req))}')
        if ilv:
            ib.append(f'|ilvl={rng(min(ilv), max(ilv))}')
        ib.append('}}')

        # lead
        lead = f"'''{esc(name)}''' is a "
        if kind == 'tiered':
            lead += f"[[Tiered Uniques|tiered unique]] "
        else:
            lead += f"[[Sacred Uniques|sacred unique]] "
        if it.get('base'):
            lead += f"{base_link(it['base'])} ({plural_lower(cat)})"
        else:
            lead += f"item ({plural_lower(cat)})"
        lead += '.'
        if kind == 'tiered' and len(it['variants']) == 4:
            lead += (f" Like every tiered unique it exists in four tiers, matching the tier of the base item: higher tiers have"
                     f" better stats but higher requirements (required level {rng(min(req), max(req))}).") if req else ''
        if kind == 'sacred' and it.get('variation'):
            lead += f" It is the '''{it['variation']}''' variation for its base, and drops on {SACRED_DROP[it['variation']]}."
        if cls:
            lead += f" It can only be used by the [[{cls}]]."
        if title != name and exists_on_wiki(name):
            hat = f"{{{{Hatnote|This page is about the item. For other uses, see [[{name}]].}}}}\n"
        else:
            hat = ''

        rows = []
        for it2, v in variants:
            label = v['label'] or (it2.get('variation') if kind == 'sacred' else None)
            rows.append(tooltip_template(name, quality, v['lines'], image=it2['image'], label=label,
                                         base=esc(it2['base']) if it2.get('base') else None))
        body = '{{Tooltip row|\n' + '\n'.join(rows) + '\n}}'

        others = [o for o in groups[(kind, cat)] if o['name'] != name]
        seen = []
        for o in others:
            if o['name'] not in seen:
                seen.append(o['name'])
        olinks = ' · '.join(f"[[{UNIQ_TITLE[(kind, n)]}|{esc(n)}]]" for n in seen)
        kindname = 'Tiered Uniques' if kind == 'tiered' else 'Sacred Uniques'

        txt = hat + '\n'.join(ib) + '\n' + lead + '\n\n== Stats ==\n' + body + '\n\n'
        if kind == 'sacred' and it.get('variation'):
            txt += ("== Notes ==\n* All sacred uniques come with the maximum number of sockets allowed for their item type.\n"
                    "* Skill bonuses without a class requirement are [[OSkills|oskills]] and work for any class.\n\n")
        else:
            txt += ("== Notes ==\n* Unique items come with the maximum number of sockets allowed for their item type"
                    + (" (lower tiers have fewer sockets)" if kind == 'tiered' and len(it['variants']) > 1 else '') + ".\n"
                    "* Skill bonuses without a class requirement are [[OSkills|oskills]] and work for any class.\n\n")
        txt += safe_changelog(name)
        if olinks:
            txt += f"\n== Other {kindname.lower()}: {cat} ==\n{olinks}\n"
        txt += footer('/doc/items/' + ('tiereduniques' if kind == 'tiered' else 'sacreduniques'),
                      [kindname, 'Unique items', cat])
        add_page(title, txt)

def intro_blocks(path, stop_at_genbig_index=1):
    """Convert the intro of a docs page (everything before the n-th p.genbig heading)."""
    page = load(path).select_one('.page')
    h = page.find('h2')
    if h: h.decompose()
    container = page.select_one('.text_on_the_left') or page
    out = []
    n = 0
    conv = Conv()
    for c in list(container.children):
        if getattr(c, 'name', None) == 'p' and 'genbig' in (c.get('class') or []):
            n += 1
            if n > stop_at_genbig_index:
                break
            continue
        if getattr(c, 'name', None) in ('table',) and n >= 1 and ('uniques' in (c.get('class') or []) or 'sets' in (c.get('class') or []) or 'runewords_table' in (c.get('class') or [])):
            break
        out.append(c)
    from bs4 import BeautifulSoup
    wrap = BeautifulSoup('<div></div>', 'lxml').div
    for c in out:
        wrap.append(c.__copy__() if hasattr(c, '__copy__') else c)
    return tidy(conv.blocks(wrap))

def unique_overviews():
    for kind, path, title in (('tiered', 'raw/doc_items_tiereduniques.html', 'Tiered Uniques'),
                               ('sacred', 'raw/doc_items_sacreduniques.html', 'Sacred Uniques')):
        intro = intro_blocks(path)
        intro = re.sub(r'^== .* ==\n+', '', intro)
        cats = list(dict.fromkeys(i['category'] for i in U[kind]))
        lines = ['{{MXL styles}}', intro.strip(), '',
                 '== How to use this page ==',
                 f"The table below lists all {len({i['name'] for i in U[kind]})} {title.lower()}. Click a column header to sort "
                 "(e.g. by required level), or click an item name for its full stats"
                 + (", all four tiers," if kind == 'tiered' else ",") + " and version history.",
                 'Items are also grouped in categories by item type: ' + ', '.join(f"[[:Category:{c}|{c}]]" for c in cats[:6]) + ', …',
                 '']
        lines.append('== Item list ==')
        if kind == 'tiered':
            hdr = '{| class="mxl-table sortable mxl-compact"\n! class="unsortable" | !! Name !! Base !! Item group !! Req. lvl T1 !! Req. lvl T2 !! Req. lvl T3 !! Req. lvl T4 !! Class'
        else:
            hdr = '{| class="mxl-table sortable mxl-compact"\n! class="unsortable" | !! Name !! Variation !! Base !! Item group !! Req. lvl !! Item lvl !! Class'
        lines.append('<div class="mxl-scroll">\n' + hdr)
        for it in U[kind]:
            t = UNIQ_TITLE[(kind, it['name'])]
            img = f"[[File:{it['image']}|x36px|link={t}]]" if it['image'] else ''
            cls = next((v['fields']['classonly'] for v in it['variants'] if v['fields'].get('classonly')), '')
            row = ['|-', f'| {img}', f'| [[{t}|<span class="mxl-unique">{esc(it["name"])}</span>]]']
            if kind == 'tiered':
                row.append(f'| {base_link(it["base"])}')
                row.append(f'| {it["category"]}')
                req = [v['fields'].get('reqlevel', '') for v in it['variants']]
                if len(req) == 4:
                    row += [f'| {r}' for r in req]
                else:
                    row += [f'| {req[0] if req else ""}', '| —', '| —', '| —']
            else:
                f = it['variants'][0]['fields']
                row.append(f'| {it.get("variation") or "—"}')
                row.append(f'| {base_link(it["base"]) if it.get("base") else "—"}')
                row.append(f'| {it["category"]}')
                row.append(f'| {f.get("reqlevel", "")}')
                row.append(f'| {f.get("ilvl", "")}')
            row.append(f'| {cls}')
            lines.append('\n'.join(row))
        lines.append('|}\n</div>')
        txt = '\n'.join(lines) + footer('/doc/items/' + ('tiereduniques' if kind == 'tiered' else 'sacreduniques'), ['Items', 'Unique items'])
        add_page(title, txt)

# ------------------------------------------------------------------ sets
def set_pages():
    for s in S:
        title = SET_TITLE[s['name']]
        reqs = [i['fields'].get('reqlevel') for i in s['items'] if i['fields'].get('reqlevel')]
        cls = s['group'].replace(' Sets', '') if s['group'] and s['group'] != 'Other Sets' else ''
        stype = s['subtitle'].strip('()') if s['subtitle'] else ''
        ib = ['{{Infobox set', f'|name={esc(s["name"])}', f'|image={s["items"][0]["image"] or ""}' if s['items'] else '|image=']
        if stype: ib.append(f'|type={esc(stype)}')
        if cls: ib.append(f'|class=[[{cls}]]')
        ib.append(f'|pieces={len(s["items"])}')
        ib.append('|items=' + '<br />'.join(f'[[#{anchor(i["name"])}|<span class="mxl-set">{esc(i["name"])}</span>]]' for i in s['items']))
        if reqs: ib.append(f'|reqlevel={rng(min(reqs), max(reqs))}')
        ib.append('}}')
        lead = f"'''{esc(s['name'])}''' is a {len(s['items'])}-piece [[Sets|set]]"
        if stype: lead += f" ({esc(stype)})"
        lead += '.'
        if cls: lead += f" It is one of the [[Sets#{s['group']}|{plural_lower(s['group'])}]]."
        lead += " Like all sets in Median XL, its items are sacred and drop from mid-Nightmare difficulty onwards."
        # bonuses tooltip
        blines = []
        for b in s['bonuses']:
            blines.append([[b['header'], 'unique', None]])
            blines.extend(b['lines'])
        summary = tooltip_template(s['name'], 'unique', [[[m, 'set', None]] for m in s['members']] + [[[' ', 'basic', None]]] + blines,
                                   label='Set bonuses', base=esc(s['subtitle']) if s['subtitle'] else None, extra={'wide': 'yes'})
        items = []
        for i in s['items']:
            items.append(tooltip_template(i['name'], 'set', i['lines'], image=i['image'], base=esc(i['base']),
                                          extra={'id': anchor(i['name']).replace(' ', '_')}))
        txt = '\n'.join(ib) + '\n' + lead + '\n\n== Set bonuses ==\n' + '{{Tooltip row|\n' + summary + '\n}}\n\n'
        txt += '== Set items ==\n'
        for i in s['items']:
            pass
        txt += '{{Tooltip row|\n' + '\n'.join(items) + '\n}}\n\n'
        # per-item quick table
        txt += '=== Summary ===\n{| class="mxl-table sortable mxl-compact"\n! Item !! Base !! Req. lvl !! Defense / damage\n'
        for i in s['items']:
            f = i['fields']
            txt += f"|-\n| <span class=\"mxl-set\">{esc(i['name'])}</span> || {esc(i['base'])} || {f.get('reqlevel', '')} || {esc(f.get('mainstat', ''))}\n"
        txt += '|}\n\n'
        txt += "== Notes ==\n* All set items come with the maximum allowed number of sockets for the item type.\n* Skill bonuses without a class requirement are [[OSkills|oskills]] and work for any class.\n\n"
        txt += safe_changelog(s['name'])
        for i in s['items']:
            cl = safe_changelog(i['name'], allow_single=False)
            if cl:
                txt += cl.replace('== Version history ==', f"=== Version history: {esc(i['name'])} ===")
        others = [x for x in S if x['group'] == s['group'] and x['name'] != s['name']]
        if others:
            txt += f"\n== Other {plural_lower(s['group'])} ==\n" + ' · '.join(f"[[{SET_TITLE[o['name']]}|{esc(o['name'])}]]" for o in others) + '\n'
        txt += footer('/doc/items/sets', ['Sets'] + ([s['group']] if s['group'] else []))
        add_page(title, txt)
        # redirects for distinctive set item names
        for i in s['items']:
            if ' ' in i['name'] or "'" in i['name']:
                add_redirect(i['name'], f"{title}#{anchor(i['name'])}")

def set_overview():
    intro = intro_blocks('raw/doc_items_sets.html')
    intro = re.sub(r'^== .* ==\n+', '', intro)
    lines = ['{{MXL styles}}', intro.strip(), '']
    lines.append(f"There are {len(S)} sets with {sum(len(s['items']) for s in S)} set items listed below. Click a set for its bonuses, full item stats and version history.\n")
    for g in dict.fromkeys(s['group'] for s in S):
        lines.append(f'== {g} ==')
        lines.append('{| class="mxl-table sortable mxl-compact"\n! class="unsortable" | !! Set !! Type !! Pieces !! Req. lvl !! Set items')
        for s in [x for x in S if x['group'] == g]:
            t = SET_TITLE[s['name']]
            reqs = [i['fields'].get('reqlevel') for i in s['items'] if i['fields'].get('reqlevel')]
            img = f"[[File:{s['items'][0]['image']}|x36px|link={t}]]" if s['items'] and s['items'][0]['image'] else ''
            items = ', '.join(f"[[{t}#{anchor(i['name'])}|{esc(i['name'])}]]" for i in s['items'])
            lines.append(f"|-\n| {img}\n| [[{t}|<span class=\"mxl-set\">{esc(s['name'])}</span>]]\n| {esc(s['subtitle'].strip('()'))}\n| {len(s['items'])}\n| {rng(min(reqs), max(reqs)) if reqs else ''}\n| {items}")
        lines.append('|}\n')
    txt = '\n'.join(lines) + footer('/doc/items/sets', ['Items', 'Sets'])
    add_page('Sets', txt)

# ------------------------------------------------------------------ runewords
def rune_link(r):
    return f"[[Gems and Runes#{anchor(r.replace(' Rune', ''))}|<span class=\"mxl-rune\">{esc(r.replace(' Rune', ''))}</span>]]"

def runeword_pages():
    by = collections.defaultdict(list)
    for r in R:
        by[r['name']].append(r)
    for name, vs in by.items():
        title = RW_TITLE[name]
        v0 = vs[0]
        ib = ['{{Infobox runeword', f'|name={esc(name)}', f"|image={v0['rune_images'][0] if v0['rune_images'] else ''}",
              '|runes=' + ' + '.join(rune_link(r) for r in v0['runes']),
              f"|recipe={esc(v0['recipe'])}", f"|sockets={len(v0['runes'])}",
              f"|level={rng(min(v['level'] for v in vs), max(v['level'] for v in vs))}",
              '|bases=' + '<br />'.join(esc(v['category']) for v in vs), '}}']
        lead = (f"'''{esc(name)}''' is a [[Runewords|runeword]] made by socketing "
                + ', '.join(rune_link(r) for r in v0['runes'])
                + (" (in that order)" if len(v0['runes']) > 1 else '') + f" into a socketed, non-magical (grey) item of a matching type. Required level {v0['level']}.")
        if len(vs) > 1:
            lead += f" It exists in {len(vs)} versions for different item types, listed below."
        txt = '\n'.join(ib) + '\n' + lead + '\n\n== Stats ==\n'
        rows = []
        for v in vs:
            stats = v['lines']
            rows.append(tooltip_template(name, 'unique', stats, label=v['category'],
                                         base=esc(v['recipe']) and f"<span class=\"mxl-grey\">'{esc(v['recipe'])}'</span>",
                                         extra={'image': v['rune_images'][0] if v['rune_images'] else ''} if False else None))
        txt += '{{Tooltip row|\n' + '\n'.join(rows) + '\n}}\n\n'
        txt += '== Item types ==\n'
        for v in vs:
            txt += f"* '''{esc(v['category'])}''': " + ' '.join(esc(b) for b in v['bases']) + '\n'
        txt += ("\n== Making this runeword ==\n"
                f"# Find a grey (non-magical) item of a valid type with at least {len(v0['runes'])} socket{'s' if len(v0['runes']) > 1 else ''}.\n"
                "# You may fill the sockets ''before'' the runes with jewels: e.g. a 2-rune word in a 4-socket item needs 2 jewels first, then the runes.\n"
                "# Insert the runes in order: " + ' → '.join(rune_link(r) for r in v0['runes']) + ".\n"
                "Some advanced runes only drop in certain areas or are made with cube recipes; see [[Gems and Runes]] and [[Cube Recipes]].\n\n")
        txt += safe_changelog(name)
        txt += footer('/doc/items/runewords', ['Runewords'])
        add_page(title, txt)

def runeword_overview():
    intro = intro_blocks('raw/doc_items_runewords.html')
    intro = re.sub(r'^== .* ==\n+', '', intro)
    lines = ['{{MXL styles}}', intro.strip(), '']
    names = list(dict.fromkeys(r['name'] for r in R))
    lines.append(f"There are {len(names)} runewords. Each table can be sorted by clicking its headers; click a name for the runeword's own page.\n")
    # master table
    lines.append('== All runewords by level ==')
    lines.append('<div class="mw-collapsible mw-collapsed" data-expandtext="show table" data-collapsetext="hide table">')
    lines.append("A compact list of every runeword, sortable by level, runes or item type.")
    lines.append('<div class="mw-collapsible-content">\n{| class="mxl-table sortable mxl-compact"\n! Name !! Runes !! Sockets !! Level !! Item type')
    for r in sorted(R, key=lambda x: (x['level'], x['name'])):
        lines.append(f"|-\n| [[{RW_TITLE[r['name']]}|<span class=\"mxl-unique\">{esc(r['name'])}</span>]] || {' '.join(rune_link(x) for x in r['runes'])} || {len(r['runes'])} || {r['level']} || {esc(r['category'])}")
    lines.append('|}\n</div></div>\n')
    for cat in dict.fromkeys(r['category'] for r in R):
        lines.append(f'== {cat} ==')
        lines.append('<div class="mxl-scroll">\n{| class="mxl-table sortable mxl-compact"\n! Name !! Level !! class="unsortable" | Runes !! Item types !! Stats')
        for r in [x for x in R if x['category'] == cat]:
            imgs = ' '.join(f"[[File:{f}|24px|link=Gems and Runes#{anchor(rn.replace(' Rune', ''))}]]" for f, rn in zip(r['rune_images'], r['runes']))
            lines.append(f"|-\n| [[{RW_TITLE[r['name']]}|<span class=\"mxl-unique\">{esc(r['name'])}</span>]]<br /><span class=\"mxl-grey\">'{esc(r['recipe'])}'</span>\n| {r['level']}\n| {imgs}<br />{'<br />'.join(rune_link(x) for x in r['runes'])}\n| {'<br />'.join(esc(b) for b in r['bases'])}\n| {render_lines(r['lines'])}")
        lines.append('|}\n</div>\n')
    txt = '\n'.join(lines) + footer('/doc/items/runewords', ['Items', 'Runewords'])
    add_page('Runewords', txt)

# ------------------------------------------------------------------ base items
MODS = {'Area Effect Attack', 'Thunderfury', 'Amazing Grace', 'Mega Impact'}

def base_pages():
    uniq_by_base = collections.defaultdict(list)
    for kind in ('tiered', 'sacred'):
        for it in U[kind]:
            if it.get('base'):
                uniq_by_base[it['base']].append((kind, it))
    for b in B:
        title = BASE_TITLE[b['name']]
        vs = b['variants']
        f1, f4, fs = vs[0]['fields'], vs[3]['fields'], vs[-1]['fields']
        mod = ''
        for v in vs:
            for ln in v['lines']:
                for t, c, ti in ln:
                    if c == 'orange':
                        mod = t.strip().rstrip(')').split('(')[-1] if 'On hit' in t else t.strip()
        cls = ''
        for v in vs:
            if v['fields'].get('classonly'):
                cls = v['fields']['classonly']
        ib = ['{{Infobox base item', f"|name={esc(b['name'])}", f"|image={b['image'] or ''}",
              f"|category={cat_link(b['category'])}", '|tiers=4 + Sacred']
        if cls: ib.append(f'|class=[[{cls}]]')
        req = [v['fields']['reqlevel'] for v in vs if v['fields'].get('reqlevel')]
        if req: ib.append(f"|reqlevel={rng(min(req), max(req))}")
        q = [v['fields'].get('qlvl') for v in vs if v['fields'].get('qlvl') is not None]
        if q: ib.append(f"|qlvl={rng(min(q), max(q))}")
        if f1.get('speed') is not None: ib.append(f"|speed={f1['speed']}")
        sk = [v['fields'].get('sockets') for v in vs if v['fields'].get('sockets')]
        if sk: ib.append(f"|sockets={max(sk)}")
        if mod: ib.append(f"|modifier={esc(mod)}")
        ib.append('}}')
        lead = (f"'''{esc(b['name'])}''' is a [[Base Items|base item]] type in the ''{esc(b['category'])}'' group. "
                "Like every base item it comes in four tiers plus a Sacred version; higher tiers have better base stats but higher requirements.")
        rows = [tooltip_template(b['name'], 'white', v['lines'], image=b['image'], label=v['label']) for v in vs]
        txt = '\n'.join(ib) + '\n' + lead + '\n\n== Tiers ==\n{{Tooltip row|\n' + '\n'.join(rows) + '\n}}\n\n'
        # compact comparison table
        txt += '=== Comparison ===\n{| class="mxl-table mxl-compact"\n! Tier !! Base stat !! Req. lvl !! Req. Str !! Req. Dex !! Quality lvl !! Sockets\n'
        for v in vs:
            f = v['fields']
            txt += f"|-\n| {v['label']} || {esc(f.get('mainstat', ''))} || {f.get('reqlevel', '—')} || {f.get('reqstr', '—')} || {f.get('reqdex', '—')} || {f.get('qlvl', '')} || {f.get('sockets', '')}\n"
        txt += '|}\n\n'
        if mod:
            txt += f"== Attack modifier ==\nThis class-specific weapon has a built-in attack modifier: '''{esc(mod)}'''. See [[Base Items#Attack Modifiers|attack modifiers]].\n\n"
        us = uniq_by_base.get(b['name'], [])
        if us:
            txt += '== Unique items on this base ==\n'
            for kind, it in us:
                lab = 'tiered unique' if kind == 'tiered' else ('sacred unique' + (f", {it['variation']}" if it.get('variation') else ''))
                txt += f"* [[{UNIQ_TITLE[(kind, it['name'])]}|<span class=\"mxl-unique\">{esc(it['name'])}</span>]] ({lab})\n"
            txt += '\n'
        others = [x for x in B if x['category'] == b['category'] and x['name'] != b['name']]
        if others:
            txt += f"== Other {plural_lower(b['category'])} ==\n" + ' · '.join(f"[[{BASE_TITLE[o['name']]}|{esc(o['name'])}]]" for o in others) + '\n'
        txt += footer('/doc/items/baseitems', ['Base items', b['category']])
        add_page(title, txt)

def base_overview():
    intro = intro_blocks('raw/doc_items_baseitems.html')
    intro = re.sub(r'^== .* ==\n+', '', intro)
    lines = ['{{MXL styles}}', intro.strip(), '']
    lines.append(f"== Item list ==\nAll {len(B)} base item types. Sort by any column; click a name for every tier's full stats and the uniques that use it.\n")
    lines.append('<div class="mxl-scroll">\n{| class="mxl-table sortable mxl-compact"\n! class="unsortable" | !! Name !! Item group !! Req. lvl T1 !! T2 !! T3 !! T4 !! Sacred !! Sacred base stat !! Quality lvl (Sacred) !! Max sockets !! Speed')
    for b in B:
        t = BASE_TITLE[b['name']]
        vs = b['variants']
        req = [v['fields'].get('reqlevel', '—') for v in vs]
        fs = vs[-1]['fields']
        sk = max([v['fields'].get('sockets', 0) for v in vs])
        img = f"[[File:{b['image']}|x36px|link={t}]]" if b['image'] else ''
        lines.append(f"|-\n| {img}\n| [[{t}|{esc(b['name'])}]]\n| {b['category']}\n| " + '\n| '.join(str(r) for r in req)
                     + f"\n| {esc(fs.get('mainstat', '').split(': ', 1)[-1])}\n| {fs.get('qlvl', '')}\n| {sk}\n| {vs[0]['fields'].get('speed', '')}")
    lines.append('|}\n</div>')
    txt = '\n'.join(lines) + footer('/doc/items/baseitems', ['Items', 'Base items'])
    add_page('Base Items', txt)

def build():
    assign_titles()
    unique_pages(); unique_overviews()
    set_pages(); set_overview()
    runeword_pages(); runeword_overview()
    base_pages(); base_overview()
