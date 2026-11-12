"""先檢查「檢查器」：用已知答案的小例子確認 check.py 的換算與解析正確（run1 後新增）"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent))
import check
def t(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg); return cond
ok = all([
  t(check.nums("約 4,674 萬韓元") == {"46740000"}, "萬單位含千分位"),
  t("42000" in check.nums("約 4.2 萬美元") and "4.2" not in check.nums("約 4.2 萬美元"), "小數＋萬不留下原 token"),
  t("3000000" in check.raw_nums("US$3 million"), "英文 million 換算"),
  t(check.nums("832 億") == {"83200000000"}, "億單位"),
])
p = check.SlideParser(); p.feed('<section id="x" data-wiki="a"><span>韓流 1.0</span><h3>1990 年代</h3></section>')
ok &= t("1.01990" not in check.nums(p.slides[0]["text"]), "HTML 文字節點不黏連")
sys.exit(0 if ok else 1)
