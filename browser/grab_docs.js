/* Median XL wiki sync — step 1: save a snapshot of docs.median-xl.com
 *
 * How to use:
 *   1. Open https://docs.median-xl.com in Chrome (pass the "verify you are human" check if shown).
 *   2. Press F12, open the Console tab, paste this whole file and press Enter.
 *      (The first time, Chrome may ask you to type "allow pasting" first.)
 *   3. Wait for "Done" — a file named mxl-docs-snapshot-<date>.json is saved to your Downloads folder.
 */
(async () => {
  if (!/docs\.median-xl\.com$/.test(location.hostname)) {
    alert('Run this on https://docs.median-xl.com (you are on ' + location.hostname + ').');
    return;
  }
  const box = document.createElement('div');
  box.style.cssText = 'position:fixed;z-index:99999;right:16px;bottom:16px;width:360px;padding:12px 14px;background:#111;color:#eee;font:13px/1.4 monospace;border:1px solid #c8a24a;border-radius:6px;box-shadow:0 4px 18px #000';
  document.body.appendChild(box);
  const say = (t) => { box.textContent = 'MXL docs snapshot\n' + t; box.style.whiteSpace = 'pre-wrap'; console.log('[mxl] ' + t); };

  const getText = async (u) => { const r = await fetch(u, { credentials: 'include' }); if (!r.ok) throw new Error(u + ' -> ' + r.status); return r.text(); };
  const b64 = (buf) => { const b = new Uint8Array(buf); let s = ''; for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000)); return btoa(s); };
  const dec = (s) => { try { return decodeURI(s); } catch (e) { return s; } };
  async function pool(items, n, fn) { let i = 0; const out = []; await Promise.all(Array.from({ length: n }, async () => { while (i < items.length) { const k = i++; out[k] = await fn(items[k], k); } })); return out; }

  say('Reading the page list…');
  const index = await getText('/');
  const paths = ['/', ...new Set([...index.matchAll(/href=["'](\/doc\/[a-z0-9_\/-]+)["']/gi)].map(m => m[1]))];
  const pages = {};
  let done = 0;
  await pool(paths, 4, async (p) => {
    try { pages[p] = await getText(p); } catch (e) { console.warn(e); pages[p] = null; }
    say(`Pages: ${++done}/${paths.length}`);
  });

  const imgs = new Set();
  for (const html of Object.values(pages)) {
    if (!html) continue;
    for (const m of html.matchAll(/["'(](?:https?:\/\/docs\.median-xl\.com)?(\/images\/[^"'()<>\n]+)["')]/g)) imgs.add(m[1].replace(/&amp;/g, '&'));
  }
  const list = [...imgs];
  const images = {}; const failed = [];
  done = 0;
  await pool(list, 6, async (src) => {
    try {
      const r = await fetch(encodeURI(dec(src)), { credentials: 'include' });
      if (!r.ok) throw new Error(r.status);
      images[dec(src)] = b64(await r.arrayBuffer());
    } catch (e) { failed.push(src); }
    if (++done % 10 === 0 || done === list.length) say(`Pages: ${paths.length} ✓\nImages: ${done}/${list.length}`);
  });

  const h1 = (pages['/'] || '').match(/Σ\s*([0-9]+\.[0-9]+(?:\.[0-9]+)?)/);
  const snap = { kind: 'mxl-docs-snapshot', source: location.origin, taken: new Date().toISOString(),
                 version: h1 ? h1[1] : null, pages, images, failed_images: failed };
  const blob = new Blob([JSON.stringify(snap)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `mxl-docs-snapshot-${snap.taken.slice(0, 10)}.json`;
  document.body.appendChild(a); a.click(); a.remove();
  say(`Done — Σ ${snap.version || '?'}\n${Object.keys(pages).length} pages, ${Object.keys(images).length} images` +
      (failed.length ? `, ${failed.length} images failed (see console)` : '') +
      `\nSaved ${a.download} (${(blob.size / 1048576).toFixed(1)} MB) to Downloads.\nClick this box to close.`);
  if (failed.length) console.warn('[mxl] images that failed:', failed);
  box.onclick = () => box.remove();
})();
