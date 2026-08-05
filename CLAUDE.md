# abr-mcp

ABR（アドレス・ベース・レジストリ）の**データ定義（仕様）と公式ドキュメント**を Claude から
参照する MCP サーバ。住所レコードそのものは扱わない（仕様・文章の参照に特化）。

**概要・構成・提供ツール・使い方・環境変数は [README.md](README.md) を参照。**
ここには README に書かない、実装・運用上の規約と実装メモだけを置く。

## 規約

- **生成物は手編集しない。** `specs/`・`docs/` の md は公式資料からの自動生成物。再生成はスキルで行う:
  `abr-spec-build`（xlsx→specs）/ `abr-doc-build-web`（Web→docs）/ `abr-doc-build-pdf`（PDF→docs）/
  `abr-doc-build-word`（docx→docs）/ `abr-doc-build-law`（e-Gov法令API→docs。法令条文はWebスキルでは取れない）。
  部分的な Edit ではなく Write（全文の作り直し）で再生成する。生成md と元データの対応は
  [SOURCES.md](SOURCES.md)（版/取得日を変えたら表も直す）。
- **KISS / YAGNI / DRY。** 実行時の依存は `mcp` のみ。変換スキルは openpyxl / Node を変換時だけ使う
  （MCP 実行時には不要）。
- `ABR_EXTRA_DOCS_DIRS` で足す外部フォルダ（ローカルの md）は手編集可・コミットしない。
  中身は検索時に LLM へ渡る点に留意（このMCPは認証を持たない・ローカル実行）。

## 実装メモ

- データが小さいので起動時に全件パースし BM25（日本語bigram・標準ライブラリ）で索引化（DB不要）。
  BM25 実装は項目（カラム単位）と文書（節＝`##`見出し単位）で共有する。
- 索引の構築は `_build()` に集約し、起動時と `reload_index()` から呼ぶ。**md を再生成しただけでは
  検索に反映されない**（索引はメモリ上）。stdio サーバは Claude Code から再起動されないので、
  セッションを続けたまま反映するには `reload_index()` を呼ぶしかない。
- `get_document` は `_MAX_FULL`（8,000字）を超える文書の全文を返さず節一覧を返す。
  `dp_address_master_2021` が 112,680 字あり、全文を返すとコンテキストを使い切るため。
- `requirements.txt` は `mcp>=1.0,<2`。2.0 で `FastMCP` が `MCPServer` に改名され、
  上限を切らないと新しい環境で `ModuleNotFoundError` になる。
- ツールの一覧と用途は `scripts/mcp_server.py` 冒頭の docstring が正本。
- `_parse_doc` は先頭フロントマターを `_split_frontmatter` で分離し、索引・節本文には載せない。
- 仕様の重複見出し（blk_pos 等）はサーバが id で dedupe（保険）。docs の id 重複は先勝ち＋警告。
- 仕様は `specs/` 配下の md を全て読む。項目定義テーブル（ヘッダ「項目No.」）を持たない md（件数・サイズ
  レポート等）は項目0個＝`list_datasets` から外し、節単位でドキュメント検索（`search_docs`/`get_document`）に回す。
- 物理名（mt_pref 等）は xlsx に無く、`abr-spec-build` の対応表 `IDS` で補う（シート構成が変わったら更新）。
- 新フォーマット（解説書/フォーマットの2025年6月版）は公開準備中。公開されたら `abr-spec-build` で再生成。
