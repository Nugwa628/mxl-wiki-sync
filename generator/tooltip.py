"""Parse docs item tooltips (nested colored spans with <br>) into lines of colored segments,
and render them back to wikitext."""
import re, html
from bs4 import NavigableString, Comment, Tag
from conv import COLOR_CLASSES, esc, norm_ws, img_file, IMAGES_USED, Conv

def color_of(tag):
    for k in reversed(tag.get('class', [])):
        if k in COLOR_CLASSES:
            return COLOR_CLASSES[k]
    return None

def segments(node, cls='basic', title=None, out=None, skip=None):
    """Yield list of tokens: ('t', text, cls, title) or ('br',)."""
    if out is None:
        out = []
    for c in node.children:
        if skip is not None and c in skip:
            continue
        if isinstance(c, Comment):
            continue
        if isinstance(c, NavigableString):
            t = norm_ws(str(c))
            if t.strip() or (t == ' ' and out and out[-1][0] == 't'):
                out.append(('t', t, cls, title))
            continue
        if not isinstance(c, Tag):
            continue
        if c.name == 'br':
            out.append(('br',))
        elif c.name == 'img':
            continue
        elif c.name in ('style', 'script'):
            continue
        else:
            ccls = color_of(c) or cls
            ttl = c.get('title') or title
            if c.name in ('p', 'div') and out and out[-1][0] != 'br':
                out.append(('br',))
            segments(c, ccls, ttl, out, skip)
            if c.name in ('p', 'div'):
                out.append(('br',))
    return out

def to_lines(tokens):
    lines = [[]]
    for tk in tokens:
        if tk[0] == 'br':
            lines.append([])
        else:
            lines[-1].append(list(tk[1:]))
    res = []
    for ln in lines:
        # merge adjacent same-class segments, trim
        merged = []
        for t, c, ti in ln:
            if merged and merged[-1][1] == c and merged[-1][2] == ti:
                merged[-1][0] += t
            else:
                merged.append([t, c, ti])
        # trim whitespace at ends
        while merged and not merged[0][0].strip():
            merged.pop(0)
        while merged and not merged[-1][0].strip():
            merged.pop()
        if merged:
            merged[0][0] = merged[0][0].lstrip()
            merged[-1][0] = merged[-1][0].rstrip()
            for m in merged:
                m[0] = re.sub(r'\s+', ' ', m[0])
            res.append(merged)
    return res

def line_text(line):
    return ''.join(s[0] for s in line).strip()

def render_line(line):
    parts = []
    for t, c, ti in line:
        t2 = esc(t)
        if ti:
            ti2 = html.escape(norm_ws(ti.replace('\r', ' ').replace('\n', ' ')).strip(), quote=True)
            parts.append(f'<span class="mxl-{c} mxl-tip" title="{ti2}">{t2}</span>')
        elif c and c != 'basic':
            parts.append(f'<span class="mxl-{c}">{t2}</span>')
        else:
            parts.append(t2)
    return ''.join(parts)

def render_lines(lines):
    return '<br />'.join(render_line(l) for l in lines)

FIELD_RE = {
    'reqlevel': re.compile(r'^Required Level:\s*(\d+)'),
    'ilvl': re.compile(r'^Item Level:\s*(\d+)'),
    'reqstr': re.compile(r'^Required Strength:\s*(\d+)'),
    'reqdex': re.compile(r'^Required Dexterity:\s*(\d+)'),
}

def fields(lines):
    f = {}
    for ln in lines:
        t = line_text(ln)
        for k, r in FIELD_RE.items():
            m = r.match(t)
            if m and k not in f:
                f[k] = int(m.group(1))
        m = re.match(r'^(One-Hand Damage|Two-Hand Damage|Throw Damage|Defense|Kick Damage|Smite Damage):\s*(.*)$', t)
        if m and m.group(2):
            f.setdefault('mainstat', f"{m.group(1)}: {m.group(2)}")
        m = re.match(r'^\((\w+) Only\)$', t)
        if m:
            f['classonly'] = m.group(1)
    return f

def tooltip_template(name, quality, lines, image=None, label=None, base=None, extra=None):
    p = ['{{Item tooltip']
    p.append(f'|name={esc(name)}')
    p.append(f'|quality={quality}')
    if label:
        p.append(f'|label={esc(label)}')
    if base:
        p.append(f'|base={esc(base)}')
    if image:
        p.append(f'|image={image}')
    if extra:
        for k, v in extra.items():
            p.append(f'|{k}={v}')
    p.append('|stats=' + render_lines(lines))
    p.append('}}')
    return '\n'.join(p)
