---
name: abr-doc-build-web
description: ABR（アドレス・ベース・レジストリ）公式サイトのWebページを defuddle で取得し、docs/…md に変換して追加する。新しい解説・方針・規約などのWebページを abr-mcp の検索対象に取り込むときに使う。
---

# abr-doc-build-web

デジタル庁ABRサイト等の公式**Webページ**を、`docs/…md` に変換・追加する。取り込めば
`list_documents` / `get_document` / `search_docs` で参照できるようになる。

取得・変換には **defuddle**（[kepano/defuddle](https://github.com/kepano/defuddle), MIT）を使う。
ページから本文を抽出して Markdown 化するライブラリ。

PDF資料はこのスキルではなく `abr-doc-build-pdf` を使う。

## 準備（変換時のみ。MCP実行時には不要）

Node（`npx`）が要る。無ければ入れる:

```
apt-get install -y nodejs npm     # または各環境の方法で Node を用意
```

## 手順

1. defuddle で対象URLを取得し、メタ＋markdown本文を JSON で得る:

   ```
   npx -y defuddle parse "<URL>" --markdown --json -o /tmp/abr_doc.json
   ```

2. JSON から本文と出典メタを取り出す:
   - `content` … markdown 本文（`##` 見出し構造を含む。参照リンクは残してよい）
   - `title` … タイトル（末尾の「｜デジタル庁」等のサイト名サフィックスは落とす）
   - `published` … 公開日（空なら version は「参照時点」とする）
3. 「出力規約」に整えて `docs/<英小文字スネークケースの名前>.md` に保存する
   （ファイル名= id。既存と重複しない名前）。一時 JSON は削除する。
4. [SOURCES.md](../../../SOURCES.md) の「ドキュメント」表に1行追加する
   （生成md／名称／形式=web／版／取得日／URL／生成方法=defuddle）。各mdのフロントマターと一致させる。
5. 反映確認: `import mcp_server` して `list_documents()` に出るか・`search_docs()` で
   代表語がヒットするかを確認する。

## 出力規約（docs/ 共通）

各 md は先頭に YAML フロントマターを置く:

```yaml
---
title: ページタイトル
source: https://…              # 元URL（必須。defuddleのメタには無いので渡したURLを入れる）
format: web
version: 2026-05-29（最終更新）  # 版の識別子のみ（日付/版番号）。著者・発行主体は入れない。published由来、空なら「参照時点」
captured: 2026-06-29           # 取得日（実行日）
---
```

- フロントマターの直後に `# タイトル` を置く（defuddle の本文は `##` から始まるため、H1 を足す）。
  以降は defuddle が出した `##`/`###` 節をそのまま使う。
- `scripts/mcp_server.py` の `_split_frontmatter` がフロントマターをメタとして分離し、
  索引・節本文には載せない（節は `##` 以下の見出し単位）。
- HTMLエンティティ（`&gt;`・`&lt;br&gt;` 等）の混入に注意して整える。推測で内容を創作しない。
