#!/usr/bin/env python3
"""K-pop LLM Wiki 檢查器：Wiki lint (W*) + 簡報追溯檢查 (P*).
用法：python3 tools/check.py [wiki|slides|all]
回傳碼 0 = 全部通過；1 = 有錯誤（loop 需回到對應節點重做）
"""
import re, sys, pathlib, json
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, WIKI, SLIDES = ROOT / "raw", ROOT / "wiki", ROOT / "slides" / "slides.html"
SKIP_PAGES = {"index", "log"}
CITE = re.compile(r"\[(S\d+)\]")
LINK = re.compile(r"\[\[([^\]]+)\]\]")
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
# 不准進簡報的詞（來自 open-questions：待查證 / 無來源）
BLOCK_TERMS = ["ARMY", "營收", "應援棒", "應援口號", "忙內", "Six Rules", "葛萊美表演"]

def nums(text):
    out = set()
    unit_tok = {m.group(1).replace(",", "") for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*[萬億]", text)}
    for m in NUM.findall(text):
        if m.replace(",", "") in unit_tok:
            continue
        n = m.replace(",", "")
        out.add(n)
        if "." in n:
            out.add(n.replace(".", ""))          # 46.74 -> 4674 (KR₩46.74m -> 4,674 萬)
    # 中文「N 萬」→ N*10000，「N 億」→ N*1e8
    for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*萬", text):
        out.add(str(int(round(float(m.group(1).replace(",", "")) * 10000))))
    for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*億", text):
        out.add(str(int(round(float(m.group(1).replace(",", "")) * 1e8))))
    return out

def raw_nums(text):
    out = nums(text)
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(million|m\b|billion|M\b)", text):
        v = float(m.group(1)) * (1e9 if m.group(2) == "billion" else 1e6)
        out.add(str(int(v)))
    return out

def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else ""

def load_raw():
    srcs = {}
    for p in RAW.glob("S*.md"):
        sid = p.name.split("-")[0]
        srcs[sid] = p.read_text(encoding="utf-8")
    return srcs

def check_wiki():
    errs, warns = [], []
    srcs = load_raw()
    pages = {p.stem: p.read_text(encoding="utf-8") for p in WIKI.glob("*.md")}
    index = pages.get("index", "")
    for name, text in pages.items():
        if name in SKIP_PAGES:
            continue
        fm = frontmatter(text)
        declared = set(re.findall(r"S\d+", fm))
        # W4 index 收錄
        if f"[[{name}]]" not in index:
            errs.append(("W4", name, "頁面未列在 index.md"))
        body = text[len(fm) + 8:]
        for ln, line in enumerate(body.splitlines(), 1):
            s = line.strip()
            # W3 連結
            for l in LINK.findall(s):
                if l not in pages:
                    errs.append(("W3", name, f"L{ln} 斷掉的連結 [[{l}]]"))
            is_fact = (s.startswith("- ") or (s.startswith("|") and not set(s) <= set("|-: ") and not s.startswith("| #") and not s.startswith("| 術語") and not s.startswith("| 星期")))
            if not is_fact or s.startswith("- 找") or "相關頁" in s:
                continue
            cites = CITE.findall(s)
            # W1 每條事實要有來源
            if not cites:
                errs.append(("W1", name, f"L{ln} 沒有來源標註：{s[:40]}"))
                continue
            # W2 來源存在且列在 frontmatter
            for c in cites:
                if c not in srcs:
                    errs.append(("W2", name, f"L{ln} 引用不存在的來源 {c}"))
                elif c not in declared:
                    errs.append(("W2", name, f"L{ln} 引用 {c} 但 frontmatter sources 沒列"))
            # W5 數字要能在被引用的原始來源找到
            if cites and name != "open-questions":
                pool = set()
                for c in cites:
                    pool |= raw_nums(srcs.get(c, ""))
                for n in nums(re.sub(r"\[S\d+\]", "", s)):
                    if n not in pool and len(n) >= 2:
                        errs.append(("W5", name, f"L{ln} 數字 {n} 在 {'/'.join(cites)} 找不到：{s[:50]}"))
            # W6 [summary] 來源事實必須標待查證
            for c in cites:
                raw_lines = [r for r in srcs.get(c, "").splitlines() if r.startswith("- [summary]")]
                for r in raw_lines:
                    key = [n for n in nums(r) if len(n) >= 3 and not re.fullmatch(r"(19|20)\d\d", n)]
                    if key and any(k in nums(s) for k in key) and "待查證" not in s:
                        warns.append(("W6", name, f"L{ln} 可能來自摘要段但未標待查證：{s[:40]}"))
    return errs, warns

class SlideParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.slides = []; self.cur = None; self.skip = 0
    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "section":
            self.cur = {"id": a.get("id"), "wiki": (a.get("data-wiki") or "").split(), "text": "", "cls": a.get("class", "")}
        if self.cur is not None and tag == "div" and "src" in (a.get("class") or "").split():
            self.skip += 1; self.cur["in_src"] = True
        if tag in ("style", "script"):
            self.skip += 1
    def handle_endtag(self, tag):
        if tag == "section" and self.cur:
            self.slides.append(self.cur); self.cur = None; self.skip = 0
        if tag in ("style", "script"):
            self.skip = max(0, self.skip - 1)
    def handle_data(self, d):
        if self.cur is not None and self.cur.get("in_src"):
            self.cur.setdefault("foot", "")
            self.cur["foot"] += d
        if self.cur is not None and not self.skip:
            self.cur["text"] += " " + d

def check_slides():
    errs, warns = [], []
    pages = {p.stem: p.read_text(encoding="utf-8") for p in WIKI.glob("*.md")}
    sp = SlideParser(); sp.feed(SLIDES.read_text(encoding="utf-8"))
    pending = [l for t in pages.values() for l in t.splitlines() if "待查證" in l and l.startswith("-")]
    pending_nums = set()
    for l in pending:
        pending_nums |= {n for n in nums(l) if len(n) >= 3}
    for s in sp.slides:
        sid = s["id"]
        # P1 每頁要指向存在的 wiki 頁
        if not s["wiki"]:
            errs.append(("P1", sid, "沒有 data-wiki")); continue
        missing = [w for w in s["wiki"] if w not in pages]
        if missing:
            errs.append(("P1", sid, f"data-wiki 指向不存在的頁 {missing}")); continue
        # P6 頁尾標示的 wiki 檔 == data-wiki
        foot = set(re.findall(r"([a-z-]+)\.md", s.get("foot", "")))
        if foot - set(s["wiki"]):
            errs.append(("P6", sid, f"頁尾標示 {sorted(foot - set(s['wiki']))} 但 data-wiki 沒列"))
        pool_text = "\n".join(pages[w] for w in s["wiki"])
        pool = nums(pool_text)
        # P2 簡報上的每個數字都要在 wiki 頁找得到
        for n in sorted(nums(s["text"])):
            if n not in pool and len(n) >= 2:
                errs.append(("P2", sid, f"數字 {n} 不在 {s['wiki']}"))
        # P3 不得使用待查證內容
        for t in BLOCK_TERMS:
            if t in s["text"]:
                errs.append(("P3", sid, f"使用了待查證/無來源詞「{t}」"))
        for n in nums(s["text"]):
            if n in pending_nums and n not in {x for l in pages.values() for x in nums("\n".join(k for k in l.splitlines() if "待查證" not in k))}:
                errs.append(("P3", sid, f"數字 {n} 只出現在待查證句"))
    # P4 教學結構
    texts = " ".join(s["text"] for s in sp.slides)
    for need in ["學習目標", "小測驗", "重點回顧"]:
        if need not in texts:
            errs.append(("P4", "deck", f"缺少教學結構：{need}"))
    covered = {w for s in sp.slides for w in s["wiki"]}
    for p in pages:
        if p not in SKIP_PAGES | {"open-questions"} and p not in covered:
            warns.append(("P5", "deck", f"wiki/{p} 沒有任何簡報頁使用"))
    return errs, warns, len(sp.slides)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    allerr, allwarn, report = [], [], {}
    if mode in ("wiki", "all"):
        e, w = check_wiki(); allerr += e; allwarn += w
        report["wiki"] = {"errors": len(e), "warnings": len(w)}
    if mode in ("slides", "all"):
        e, w, n = check_slides(); allerr += e; allwarn += w
        report["slides"] = {"slides": n, "errors": len(e), "warnings": len(w)}
    for code, where, msg in allerr:
        print(f"ERROR {code} [{where}] {msg}")
    for code, where, msg in allwarn:
        print(f"WARN  {code} [{where}] {msg}")
    print("SUMMARY", json.dumps(report, ensure_ascii=False))
    sys.exit(1 if allerr else 0)

if __name__ == "__main__":
    main()
