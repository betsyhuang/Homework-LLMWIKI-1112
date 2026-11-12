#!/usr/bin/env python3
"""把 wiki/、raw/、discussions/ 編成一頁可瀏覽的 HTML（wiki.html）。"""
import re, pathlib, markdown, html
ROOT = pathlib.Path(__file__).resolve().parent.parent

ORDER = ["index", "kpop-overview", "timeline", "agencies-trainees", "idol-terms-fandom",
         "music-shows", "global-milestones", "open-questions", "log"]

def strip_fm(t):
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    return (m.group(1), t[m.end():]) if m else ("", t)

def title_of(fm, body, fallback):
    m = re.search(r"^title:\s*(.+)$", fm, re.M)
    if m: return m.group(1).strip()
    m = re.search(r"^#\s+(.+)$", body, re.M)
    return m.group(1).strip() if m else fallback

def render(body):
    body = re.sub(r"\[\[([^\]]+)\]\]", lambda m: f'<a class="wl" href="#{m.group(1)}">{m.group(1)}</a>', body)
    out = markdown.markdown(body, extensions=["tables"])
    out = re.sub(r"\[(S\d)\]", r'<a class="cite" href="#\1">\1</a>', out)
    out = out.replace("（待查證）", '<span class="pend">待查證</span>').replace("(待查證)", '<span class="pend">待查證</span>')
    return out

pages = []
for name in ORDER:
    fm, body = strip_fm((ROOT / "wiki" / f"{name}.md").read_text(encoding="utf-8"))
    pages.append(("wiki", name, title_of(fm, body, name), fm, render(body)))
for p in sorted((ROOT / "raw").glob("*.md")):
    fm, body = strip_fm(p.read_text(encoding="utf-8"))
    sid = p.stem.split("-")[0] if p.stem.startswith("S") else "rejected"
    pages.append(("raw", sid, title_of(fm, body, p.stem), fm, render(body)))
for p in sorted((ROOT / "discussions").glob("*.md")):
    fm, body = strip_fm(p.read_text(encoding="utf-8"))
    pages.append(("disc", p.stem, title_of(fm, body, p.stem), fm, render(body)))
fm, body = strip_fm((ROOT / "CLAUDE.md").read_text(encoding="utf-8"))
pages.append(("disc", "schema", "Schema（CLAUDE.md）", "", render(body)))

def navgroup(kind, label):
    items = "".join(f'<a href="#{n}" data-k="{n}">{html.escape(t)}</a>' for k, n, t, _, _ in pages if k == kind)
    return f'<div class="ng"><span class="nl">{label}</span>{items}</div>'

sections = []
for k, n, t, fm, body in pages:
    meta = ""
    if fm:
        meta = f'<pre class="fm">{html.escape(fm)}</pre>'
    path = {"wiki": f"wiki/{n}.md", "raw": "raw/", "disc": "discussions/"}[k]
    sections.append(f'<article id="{n}" data-kind="{k}" hidden><div class="path">{path}</div>{meta}{body}</article>')

tpl = (ROOT / "tools" / "wiki_template.html").read_text(encoding="utf-8")
out = tpl.replace("{{NAV}}", navgroup("wiki", "Wiki 頁面") + navgroup("raw", "原始來源 raw/") + navgroup("disc", "討論與規則")).replace("{{PAGES}}", "\n".join(sections))
(ROOT / "site").mkdir(exist_ok=True)
(ROOT / "site" / "wiki.html").write_text(out, encoding="utf-8")
print("pages:", len(pages))
