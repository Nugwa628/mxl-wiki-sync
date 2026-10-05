"""Minimal template expander for our own templates (for preview/testing only)."""
import re

def strip_tags(body):
    body = re.sub(r'<noinclude>.*?</noinclude>', '', body, flags=re.S)
    body = body.replace('<includeonly>', '').replace('</includeonly>', '')
    return body

def split_top(s, sep='|'):
    parts, depth, cur, i = [], 0, '', 0
    dl = 0
    while i < len(s):
        if s.startswith('{{', i):
            depth += 1; cur += '{{'; i += 2; continue
        if s.startswith('}}', i) and depth:
            depth -= 1; cur += '}}'; i += 2; continue
        if s.startswith('[[', i):
            dl += 1; cur += '[['; i += 2; continue
        if s.startswith(']]', i) and dl:
            dl -= 1; cur += ']]'; i += 2; continue
        if s[i] == sep and depth == 0 and dl == 0:
            parts.append(cur); cur = ''; i += 1; continue
        cur += s[i]; i += 1
    parts.append(cur)
    return parts

def find_innermost(text, start=0):
    """Find a {{...}} with no nested {{ inside (ignoring {{{ params)."""
    i = text.find('{{', start)
    while i != -1:
        if text.startswith('{{{', i):
            # param: skip to its end
            j = text.find('}}}', i)
            i = text.find('{{', j + 3) if j != -1 else -1
            continue
        # find matching close for this {{ with nested tracking
        depth, k = 0, i
        while k < len(text):
            if text.startswith('{{{', k) and not text.startswith('{{{{', k):
                e = text.find('}}}', k); k = e + 3; continue
            if text.startswith('{{', k):
                depth += 1; k += 2; continue
            if text.startswith('}}', k):
                depth -= 1; k += 2
                if depth == 0:
                    return i, k
                continue
            k += 1
        return None
    return None

def subst_params(body, args):
    # repeatedly replace innermost {{{name|default}}}
    pat = re.compile(r'\{\{\{([^{}|]*)(?:\|([^{}]*))?\}\}\}')
    for _ in range(50):
        new = pat.sub(lambda m: args.get(m.group(1).strip(), m.group(2) if m.group(2) is not None else '{{{%s}}}' % m.group(1)), body)
        if new == body:
            break
        body = new
    return body

def eval_pf(text, pagename):
    text = text.replace('{{!}}', '\x00')
    text = re.sub(r'\{\{\{[^{}|]*\}\}\}', '\x01', text)  # unresolved params without default
    text = _eval_pf(text, pagename)
    return text.replace('\x00', '|').replace('\x01', '')

def _eval_pf(text, pagename):
    # evaluate parser functions innermost-first
    for _ in range(2000):
        m = re.search(r'\{\{(#if|#ifeq|!|PAGENAME)(:|\}\})', text)
        if not m:
            break
        # find the innermost parser function call
        best = None
        for mm in re.finditer(r'\{\{(#if:|#ifeq:|!\}\}|PAGENAME\}\})', text):
            s = mm.start()
            if text[s:].startswith('{{!}}'):
                best = (s, s + 5, '|'); break
            if text[s:].startswith('{{PAGENAME}}'):
                best = (s, s + 12, pagename); break
            # check content has no nested {{
            depth, k = 0, s
            while k < len(text):
                if text.startswith('{{', k):
                    depth += 1; k += 2; continue
                if text.startswith('}}', k):
                    depth -= 1; k += 2
                    if depth == 0: break
                    continue
                k += 1
            inner = text[s + 2:k - 2]
            if '{{' in inner:
                continue
            fn, _, rest = inner.partition(':')
            parts = split_top(rest)
            if fn == '#if':
                cond = parts[0].strip()
                a = parts[1] if len(parts) > 1 else ''
                b = parts[2] if len(parts) > 2 else ''
                best = (s, k, (a if cond else b).strip()); break
            if fn == '#ifeq':
                a = parts[0].strip(); b = parts[1].strip() if len(parts) > 1 else ''
                c = parts[2] if len(parts) > 2 else ''; d = parts[3] if len(parts) > 3 else ''
                best = (s, k, (c if a == b else d).strip()); break
        if not best:
            break
        s, e, rep = best
        text = text[:s] + rep + text[e:]
    return text

def expand(text, T, pagename='Test'):
    for _ in range(5000):
        found = False
        pos = 0
        while True:
            r = find_innermost(text, pos)
            if not r:
                break
            s, e = r
            inner = text[s + 2:e - 2]
            if '{{' in inner.replace('{{{', '') and not inner.startswith('#'):
                pos = s + 2; continue
            parts = split_top(inner)
            name = parts[0].strip()
            tname = 'Template:' + name[0].upper() + name[1:] if name and not name.startswith('#') else None
            if tname and tname in T:
                args = {}
                n = 1
                for p in parts[1:]:
                    k, eq, v = p.partition('=')
                    if eq and '{{' not in k and '[[' not in k and '<' not in k:
                        args[k.strip()] = v.strip()
                    else:
                        args[str(n)] = p; n += 1
                body = strip_tags(T[tname]).replace('{{PAGENAME}}', pagename)
                body = subst_params(body, args)
                body = eval_pf(body, pagename)
                text = text[:s] + body + text[e:]
                found = True
                break
            pos = s + 2
        if not found:
            break
    return text
