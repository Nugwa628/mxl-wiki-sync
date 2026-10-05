import re, json
from conv import load, norm_ws, img_file, IMAGES_USED
from tooltip import segments, to_lines, line_text

def parse(path='raw/doc_items_runewords.html'):
    page = load(path).select_one('.page')
    rws = []
    cat = None
    for el in page.find_all(['p', 'table']):
        if el.name == 'p' and 'genbig' in el.get('class', []):
            cat = norm_ws(el.get_text()).strip()
            continue
        if el.name != 'table' or 'runewords_table' not in el.get('class', []):
            continue
        for tr in el.find_all('tr'):
            tds = tr.find_all('td', recursive=False)
            if len(tds) != 6:
                continue
            nm = tds[0].find('span', class_='item-unique')
            name = norm_ws(nm.get_text()).strip()
            rw = tds[0].find('span', class_='item-runeword')
            recipe = norm_ws(rw.get_text()).strip().strip("'") if rw else ''
            level = int(norm_ws(tds[1].get_text()).strip() or 0)
            imgs = []
            for im in tds[2].find_all('img'):
                f = img_file(im['src']); IMAGES_USED[f] = im['src']; imgs.append(f)
            runes = [norm_ws(s.get_text()).strip() for s in tds[3].find_all('span', class_='item-eruneword')]
            bases_lines = to_lines(segments(tds[4]))
            bases = [line_text(l) for l in bases_lines]
            stats = to_lines(segments(tds[5]))
            rws.append(dict(name=name, recipe=recipe, level=level, rune_images=imgs, runes=runes,
                            bases=bases, base_lines=bases_lines, lines=stats, category=cat))
    return rws

if __name__ == '__main__':
    r = parse()
    print(len(r))
    import collections
    names = collections.Counter(x['name'] for x in r)
    print('dupe names', [n for n, c in names.items() if c > 1])
    print(r[0])
    json.dump(r, open('data_runewords.json', 'w'), indent=1)
