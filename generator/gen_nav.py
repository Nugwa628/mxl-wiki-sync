"""Navigation: site navbox, categories, main page proposal, extra redirects."""
from common import *
import json
import settings

def L(*items):
    return '\n'.join(f'* [[{i}]]' if '|' not in i else f'* [[{i}]]' for i in items)

NAVBOX = '''{{Navbox
|title=[[Main Page|Median XL Wiki]] · Σ ''' + settings.VERSION + '''
|state={{{state|}}}
|group1=Classes
|list1=''' + L('Amazon', 'Assassin', 'Barbarian', 'Druid', 'Necromancer', 'Paladin', 'Sorceress', 'Mercenaries') + '''
|group2=Items
|list2=''' + L('Base Items', 'Tiered Uniques', 'Sacred Uniques', 'Sets', 'Runewords', 'Gems and Runes', 'Relics',
               'Charms', 'Cycles', 'Unique Mystic Orbs', 'Mystic Orbs', 'Angelic Items', 'Secret Items', 'Armor Looks') + '''
|group3=Crafting
|list3=''' + L('Cube Recipes', 'Item Affixes', 'Shrine Bonuses', 'Trophy Bonuses', 'Soulforge') + '''
|group4=Endgame
|list4=''' + L('Challenges', 'Dungeons', 'Nephalem Rifts') + '''
|group5=Mechanics
|list5=''' + L('Defense and Block', 'Experience', 'Spell Focus', 'Minion Mechanics', 'OSkills', 'Procs', 'Difficulty Levels') + '''
|group6=Reference
|list6=''' + L('Patch Notes', 'Acronyms & Abbreviations', 'F-A-Q', 'Loot Filter', 'D2GL Wrapper') + '''
}}'''

def build_templates(T):
    T['Template:Navbox Median XL'] = '<includeonly>' + NAVBOX + '</includeonly><noinclude>Site-wide navigation box, placed at the bottom of every page. Use <code><nowiki>{{Navbox Median XL|state=collapsed}}</nowiki></code> to collapse it.\n[[Category:MXL templates]]</noinclude>'

CAT_DESC = {
    'Items': "All item reference pages. Start with [[Base Items]], [[Tiered Uniques]], [[Sacred Uniques]], [[Sets]] and [[Runewords]].",
    'Unique items': "Every [[Tiered Uniques|tiered]] and [[Sacred Uniques|sacred]] unique item has its own page here, with full stats for every tier or variation.",
    'Tiered Uniques': "Pages for each tiered unique. See [[Tiered Uniques]] for a sortable overview.",
    'Sacred Uniques': "Pages for each sacred unique. See [[Sacred Uniques]] for a sortable overview.",
    'Base items': "Pages for each base item type with all four tiers plus the sacred version. See [[Base Items]] for a sortable overview.",
    'Runewords': "Pages for each runeword. See [[Runewords]] for full tables by item type.",
    'Sets': "Pages for each item set. See [[Sets]] for an overview.",
    'Quests': "Challenges, dungeons and rifts.",
    'Endgame': "Endgame content: [[Challenges]], [[Dungeons]] and [[Nephalem Rifts]].",
    'Dungeons': "See [[Dungeons]].",
    'Rifts': "See [[Nephalem Rifts]].",
    'Game mechanics': "How the game's systems work.",
    'Crafting': "Cube recipes, affixes, shrines and other crafting reference.",
    'Classes': "The seven playable classes.",
    'Characters': "Player characters and mercenaries.",
    'Mercenaries': "See [[Mercenaries]].",
    'Patch notes': "Version logs. See [[Patch Notes]].",
    'Charms': "Charms and charm-related items.",
    'Mystic Orbs': "Mystic orbs. See [[Mystic Orbs]] and [[Unique Mystic Orbs]].",
    'Socketables': "Gems, runes and jewels. See [[Gems and Runes]].",
    'Relics': "See [[Relics]].",
    'MXL templates': "Templates used by the Median XL item and reference pages. Shared styles live in [[Template:MXL/styles.css]].",
    'Infobox templates': "Infobox templates.",
}

def build_categories(item_groups, set_groups):
    out = {}
    for k, v in CAT_DESC.items():
        parent = {'Unique items': 'Items', 'Tiered Uniques': 'Unique items', 'Sacred Uniques': 'Unique items',
                  'Base items': 'Items', 'Runewords': 'Items', 'Sets': 'Items', 'Dungeons': 'Endgame', 'Rifts': 'Endgame',
                  'Endgame': 'Quests', 'Classes': 'Characters', 'Mercenaries': 'Characters', 'Charms': 'Items',
                  'Mystic Orbs': 'Items', 'Socketables': 'Items', 'Relics': 'Items', 'Infobox templates': 'MXL templates'}.get(k)
        out['Category:' + k] = v + (f'\n[[Category:{parent}]]' if parent else '')
    for g in item_groups:
        out['Category:' + g] = (f"Items in the '''{g.lower()}''' item group: the base item types, plus the tiered and sacred uniques built on them.\n"
                                f"See also [[Base Items]], [[Tiered Uniques]] and [[Sacred Uniques]].\n[[Category:Item groups]]")
    out['Category:Item groups'] = "Item groups (weapon and armour types) used to organise base items and uniques.\n[[Category:Items]]"
    for g in set_groups:
        out['Category:' + g] = f"{g}. See [[Sets#{g}|{g} on the Sets page]].\n[[Category:Sets]]"
    return out

MAIN = '''__NOTOC__
{{MXL styles}}
<div class="mainpage-header">
=<span class="h1-2">The Median XL Wiki</span>=
This is the official [[Median XL]] wiki, maintained by the community and hosted by [https://www.Median-xl.com Median-XL.com]. It now includes the full contents of the official game guide at [https://docs.median-xl.com/ docs.median-xl.com] (Σ 2.14) – every unique, set, runeword and base item has its own searchable page, with sortable lists and per-item version history.

Join us on our [https://discord.gg/medianxl Discord server].
</div>

== Classes ==
<div class="mxl-scroll">
{| class="mxl-table mxl-classtable"
|-
| [[File:Amazon.gif|x80px|link=Amazon]]<br /><b>[[Amazon]]</b>
| [[File:Assassin.gif|x80px|link=Assassin]]<br /><b>[[Assassin]]</b>
| [[File:Barbarian.gif|x80px|link=Barbarian]]<br /><b>[[Barbarian]]</b>
| [[File:Druid.gif|x80px|link=Druid]]<br /><b>[[Druid]]</b>
| [[File:Necromancer.gif|x80px|link=Necromancer]]<br /><b>[[Necromancer]]</b>
| [[File:Paladin.gif|x80px|link=Paladin]]<br /><b>[[Paladin]]</b>
| [[File:Sorceress.gif|x80px|link=Sorceress]]<br /><b>[[Sorceress]]</b>
|-
| <small>Bow<br />Javelin<br />Spear<br />Storm<br />Blood<br />Divine</small>
| <small>Throwing<br />Claw<br />Naginata<br />Traps<br />Psionic<br />Ninja</small>
| <small>Earthshaker<br />Windcarver<br />Elementalist<br />Warmonger<br />Shaman<br />Nomad</small>
| <small>Werebear<br />Werewolf<br />Wereowl<br />Hunter<br />Seer<br />Nature</small>
| <small>Summon<br />Melee<br />Crossbow<br />Malice<br />Totem<br />Deathspeaker</small>
| <small>Templar<br />Incarnation<br />Nephalem<br />Ritualist<br />Warlock<br />Aspects</small>
| <small>Fire<br />Lightning<br />Cold<br />Poison<br />Melee<br />Arcane</small>
|}
</div>
Every class page lists all skill trees with requirements and descriptions taken from the game files. See also [[Mercenaries]].

<div class="mxl-cards">
<div class="mxl-card"><div class="mxl-card-title">Items</div>
* [[Base Items]] – all item types and tiers
* [[Tiered Uniques]] · [[Sacred Uniques]]
* [[Sets]] · [[Runewords]]
* [[Gems and Runes]] · [[Relics]] · [[Charms]]
* [[Unique Mystic Orbs]] · [[Mystic Orbs]] · [[Cycles]]
* [[Angelic Items]] · [[Secret Items]]
</div>
<div class="mxl-card"><div class="mxl-card-title">Crafting</div>
* [[Cube Recipes]]
* [[Item Affixes]] – with affix level calculator
* [[Shrine Bonuses]] · [[Trophy Bonuses]]
* [[Soulforge]]
</div>
<div class="mxl-card"><div class="mxl-card-title">Endgame</div>
* [[Challenges]]
* [[Dungeons]] – bosses and charm rewards
* [[Nephalem Rifts]]
* [[Diablo 2 Quests]]
</div>
<div class="mxl-card"><div class="mxl-card-title">Mechanics</div>
* [[Defense and Block]] · [[Experience]]
* [[Spell Focus]] · [[Minion Mechanics]]
* [[OSkills]] · [[Procs]] · [[Difficulty Levels]]
</div>
<div class="mxl-card"><div class="mxl-card-title">Guides & reference</div>
* [[Patch Notes]] (Σ 2.14)
* [[F-A-Q]] · [[Acronyms & Abbreviations]]
* [[D2GL Wrapper]] · [[Loot Filter]]
* [[Maps]] · [[Armor Looks]] · [[Bestiary]]
</div>
</div>

== Find an item ==
<inputbox>
type=search
width=40
placeholder=Search for an item, skill or area…
buttonlabel=Search
</inputbox>
Every item page is also listed in categories such as [[:Category:Sacred Uniques]], [[:Category:Runewords]] or [[:Category:One-Handed Swords]].
'''

EXTRA_REDIRECTS = {
    'Uniques': 'Tiered Uniques', 'Unique Items': 'Tiered Uniques', 'Tiered uniques': 'Tiered Uniques', 'TU': 'Tiered Uniques',
    'Sacred uniques': 'Sacred Uniques', 'SU': 'Sacred Uniques', 'SSU': 'Sacred Uniques', 'SSSU': 'Sacred Uniques',
    'Set items': 'Sets', 'Set Items': 'Sets', 'Item sets': 'Sets', 'Runeword': 'Runewords', 'RW': 'Runewords',
    'Base items': 'Base Items', 'Item tiers': 'Base Items', 'Bases': 'Base Items', 'Superior items': 'Base Items',
    'Attack Modifiers': 'Base Items', 'Mega Impact': 'Base Items', 'Thunderfury': 'Base Items', 'Amazing Grace': 'Base Items',
    'Area Effect Attack': 'Base Items', 'UMOs': 'Unique Mystic Orbs', 'Patch': 'Patch Notes',
}
