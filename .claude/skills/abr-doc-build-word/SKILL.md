---
name: abr-doc-build-word
description: ABR（アドレス・ベース・レジストリ）関連の Word 文書（.docx）を pandoc で変換し、docs/…md に追加する。ディスカッションペーパー等の docx 資料を abr-mcp の検索対象に取り込むときに使う。
---

# abr-doc-build-word

ABR 関連の **Word 文書（.docx）** を `docs/…md` に変換・追加する。変換には **pandoc**（決定的・
表/見出し/箇条書きに強い）を使う。Webは `abr-doc-build-web`、PDFは `abr-doc-build-pdf`。

## 準備（変換時のみ。MCP実行時には不要）

pandoc が無ければ入れる:

```
apt-get install -y pandoc     # または各環境の方法で pandoc を用意
```

## 手順

1. docx を GitHub-flavored Markdown に変換する（画像は自動で落ちる。改行を畳む）:

   ```
   pandoc <file>.docx -t gfm --wrap=none -o /tmp/doc.md
   ```

2. 整形する（pandoc は章を `#`(h1) で出すので、本リポジトリの「1文書=1つの# タイトル＋`##`節」に合わせる）:
   - **表紙・目次を除去**（先頭の `# 目 次` とアンカーリンクの並ぶブロックを落とす。`tail -n +<行>`）。
   - **アンカーリンク除去＋見出しを1段下げる**（`#`→`##` …。先頭の全角スペースも除去）:
     `sed -E 's/\[([^]]*)\]\(#[^)]*\)/\1/g; s/^(#{1,5}) 　?/#\1 /'`
   - **テーブルを均す**: pandoc は Word の罫線囲み（1セルのテキストボックス）を、内容により
     HTML `<table>` か単一列のパイプ表として出す。同梱の `flatten_html_tables.py` に通すと、
     単一セル/単一列→引用、複数列→パイプ表 に変換する（HTML表・単一列パイプ表の両方、入れ子も対応）:
     `python3 .claude/skills/abr-doc-build-word/flatten_html_tables.py`
   - 図のみは「（図: 要約）」で補足してよい。**内容は創作しない**。
   - 図（フロー図・構成図・before→after の遷移図など）は docx→md で失われたりラベルだけ並ぶ。
     重要な図は手作業で **mermaid** に再現する（スクリプトは行わない＝再生成時は要再適用）。

   一括例:
   ```
   pandoc <file>.docx -t gfm --wrap=none -o /tmp/doc.md
   tail -n +<本文開始行> /tmp/doc.md \
     | sed -E 's/\[([^]]*)\]\(#[^)]*\)/\1/g; s/^(#{1,5}) 　?/#\1 /' \
     | python3 .claude/skills/abr-doc-build-word/flatten_html_tables.py
   ```
   （これにフロントマター＋`# タイトル` を前置して docs/ に保存）
3. 先頭に「出力規約」のフロントマター＋`# タイトル` を付け、`docs/<英小文字スネークケース>.md` に保存する。
4. [SOURCES.md](../../../SOURCES.md) の該当表に1行追加（形式=docx、生成スキル=`abr-doc-build-word`）。
5. 反映確認: `import mcp_server` して `list_documents()` に出るか・`search_docs()` で代表語がヒットするか。

## 出力規約（docs/ 共通）

各 md は先頭に YAML フロントマターを置く:

```yaml
---
title: 文書タイトル
source: 取得元（URL。ローカルdocxなら元ファイル名や出典の説明）
format: docx
version: 版の識別子（日付/版番号など）。著者・発行主体は入れない（title/source/本文へ）
captured: 2026-06-29
---
```

- 本文は `# タイトル` → `##`/`###` 節。`scripts/mcp_server.py` の `_split_frontmatter` が
  フロントマターをメタとして分離し、索引・節本文には載せない。
- `version` は**版を表す簡潔な値のみ**（日付・版番号・法令番号）。著者名や発行主体・取得メモは入れない。
