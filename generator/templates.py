import os
import settings
"""Wiki templates/modules generated alongside the content pages."""

TS = '<templatestyles src="MXL/styles.css" />'

T = {}

T['Template:MXL/styles.css'] = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tpl', 'MXL_styles.css'), encoding='utf-8').read()

T['Template:MXL styles'] = f'''<includeonly>{TS}</includeonly><noinclude>
Loads [[Template:MXL/styles.css]] (item colours, tooltips, tables, navboxes) on a page.
Every MXL template already loads it; place <code><nowiki>{{{{MXL styles}}}}</nowiki></code> at the top of pages that use the colour classes directly
(e.g. <code><nowiki><span class="mxl-magic">…</span></nowiki></code>).

Available colour classes: <code>mxl-basic, mxl-white, mxl-grey, mxl-magic, mxl-rare, mxl-set, mxl-unique, mxl-rune, mxl-red, mxl-orange, mxl-tan, mxl-darkgreen, mxl-holy, mxl-unholy</code>; add <code>mxl-tip</code> + a <code>title</code> for a dotted hover hint.
[[Category:MXL templates]]</noinclude>'''

T['Template:Item tooltip'] = f'''<includeonly>{TS}{{{{#if:{{{{{{id|}}}}}}|<span id="{{{{{{id}}}}}}"></span>}}}}<div class="mxl-tooltip {{{{#if:{{{{{{wide|}}}}}}|mxl-wide}}}}">{{{{#if:{{{{{{image|}}}}}}|<div class="mxl-tt-img">[[File:{{{{{{image}}}}}}|link=]]</div>}}}}{{{{#if:{{{{{{label|}}}}}}|<div class="mxl-tt-label">{{{{{{label}}}}}}</div>}}}}<div class="mxl-tt-name mxl-{{{{{{quality|unique}}}}}}">{{{{#if:{{{{{{link|}}}}}}|[[{{{{{{link}}}}}}|<span class="mxl-{{{{{{quality|unique}}}}}}">{{{{{{name|}}}}}}</span>]]|{{{{{{name|}}}}}}}}}}</div>{{{{#if:{{{{{{base|}}}}}}|<div class="mxl-tt-base">{{{{{{base}}}}}}</div>}}}}{{{{#if:{{{{{{stats|}}}}}}|<div class="mxl-tt-stats">{{{{{{stats}}}}}}</div>}}}}</div></includeonly><noinclude>
An in-game style item tooltip.

{{| class="wikitable"
! Parameter !! Meaning
|-
| <code>name</code> || Item name (coloured by <code>quality</code>)
|-
| <code>quality</code> || <code>unique</code> (default), <code>set</code>, <code>runeword</code>, <code>rare</code>, <code>magic</code>, <code>basic</code>, <code>rune</code>, <code>orange</code>…
|-
| <code>label</code> || Small caption above the name, e.g. <code>Tier 3</code> or <code>SSU</code>
|-
| <code>base</code> || Base item line under the name
|-
| <code>image</code> || File name (without <code>File:</code>)
|-
| <code>stats</code> || Tooltip body. Lines separated by <code>&lt;br /&gt;</code>; colour with <code>&lt;span class="mxl-magic"&gt;</code> etc.
|-
| <code>link</code> || Optional page the name links to
|-
| <code>wide</code> || Any value makes the box wider
|-
| <code>id</code> || Optional HTML anchor id
|}}

Example:
<pre>
{{{{Item tooltip
|name=The Xiphos |quality=unique |label=SU |base=Short Sword |image=Invssd.jpg
|stats=One-Hand Damage: <span class="mxl-magic">(60 - 114) to (102 - 136)</span><br />Required Level: 60<br /><span class="mxl-magic">(5 to 50)% Attack Speed</span>
}}}}
</pre>
{{{{Item tooltip
|name=The Xiphos |quality=unique |label=SU |base=Short Sword |image=Invssd.jpg
|stats=One-Hand Damage: <span class="mxl-magic">(60 - 114) to (102 - 136)</span><br />Required Level: 60<br /><span class="mxl-magic">(5 to 50)% Attack Speed</span>
}}}}
Wrap several tooltips in [[Template:Tooltip row]] to lay them out side by side.
[[Category:MXL templates]]</noinclude>'''

T['Template:Tooltip row'] = f'''<includeonly>{TS}<div class="mxl-tooltip-row">{{{{{{1|}}}}}}</div></includeonly><noinclude>
Lays out [[Template:Item tooltip]] boxes side by side, wrapping on narrow screens.
<pre>{{{{Tooltip row|
{{{{Item tooltip|…}}}}
{{{{Item tooltip|…}}}}
}}}}</pre>
[[Category:MXL templates]]</noinclude>'''

def _rows(fields):
    out = []
    for key, label in fields:
        if key.startswith('#'):
            out.append(f'<tr><th colspan="2" class="mxl-infobox-section">{label}</th></tr>')
            continue
        out.append(f'{{{{#if:{{{{{{{key}|}}}}}}|<tr><th>{label}</th><td>{{{{{{{key}}}}}}}</td></tr>}}}}')
    return ''.join(out)

def infobox(name, title_cls, fields, doc, cats):
    body = f'''<includeonly>{TS}<div class="mxl-infobox">
<div class="mxl-infobox-title mxl-{title_cls}">{{{{{{name|{{{{PAGENAME}}}}}}}}}}</div>{{{{#if:{{{{{{image|}}}}}}|<div class="mxl-infobox-image">[[File:{{{{{{image}}}}}}|link=]]</div>}}}}
<table>{_rows(fields)}</table>
</div>{cats}</includeonly><noinclude>
{doc}
[[Category:MXL templates]][[Category:Infobox templates]]</noinclude>'''
    T[name] = body

infobox('Template:Infobox unique', '{{{quality|unique}}}', [
    ('type', 'Type'), ('base', 'Base item'), ('category', 'Item group'), ('class', 'Class'),
    ('variation', 'Variation'), ('tiers', 'Tiers'), ('reqlevel', 'Required level'), ('ilvl', 'Item level'),
    ('drops', 'Drops'),
], 'Infobox for unique items. Parameters: <code>name, image, quality, type, base, category, class, variation, tiers, reqlevel, ilvl, drops</code>.', '')

infobox('Template:Infobox base item', 'white', [
    ('category', 'Item group'), ('class', 'Class'), ('tiers', 'Tiers'), ('reqlevel', 'Required level'),
    ('qlvl', 'Quality level'), ('speed', 'Attack speed mod.'), ('sockets', 'Max sockets'), ('modifier', 'Attack modifier'),
], 'Infobox for base item types. Parameters: <code>name, image, category, class, tiers, reqlevel, qlvl, speed, sockets, modifier</code>.', '')

infobox('Template:Infobox runeword', 'unique', [
    ('runes', 'Runes'), ('recipe', 'Rune order'), ('sockets', 'Sockets'), ('level', 'Required level'), ('bases', 'Item types'),
], 'Infobox for runewords. Parameters: <code>name, image, runes, recipe, sockets, level, bases</code>.', '')

infobox('Template:Infobox set', 'set', [
    ('type', 'Set type'), ('class', 'Class'), ('pieces', 'Pieces'), ('items', 'Set items'), ('reqlevel', 'Required level'),
], 'Infobox for item sets. Parameters: <code>name, image, type, class, pieces, items, reqlevel</code>.', '')

infobox('Template:Infobox dungeon', 'unique', [
    ('reqlevel', 'Required level'), ('difficulty', 'Difficulty'), ('lockdown', 'Lockdown'), ('location', 'Location'),
    ('reward', 'Reward'),
], 'Infobox for endgame dungeons. Parameters: <code>name, image, reqlevel, difficulty, lockdown, location, reward</code>.', '')

T['Template:Navbox'] = f'''<includeonly>{TS}<div class="mxl-navbox mw-collapsible {{{{#ifeq:{{{{{{state|}}}}}}|collapsed|mw-collapsed}}}}">
<div class="mxl-navbox-title">{{{{{{title}}}}}}</div>
<div class="mw-collapsible-content">{{{{#if:{{{{{{list1|}}}}}}|<div class="mxl-navbox-row"><div class="mxl-navbox-group">{{{{{{group1|}}}}}}</div><div class="mxl-navbox-list">
{{{{{{list1}}}}}}
</div></div>}}}}{{{{#if:{{{{{{list2|}}}}}}|<div class="mxl-navbox-row"><div class="mxl-navbox-group">{{{{{{group2|}}}}}}</div><div class="mxl-navbox-list">
{{{{{{list2}}}}}}
</div></div>}}}}{{{{#if:{{{{{{list3|}}}}}}|<div class="mxl-navbox-row"><div class="mxl-navbox-group">{{{{{{group3|}}}}}}</div><div class="mxl-navbox-list">
{{{{{{list3}}}}}}
</div></div>}}}}{{{{#if:{{{{{{list4|}}}}}}|<div class="mxl-navbox-row"><div class="mxl-navbox-group">{{{{{{group4|}}}}}}</div><div class="mxl-navbox-list">
{{{{{{list4}}}}}}
</div></div>}}}}{{{{#if:{{{{{{list5|}}}}}}|<div class="mxl-navbox-row"><div class="mxl-navbox-group">{{{{{{group5|}}}}}}</div><div class="mxl-navbox-list">
{{{{{{list5}}}}}}
</div></div>}}}}{{{{#if:{{{{{{list6|}}}}}}|<div class="mxl-navbox-row"><div class="mxl-navbox-group">{{{{{{group6|}}}}}}</div><div class="mxl-navbox-list">
{{{{{{list6}}}}}}
</div></div>}}}}{{{{#if:{{{{{{list7|}}}}}}|<div class="mxl-navbox-row"><div class="mxl-navbox-group">{{{{{{group7|}}}}}}</div><div class="mxl-navbox-list">
{{{{{{list7}}}}}}
</div></div>}}}}{{{{#if:{{{{{{list8|}}}}}}|<div class="mxl-navbox-row"><div class="mxl-navbox-group">{{{{{{group8|}}}}}}</div><div class="mxl-navbox-list">
{{{{{{list8}}}}}}
</div></div>}}}}</div>
</div></includeonly><noinclude>
Collapsible navigation box. Parameters: <code>title</code>, <code>state=collapsed</code>, and up to 8 pairs of <code>groupN</code> / <code>listN</code> (lists are bullet lists, shown inline).
[[Category:MXL templates]]</noinclude>'''

T['Template:Docs source'] = f'''<includeonly>{TS}<div class="mxl-source">Data source: [https://docs.median-xl.com{{{{{{1|/}}}}}} docs.median-xl.com{{{{{{1|/}}}}}}] · Median XL Σ {{{{{{version|{settings.VERSION}}}}}}}. Values shown are as listed in the official game guide; if you notice a difference in-game, please update this page.</div></includeonly><noinclude>
Footer crediting the official game guide. Usage: <code><nowiki>{{{{Docs source|/doc/items/sets}}}}</nowiki></code>.
[[Category:MXL templates]]</noinclude>'''

T['Template:Main'] = '''<includeonly><div role="note" class="hatnote" style="font-style:italic;padding-left:1.6em;margin-bottom:0.5em">Main article: [[{{{1}}}{{#if:{{{2|}}}|{{!}}{{{2}}}}}]]</div></includeonly><noinclude>Hatnote linking to a main article: <code><nowiki>{{Main|Page|label}}</nowiki></code>.
[[Category:MXL templates]]</noinclude>'''

T['Module:Affix level'] = '''-- Affix level calculator, ported from the calculator on docs.median-xl.com/doc/wiki/affixes
local p = {}

local function num(v, default)
	v = tonumber(v)
	if v == nil then return default end
	return math.floor(v)
end

-- affix level for rare / crafted items
function p.alvl(ilvl, qlvl)
	local alvl = math.min(ilvl, 99)
	alvl = math.max(alvl, qlvl)
	local half = math.floor(qlvl / 2)
	if alvl < 99 - half then
		alvl = alvl - half
	else
		alvl = 2 * alvl - 99
	end
	return math.min(alvl, 99)
end

-- {{#invoke:Affix level|rare|ilvl|qlvl}}
function p.rare(frame)
	local a = frame.args
	local ilvl = math.max(num(a[1], 1), 1)
	local qlvl = math.min(math.max(num(a[2], 0), 0), 90)
	return p.alvl(ilvl, qlvl)
end

-- {{#invoke:Affix level|craft|ilvl|qlvl|jewel=yes}}
function p.craft(frame)
	local a = frame.args
	local ilvl = math.max(num(a[1], 1), 1)
	local qlvl
	if a.jewel and a.jewel ~= '' then
		ilvl = math.max(math.floor(ilvl * 95 / 100), 1)
		qlvl = 1
	else
		qlvl = math.min(math.max(num(a[2], 71), 71), 90)
	end
	return p.alvl(ilvl, qlvl)
end

-- crafted output item level (capped at 99)
function p.craftilvl(frame)
	local a = frame.args
	local ilvl = math.max(num(a[1], 1), 1)
	if a.jewel and a.jewel ~= '' then
		ilvl = math.max(math.floor(ilvl * 95 / 100), 1)
	end
	return math.min(ilvl, 99)
end

-- reference table: affix level by item level (rows) and quality level (columns)
function p.table(frame)
	local a = frame.args
	local qlvls = {}
	for q in mw.text.gsplit(a.qlvls or '1,20,40,60,71,75,80,85,90', ',') do
		table.insert(qlvls, tonumber(mw.text.trim(q)))
	end
	local ilvls = {}
	for i in mw.text.gsplit(a.ilvls or '1,10,20,30,40,50,60,70,75,80,85,90,95,99', ',') do
		table.insert(ilvls, tonumber(mw.text.trim(i)))
	end
	local out = {'{| class="mxl-table sortable"', '! Item level \\\\ Quality level'}
	for _, q in ipairs(qlvls) do table.insert(out, '! ' .. q) end
	for _, i in ipairs(ilvls) do
		table.insert(out, '|-')
		table.insert(out, '! ' .. i)
		for _, q in ipairs(qlvls) do
			table.insert(out, '| ' .. p.alvl(i, q))
		end
	end
	table.insert(out, '|}')
	return table.concat(out, '\\n')
end

return p
'''

T['Template:Affix level'] = '''<includeonly>{{#ifeq:{{{type|rare}}}|craft|{{#invoke:Affix level|craft|{{{1|1}}}|{{{2|71}}}|jewel={{{jewel|}}}}}|{{#invoke:Affix level|rare|{{{1|1}}}|{{{2|0}}}}}}}</includeonly><noinclude>
Returns the affix level of an item, using the same formula as the calculator on the official game guide.
* Rare item: <code><nowiki>{{Affix level|item level|quality level}}</nowiki></code> → e.g. <code><nowiki>{{Affix level|85|80}}</nowiki></code> = {{Affix level|85|80}}
* Crafted item: <code><nowiki>{{Affix level|item level|quality level|type=craft}}</nowiki></code> (quality level is clamped to 71–90)
* Crafted jewel: <code><nowiki>{{Affix level|item level|type=craft|jewel=yes}}</nowiki></code>
[[Category:MXL templates]]</noinclude>'''

infobox('Template:Infobox class', 'unique', [
    ('#s', 'Base stats'), ('str', 'Strength'), ('dex', 'Dexterity'), ('vit', 'Vitality'), ('ene', 'Energy'),
    ('perlevel', 'Per level'), ('vitality', 'Per vitality'), ('energy', 'Per energy'),
    ('#e', 'Equipment'), ('weapons', 'Weapons'), ('armour', 'Armour'),
], 'Infobox for character classes. Parameters: <code>name, image, str, dex, vit, ene, perlevel, vitality, energy, weapons, armour</code>.', '')
