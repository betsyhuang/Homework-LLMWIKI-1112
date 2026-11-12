# Log（append-only）

## [2026-11-12] discuss | 主題確定：K-pop 韓團入門（D1 第一輪）
## [2026-11-12] fetch | 抓取 7 個網址；S4b K-pop_fandom 內容與 S1 重複 → 拒收
## [2026-11-12] discuss | 讀完 S1–S6 後提案架構；使用者改為精簡 6–7 頁、觀眾=輕度粉絲（D1 第二輪、D2）
## [2026-11-12] ingest | S1 → kpop-overview, timeline, agencies-trainees, idol-terms-fandom
## [2026-11-12] ingest | S2 → kpop-overview, timeline, global-milestones
## [2026-11-12] ingest | S3 → agencies-trainees, idol-terms-fandom, global-milestones
## [2026-11-12] ingest | S4 → music-shows, idol-terms-fandom, timeline
## [2026-11-12] ingest | S5 → timeline, agencies-trainees
## [2026-11-12] ingest | S6 → global-milestones, music-shows, timeline
## [2026-11-12] ingest | 建立 open-questions（Q1–Q6）與 index
## [2026-11-12] lint | run1：21 錯誤 + 7 警告；判定 checker 自身 bug 10 項（萬單位換算、年份誤判、HTML 文字黏連）→ 修 checker
## [2026-11-12] lint | run2：12 錯誤（全為真錯誤）→ 修 frontmatter 來源同步、表格逐列標來源、簡報 s1/s2/s8 追溯
## [2026-11-12] review | run3：規則檢查 0 錯誤後做語意審查（人工＋LLM 對照 wiki），找到 2 處：s5 把「嘻哈」併入「引入」的過度宣稱、s9 加了 wiki 沒有的評論 → 修正
## [2026-11-12] lint | 新增 tools/test_check.py（先測檢查器）；run4：check.py 0 錯誤 0 警告，16 頁簡報全數可追溯
