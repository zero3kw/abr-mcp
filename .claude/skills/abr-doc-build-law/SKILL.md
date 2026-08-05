---
name: abr-doc-build-law
description: ABR（アドレス・ベース・レジストリ）の根拠となる法令の条文を e-Gov 法令APIから逐語取得し、docs/…md に変換して追加する。e-Gov の法令ページ（laws.e-gov.go.jp）を検索対象に取り込むときに使う（defuddle では取れないため Web スキルではなくこちらを使う）。
---

# abr-doc-build-law

e-Gov 法令検索の**法令条文**を、`docs/…md` に変換・追加する。取り込めば
`list_documents` / `get_document` / `search_docs` で参照できるようになる。

**e-Gov の法令ページ（`laws.e-gov.go.jp/law/<lawId>`）は JS レンダリングのため、
`abr-doc-build-web`（defuddle）では本文が取れない。** 法令は e-Gov 法令API（v2）の
JSON 法令ツリーから条単位で逐語抽出する。そのための補助スクリプト `build_law.py` を同梱する。

ABR公式サイト等の通常Webページは `abr-doc-build-web`、PDFは `abr-doc-build-pdf`、
docx は `abr-doc-build-word` を使う。

## 準備

`curl` と Python3（いずれも標準）。追加依存なし（実行時の MCP には不要・変換時だけ使う）。

## 手順

1. lawId を確認する。e-Gov の法令URL `https://laws.e-gov.go.jp/law/<lawId>` の末尾。
   例: 独立行政法人国立印刷局法 = `414AC0000000041`。

2. 条文を抽出する。ABR関連の根拠条だけを収録する方針なので、対象条を絞る:

   ```
   # 条番号を指定（本則 MainProvision のみ対象）
   python3 .claude/skills/abr-doc-build-law/build_law.py 414AC0000000041 --articles 3,11

   # ある語を含む条だけ拾う（収録範囲の当たりを付けるのに便利）
   python3 .claude/skills/abr-doc-build-law/build_law.py 414AC0000000041 --keyword 公的基礎情報データベース
   ```

   出力は2ブロック:
   - `# META` … `revision_id`・`amendment_law_num`・`amendment_enforcement_date`・
     `current_revision_status`・`source` 等。**版**（フロントマター `version`）と
     冒頭の**抽出方針**を書くのに使う。`current_revision_status: CurrentEnforced` なら
     施行済みの現行版。未施行版が返ることもあるので必ず確認する。
   - `# BODY` … 各条の `## 第x条（見出し）` 以下の Markdown 断片。これを本文に貼る。

3. 「出力規約」に整えて `docs/law_<英小文字スネークケース>.md` に保存する
   （ファイル名= id。法令は `law_` 接頭辞で揃える。既存と重複しない名前）。

4. [SOURCES.md](../../../SOURCES.md) の「関連法令・標準」または「ベース・レジストリ制度の根拠」
   表に1行追加する（生成md／名称／形式=法令(e-Gov)／版／取得日／URL／生成スキル=`abr-doc-build-law`）。
   各md のフロントマターと一致させる。

5. 反映確認: `scripts/` で `import mcp_server` し、`list_documents()` に出るか・
   `search_docs()` で代表語がヒットするかを確認する。

## 出力規約（docs/ 共通）

先頭に YAML フロントマター:

```yaml
---
title: 独立行政法人国立印刷局法（ベース・レジストリ関連条）
source: https://laws.e-gov.go.jp/law/414AC0000000041   # META の source
format: web
version: 令和6法46改正の溶け込み版（2025-04-01施行・現行）  # META の改正法/施行日から
captured: 2026-06-29                                    # 取得日（実行日）
---
```

- `format` は `web`（既存の法令mdに合わせる。元が e-Gov である旨は version と抽出方針に書く）。
- フロントマターの直後に `# タイトル`。続けて**抽出方針**を1段落で書く:
  正式名称、lawId と `revision_id`、どの条を何の基準で抜いたか（例: 「『公的基礎情報
  データベース』が現れる条のみ」）、改正法・施行日、用語定義が他法令にある場合はその参照
  （`[[name]]` 形式で関連docへリンク）。
- その後ろに `# BODY` の `##` 条見出しブロックをそのまま貼る。
- 末尾に「## 注記（収録範囲）」で、収録した条・しなかった条と理由を補足すると後の再生成で迷わない。
- 推測で条文を創作しない。号の番号・全角項番号は API 出力のまま使う。
  （改正で号が繰り下がることがあるため、解説資料の号番号を鵜呑みにせず API 本文を正とする。）

## 注意

- 同じ法令でも改正前後で条・号の構成が変わる。**解説/概要資料の「第○条」表記と現行条文の
  号番号がずれることがある**ので、必ず `build_law.py` の出力（＝e-Gov 本文）を正とする。
- 用語の定義が当該法令になく他法令を参照する場合（例: 「国の公的基礎情報データベース」の定義は
  デジタル手続法側）、抽出方針にその旨と参照先を明記する。
