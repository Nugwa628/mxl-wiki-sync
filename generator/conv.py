"""Generic docs-HTML -> MediaWiki wikitext converter for Median XL docs."""
import re, html, os
from bs4 import BeautifulSoup, NavigableString, Comment, Tag

DOCS = 'https://docs.median-xl.com'

PAGE_TITLES = {
    '/': 'Patch Notes',
    '/doc/class/amazon': 'Amazon', '/doc/class/assassin': 'Assassin',
    '/doc/class/barbarian': 'Barbarian', '/doc/class/druid': 'Druid',
    '/doc/class/necromancer': 'Necromancer', '/doc/class/paladin': 'Paladin',
    '/doc/class/sorceress': 'Sorceress', '/doc/class/hirelings': 'Mercenaries',
    '/doc/items/cube': 'Cube Recipes', '/doc/items/tiereduniques': 'Tiered Uniques',
    '/doc/items/sacreduniques': 'Sacred Uniques', '/doc/items/runewords': 'Runewords',
    '/doc/items/sets': 'Sets', '/doc/items/socketables': 'Gems and Runes',
    '/doc/items/baseitems': 'Base Items',
    '/doc/quests/challenges': 'Challenges', '/doc/quests/dungeons': 'Dungeons',
    '/doc/quests/rifts': 'Nephalem Rifts',
    '/doc/concepts/defense': 'Defense and Block', '/doc/concepts/experience': 'Experience',
    '/doc/concepts/spellfocus': 'Spell Focus', '/doc/concepts/minion': 'Minion Mechanics',
    '/doc/wiki/cycles': 'Cycles', '/doc/wiki/relics': 'Relics',
    '/doc/wiki/umos': 'Unique Mystic Orbs', '/doc/wiki/affixes': 'Item Affixes',
    '/doc/wiki/shrines': 'Shrine Bonuses', '/doc/wiki/trophies': 'Trophy Bonuses',
    '/doc/wiki/armorlooks': 'Armor Looks',
}
# allow override (e.g. to avoid clobbering existing wiki pages)
TITLE_OVERRIDE = {}

def page_title(path):
    t = PAGE_TITLES.get(path, path)
    return TITLE_OVERRIDE.get(t, t)

# class -> css class used on the wiki
COLOR_CLASSES = {
    'item-basic': 'basic', 'item-magic': 'magic', 'magic': 'magic',
    'item-unique': 'unique', 'unique': 'unique', 'item-set': 'set',
    'item-red': 'red', 'red': 'red', 'item-orange': 'orange', 'orange': 'orange',
    'item-eruneword': 'rune', 'item-runeword': 'grey', 'grey': 'grey',
    'item-yellow': 'yellow', 'item-tan': 'tan', 'item-darkgreen': 'darkgreen',
    'item-white': 'white', 'item-grey': 'grey', 'holy': 'holy', 'unholy': 'unholy',
    'brightgreen': 'brightgreen',
    'diff-veryeasy': 'diff-veryeasy', 'diff-easy': 'diff-easy', 'diff-moderate': 'diff-moderate',
    'diff-hard': 'diff-hard', 'diff-veryhard': 'diff-veryhard', 'diff-extreme': 'diff-extreme',
    'diff-impossible': 'diff-impossible',
}

def img_file(src):
    """Map a docs image src to the wiki File: name."""
    src = src.replace(DOCS, '')
    base = os.path.basename(src)
    d = os.path.dirname(src)
    if '/uberquests' in d or '/art' in d or '/hirelings' in d or '/highlights' in d or '/menu' in d:
        if not base.lower().startswith('mxl'):
            base = 'MXL ' + base
    base = base.replace('_', ' ')
    return base[0].upper() + base[1:]

IMAGES_USED = {}  # file name -> docs src

def esc(t):
    """Escape characters that would be interpreted as wiki markup in plain text."""
    t = t.replace('[[', '&#91;&#91;').replace(']]', '&#93;&#93;')
    t = t.replace('{{', '&#123;&#123;').replace('}}', '&#125;&#125;')
    t = t.replace('|', '&#124;')
    t = t.replace("''", "&#39;&#39;")
    t = t.replace('~~~', '&#126;~~')
    t = t.replace('__', '&#95;_')
    return t

def norm_ws(t):
    return re.sub(r'\s+', ' ', t)

SLUGS = {'affixes': '/doc/wiki/affixes', 'relics': '/doc/wiki/relics', 'umos': '/doc/wiki/umos',
         'cycles': '/doc/wiki/cycles', 'shrines': '/doc/wiki/shrines', 'trophies': '/doc/wiki/trophies',
         'cube': '/doc/items/cube', 'runewords': '/doc/items/runewords', 'sets': '/doc/items/sets',
         'socketables': '/doc/items/socketables', 'baseitems': '/doc/items/baseitems',
         'tiereduniques': '/doc/items/tiereduniques', 'sacreduniques': '/doc/items/sacreduniques',
         'dungeons': '/doc/quests/dungeons', 'rifts': '/doc/quests/rifts', 'challenges': '/doc/quests/challenges'}

def link_target(href):
    if not href:
        return None, None
    h = href.strip().replace('\\', '/')
    if h.startswith(DOCS):
        rest = h[len(DOCS):]
        rest = re.sub(r'^(/\.\.)+', '', rest)
        rest = re.sub(r'^/(\.\./)+', '/', rest)
        path, _, frag = rest.partition('#')
        slug = path.strip('/').split('/')[-1] if path.strip('/') else ''
        if path not in PAGE_TITLES and slug in SLUGS:
            h = SLUGS[slug] + ('#' + frag if frag else '')
    elif not h.startswith(('http', '#', '/')):
        path, _, frag = h.partition('#')
        slug = path.strip('/').split('/')[-1]
        if slug in SLUGS:
            h = SLUGS[slug] + ('#' + frag if frag else '')
    if h.startswith(DOCS):
        h = h[len(DOCS):] or '/'
    if h.startswith('/doc') or h == '/':
        path, _, frag = h.partition('#')
        return 'int', page_title(path) + ('#' + frag if frag else '')
    if h.startswith('#'):
        return 'anchor', h
    if h.startswith('http'):
        return 'ext', h
    return 'ext', DOCS + '/' + h.lstrip('/')

class Conv:
    def __init__(self, heading_base=2, table_class='wikitable mxl-table'):
        self.hb = heading_base
        self.table_class = table_class

    # ---------- inline ----------
    def inline(self, node):
        out = []
        for c in node.children:
            out.append(self.inline_node(c))
        return ''.join(out)

    def inline_node(self, c):
        if isinstance(c, Comment):
            return ''
        if isinstance(c, NavigableString):
            return esc(norm_ws(str(c)))
        if not isinstance(c, Tag):
            return ''
        n = c.name
        if n in ('style', 'script', 'input', 'button', 'select', 'option', 'label', 'legend'):
            return ''
        if n == 'br':
            return '<br />'
        if n in ('b', 'strong'):
            inner = self.inline(c).strip()
            return f"'''{inner}'''" if inner else ''
        if n in ('i', 'em'):
            if 'fa' in c.get('class', []):
                return '› ' if 'fa-angle-right' in c.get('class', []) else ''
            inner = self.inline(c).strip()
            return f"''{inner}''" if inner else ''
        if n == 'u':
            return f"<u>{self.inline(c)}</u>"
        if n == 'img':
            return self.img(c)
        if n == 'a':
            kind, tgt = link_target(c.get('href'))
            text = self.inline(c).strip()
            if kind == 'int':
                return f"[[{tgt}|{text}]]" if text else f"[[{tgt}]]"
            if kind == 'ext':
                return f"[{tgt} {text}]" if text else f"[{tgt}]"
            return text
        if n == 'div' and 'fractions' in c.get('class', []):
            num = c.find(class_='fnum'); den = c.find(class_='fden')
            return ('<span class="mxl-frac"><span class="mxl-num">%s</span><span class="mxl-den">%s</span></span>'
                    % (self.inline(num).strip() if num else '', self.inline(den).strip() if den else ''))
        if n == 'span' or n == 'center' or n == 'p' or n == 'div' or n == 'h4':
            return self.span(c)
        return self.inline(c)

    def span(self, c):
        classes = c.get('class', [])
        inner = self.inline(c)
        cls = [COLOR_CLASSES[k] for k in classes if k in COLOR_CLASSES]
        title = c.get('title')
        attrs = []
        css = []
        if cls:
            css.append('mxl-' + cls[-1])
        if 'underdotted' in classes or title:
            css.append('mxl-tip')
        if css:
            attrs.append(f'class="{" ".join(css)}"')
        if title:
            t = html.escape(norm_ws(title.replace('\r', ' ').replace('\n', ' ')).strip(), quote=True)
            attrs.append(f'title="{t}"')
        if attrs and inner.strip():
            return f'<span {" ".join(attrs)}>{inner}</span>'
        return inner

    def img(self, c, size=None):
        src = c.get('src') or ''
        if not src or src.startswith('data:'):
            return ''
        f = img_file(src)
        IMAGES_USED[f] = src.replace(DOCS, '')
        title = c.get('title') or c.get('alt') or ''
        cls = c.get('class', [])
        opts = []
        if size:
            opts.append(size)
        elif 'classintro' in cls or (c.get('style') and 'max-width' in c.get('style')):
            opts.append('frameless'); opts.append('upright=2')
        if title and title.lower() not in ('skill icon',):
            opts.append('link='); opts.append(esc(title))
        else:
            opts.append('link=')
        anc = f'<span id="{c.get("id")}"></span>' if c.get('id') else ''
        return anc + f"[[File:{f}|{'|'.join(opts)}]]"

    # ---------- blocks ----------
    def blocks(self, node):
        out = []
        buf = []
        def flush():
            s = ''.join(buf).strip()
            s = re.sub(r'^(<br />\s*)+|(<br />\s*)+$', '', s).strip()
            if s:
                out.append(s)
            buf.clear()
        for c in node.children:
            if isinstance(c, Comment):
                continue
            if isinstance(c, Tag) and c.name in BLOCK:
                flush()
                b = self.block(c)
                if b and b.strip():
                    out.append(b.strip())
            else:
                buf.append(self.inline_node(c))
        flush()
        return '\n\n'.join(out)

    def heading(self, level, text):
        text = re.sub(r"'''|''", '', text)
        text = re.sub(r'<br />', ' ', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = norm_ws(text).strip()
        if not text:
            return ''
        if text.isupper() and len(text) > 3:
            text = smart_title(text)
        eq = '=' * level
        return f"{eq} {text} {eq}"

    def block(self, c):
        n = c.name
        cls = c.get('class', [])
        if n in ('style', 'script'):
            return ''
        anc = ''
        if c.get('id') and n in ('p', 'h1', 'h2', 'h3', 'h4'):
            anc = f'<span id="{c.get("id")}"></span>'
        if n == 'p':
            if 'genbig' in cls:
                # may contain a subtitle span.genflat
                sub = c.find('span', class_='genflat')
                subtxt = ''
                if sub:
                    subtxt = self.inline(sub).strip()
                    sub.extract()
                h = self.heading(self.hb, self.inline(c))
                return anc + h + (f"\n''{re.sub(chr(39)*3, '', subtxt)}''" if subtxt else '')
            if 'gensmall' in cls:
                return self.heading(self.hb + 1, self.inline(c))
            return self.blocks_or_inline(c)
        if n == 'div' and ('reagent' in cls) and not c.find(['table', 'ul', 'p']):
            return '<div class="mxl-formula">' + self.inline(c).strip() + '</div>'
        if n in ('h1', 'h2'):
            return self.heading(self.hb, self.inline(c))
        if n == 'h3':
            return self.heading(self.hb + 1, self.inline(c))
        if n == 'h4':
            return self.heading(self.hb + 2, self.inline(c))
        if n == 'hr':
            return ''
        if n == 'ul' or n == 'ol':
            return self.list(c, '*' if n == 'ul' else '#')
        if n == 'table':
            return self.table(c)
        if n == 'div' and 'charms' in cls:
            parts = []
            for d in c.find_all('div', recursive=False) or [c]:
                parts.append(self.tooltip_cell(d))
            return '{{Tooltip row|\n' + '\n'.join(parts) + '\n}}'
        if n in ('div', 'center', 'fieldset', 'form'):
            return self.blocks(c)
        return self.inline(c)

    def blocks_or_inline(self, c):
        if any(isinstance(x, Tag) and x.name in BLOCK for x in c.children):
            return self.blocks(c)
        s = self.inline(c).strip()
        s = re.sub(r'^(<br />\s*)+|(<br />\s*)+$', '', s).strip()
        return s

    def list(self, c, mark, prefix=''):
        lines = []
        pre = prefix + mark
        for x in c.children:
            if not isinstance(x, Tag):
                continue
            if x.name in ('ul', 'ol'):
                lines.append(self.list(x, '*' if x.name == 'ul' else '#', pre))
                continue
            if x.name != 'li':
                continue
            parts, subs = [], []
            for y in x.children:
                if isinstance(y, Tag) and y.name in ('ul', 'ol'):
                    subs.append(y)
                else:
                    parts.append(self.inline_node(y))
            txt = norm_ws(''.join(parts)).strip()
            if txt:
                lines.append(pre + ' ' + txt)
            for sb in subs:
                lines.append(self.list(sb, '*' if sb.name == 'ul' else '#', pre))
        return '\n'.join(l for l in lines if l)

    def cell(self, td):
        if any(isinstance(x, Tag) and x.name in ('table', 'ul', 'ol') for x in td.descendants):
            inner = self.blocks(td)
            return '\n' + inner + '\n'
        s = self.inline(td).strip()
        s = re.sub(r'^(<br />\s*)+|(<br />\s*)+$', '', s).strip()
        s = re.sub(r'\n+', ' ', s)
        return s

    def is_tooltip_cell(self, td):
        if td.find('table'):
            return False
        spans = td.find_all('span', class_=['item-basic', 'item-unique', 'item-set'])
        return bool(spans) and bool(td.find('img'))

    def tooltip_cell(self, td):
        from tooltip import segments, to_lines, line_text, render_lines
        img = td.find('img')
        image = None
        if img and img.get('src'):
            image = img_file(img['src']); IMAGES_USED[image] = img['src'].replace(DOCS, '')
        lines = to_lines(segments(td))
        name, quality = '', 'basic'
        if lines and lines[0][0][1] in ('unique', 'set', 'rune', 'orange', 'yellow', 'white', 'magic', 'red', 'grey') and len(lines[0]) == 1:
            name = line_text(lines[0]); quality = lines[0][0][1]; lines = lines[1:]
        p = ['{{Item tooltip']
        if name: p.append('|name=' + esc(name))
        p.append('|quality=' + quality)
        if image: p.append('|image=' + image)
        p.append('|stats=' + render_lines(lines))
        p.append('}}')
        return '\n'.join(p)

    def table(self, t, cls=None):
        rows = t.find_all('tr')
        rows_ = [r for r in rows if r.find_parent('table') is t]
        tds = [c for r in rows_ for c in r.find_all('td', recursive=False) if c.get_text(strip=True) or c.find('img')]
        if tds and all(self.is_tooltip_cell(c) for c in tds):
            out = []
            buf = []
            for r in rows_:
                for c in r.find_all(['th', 'td'], recursive=False):
                    if c.name == 'th':
                        if buf: out.append('{{Tooltip row|\n' + '\n'.join(buf) + '\n}}'); buf = []
                        h = self.heading(self.hb + 1, self.inline(c))
                        if h: out.append(h)
                    elif c.get_text(strip=True) or c.find('img'):
                        buf.append(self.tooltip_cell(c))
            if buf: out.append('{{Tooltip row|\n' + '\n'.join(buf) + '\n}}')
            return '\n\n'.join(out)
        rows = [r for r in rows if r.find_parent('table') is t]
        out = ['{| class="%s"' % (cls or self.table_class)]
        cap = t.find('caption')
        if cap:
            out.append('|+ ' + self.inline(cap).strip())
        for r in rows:
            cells = r.find_all(['td', 'th'], recursive=False)
            if not cells:
                continue
            if all(not c.get_text(strip=True) and not c.find('img') for c in cells):
                continue
            out.append('|-')
            for c in cells:
                attrs = []
                for a in ('colspan', 'rowspan'):
                    if c.get(a) and c.get(a) != '1':
                        attrs.append(f'{a}="{c.get(a)}"')
                ccls = [COLOR_CLASSES[k] for k in c.get('class', []) if k in COLOR_CLASSES]
                if ccls:
                    attrs.append(f'class="mxl-{ccls[-1]}"')
                content = self.cell(c)
                mark = '!' if c.name == 'th' else '|'
                if attrs:
                    out.append(f"{mark} {' '.join(attrs)} | {content}")
                else:
                    out.append(f"{mark} {content}" if not content.startswith(('-', '+', '}')) else f"{mark} <nowiki/>{content}")
        out.append('|}')
        return '\n'.join(out)

BLOCK = {'p', 'div', 'table', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'hr', 'center', 'fieldset', 'form', 'style', 'script'}

SMALL = {'of', 'the', 'and', 'a', 'an', 'in', 'on', 'to', 'for', 'with', 'by', 'or', 'at', 'vs'}
KEEP = {'xl': 'XL', 'ii': 'II', 'iii': 'III', '(umos)': '(UMOs)', 'umos': 'UMOs', 'umo': 'UMO', 'su': 'SU', 'ssu': 'SSU',
        'sssu': 'SSSU', 'lod': 'LoD', 'clod': 'CLOD', 'mf': 'MF', 'tg': 'TG', 'hc': 'HC', 'sc': 'SC', 'k3k': 'K3K',
        'ba': 'BA', 'xp': 'XP', 'gsf': 'GSF', 'ssf': 'SSF', 'tsw': 'TSW', 'hp': 'HP', 'ar': 'AR', 'alvl': 'alvl',
        'ilvl': 'ilvl', 'qlvl': 'qlvl', 'clvl': 'clvl'}
def smart_title(s):
    words = s.lower().split(' ')
    res = []
    for i, w in enumerate(words):
        if w in KEEP:
            res.append(KEEP[w])
        elif i and w in SMALL:
            res.append(w)
        else:
            res.append(w[:1].upper() + w[1:])
    return ' '.join(res)

def load(path):
    soup = BeautifulSoup(open(path, encoding='utf-8'), 'lxml')
    for t in soup.find_all(['input', 'select', 'option', 'button', 'label', 'script', 'noscript', 'style']):
        t.decompose()
    return soup

def tidy(text):
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'(<br />\s*){3,}', '<br /><br />', text)
    return text.strip() + '\n'
