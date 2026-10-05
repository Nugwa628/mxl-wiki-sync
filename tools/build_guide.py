import html, datetime, os
P=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
t=open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "guide_template.html"),encoding='utf-8').read()
for name in ['grab_docs','grab_wiki','apply_update']:
    js=open(f'{P}/browser/{name}.js',encoding='utf-8').read()
    box=(f'<div class="script"><div class="bar"><span class="fn">{name}.js</span><span class="sz">{len(js)/1024:.1f} KB · also in the browser folder</span>'
         f'<button type="button">Copy script</button></div><details><summary>Show the script</summary>'
         f'<textarea readonly spellcheck="false">{html.escape(js)}</textarea></details></div>')
    assert f'<!--SCRIPT:{name}-->' in t
    t=t.replace(f'<!--SCRIPT:{name}-->',box)
t=t.replace('<!--DATE-->',datetime.date.today().isoformat())
open(f'{P}/GUIDE.html','w',encoding='utf-8').write(t)
print(len(t))
