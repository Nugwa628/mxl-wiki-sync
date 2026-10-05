import re, json
from conv import load, norm_ws, img_file, IMAGES_USED
from tooltip import segments, to_lines, line_text, fields

def parse(path='raw/doc_items_baseitems.html'):
    page = load(path).select_one('.page')
    bases = []
    cat = None
    for el in page.find_all(['p', 'table']):
        if el.name == 'p' and 'genbig' in el.get('class', []):
            cat = norm_ws(el.get_text()).strip()
            continue
        if el.name != 'table' or 'baselegend_table' in (el.get('class') or []) or cat in (None, 'BASE ITEMS'):
            continue
        th = el.find('th')
        name = norm_ws(th.get_text()).strip()
        b = dict(name=name, category=cat, image=None, variants=[])
        for td in el.find_all('td'):
            img = td.find('img')
            if img and not td.find('span'):
                b['image'] = img_file(img['src']); IMAGES_USED[b['image']] = img['src']
                continue
            lab = td.find('b')
            label = norm_ws(lab.get_text()).strip() if lab else None
            lines = to_lines(segments(td, skip={lab.parent} if lab and lab.parent.name == 'span' and norm_ws(lab.parent.get_text()).strip() == label else ({lab} if lab else None)))
            f = fields(lines)
            for ln in lines:
                t = line_text(ln)
                m = re.match(r'^Quality Level:\s*(\d+)', t)
                if m: f['qlvl'] = int(m.group(1))
                m = re.match(r'^Attack Speed Modifier:\s*(-?\d+)', t)
                if m: f['speed'] = int(m.group(1))
                m = re.match(r'^Socketed \((\d+)\)', t)
                if m: f['sockets'] = int(m.group(1))
            b['variants'].append(dict(label=label, lines=lines, fields=f))
        bases.append(b)
    return bases

if __name__ == '__main__':
    b = parse()
    import collections
    print(len(b), collections.Counter(len(x['variants']) for x in b))
    print(collections.Counter(tuple(v['label'] for v in x['variants']) for x in b))
    print(b[0]['variants'][4])
    names = collections.Counter(x['name'] for x in b); print([n for n, c in names.items() if c > 1])
    json.dump(b, open('data_bases.json', 'w'), indent=1)
