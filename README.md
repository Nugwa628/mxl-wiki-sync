# MXL Wiki Sync

Keeps [wiki.median-xl.com](https://wiki.median-xl.com) in step with [docs.median-xl.com](https://docs.median-xl.com).

When the docs update (for example to Σ 2.15), this tool finds every wiki page that needs to change and shows you each change before anything is written. It then applies the update while keeping any edits people made on the wiki by hand.

```
 1. Snapshot the docs   →  2. Snapshot the wiki  →  3. Compare & 4. Review  →  5. Apply
    (Chrome, docs site)      (Chrome, wiki)            (your PC: run_sync.bat)      (Chrome, wiki)
```

Nothing on the wiki changes until step 5. The comparison uses the same converter that originally built the wiki pages, so if the docs haven't changed it reports **no changes at all**. Running it once that way is a good first test.

## Contents

- [One-time setup](#one-time-setup)
- [1 · Snapshot the docs](#1--snapshot-the-docs)
- [2 · Snapshot the wiki](#2--snapshot-the-wiki)
- [3 · Compare](#3--compare)
- [4 · Review the report](#4--review-the-report)
- [5 · Apply](#5--apply)
- [5 · Apply with Special:Import (admins)](#5--apply-with-specialimport-admins)
- [Hand edits and conflicts](#hand-edits-and-conflicts)
- [Pages it never touches](#pages-it-never-touches)
- [Troubleshooting](#troubleshooting)
- [Options](#options)
- [FAQ](#faq)
- [Repository layout](#repository-layout)
- [License](#license)

---

## One-time setup

1. **Download the tool.** On GitHub, click **Code → Download ZIP**, or clone the repo. Unzip it somewhere permanent, such as `Desktop\sugma\mxl-wiki-sync`, and use the same folder every time. Its `data` folder is how the tool remembers what it made before, which is how it spots hand edits.
2. **Install Python 3.10 or newer** from [python.org/downloads](https://www.python.org/downloads/). During the install, **tick "Add python.exe to PATH"**. That's the only setting that matters.
   The first time you run `run_sync.bat`, it installs the two add-ons it needs (`beautifulsoup4` and `lxml`) automatically.
3. **Learn to open Chrome's Console.** On any page, press <kbd>F12</kbd> (or <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>J</kbd>) and click the **Console** tab. You'll paste scripts there and press <kbd>Enter</kbd>.

> [!IMPORTANT]
> The first time you paste into the Console, Chrome blocks it until you type `allow pasting` and press Enter. After that, pasting works normally.

---

## 1 · Snapshot the docs

1. Open [docs.median-xl.com](https://docs.median-xl.com) in Chrome. If a "verify you are human" check appears, complete it.
2. Open the Console (<kbd>F12</kbd> → Console).
3. Copy the whole of [`browser/grab_docs.js`](browser/grab_docs.js), paste it into the Console and press <kbd>Enter</kbd>. On GitHub, the copy button is at the top-right of the file view.
4. A small box in the bottom-right corner shows progress. After about a minute it says **Done**, and `mxl-docs-snapshot-<date>.json` (about 13 MB) is in your Downloads folder.

> [!NOTE]
> The Done box also shows the version it read from the docs front page, e.g. `Σ 2.15`. If it shows `?`, the front page layout changed. You can still continue: pass the version yourself in step 3 (see [Options](#options)).

## 2 · Snapshot the wiki

1. Open [wiki.median-xl.com](https://wiki.median-xl.com) in Chrome.
2. Open the Console, paste [`browser/grab_wiki.js`](browser/grab_wiki.js) and press <kbd>Enter</kbd>.
3. When the box says **Done**, `mxl-wiki-snapshot-<date>.json` (about 8 MB) is in Downloads.

This script only reads pages. You don't need to be logged in for it, and it can't change anything.

> [!TIP]
> Take the wiki snapshot just before comparing. If someone edits a page between the snapshot and step 5, that page is skipped rather than overwritten, so a fresh snapshot means fewer skipped pages.

## 3 · Compare

Double-click **`run_sync.bat`**. A black window opens and does four things:

1. Finds the newest docs and wiki snapshots in your Downloads folder.
2. Builds every wiki page from the docs, which takes about 10 seconds.
3. Compares those pages with the wiki and prints a summary.
4. Opens `report.html` in your browser.

```
Docs snapshot: C:\Users\you\Downloads\mxl-docs-snapshot-2026-11-02.json
Wiki snapshot: C:\Users\you\Downloads\mxl-wiki-snapshot-2026-11-02.json
Game version: Σ 2.15
1677 pages generated

  new pages        12
  updated          57  (+482 version-number-only)
  merged w/ edits  3
  CONFLICTS        1  (not in the update — see report)
  unchanged        1122
  images to upload 9

Done. Open ...\output\sync-2.15-2026-11-02_1930\report.html
```

Everything from the run is saved in a new folder:

```
output\sync-2.15-2026-11-02_1930\
  report.html          ← what will change, page by page
  wiki-update.json     ← the update (used in step 5)
  apply_update.js      ← the apply script
  for-special-import\  ← the same update as XML, for admins
  conflicts\           ← only if there are conflicts
```

## 4 · Review the report

The report opens with a row of counts. Click a count to jump to that list, and click a page name to see its exact change (added lines in green, removed lines in red). Each page name also links to the live wiki page.

| Section | Meaning | In the update? |
|---|---|---|
| 🔴 **Conflicts** | Edited by hand on the wiki *and* changed by the docs on the same lines. See [resolving a conflict](#resolving-a-conflict). | No: fix by hand |
| 🔴 **Not ours** | A page with that title exists, but this tool didn't create it, so it's left alone. | No |
| 🟢 **New pages** | New items, sets, runewords and redirects from the docs. | Yes |
| 🟢 **Updated** | Pages the docs changed and nobody has edited by hand since the last sync. | Yes |
| ⚪ **Version number only** | The only change is the game version, e.g. in the "Version history" box. A new major version produces hundreds of these, so they get their own list and don't hide the real changes. | Yes |
| 🟢 **Merged with hand edits** | Hand-edited pages where the docs changed a different part. Both changes are kept. | Yes |
| 🟢 **New images** | Images the pages use that aren't on the wiki yet. | Yes |
| 🟡 **Images that differ** | A wiki image doesn't match the docs version. | Only with `--update-images` |
| 🟡 **No longer in the docs** | Pages the tool made earlier that the docs no longer produce, such as removed or renamed items. | No: nothing is deleted |
| 🟡 **Docs pages to check by hand** | Docs pages that changed but feed pages this tool doesn't update, mainly the class pages. | No: update by hand |
| ⚪ **Hand edits kept** | Edited on the wiki, and the docs didn't change them. | Nothing to do |

> [!CAUTION]
> **Stop if the report looks wrong.** If hundreds of pages show strange changes, such as missing stats, broken tables or garbled text, the docs probably changed their page layout. Don't apply that update. The converter in `generator/` needs adjusting first.

## 5 · Apply

1. Open [wiki.median-xl.com](https://wiki.median-xl.com) and make sure you're **logged in**.
2. Open the Console, paste [`browser/apply_update.js`](browser/apply_update.js) (or the copy in the output folder) and press <kbd>Enter</kbd>.
3. A panel appears in the bottom-right corner. Click **Choose File** and pick `wiki-update.json` from the output folder.
4. Check that the counts in the panel match the report.
5. *Optional:* tick **dry run** and click **Start**. This lists everything it would do without changing anything. To do the real run afterwards, paste the script again.
6. Untick dry run and click **Start**.

The script uploads new images first, then edits pages about once a second, staying under the wiki's limit of about 90 edits a minute. A 500-page update takes about 8–10 minutes. Leave the tab open while it runs.

- **Stop** finishes the current page and then stops, so nothing is left half-written. To carry on later, take a new wiki snapshot and run steps 3–5 again. Pages that were already done will show as unchanged.
- If the wiki reports it's busy or rate-limited, the script waits and tries again on its own.
- At the end, it saves `wiki-update-result-<date>.json` to Downloads. It lists every page that was done, skipped or failed.

Works with any normal logged-in editor account. Admin rights aren't needed.

> [!NOTE]
> **Built-in safety:** a "new page" edit can never overwrite an existing page, and an "update" can never create one. A page someone edited after your wiki snapshot is skipped with the message *changed on the wiki after the snapshot*. Every edit appears in page history with the summary "Sync with docs.median-xl.com (Σ x.y)", so it can be undone from there.

## 5 · Apply with Special:Import (admins)

An alternative to the step above for accounts with the **import** right (admins on this wiki). It loads the whole update in a few seconds instead of running `apply_update.js`. Steps 1–4 are the same. Every run also writes the files this method needs:

```
output\sync-2.15-2026-11-02_1930\for-special-import\
  pages-part01.xml             ← page updates, split into files of about 1.5 MB
  pages-part02.xml
  images-for-batchupload\      ← new images (only if there are any)
  pages-in-this-import.txt     ← list of every page in the XML files
```

The XML files hold the same pages as `wiki-update.json`. Conflicts are already left out.

1. **Do steps 2–4 right before importing.** The import protects pages edited *after the wiki snapshot* (see below).
2. **Upload the images first.** Skip this if there's no `images-for-batchupload` folder.
   1. Open [Special:BatchUpload](https://wiki.median-xl.com/index.php?title=Special:BatchUpload) while logged in.
   2. Drag every file from `images-for-batchupload` onto the drop area. Don't rename them; the file names already match what the pages use.
   3. Wait until every file shows a tick.
3. **Import the XML files.**
   1. Open [Special:Import](https://wiki.median-xl.com/index.php?title=Special:Import) and use the **Import from an XML file** section.
   2. Choose `pages-part01.xml`.
   3. **Interwiki prefix:** type `docs`. The form requires a prefix; it's only used to label the imported edits.
   4. Leave *Assign edits to local users* unticked. Only tick it if you ran sync with `--import-user YourName` and want the edits under your own name.
   5. Optionally enter a reason, e.g. `Sync with docs Σ 2.15`, then click **Upload file**.
   6. The wiki lists every page with either "1 revision" (imported) or "0 revisions" (already identical).
   7. Repeat for `pages-part02.xml` and any further files, in order.
4. **Check the result.** Take a fresh wiki snapshot and run the compare again. Only conflicts should be left. Any page that someone edited after your first snapshot will appear again; apply it the normal way.

> [!TIP]
> If you get "File too large" or a timeout, run the compare again with smaller files, e.g. `run_sync.bat --import-part-mb 0.5`.

**Why pages edited after the snapshot are safe:** every imported revision is dated at the time of your wiki snapshot, and MediaWiki always keeps the *newest* revision as the current page. If someone edited a page after the snapshot, their edit stays current and the imported text only goes into that page's history. It's the same protection `apply_update.js` gives.

| | `apply_update.js` | Special:Import |
|---|---|---|
| Who can use it | Any logged-in editor | Accounts with the import right (admins) |
| Speed, 500 pages | About 8–10 minutes | Under a minute, plus a few clicks per file |
| Images | Uploaded automatically | Separate drag-and-drop on Special:BatchUpload |
| Pages edited after the snapshot | Skipped and listed | Kept; the import goes into history only. Not listed, so run the compare again to find them |
| In page history | Your user name, dated now | `docs>MXL Docs Sync`, dated at the snapshot time |
| Recent Changes | One entry per edit | Import log entries |
| Results file | Yes | No: the import page lists what it did |

You can undo an import like any other edit: open the page history and restore the previous revision.

---

## Hand edits and conflicts

The tool keeps a copy of every set of pages it generates. By comparing that copy with the wiki, it can tell whether someone edited a page by hand:

| The wiki page is… | What happens |
|---|---|
| Missing | Created |
| Exactly what the tool made last time | Replaced with the new docs version |
| Hand-edited, and the docs changed a *different* part | **Merged:** the hand edit stays and the docs change goes in |
| Hand-edited, and the docs changed the *same* lines | **Conflict:** left out of the update |
| Hand-edited, and the docs didn't change it | Left alone |

For example, Assur's Bane was added by hand to the Sacred Uniques list. If 2.15 changes Earth Rouser's level on that same page, the new level goes in and the Assur's Bane row stays.

### Resolving a conflict

For each conflicting page, the `conflicts` folder has two files:

- `<Page>.docs-version.wiki`: the page exactly as the docs would make it.
- `<Page>.merged-with-markers.wiki`: everything merged, with the clashing parts marked like this:

```
<<<<<<< wiki (hand edit)
+1100 Defense
=======
+1200 Defense
>>>>>>> docs
```

Open the page on the wiki, click **Edit source**, decide which version is right (or combine them) and save. You can open the `.wiki` files in Notepad to copy from them. On the next run, the page will show as "hand edits kept" or "unchanged".

## Pages it never touches

- **The seven class pages** (Amazon … Sorceress). Their skill trees come from the game files, not the docs. If a docs class page changes, the report lists it under "Docs pages to check by hand".
- **Secret Items.** It's built from the game files.
- **The Main Page.**
- **Pages written by hand**, such as Assur's Bane, and any other page this tool didn't create.
- **Docs pages that were never converted** (FAQ, OSkills, Monsters, …). Changes to these are listed so you can decide whether the wiki needs anything.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Console won't let me paste | Type `allow pasting`, press Enter, then paste again. |
| Box says Done but there's no file in Downloads | Chrome is holding the download. Look for a **Keep** / **Allow** prompt on the download icon at the top right. If a `.tmp` file appears in Downloads instead, the save didn't finish: allow downloads for the site and run the script again. |
| "Python was not found" | Install Python and tick "Add python.exe to PATH". If it's already installed, reinstall with that box ticked, or run `py sync.py` from a terminal instead. |
| Installing the add-ons fails | In a terminal in this folder, run `python -m pip install --user beautifulsoup4 lxml` to see the error. |
| "Could not find the snapshots" | The files must be named `mxl-docs-snapshot…json` and `mxl-wiki-snapshot…json`. Put them in Downloads or in a `snapshots` folder inside the tool, or pass them with `--docs` / `--wiki`. |
| "Could not read the version" | Run `python sync.py --version 2.15`, using the real version. |
| `sync.py` stops with a Python error | Usually the docs changed their HTML layout. Don't apply anything; the converter needs updating. |
| Apply panel says "not logged in" | Log in to the wiki, reload the page and paste the script again. |
| Many pages "skipped: changed on the wiki after the snapshot" | Someone was editing at the same time. Take a new wiki snapshot and run steps 3–5 again; only the skipped pages will be left. |
| "✗ failed" lines in the apply log | The results file in Downloads has the wiki's error for each one. The usual cause is a protected page or a permission problem with your account. |
| Docs site keeps showing "verify you are human" | Complete the check in a normal tab, then run the docs script in that same tab. |

## Options

Normally you just double-click `run_sync.bat`. For special cases, open a terminal in the folder (in Explorer, click the address bar, type `cmd`, press Enter) and add options. `run_sync.bat` passes options through too, e.g. `run_sync.bat --update-images`.

| Command | Use when |
|---|---|
| `python sync.py --docs FILE --wiki FILE` | You want specific snapshot files |
| `python sync.py --version 2.15` | The version can't be read from the docs front page |
| `python sync.py --update-images` | You also want to replace wiki images that differ from the docs |
| `python sync.py --recreate` | You want to bring back pages the tool made earlier that have since been deleted |
| `python sync.py --no-save` | A test run that isn't recorded in `data/history` |
| `python sync.py --out D:\somewhere` | The output folder should go somewhere else |
| `python sync.py --import-part-mb 0.5` | The wiki rejects the Special:Import files as too large |
| `python sync.py --import-user YourName` | Your own name should go on Special:Import edits |

## FAQ

<details>
<summary><b>Can I run the comparison more than once?</b></summary>

Yes, as often as you like. Nothing changes on the wiki until you apply.
</details>

<details>
<summary><b>What if I compare but never apply?</b></summary>

Nothing happens. Next time, the tool still recognises the wiki's pages from earlier runs.
</details>

<details>
<summary><b>How do I undo an update?</b></summary>

Every edit is in the page history with the summary "Sync with docs.median-xl.com (Σ x.y)". Use undo or restore on that page's history.
</details>

<details>
<summary><b>Will it ever delete pages?</b></summary>

No. Removed or renamed items only appear in the report under "No longer in the docs".
</details>

<details>
<summary><b>Why does a new version touch hundreds of pages?</b></summary>

Every item with a "Version history" box records which game version the page is current for. When the version changes, that number changes on every one of those pages. The report lists these separately as "Version number only".
</details>

<details>
<summary><b>Can I move the tool to another computer?</b></summary>

Yes. Copy the whole folder, including `data`, or clone this repo, which already includes `data`.
</details>

---

## Repository layout

```
mxl-wiki-sync/
  README.md               ← this guide
  GUIDE.html              ← the same guide as a web page, with copy buttons for the scripts
  run_sync.bat            ← double-click to compare (step 3)
  sync.py                 ← the program
  merge3.py               ← three-way merge for hand-edited pages
  requirements.txt
  browser/                ← the three Chrome console scripts
    grab_docs.js  grab_wiki.js  apply_update.js
  generator/              ← converts docs pages into wiki pages (the code that built the wiki)
  data/
    pre_import_wiki.json  ← the wiki before the first import (keeps page names stable)
    history/              ← what each run generated; don't delete
  tools/
    build_guide.py        ← rebuilds GUIDE.html from guide_template.html and the browser scripts
    guide_template.html
  output/                 ← created by each run (not in git)
```

For development: after changing a browser script or the guide template, run `python tools/build_guide.py` so `GUIDE.html` contains the current scripts. Requirements: Python 3.10+, `pip install -r requirements.txt`.

## License

The code is released under the [MIT License](LICENSE). Median XL game content, and the docs and wiki text stored in `data/`, belong to their respective owners and are not covered by this license.
