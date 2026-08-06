#!/usr/bin/env python3
"""Render the CCC paper markdown to a styled HTML page, verbatim.

Mechanical conversion only — no word of the source is altered. Styling uses the
project's existing token set from docs/EXPERIMENT_DIAGRAMS.md.
"""
import base64, io as _io, pathlib
import html as H
import re
import sys
from PIL import Image

SRC = sys.argv[1]
OUT = sys.argv[2]

CSS = """
:root{
  --paper:#F8FAFB; --ink:#1C2733; --muted:#5B6B7A; --line:#D5DDE4; --panel:#FFFFFF;
  --steel:#3D5A73; --rust:#BC4B33; --teal:#1F8A70;
  --teal-soft:#E4F2EE; --rust-soft:#F7E9E5; --wash:#F1F5F7;
}
@media (prefers-color-scheme:dark){:root{
  --paper:#12181F; --ink:#E6EBF0; --muted:#93A3B1; --line:#2A3540; --panel:#1A222B;
  --steel:#7FA0BC; --rust:#D96A50; --teal:#3FAE93;
  --teal-soft:#16302A; --rust-soft:#33201B; --wash:#171F28;
}}
:root[data-theme="dark"]{
  --paper:#12181F; --ink:#E6EBF0; --muted:#93A3B1; --line:#2A3540; --panel:#1A222B;
  --steel:#7FA0BC; --rust:#D96A50; --teal:#3FAE93;
  --teal-soft:#16302A; --rust-soft:#33201B; --wash:#171F28;
}
:root[data-theme="light"]{
  --paper:#F8FAFB; --ink:#1C2733; --muted:#5B6B7A; --line:#D5DDE4; --panel:#FFFFFF;
  --steel:#3D5A73; --rust:#BC4B33; --teal:#1F8A70;
  --teal-soft:#E4F2EE; --rust-soft:#F7E9E5; --wash:#F1F5F7;
}
*{box-sizing:border-box}
body{
  background:var(--paper); color:var(--ink); margin:0;
  font-family:"Seravek","Gill Sans Nova",Ubuntu,Calibri,"DejaVu Sans",source-sans-pro,sans-serif;
  font-size:16.5px; line-height:1.68; -webkit-font-smoothing:antialiased;
}
.wrap{display:grid; grid-template-columns:minmax(0,1fr); max-width:1180px; margin:0 auto; padding:0 1.5rem 6rem;}
@media (min-width:1040px){ .wrap{grid-template-columns:15.5rem minmax(0,1fr); gap:3.5rem;} }
nav.toc{display:none}
@media (min-width:1040px){
  nav.toc{
    display:block; position:sticky; top:0; align-self:start; max-height:100vh;
    overflow-y:auto; padding:3.4rem 0 3rem; font-size:.82rem; line-height:1.5;
  }
}
nav.toc .lbl{
  font-family:ui-monospace,"Cascadia Code",Menlo,Consolas,monospace; font-size:.66rem;
  letter-spacing:.15em; text-transform:uppercase; color:var(--steel);
  display:block; margin:0 0 .9rem;
}
nav.toc a{
  display:block; color:var(--muted); text-decoration:none;
  padding:.24rem 0 .24rem .8rem; border-left:2px solid var(--line);
}
nav.toc a:hover,nav.toc a:focus-visible{color:var(--ink); border-left-color:var(--steel);}
nav.toc a.sub{padding-left:1.7rem; font-size:.78rem;}
main{padding:3.2rem 0 0; min-width:0;}
.masthead{border-bottom:2px solid var(--ink); padding-bottom:1.6rem; margin-bottom:2.4rem;}
.eyebrow{
  font-family:ui-monospace,"Cascadia Code",Menlo,Consolas,monospace; font-size:.68rem;
  letter-spacing:.16em; text-transform:uppercase; color:var(--rust); margin:0 0 1rem;
}
h1{
  font-family:Avenir,"Avenir Next",Montserrat,Corbel,"URW Gothic",sans-serif;
  font-weight:700; font-size:clamp(1.7rem,3.4vw,2.5rem); line-height:1.16;
  letter-spacing:-.018em; margin:0 0 1rem; text-wrap:balance; max-width:24ch;
}
h2{
  font-family:Avenir,"Avenir Next",Montserrat,Corbel,sans-serif; font-weight:700;
  font-size:1.32rem; letter-spacing:-.008em; margin:3.4rem 0 1rem;
  padding-top:1.1rem; border-top:1px solid var(--line); text-wrap:balance;
}
h3{
  font-family:Avenir,"Avenir Next",Montserrat,Corbel,sans-serif; font-weight:700;
  font-size:1.06rem; margin:2.3rem 0 .7rem; color:var(--steel); text-wrap:balance;
}
p{margin:0 0 1.15rem; max-width:70ch;}
main>p:first-of-type{max-width:70ch;}
strong{font-weight:670; color:var(--ink);}
em{font-style:italic;}
a{color:var(--steel); text-underline-offset:2px;}
hr{border:0; height:1px; background:var(--line); margin:2.6rem 0;}
ul,ol{margin:0 0 1.15rem; padding-left:1.3rem; max-width:70ch;}
li{margin:0 0 .5rem;}
li::marker{color:var(--muted);}
code{
  font-family:ui-monospace,"Cascadia Code",Menlo,Consolas,monospace; font-size:.855em;
  background:var(--wash); padding:.1em .34em; border-radius:3px;
  border:1px solid var(--line); overflow-wrap:anywhere;
}
pre{
  background:var(--panel); border:1px solid var(--line); border-left:3px solid var(--steel);
  border-radius:5px; padding:1rem 1.1rem; overflow-x:auto; margin:0 0 1.4rem;
  font-size:.79rem; line-height:1.62;
}
pre code{background:none; border:0; padding:0; font-size:inherit;}
blockquote{
  margin:1.5rem 0; padding:1rem 1.25rem; background:var(--teal-soft);
  border-left:3px solid var(--teal); border-radius:0 5px 5px 0; max-width:70ch;
}
blockquote p{margin:0; max-width:none;}
blockquote p+p{margin-top:.7rem;}
.tablewrap{overflow-x:auto; margin:0 0 1.5rem; border:1px solid var(--line); border-radius:5px;}
table{border-collapse:collapse; width:100%; font-size:.86rem; font-variant-numeric:tabular-nums;}
thead th{
  background:var(--wash); text-align:left; font-weight:670; color:var(--steel);
  padding:.6rem .8rem; border-bottom:1px solid var(--line); white-space:nowrap;
}
tbody td{padding:.55rem .8rem; border-bottom:1px solid var(--line); vertical-align:top;}
tbody tr:last-child td{border-bottom:0;}
td[align="right"],th[align="right"]{text-align:right;}
.note{
  margin:0 0 2.4rem; padding:1rem 1.2rem; background:var(--rust-soft);
  border:1px solid var(--rust); border-radius:5px; font-size:.88rem;
  color:var(--ink); max-width:70ch;
}
.note b{color:var(--rust);}
img.figimg{display:block; width:100%; height:auto; border:1px solid var(--line);
  border-radius:5px; background:#fff; margin:1.8rem 0 .8rem;}
p:has(>img.figimg){max-width:none;}
p:has(>img.figimg)+p{font-size:.85rem; color:var(--muted); line-height:1.56;
  max-width:82ch; margin:0 0 2.8rem;}
p:has(>img.figimg)+p em{font-style:normal;}
p:has(>img.figimg)+p em strong{color:var(--steel); font-style:normal; letter-spacing:.01em;}
:focus-visible{outline:2px solid var(--steel); outline-offset:3px;}
@media (prefers-reduced-motion:reduce){*{animation:none!important; transition:none!important}}

@page{ size:A4; margin:19mm 17mm 20mm 17mm; }
@media print{
  /* force the light palette: printers get a white page regardless of viewer theme */
  :root, :root[data-theme="dark"], :root[data-theme="light"]{
    --paper:#FFFFFF; --ink:#111820; --muted:#4A5A68; --line:#C8D2DA; --panel:#FFFFFF;
    --steel:#2E4759; --rust:#9B3A26; --teal:#146B56;
    --teal-soft:#EEF6F4; --rust-soft:#FBF1EE; --wash:#F4F7F9;
  }
  body{ background:#fff; font-size:10.2pt; line-height:1.5; }
  .wrap{ display:block; max-width:none; padding:0; }
  nav.toc{ display:none !important; }
  main{ padding:0; }
  a{ color:var(--ink); text-decoration:none; }

  h1{ font-size:19pt; max-width:none; }
  h2{ font-size:13pt; margin:1.4em 0 .5em; padding-top:.5em; break-after:avoid; }
  h3{ font-size:11pt; margin:1.1em 0 .35em; break-after:avoid; }
  p, li{ max-width:none; orphans:3; widows:3; }
  ul, ol{ max-width:none; }

  /* keep evidence intact across page boundaries */
  .tablewrap{ break-inside:avoid; overflow:visible; }
  table{ font-size:8.6pt; }
  thead{ display:table-header-group; }
  tr{ break-inside:avoid; }
  pre{ break-inside:avoid; font-size:7.6pt; }
  blockquote{ break-inside:avoid; max-width:none; }

  /* a figure and its caption travel together */
  p:has(>img.figimg){ break-inside:avoid; break-before:auto; }
  p:has(>img.figimg)+p{ break-before:avoid; max-width:none; font-size:8.6pt; }
  img.figimg{ margin:.9em 0 .4em; max-height:21cm; object-fit:contain; }

  .masthead{ break-after:avoid; }
  hr{ display:none; }
}
"""

# ---------------------------------------------------------------- inline ---
_IMGCACHE = {}
def _datauri(rel):
    if rel in _IMGCACHE:
        return _IMGCACHE[rel]
    path = (pathlib.Path(SRC).parent / rel).resolve()
    im = Image.open(path)
    if im.width > 1600:
        im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
    q = im.convert("RGB").quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE)
    b = _io.BytesIO(); q.save(b, "PNG", optimize=True)
    _IMGCACHE[rel] = "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
    return _IMGCACHE[rel]

def inline(t):
    t = H.escape(t, quote=False)
    t = re.sub(r'`([^`]+)`', lambda m: f'<code>{m.group(1)}</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',
               lambda m: f'<img class="figimg" src="{_datauri(m.group(2))}" alt="{m.group(1)}" loading="lazy">', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
    return t

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:60]

lines = open(SRC, encoding='utf-8').read().split('\n')
out, toc = [], []
i, n = 0, len(lines)

while i < n:
    ln = lines[i]

    if ln.startswith('```'):
        i += 1
        buf = []
        while i < n and not lines[i].startswith('```'):
            buf.append(H.escape(lines[i], quote=False)); i += 1
        i += 1
        out.append('<pre><code>' + '\n'.join(buf) + '</code></pre>')
        continue

    if re.match(r'^\s*$', ln):
        i += 1; continue

    if ln.startswith('#'):
        lvl = len(ln) - len(ln.lstrip('#'))
        txt = ln[lvl:].strip()
        sid = slug(txt)
        if lvl == 1:
            out.append(f'<h1 id="{sid}">{inline(txt)}</h1>')
        else:
            out.append(f'<h{lvl} id="{sid}">{inline(txt)}</h{lvl}>')
            if lvl in (2, 3):
                toc.append((lvl, sid, txt))
        i += 1; continue

    if re.match(r'^---+\s*$', ln):
        out.append('<hr>'); i += 1; continue

    # table
    if ln.lstrip().startswith('|') and i + 1 < n and re.match(r'^\s*\|[\s:|-]+\|\s*$', lines[i+1]):
        header = [c.strip() for c in ln.strip().strip('|').split('|')]
        aligns = []
        for c in lines[i+1].strip().strip('|').split('|'):
            c = c.strip()
            aligns.append('right' if c.endswith(':') and not c.startswith(':') else
                          ('center' if c.startswith(':') and c.endswith(':') else 'left'))
        i += 2
        rows = []
        while i < n and lines[i].lstrip().startswith('|'):
            rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
        th = ''.join(f'<th align="{a}">{inline(c)}</th>' for c, a in zip(header, aligns))
        tb = ''
        for r in rows:
            tb += '<tr>' + ''.join(
                f'<td align="{aligns[k] if k < len(aligns) else "left"}">{inline(c)}</td>'
                for k, c in enumerate(r)) + '</tr>'
        out.append(f'<div class="tablewrap"><table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>')
        continue

    if ln.lstrip().startswith('>'):
        buf = []
        while i < n and lines[i].lstrip().startswith('>'):
            buf.append(lines[i].lstrip()[1:].strip()); i += 1
        paras = [p for p in '\n'.join(buf).split('\n\n') if p.strip()]
        body = ''.join(f'<p>{inline(p.replace(chr(10)," "))}</p>' for p in paras)
        out.append(f'<blockquote>{body}</blockquote>')
        continue

    m = re.match(r'^(\s*)([-*]|\d+\.)\s+', ln)
    if m:
        ordered = not m.group(2) in ('-', '*')
        tag = 'ol' if ordered else 'ul'
        items, cur = [], None
        while i < n:
            mm = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', lines[i])
            if mm:
                if cur is not None:
                    items.append(cur)
                cur = mm.group(3)
                i += 1
            elif lines[i].startswith('  ') and lines[i].strip() and cur is not None:
                cur += ' ' + lines[i].strip(); i += 1
            else:
                break
        if cur is not None:
            items.append(cur)
        out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>')
        continue

    buf = []
    while i < n and lines[i].strip() and not lines[i].startswith('#') \
            and not lines[i].lstrip().startswith('|') and not lines[i].lstrip().startswith('>') \
            and not lines[i].startswith('```') and not re.match(r'^---+\s*$', lines[i]) \
            and not re.match(r'^(\s*)([-*]|\d+\.)\s+', lines[i]):
        buf.append(lines[i].strip()); i += 1
    out.append(f'<p>{inline(" ".join(buf))}</p>')

nav = '<nav class="toc"><span class="lbl">Contents</span>' + ''.join(
    f'<a class="{"sub" if l == 3 else ""}" href="#{s}">{H.escape(t)}</a>' for l, s, t in toc) + '</nav>'

banner = ''

body = '\n'.join(out)
# lift the h1 into a masthead
body = body.replace('<h1', '<div class="masthead"><p class="eyebrow">Preprint · 2026-08</p><h1', 1)
body = re.sub(r'(</h1>)', r'\1', body, count=1)

page = f"""<title>Contextual Conclusion Capture — preprint draft</title>
<style>{CSS}</style>
<div class="wrap">
{nav}
<main>
{body}
</main>
</div>"""
# close masthead after the author + status paragraphs (first two <p> after h1)
page = page.replace('</h1>', '</h1>', 1)
parts = page.split('</h1>', 1)
head, tail = parts[0], parts[1]
p_count = 0
idx = 0
while p_count < 2:
    nxt = tail.find('</p>', idx)
    if nxt == -1:
        break
    idx = nxt + 4
    p_count += 1
tail = tail[:idx] + '</div>' + banner + tail[idx:]
page = head + '</h1>' + tail

open(OUT, 'w', encoding='utf-8').write(page)
print(f"wrote {OUT}  ({len(page)} bytes, {len(toc)} toc entries)")
