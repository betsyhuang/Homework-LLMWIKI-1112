# K-pop 入門 LLM Wiki — Schema（給 LLM 的維護規則）

本 Wiki 採 Karpathy「LLM Wiki」模式：LLM 不是每次都從原始資料重新檢索，而是把資料「編譯」成一份持續維護、互相連結的 Markdown Wiki，之後所有產出（簡報）都只從 Wiki 取材。

## 三層結構
- `raw/`：原始來源摘錄（S1–S6）。**唯讀**，只新增不修改內容；每篇有 frontmatter（id、url、fetch_status、confidence）。
- `discussions/`：每次 ingest 前的「先討論」紀錄（重點、疑問、決策）。
- `wiki/`：LLM 撰寫與維護的頁面。`index.md` 為目錄，`log.md` 為操作紀錄（append-only）。

## 寫作規則
1. 先討論、後生成：ingest 一篇來源前，先在 `discussions/` 寫下「這篇最重要的 3–5 點、跟現有頁面的關係、有無衝突」，與使用者確認方向後才改 wiki。
2. 每一條事實句尾必須標來源，如 `[S3]`；多來源寫 `[S1][S2]`。沒有來源的句子不准寫。
3. 來源標 `[summary]`（模型摘要段落，非逐字）的事實，只能在句尾加 `(待查證)`，且不得進簡報。
4. 來源互相矛盾時，不擇一，寫進 `open-questions.md`。
5. 頁面間用 `[[頁面檔名]]` 連結；新增頁面必須同步更新 `index.md`。
6. 每次動作在 `log.md` 追加一行：`## [日期] ingest|query|lint | 說明`。

## 簡報產生規則
- 簡報每一頁 `<section>` 必須有 `data-wiki="頁面檔名"`，指出內容出自哪一頁 Wiki。
- 簡報上出現的每一個數字（年份、數量、百分比）必須能在該 Wiki 頁中找到。
- 由 `tools/check.py` 自動檢查，不通過就回到對應節點重做。
