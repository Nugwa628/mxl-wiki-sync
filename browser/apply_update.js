/* Median XL wiki sync — step 4: apply wiki-update.json to wiki.median-xl.com
 *
 * How to use:
 *   1. Open https://wiki.median-xl.com in Chrome and log in.
 *   2. Press F12, open the Console tab, paste this whole file and press Enter.
 *   3. In the panel, choose the wiki-update.json made by sync.py, check the counts, click Start.
 * Safety:
 *   - A page that someone edited after the wiki snapshot was taken is skipped (edit conflict), not overwritten.
 *   - "create" edits never overwrite an existing page; "update" edits never create a page.
 *   - You can click Stop at any time; nothing is half-written.
 * At the end a results file (wiki-update-result-<date>.json) is saved to Downloads.
 */
(() => {
  if (!window.mw || !/median-xl/.test(location.hostname)) { alert('Run this on https://wiki.median-xl.com'); return; }
  const user = mw.config.get('wgUserName');
  if (!user) { alert('You are not logged in. Log in to the wiki, reload, and paste the script again.'); return; }
  document.getElementById('mxl-sync-panel')?.remove();
  const P = document.createElement('div');
  P.id = 'mxl-sync-panel';
  P.style.cssText = 'position:fixed;z-index:99999;right:16px;bottom:16px;width:440px;max-height:80vh;display:flex;flex-direction:column;background:#14110d;color:#e8e0d0;font:13px/1.45 system-ui,sans-serif;border:1px solid #c8a24a;border-radius:8px;box-shadow:0 6px 24px #000;padding:12px 14px';
  P.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center"><b style="color:#c8a24a;font-size:15px">MXL wiki sync — apply update</b><a href="#" id="mx-x" style="color:#9a8f7d;text-decoration:none">✕</a></div>
    <div style="margin:4px 0 8px;color:#9a8f7d">Logged in as <b style="color:#e8e0d0">${mw.html.escape(user)}</b></div>
    <input type="file" id="mx-file" accept=".json" style="margin-bottom:8px;color:#e8e0d0">
    <div id="mx-info" style="margin-bottom:8px"></div>
    <div style="display:flex;gap:8px;margin-bottom:8px"><button id="mx-go" disabled>Start</button><button id="mx-stop" disabled>Stop</button>
      <label style="margin-left:auto;color:#9a8f7d"><input type="checkbox" id="mx-dry"> dry run (no changes)</label></div>
    <div style="background:#2a241c;border-radius:4px;height:8px;margin-bottom:8px"><div id="mx-bar" style="background:#c8a24a;height:8px;width:0;border-radius:4px"></div></div>
    <div id="mx-log" style="overflow:auto;flex:1;font:12px/1.4 ui-monospace,Consolas,monospace;white-space:pre-wrap;background:#000;padding:6px;border-radius:4px;min-height:120px"></div>`;
  document.body.appendChild(P);
  const $ = (id) => P.querySelector('#' + id);
  const logEl = $('mx-log');
  const log = (t, c) => { const d = document.createElement('div'); d.textContent = t; if (c) d.style.color = c; logEl.appendChild(d); logEl.scrollTop = 1e9; console.log('[mxl] ' + t); };
  $('mx-x').onclick = (e) => { e.preventDefault(); P.remove(); };

  let U = null, stop = false;
  $('mx-file').onchange = async (e) => {
    const f = e.target.files[0]; if (!f) return;
    try { U = JSON.parse(await f.text()); } catch (err) { log('Could not read that file: ' + err, '#e0705a'); return; }
    if (U.kind !== 'mxl-wiki-update') { log('That is not a wiki-update.json from sync.py', '#e0705a'); U = null; return; }
    const c = U.edits.filter(e => e.action === 'create').length;
    $('mx-info').innerHTML = `<b>Σ ${mw.html.escape(U.version)}</b> · made ${mw.html.escape(U.generated)}<br>` +
      `${c} new pages · ${U.edits.length - c} page updates · ${U.uploads.length} image uploads` +
      (U.uploads.some(u => u.overwrite) ? ` (${U.uploads.filter(u => u.overwrite).length} replace existing images)` : '');
    $('mx-go').disabled = !(U.edits.length || U.uploads.length);
    if ($('mx-go').disabled) log('Nothing to do — the wiki is already up to date.');
  };

  const api = mw.util.wikiScript('api');
  let token = null;
  const getToken = async () => { const j = await (await fetch(api + '?action=query&meta=tokens&format=json', { credentials: 'include' })).json(); token = j.query.tokens.csrftoken; };
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  async function post(fd) {
    for (let tries = 0; tries < 6; tries++) {
      fd.set('token', token);
      let j;
      try { j = await (await fetch(api, { method: 'POST', body: fd, credentials: 'include' })).json(); }
      catch (err) { await sleep(5000); continue; }
      const code = j.error && j.error.code;
      if (code === 'ratelimited' || code === 'maxlag' || code === 'readonly') { log(`  wiki says "${code}", waiting…`, '#9a8f7d'); await sleep(30000 * (tries + 1)); continue; }
      if (code === 'badtoken') { await getToken(); continue; }
      return j;
    }
    return { error: { code: 'gave-up', info: 'too many retries' } };
  }

  $('mx-stop').onclick = () => { stop = true; log('Stopping after the current item…', '#e0a040'); };
  $('mx-go').onclick = async () => {
    const dry = $('mx-dry').checked;
    $('mx-go').disabled = true; $('mx-stop').disabled = false; $('mx-file').disabled = true; stop = false;
    await getToken();
    const res = { version: U.version, started: new Date().toISOString(), user, dry, done: [], skipped: [], failed: [] };
    const total = U.uploads.length + U.edits.length; let n = 0;
    const tick = () => { $('mx-bar').style.width = (100 * ++n / total) + '%'; };
    log(`${dry ? 'DRY RUN: ' : ''}starting — ${total} items`);

    // images first, so the pages show them straight away
    for (const up of U.uploads) {
      if (stop) break;
      if (dry) { log('would upload File:' + up.name); tick(); continue; }
      const bin = Uint8Array.from(atob(up.b64), ch => ch.charCodeAt(0));
      const fd = new FormData();
      fd.set('action', 'upload'); fd.set('format', 'json'); fd.set('filename', up.name);
      fd.set('comment', U.summary); fd.set('text', 'Image from docs.median-xl.com\n[[Category:Images from the game guide]]');
      if (up.overwrite) fd.set('ignorewarnings', '1');
      fd.set('file', new Blob([bin]), up.name);
      const j = await post(fd);
      const r = j.upload && j.upload.result;
      if (r === 'Success') { res.done.push({ file: up.name }); log('✓ File:' + up.name, '#7fbf6a'); }
      else if (j.upload && j.upload.warnings && (j.upload.warnings.exists || j.upload.warnings.duplicate)) { res.skipped.push({ file: up.name, why: 'already exists' }); log('– File:' + up.name + ' already exists, skipped', '#9a8f7d'); }
      else { res.failed.push({ file: up.name, error: JSON.stringify(j.error || j.upload) }); log('✗ File:' + up.name + ' ' + JSON.stringify(j.error || j.upload), '#e0705a'); }
      tick(); await sleep(700);
    }
    for (const e of U.edits) {
      if (stop) break;
      if (dry) { log(`would ${e.action} ${e.title}`); tick(); continue; }
      const fd = new FormData();
      fd.set('action', 'edit'); fd.set('format', 'json'); fd.set('title', e.title); fd.set('text', e.text);
      fd.set('summary', U.summary);
      if (e.action === 'create') fd.set('createonly', '1');
      else { fd.set('nocreate', '1'); if (e.basets) fd.set('basetimestamp', e.basets); }
      const j = await post(fd);
      const code = j.error && j.error.code;
      if (j.edit && j.edit.result === 'Success') { res.done.push({ title: e.title, action: e.action }); log(`✓ ${e.action === 'create' ? 'created' : 'updated'} ${e.title}`, '#7fbf6a'); }
      else if (code === 'editconflict' || code === 'articleexists' || code === 'missingtitle') {
        const why = { editconflict: 'changed on the wiki after the snapshot', articleexists: 'page now exists', missingtitle: 'page was deleted' }[code];
        res.skipped.push({ title: e.title, why }); log(`– skipped ${e.title}: ${why}`, '#e0a040');
      } else { res.failed.push({ title: e.title, error: JSON.stringify(j.error || j) }); log(`✗ ${e.title}: ${JSON.stringify(j.error || j)}`, '#e0705a'); }
      tick(); await sleep(700);
    }
    res.finished = new Date().toISOString(); res.stopped = stop;
    log(`${stop ? 'Stopped' : 'Finished'}: ${res.done.length} done, ${res.skipped.length} skipped, ${res.failed.length} failed.`, '#c8a24a');
    if (res.skipped.length) log('Skipped pages were changed on the wiki while you worked. Take new snapshots and run sync.py again to pick them up.', '#9a8f7d');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([JSON.stringify(res, null, 1)], { type: 'application/json' }));
    a.download = `wiki-update-result-${res.started.slice(0, 10)}.json`;
    document.body.appendChild(a); a.click(); a.remove();
    $('mx-stop').disabled = true;
  };
  log('Choose the wiki-update.json file made by sync.py.');
})();
