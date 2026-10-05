import re, json
from conv import load, norm_ws, img_file, IMAGES_USED
from tooltip import segments, to_lines, line_text, fields

def parse(path, kind):
    page = load(path).select_one('.page')
    items = []
    cat = None
    for el in page.find_all(['p', 'table']):
        if el.name == 'p' and 'genbig' in el.get('class', []):
            cat = norm_ws(el.get_text()).strip()
            continue
        if el.name != 'table' or 'uniques' not in el.get('class', []):
            continue
        th = el.find('th')
        header = norm_ws(th.get_text()).strip() if th else None
        tier_item = None
        if kind == 'tiered' and header:
            m = re.match(r'^(.*)\((.*)\)\s*$', header)
            name, base = (m.group(1).strip(), m.group(2).strip()) if m else (header, None)
            tier_item = dict(name=name, base=base, category=cat, kind=kind, variants=[], image=None)
            items.append(tier_item)
        image = None
        for tr in el.find_all('tr'):
            tds = tr.find_all('td', recursive=False)
            col = 0
            row_items = []
            for td in tds:
                img = td.find('img')
                if img and not td.find('span'):
                    image = img_file(img['src']); IMAGES_USED[image] = img['src']
                    if tier_item and not tier_item['image']:
                        tier_item['image'] = image
                    continue
                if not td.get_text(strip=True):
                    continue
                nm = td.find('span', class_='item-unique')
                if nm and nm.find('b') and kind != 'tiered' or (kind == 'tiered' and not header and nm):
                    name = norm_ws(nm.get_text()).strip()
                    toks = segments(td, skip={nm})
                    lines = to_lines(toks)
                    it = dict(name=name, base=header, category=cat, kind=kind, image=image,
                              variants=[dict(label=None, lines=lines, fields=fields(lines))], col=col)
                    items.append(it); row_items.append(it)
                    col += 1
                else:
                    b = td.find('b')
                    label = norm_ws(b.get_text()).strip() if b else None
                    toks = segments(td, skip={b} if b else None)
                    lines = to_lines(toks)
                    tier_item['variants'].append(dict(label=label, lines=lines, fields=fields(lines)))
            # sacred variation labels by column
            if kind == 'sacred' and row_items and cat not in ('Amulets', 'Rings', 'Jewels', 'Arrow Quivers', 'Crossbow Quivers'):
                n = len(row_items)
                labels = ['SU', 'SSU', 'SSSU'][:n] if n > 1 else ['SU']
                for it, lb in zip(row_items, labels):
                    it['variation'] = lb
    return items

if __name__ == '__main__':
    t = parse('raw/doc_items_tiereduniques.html', 'tiered')
    s = parse('raw/doc_items_sacreduniques.html', 'sacred')
    print(len(t), len(s))
    import collections
    print(collections.Counter(len(i['variants']) for i in t))
    print([i['name'] for i in t if len(i['variants']) != 4][:40])
    print(collections.Counter(i.get('variation') for i in s))
    json.dump(dict(tiered=t, sacred=s), open('data_uniques.json', 'w'), indent=1)
    print(t[0]['name'], t[0]['base'], t[0]['variants'][0]['fields'])
    print(s[0])
