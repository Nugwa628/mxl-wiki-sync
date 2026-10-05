import re, json
from conv import load, norm_ws, img_file, IMAGES_USED, smart_title
from tooltip import segments, to_lines, line_text, fields

def parse(path='raw/doc_items_sets.html'):
    page = load(path).select_one('.page')
    sets = []
    group = None
    for el in page.find_all(['p', 'table']):
        if el.name == 'p' and 'genbig' in el.get('class', []):
            g = norm_ws(el.get_text()).strip()
            if g != 'SETS':
                group = smart_title(g)
            continue
        if el.name != 'table' or 'sets' not in el.get('class', []):
            continue
        tds = el.find_all('td')
        summary = tds[0]
        lines = to_lines(segments(summary))
        name = line_text(lines[0])
        subtitle = line_text(lines[1]) if len(lines) > 1 and line_text(lines[1]).startswith('(') else ''
        # members: set-colored lines before first bonus header
        members = []
        bonuses = []
        cur = None
        start = 2 if subtitle else 1
        for ln in lines[start:]:
            t = line_text(ln)
            cls = ln[0][1]
            if cls == 'unique' and t.lower().startswith('set bonus'):
                cur = dict(header=t, lines=[])
                bonuses.append(cur)
            elif cur is None:
                members.append(t)
            else:
                cur['lines'].append(ln)
        items = []
        for td in tds[1:]:
            img = td.find('img')
            image = None
            if img:
                image = img_file(img['src']); IMAGES_USED[image] = img['src']
            first = td.find('span', class_='item-set')
            if not first:
                continue
            head = to_lines(segments(first))
            iname = line_text(head[0])
            base = line_text(head[1]) if len(head) > 1 else ''
            body = to_lines(segments(td, skip={first}))
            items.append(dict(name=iname, base=base, image=image, lines=body, fields=fields(body)))
        sets.append(dict(name=name, subtitle=subtitle, group=group, members=members,
                         bonuses=bonuses, items=items, summary_lines=lines))
    return sets

if __name__ == '__main__':
    s = parse()
    print(len(s), sum(len(x['items']) for x in s))
    for x in s:
        if len(x['members']) != len(x['items']):
            print('MISMATCH', x['name'], x['members'], [i['name'] for i in x['items']])
    print(s[0]['name'], s[0]['subtitle'], s[0]['group'], s[0]['members'], [b['header'] for b in s[0]['bonuses']])
    print(s[0]['items'][0]['name'], s[0]['items'][0]['base'], s[0]['items'][0]['fields'])
    print([ (x['name'], x['group']) for x in s][-12:])
    json.dump(s, open('data_sets.json', 'w'), indent=1)
