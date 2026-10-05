"""Turn a folder of docs pages (raw/*.html + images/) into wiki pages.

Must be called with the current directory set to that folder, after settings.py has been filled in.
Returns (pages, images): pages is {title: wikitext}; images is {wiki file name: local path} for every
image the pages reference that came from the docs.
"""
import os, re, json, glob, collections


def run():
    import parse_uniques, parse_sets, parse_runewords, parse_bases
    # 1. parse the four item databases out of the docs HTML
    json.dump(dict(tiered=parse_uniques.parse('raw/doc_items_tiereduniques.html', 'tiered'),
                   sacred=parse_uniques.parse('raw/doc_items_sacreduniques.html', 'sacred')),
              open('data_uniques.json', 'w', encoding='utf-8'), indent=1)
    json.dump(parse_sets.parse(), open('data_sets.json', 'w', encoding='utf-8'), indent=1)
    json.dump(parse_runewords.parse(), open('data_runewords.json', 'w', encoding='utf-8'), indent=1)
    json.dump(parse_bases.parse(), open('data_bases.json', 'w', encoding='utf-8'), indent=1)

    # 2. generate pages (same order as the original build)
    import common, conv, templates
    from common import PAGES, REDIRECTS, add_redirect
    import gen_items, gen_pages, gen_nav
    gen_items.build()
    gen_pages.build()
    T = templates.T
    gen_nav.build_templates(T)
    item_groups = sorted({b['category'] for b in gen_items.B} | {i['category'] for k in ('tiered', 'sacred') for i in gen_items.U[k]})
    set_groups = sorted({s['group'] for s in gen_items.S if s['group']})
    CATS = gen_nav.build_categories(item_groups, set_groups)
    for k, v in gen_nav.EXTRA_REDIRECTS.items():
        add_redirect(k, v)

    ALL = collections.OrderedDict()
    for t, v in T.items(): ALL[t] = v
    for t, v in CATS.items(): ALL[t] = v
    for t, v in PAGES.items(): ALL[t] = v
    for t, v in REDIRECTS.items(): ALL[t] = f'#REDIRECT [[{v}]]\n'

    # 3. images the pages use, mapped to local files from the docs snapshot
    referenced = set()
    for v in ALL.values():
        for m in re.finditer(r'\[\[File:([^|\]]+)', v):
            referenced.add(m.group(1).strip())
        for m in re.finditer(r'\|image=([^\n|}]+)', v):
            if m.group(1).strip():
                referenced.add(m.group(1).strip())
    referenced.discard('{{{image}}}')
    local = {}
    for pth in glob.glob('images/**/*', recursive=True):
        if os.path.isfile(pth):
            rel = pth[len('images/'):].replace(os.sep, '/')
            local[conv.img_file('/images/' + rel)] = '/images/' + rel
    images = {}
    for f in sorted(referenced):
        src = conv.IMAGES_USED.get(f) or local.get(f)
        if src:
            src = re.sub(r'^https?://[^/]+', '', src.replace(conv.DOCS, ''))
        p = ('images' + src[len('/images'):]) if src else None
        images[f] = p if p and os.path.exists(p) else None
    return ALL, images
