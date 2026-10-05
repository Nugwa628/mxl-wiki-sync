/* Median XL wiki sync — step 2: save a snapshot of wiki.median-xl.com
 *
 * How to use:
 *   1. Open https://wiki.median-xl.com in Chrome.
 *   2. Press F12, open the Console tab, paste this whole file and press Enter.
 *   3. Wait for "Done" — a file named mxl-wiki-snapshot-<date>.json is saved to your Downloads folder.
 * It only reads the wiki; nothing is changed.
 */
(async () => {
  if (!window.mw || !/median-xl/.test(location.hostname)) { alert('Run this on https://wiki.median-xl.com'); return; }
  const box = document.createElement('div');
  box.style.cssText = 'position:fixed;z-index:99999;right:16px;bottom:16px;width:360px;padding:12px 14px;background:#111;color:#eee;font:13px/1.4 monospace;border:1px solid #c8a24a;border-radius:6px;box-shadow:0 4px 18px #000;white-space:pre-wrap';
  document.body.appendChild(box);
  const say = (t) => { box.textContent = 'MXL wiki snapshot\n' + t; console.log('[mxl] ' + t); };
  const api = mw.util.wikiScript('api');
  const get = async (params) => {
    const q = new URLSearchParams({ format: 'json', formatversion: '2', ...params });
    for (let tries = 0; ; tries++) {
      const r = await fetch(api + '?' + q, { credentials: 'include' });
      if (r.ok) return r.json();
      if (tries > 4) throw new Error('API ' + r.status);
      await new Promise(res => setTimeout(res, 2000 * (tries + 1)));
    }
  };

  const pages = {};
  const NS = { 0: 'Main', 4: 'Project', 8: 'MediaWiki', 10: 'Template', 14: 'Category', 828: 'Module' };
  for (const ns of Object.keys(NS)) {
    let cont = {};
    do {
      const j = await get({ action: 'query', generator: 'allpages', gapnamespace: ns, gaplimit: '50',
                            prop: 'revisions', rvprop: 'content|timestamp|user|ids', rvslots: 'main', ...cont });
      for (const p of (j.query ? j.query.pages : [])) {
        const rv = p.revisions && p.revisions[0];
        if (!rv) continue;
        pages[p.title] = { text: rv.slots.main.content, ts: rv.timestamp, user: rv.user, revid: rv.revid,
                           model: rv.slots.main.contentmodel };
      }
      cont = j.continue || null;
      say(`${NS[ns]} pages… ${Object.keys(pages).length} read`);
    } while (cont);
  }

  const files = [];
  let cont = {};
  do {
    const j = await get({ action: 'query', list: 'allimages', ailimit: '500', aiprop: 'sha1|size|url|user|timestamp', ...cont });
    for (const f of j.query.allimages) files.push({ name: f.name, sha1: f.sha1, w: f.width, h: f.height, url: f.url, user: f.user, ts: f.timestamp });
    cont = j.continue || null;
    say(`${Object.keys(pages).length} pages ✓\nFiles… ${files.length}`);
  } while (cont);

  const snap = { kind: 'mxl-wiki-snapshot', source: location.origin, taken: new Date().toISOString(),
                 user: mw.config.get('wgUserName'), pages, files };
  const blob = new Blob([JSON.stringify(snap)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `mxl-wiki-snapshot-${snap.taken.slice(0, 10)}.json`;
  document.body.appendChild(a); a.click(); a.remove();
  say(`Done — ${Object.keys(pages).length} pages, ${files.length} files.\nSaved ${a.download} (${(blob.size / 1048576).toFixed(1)} MB) to Downloads.\nClick this box to close.`);
  box.onclick = () => box.remove();
})();
