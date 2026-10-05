#!/usr/bin/env python3
"""Median XL wiki sync: compare wiki.median-xl.com with docs.median-xl.com and build an update.

Usage (see README.md for the full walkthrough):
    python sync.py                         # finds the newest snapshots in ./snapshots or your Downloads folder
    python sync.py --docs D.json --wiki W.json
Options:
    --version 2.15        override the game version (normally read from the docs front page)
    --update-images       also replace wiki images whose docs version changed
    --recreate            re-create pages this tool made before that are now missing from the wiki
    --out DIR             where to write the result folder (default: ./output)
    --no-save             don't record this run in data/history (for test runs)
Result: output/sync-<version>-<date>/report.html, wiki-update.json and apply_update.js,
        plus for-special-import/ (XML + images) for admins who prefer Special:Import.
    --import-user NAME    user name written into the Special:Import XML (default: MXL Docs Sync)
    --import-part-mb 1.5  maximum size of each Special:Import XML file
"""
import argparse, base64, collections, datetime, difflib, glob, gzip, hashlib, html, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from merge3 import merge

HISTORY = os.path.join(HERE, 'data', 'history')
KEEP_HISTORY = 12
# pages this tool never edits: built from the game files or written by hand
UNMANAGED = {'Main Page', 'Secret Items', 'Amazon', 'Assassin', 'Barbarian', 'Druid', 'Necromancer', 'Paladin', 'Sorceress'}
# docs pages whose content lands on pages this tool does not update (or is not converted at all)
DOCS_FEEDS = {
    '/doc/class/amazon': 'Amazon (class page — not auto-updated)', '/doc/class/assassin': 'Assassin (class page — not auto-updated)',
    '/doc/class/barbarian': 'Barbarian (class page — not auto-updated)', '/doc/class/druid': 'Druid (class page — not auto-updated)',
    '/doc/class/necromancer': 'Necromancer (class page — not auto-updated)', '/doc/class/paladin': 'Paladin (class page — not auto-updated)',
    '/doc/class/sorceress': 'Sorceress (class page — not auto-updated)',
}
USED_DOCS = {'/', '/doc/class/hirelings', '/doc/concepts/defense', '/doc/concepts/experience', '/doc/concepts/minion',
             '/doc/concepts/spellfocus', '/doc/items/baseitems', '/doc/items/cube', '/doc/items/runewords',
             '/doc/items/sacreduniques', '/doc/items/sets', '/doc/items/socketables', '/doc/items/tiereduniques',
             '/doc/quests/challenges', '/doc/quests/dungeons', '/doc/quests/rifts', '/doc/wiki/affixes',
             '/doc/wiki/armorlooks', '/doc/wiki/cycles', '/doc/wiki/relics', '/doc/wiki/shrines',
             '/doc/wiki/trophies', '/doc/wiki/umos'}


def log(*a):
    print(*a, flush=True)


def norm(t):
    """MediaWiki trims trailing whitespace when it saves a page."""
    return (t or '').rstrip() + '\n'


def vnorm(t):
    """Text with the game version numbers blanked out (to spot edits that only bump the version)."""
    t = re.sub(r'(\{\{Changelog\|[^|}]+\|)[0-9.]+\}\}', r'\1V}}', t)
    t = re.sub(r'Σ ?[0-9]+\.[0-9]+(\.[0-9]+)?', 'Σ V', t)
    return re.sub(r'\{\{\{version\|[0-9.]+\}\}\}', '{{{version|V}}}', t)


def key(name):
    return name.replace('_', ' ').strip().lower()


# ------------------------------------------------------------------ inputs
def find_snapshot(kind):
    dirs = [os.path.join(HERE, 'snapshots'), os.path.join(os.path.expanduser('~'), 'Downloads'), os.getcwd()]
    found = []
    for d in dirs:
        found += glob.glob(os.path.join(d, f'mxl-{kind}-snapshot*.json'))
    return max(found, key=os.path.getmtime) if found else None


def load_json(path, kind):
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    if d.get('kind') != f'mxl-{kind}-snapshot':
        sys.exit(f'{path} is not a {kind} snapshot (made with browser/grab_{kind}.js)')
    return d


def load_history():
    out = []
    for p in sorted(glob.glob(os.path.join(HISTORY, 'gen-*.json.gz')), reverse=True):
        with gzip.open(p, 'rt', encoding='utf-8') as f:
            d = json.load(f)
        out.append((os.path.basename(p), {t: norm(v) for t, v in d['pages'].items()}, d))
    return out


def docs_to_folder(docs, work):
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(os.path.join(work, 'raw'))
    for path, text in docs['pages'].items():
        if text is None:
            continue
        name = 'index.html' if path == '/' else 'doc_' + path.strip('/').split('/', 1)[1].replace('/', '_') + '.html'
        with open(os.path.join(work, 'raw', name), 'w', encoding='utf-8', newline='') as f:
            f.write(text)
    for src, b64 in docs['images'].items():
        rel = src[len('/images/'):]
        if '..' in rel.split('/'):
            continue
        p = os.path.join(work, 'images', *rel.split('/'))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as f:
            f.write(base64.b64decode(b64))


def docs_text_hashes(docs):
    from bs4 import BeautifulSoup
    out = {}
    for path, text in docs['pages'].items():
        if not text:
            continue
        soup = BeautifulSoup(text, 'lxml')
        page = soup.select_one('.page') or soup.body or soup
        out[path] = hashlib.sha1(re.sub(r'\s+', ' ', page.get_text(' ')).strip().encode()).hexdigest()
    return out


# ------------------------------------------------------------------ main
def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors='replace')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='Compare the Median XL wiki with the docs and build an update.')
    ap.add_argument('--docs'); ap.add_argument('--wiki'); ap.add_argument('--version')
    ap.add_argument('--out', default=os.path.join(HERE, 'output'))
    ap.add_argument('--update-images', action='store_true')
    ap.add_argument('--recreate', action='store_true')
    ap.add_argument('--no-save', action='store_true')
    ap.add_argument('--import-user', default='MXL Docs Sync', help='user name written into the Special:Import XML')
    ap.add_argument('--import-part-mb', type=float, default=1.5, help='max size of each Special:Import XML file')
    a = ap.parse_args()

    docs_path = a.docs or find_snapshot('docs')
    wiki_path = a.wiki or find_snapshot('wiki')
    if not docs_path or not wiki_path:
        sys.exit('Could not find the snapshots. Run browser/grab_docs.js and browser/grab_wiki.js first '
                 '(see README.md), or pass --docs and --wiki.')
    log(f'Docs snapshot: {docs_path}')
    log(f'Wiki snapshot: {wiki_path}')
    docs = load_json(docs_path, 'docs')
    wiki = load_json(wiki_path, 'wiki')
    version = a.version or docs.get('version')
    if not version:
        sys.exit('Could not read the version from the docs front page; pass --version, e.g. --version 2.15')
    vfull = version if version.count('.') >= 2 else version + '.0'
    log(f'Game version: Σ {version}')

    live = {t: p for t, p in wiki['pages'].items()}
    history = load_history()
    hist_titles = set().union(*[set(h) for _, h, _ in history]) if history else set()
    pre = json.load(open(os.path.join(HERE, 'data', 'pre_import_wiki.json'), encoding='utf-8'))

    # ---- generate pages from the docs
    stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
    outdir = os.path.join(a.out, f'sync-{version}-{stamp}')
    work = os.path.join(outdir, '_work')
    log('Unpacking docs snapshot…')
    docs_to_folder(docs, work)
    sys.path.insert(0, os.path.join(HERE, 'generator'))
    import settings
    settings.VERSION, settings.VERSION_FULL = version, vfull
    settings.PRE_IMPORT = os.path.join(HERE, 'data', 'pre_import_wiki.json')
    settings.LIVE_OTHER_TITLES = {t for t in live if t not in pre['pages'] and t not in hist_titles}
    cl = live.get('Module:Changelog/data')
    settings.CHANGELOG_DATA = cl['text'] if cl else None
    log('Generating pages from the docs (this takes a few seconds)…')
    cwd = os.getcwd()
    os.chdir(work)
    try:
        import build_pages
        ALL, images = build_pages.run()
    finally:
        os.chdir(cwd)
    ALL = collections.OrderedDict((t, norm(v)) for t, v in ALL.items() if t not in UNMANAGED)
    log(f'{len(ALL)} pages generated')

    # ---- compare with the wiki
    R = collections.defaultdict(list)   # category -> list of dict
    edits = []
    conflict_dir = os.path.join(outdir, 'conflicts')
    for t, new in ALL.items():
        lp = live.get(t)
        if lp is None:
            if t in hist_titles and not a.recreate:
                R['missing'].append(dict(title=t))
                continue
            R['create'].append(dict(title=t, new=new))
            edits.append(dict(title=t, text=new, action='create'))
            continue
        cur = norm(lp['text'])
        if cur == new:
            R['same'].append(dict(title=t)); continue
        if any(h.get(t) == cur for _, h, _ in history):
            R['update_version' if vnorm(cur) == vnorm(new) else 'update'].append(dict(title=t, old=cur, new=new, user=lp.get('user')))
            edits.append(dict(title=t, text=new, action='update', basets=lp['ts']))
            continue
        cands = [h[t] for _, h, _ in history if t in h]
        if not cands:
            R['foreign'].append(dict(title=t, old=cur, new=new, user=lp.get('user')))
            continue
        cl_ = cur.splitlines()
        base = max(cands, key=lambda b: difflib.SequenceMatcher(None, b.splitlines(), cl_, autojunk=False).ratio())
        merged, conf = merge(base, cur, new)
        if norm(merged) == cur:
            R['kept'].append(dict(title=t, user=lp.get('user')))
        elif not conf:
            R['merge'].append(dict(title=t, old=cur, new=norm(merged), user=lp.get('user')))
            edits.append(dict(title=t, text=norm(merged), action='update', basets=lp['ts']))
        else:
            os.makedirs(conflict_dir, exist_ok=True)
            fn = re.sub(r'[\\/:*?"<>|]', '_', t)
            open(os.path.join(conflict_dir, fn + '.merged-with-markers.wiki'), 'w', encoding='utf-8').write(merged)
            open(os.path.join(conflict_dir, fn + '.docs-version.wiki'), 'w', encoding='utf-8').write(new)
            R['conflict'].append(dict(title=t, old=cur, new=new, n=len(conf), user=lp.get('user'), file=fn))
    if history:
        latest = history[0][1]
        for t in latest:
            if t not in ALL and t not in UNMANAGED and t in live:
                R['gone'].append(dict(title=t))

    # ---- images
    live_files = {key(f['name']): f for f in wiki['files']}
    uploads = []
    for f, p in images.items():
        lf = live_files.get(key(f))
        if p is None:
            if not lf:
                R['img_missing'].append(dict(title=f))
            continue
        data = open(os.path.join(work, p), 'rb').read()
        if not lf:
            R['img_new'].append(dict(title=f))
            uploads.append(dict(name=f.replace(' ', '_'), b64=base64.b64encode(data).decode(), overwrite=False))
        elif hashlib.sha1(data).hexdigest() != lf['sha1']:
            R['img_changed'].append(dict(title=f, user=lf.get('user')))
            if a.update_images:
                uploads.append(dict(name=f.replace(' ', '_'), b64=base64.b64encode(data).decode(), overwrite=True))

    # ---- docs pages that changed but are not (fully) handled automatically
    hashes = docs_text_hashes(docs)
    prev_hashes = {}
    hp = sorted(glob.glob(os.path.join(HISTORY, 'docs-*.json')))
    if hp:
        prev_hashes = json.load(open(hp[-1], encoding='utf-8'))
    for path, h in sorted(hashes.items()):
        if prev_hashes and prev_hashes.get(path) != h and path not in USED_DOCS:
            R['docs_manual'].append(dict(title=path, note=DOCS_FEEDS.get(path, 'not converted to a wiki page by this tool')))

    # ---- write the results
    os.makedirs(outdir, exist_ok=True)
    summary = f'Sync with docs.median-xl.com (Σ {version})'
    payload = dict(kind='mxl-wiki-update', version=version, generated=datetime.datetime.now().isoformat(timespec='seconds'),
                   summary=summary, wiki_snapshot=wiki.get('taken'), edits=edits, uploads=uploads)
    with open(os.path.join(outdir, 'wiki-update.json'), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
    shutil.copy(os.path.join(HERE, 'browser', 'apply_update.js'), os.path.join(outdir, 'apply_update.js'))
    global IMPORT_PART_LIMIT
    IMPORT_PART_LIMIT = int(a.import_part_mb * 1_000_000)
    import_parts = write_import(os.path.join(outdir, 'for-special-import'), payload, wiki.get('taken'), a.import_user)
    write_report(os.path.join(outdir, 'report.html'), R, version, docs, wiki, payload, a)
    shutil.rmtree(work, ignore_errors=True)

    if not a.no_save:
        save_history(ALL, version, hashes, history)

    counts = {k: len(v) for k, v in R.items()}
    log('')
    log(f"  new pages        {counts.get('create', 0)}")
    log(f"  updated          {counts.get('update', 0)}  (+{counts.get('update_version', 0)} version-number-only)")
    log(f"  merged w/ edits  {counts.get('merge', 0)}")
    log(f"  CONFLICTS        {counts.get('conflict', 0) + counts.get('foreign', 0)}  (not in the update — see report)")
    log(f"  unchanged        {counts.get('same', 0) + counts.get('kept', 0)}")
    log(f"  images to upload {len(uploads)}")
    log('')
    log(f'Done. Open {os.path.join(outdir, "report.html")}')
    if import_parts:
        log(f'Admins: Special:Import files are in {os.path.join(outdir, "for-special-import")} ({len(import_parts)} XML file(s))')
    if not edits and not uploads:
        log('The wiki is already up to date with the docs — nothing to apply.')


def save_history(ALL, version, hashes, history):
    os.makedirs(HISTORY, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    if not history or history[0][1] != dict(ALL):
        with gzip.open(os.path.join(HISTORY, f'gen-{version}-{stamp}.json.gz'), 'wt', encoding='utf-8') as f:
            json.dump(dict(version=version, created=stamp, pages=ALL), f, ensure_ascii=False)
    with open(os.path.join(HISTORY, f'docs-{stamp}.json'), 'w', encoding='utf-8') as f:
        json.dump(hashes, f)
    gens = sorted(glob.glob(os.path.join(HISTORY, 'gen-*.json.gz')))
    for old in gens[1:-KEEP_HISTORY]:          # keep the very first (initial import) and the newest few
        os.remove(old)
    for old in sorted(glob.glob(os.path.join(HISTORY, 'docs-*.json')))[:-KEEP_HISTORY]:
        os.remove(old)


# ------------------------------------------------------------------ Special:Import (admins)
IMPORT_PART_LIMIT = 1_500_000   # bytes per XML file, to stay under typical upload limits


def _ns(title):
    for pre, n in (('Template:', 10), ('Category:', 14), ('Module:', 828), ('MediaWiki:', 8), ('File:', 6), ('Project:', 4)):
        if title.startswith(pre):
            return n
    return 0


def _model(title):
    if title.startswith('Module:'):
        return 'Scribunto', 'text/plain'
    if title.startswith('Template:') and title.endswith('.css'):
        return 'sanitized-css', 'text/css'
    return 'wikitext', 'text/x-wiki'


def write_import(folder, payload, snapshot_taken, user):
    """XML files for Special:Import plus a folder of images for Special:BatchUpload.

    Every revision is dated at the moment the wiki snapshot was taken. MediaWiki keeps the newest
    revision as the current one, so a page someone edited after the snapshot keeps their edit
    (the imported text only goes into its history) - the same protection apply_update.js gives."""
    shutil.rmtree(folder, ignore_errors=True)
    if not payload['edits'] and not payload['uploads']:
        return []
    os.makedirs(folder)
    ts = (snapshot_taken or datetime.datetime.now(datetime.timezone.utc).isoformat())[:19] + 'Z'
    head = ('<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/" version="0.11" xml:lang="en">\n'
            '  <siteinfo>\n    <sitename>Median-XL</sitename>\n    <case>first-letter</case>\n    <namespaces>\n'
            '      <namespace key="0" case="first-letter" />\n      <namespace key="4" case="first-letter">Project</namespace>\n'
            '      <namespace key="6" case="first-letter">File</namespace>\n      <namespace key="8" case="first-letter">MediaWiki</namespace>\n'
            '      <namespace key="10" case="first-letter">Template</namespace>\n      <namespace key="14" case="first-letter">Category</namespace>\n'
            '      <namespace key="828" case="first-letter">Module</namespace>\n    </namespaces>\n  </siteinfo>\n')
    esc = lambda t: html.escape(t, quote=False)
    parts, cur, size = [], [], 0
    for e in payload['edits']:
        model, fmt = _model(e['title'])
        text = e['text'].rstrip()
        x = (f'  <page>\n    <title>{esc(e["title"])}</title>\n    <ns>{_ns(e["title"])}</ns>\n    <revision>\n'
             f'      <timestamp>{ts}</timestamp>\n      <contributor><username>{esc(user)}</username></contributor>\n'
             f'      <comment>{esc(payload["summary"])}</comment>\n      <model>{model}</model>\n      <format>{fmt}</format>\n'
             f'      <text xml:space="preserve" bytes="{len(text.encode())}">{esc(text)}</text>\n'
             f'      <sha1>{_sha1_base36(text)}</sha1>\n    </revision>\n  </page>\n')
        if cur and size + len(x.encode()) > IMPORT_PART_LIMIT:
            parts.append(cur); cur, size = [], 0
        cur.append(x); size += len(x.encode())
    if cur:
        parts.append(cur)
    names = []
    for i, p in enumerate(parts, 1):
        n = f'pages-part{i:02d}.xml'
        with open(os.path.join(folder, n), 'w', encoding='utf-8', newline='\n') as f:
            f.write(head + ''.join(p) + '</mediawiki>\n')
        names.append(n)
    if payload['uploads']:
        img = os.path.join(folder, 'images-for-batchupload')
        os.makedirs(img)
        for u in payload['uploads']:
            with open(os.path.join(img, u['name']), 'wb') as f:
                f.write(base64.b64decode(u['b64']))
    titles = '\n'.join(e['title'] for e in payload['edits'])
    with open(os.path.join(folder, 'pages-in-this-import.txt'), 'w', encoding='utf-8') as f:
        f.write(titles + '\n')
    return names


def _sha1_base36(text):
    n = int(hashlib.sha1(text.encode()).hexdigest(), 16)
    digits = '0123456789abcdefghijklmnopqrstuvwxyz'
    out = ''
    while n:
        n, r = divmod(n, 36)
        out = digits[r] + out
    return out.rjust(31, '0')


# ------------------------------------------------------------------ report
WIKI = 'https://wiki.median-xl.com/index.php?title='


def link(t):
    return f'<a href="{WIKI}{html.escape(t.replace(" ", "_"), quote=True)}" target="_blank">{html.escape(t)}</a>'


def diff_html(old, new, limit=400):
    lines = list(difflib.unified_diff(old.splitlines(), new.splitlines(), 'wiki now', 'after update', lineterm='', n=1))
    more = ''
    if len(lines) > limit:
        more = f'<div class="more">… {len(lines) - limit} more diff lines not shown</div>'
        lines = lines[:limit]
    out = []
    for l in lines[2:]:
        cls = 'add' if l.startswith('+') else 'del' if l.startswith('-') else 'hunk' if l.startswith('@@') else 'ctx'
        out.append(f'<div class="{cls}">{html.escape(l)}</div>')
    return '<div class="diff">' + ''.join(out) + more + '</div>'


def write_report(path, R, version, docs, wiki, payload, a):
    def section(key, title, blurb, with_diff=False, extra=None):
        items = R.get(key, [])
        if not items:
            return ''
        rows = []
        for it in items:
            if key == 'docs_manual':
                head = f'<a href="https://docs.median-xl.com{html.escape(it["title"], quote=True)}" target="_blank">docs{html.escape(it["title"])}</a>'
            elif key.startswith('img'):
                head = html.escape(it['title'])
            else:
                head = link(it['title'])
            meta = []
            if it.get('user'):
                meta.append(f'last edit: {html.escape(str(it["user"]))}')
            if it.get('n'):
                meta.append(f'{it["n"]} conflicting part(s) — see conflicts/{html.escape(it["file"])}.*')
            if it.get('note'):
                meta.append(html.escape(it['note']))
            m = f' <span class="meta">{" · ".join(meta)}</span>' if meta else ''
            if with_diff and 'old' in it:
                rows.append(f'<details><summary>{head}{m}</summary>{diff_html(it["old"], it["new"])}</details>')
            elif with_diff and 'new' in it:
                rows.append(f'<details><summary>{head}{m}</summary><pre class="newpage">{html.escape(it["new"][:6000])}</pre></details>')
            else:
                rows.append(f'<div class="row">{head}{m}</div>')
        return (f'<section id="{key}"><h2>{title} <span class="n">{len(items)}</span></h2><p>{blurb}</p>'
                + (extra or '') + ''.join(rows) + '</section>')

    n = lambda k: len(R.get(k, []))
    cards = [('create', 'New pages', 'good'), ('update', 'Updated', 'good'), ('update_version', 'Version number only', 'dim'), ('merge', 'Merged with hand edits', 'good'),
             ('conflict', 'Conflicts', 'bad'), ('foreign', 'Not ours', 'bad'), ('same', 'Unchanged', 'dim'),
             ('kept', 'Hand edits kept', 'dim'), ('img_new', 'New images', 'good')]
    card_html = ''.join(f'<a class="card {c}" href="#{k}"><b>{n(k)}</b><span>{lbl}</span></a>' for k, lbl, c in cards)
    body = ''.join([
        section('conflict', 'Conflicts — not included in the update',
                'These pages were edited by hand on the wiki <i>and</i> changed in the docs in the same place. '
                'The <code>conflicts</code> folder has, for each page, the docs version and a merged copy with '
                '<code>&lt;&lt;&lt;&lt;&lt;&lt;&lt;</code> markers. Fix the page on the wiki by hand, or copy in the docs version.', True),
        section('foreign', 'Pages not made by this tool — not included',
                'A page with this title exists on the wiki but was never created by this tool, so it is left alone. '
                'The diff shows what the docs version would change.', True),
        section('create', 'New pages', 'Pages that do not exist on the wiki yet (new items, new redirects, …).', True),
        section('update', 'Updated pages', 'Pages nobody edited by hand since the last sync; they are replaced with the docs version.', True),
        section('update_version', 'Version number only',
                'The only change on these pages is the game version (for example in the Version history box).', True),
        section('merge', 'Updated, keeping hand edits',
                'These pages had hand edits. The docs changes were applied around them; the diff shows the final result.', True),
        section('img_new', 'New images', 'Uploaded from the docs snapshot.'),
        section('img_changed', 'Images that differ from the docs',
                ('These will be <b>replaced</b> (you ran with --update-images).' if a.update_images else
                 'Not replaced. Run again with <code>--update-images</code> to replace them.')),
        section('img_missing', 'Images used but not available', 'Not on the wiki and not in the docs snapshot.'),
        section('gone', 'No longer in the docs',
                'This tool made these pages earlier, but the docs no longer produce them (removed or renamed items). '
                'Nothing is deleted automatically — delete them or turn them into redirects by hand if appropriate.'),
        section('missing', 'Made earlier but missing from the wiki',
                'These pages were created by an earlier sync but are not on the wiki now (maybe deleted on purpose). '
                'Not re-created; run with <code>--recreate</code> to bring them back.'),
        section('docs_manual', 'Docs pages to check by hand',
                'These docs pages changed since the last run, but their content goes to pages this tool does not update '
                '(class pages are built from the game files) or is not converted at all.'),
        section('kept', 'Hand edits, no docs changes', 'Edited on the wiki; the docs did not change these pages, so nothing to do.'),
    ])
    nedits, nup = len(payload['edits']), len(payload['uploads'])
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MXL wiki sync — Σ {html.escape(version)}</title>
<style>
:root{{--bg:#14110d;--panel:#1f1a14;--line:#3a3127;--text:#e8e0d0;--dim:#9a8f7d;--gold:#c8a24a;--good:#7fbf6a;--bad:#e0705a;--add:#173a17;--del:#4a1c1c}}
body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,Segoe UI,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:24px 16px 80px}}
h1{{color:var(--gold);font-weight:600;margin:0 0 4px}} h2{{color:var(--gold);font-size:19px;margin:32px 0 6px;border-bottom:1px solid var(--line);padding-bottom:4px}}
.n{{background:var(--line);color:var(--text);border-radius:10px;padding:0 9px;font-size:13px;vertical-align:middle}}
.sub{{color:var(--dim);margin-bottom:18px}} p{{color:var(--dim);margin:4px 0 10px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:18px 0}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 12px;text-decoration:none;color:var(--text)}}
.card b{{display:block;font-size:26px}} .card span{{color:var(--dim);font-size:13px}}
.card.good b{{color:var(--good)}} .card.bad b{{color:var(--bad)}} .card.dim b{{color:var(--dim)}}
.steps{{background:var(--panel);border:1px solid var(--gold);border-radius:8px;padding:12px 18px}}
.steps li{{margin:4px 0}} code{{background:#000;padding:1px 5px;border-radius:4px}}
a{{color:#e6c46c}} details,.row{{background:var(--panel);border:1px solid var(--line);border-radius:6px;margin:4px 0;padding:6px 10px}}
summary{{cursor:pointer}} .meta{{color:var(--dim);font-size:13px;margin-left:8px}}
.diff{{font:12px/1.45 ui-monospace,Consolas,monospace;margin-top:8px;overflow-x:auto;white-space:pre-wrap;word-break:break-all}}
.diff .add{{background:var(--add)}} .diff .del{{background:var(--del)}} .diff .hunk{{color:var(--gold);margin-top:6px}} .diff .ctx{{color:var(--dim)}}
pre.newpage{{font:12px/1.45 ui-monospace,Consolas,monospace;white-space:pre-wrap;word-break:break-all;max-height:420px;overflow:auto}}
.more{{color:var(--dim);font-style:italic}}
</style></head><body><main>
<h1>Median XL wiki sync — Σ {html.escape(version)}</h1>
<div class="sub">Docs snapshot {html.escape(str(docs.get("taken", "?")))[:16]} · Wiki snapshot {html.escape(str(wiki.get("taken", "?")))[:16]} · {nedits} page edits and {nup} image uploads ready</div>
<div class="cards">{card_html}</div>
<div class="steps"><b>To apply the update</b><ol>
<li>Read the conflicts (if any) below — those pages are <i>not</i> changed automatically.</li>
<li>Open <a href="https://wiki.median-xl.com" target="_blank">wiki.median-xl.com</a> in Chrome and make sure you are logged in.</li>
<li>Press F12 → Console, paste the contents of <code>apply_update.js</code> (in this folder) and press Enter.</li>
<li>In the panel that appears, choose <code>wiki-update.json</code> from this folder, check the counts and click <b>Start</b>.</li>
</ol><b>Admins:</b> instead of steps 2–4 you can use <code>Special:Import</code> with the files in <code>for-special-import</code> — see “Step 5 for admins” in GUIDE.html.</div>
{body or "<p>The wiki already matches the docs.</p>"}
</main></body></html>'''
    open(path, 'w', encoding='utf-8').write(doc)


if __name__ == '__main__':
    main()
