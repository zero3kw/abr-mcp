# abr-mcp

アドレス・ベース・レジストリ（ABR / デジタル庁）の**データ定義（仕様）と公式ドキュメント**を
Claude から参照する MCP サーバ。

データ源は2系統（いずれも公式資料を Markdown 化して同梱、ビルド不要）:

1. **データ項目定義**（カラム単位）… 公式「データフォーマット（仕様確定版）」（Excel・2024-01-15）を
   変換した [specs/20240115_policies_base_registry_format_01.md](specs/20240115_policies_base_registry_format_01.md)
   （ファイル名は元の公式 Excel に合わせている）。各データセット（`mt_pref`, `mt_city`,
   `mt_town_fullset`, `mt_rsdtdsp_*`, `mt_*_pos` …）の項目定義表を収録。
2. **ドキュメント**（解説・方針・規約）… [docs/](docs/) 配下の md。デジタル庁公式の
   データ解説書（試験公開版）・整備改善計画・住所所在地システム共通化・利用規約を、見出し（節）単位で
   索引化。「項目の意味」だけでなく「背景・経緯・手続・規約」への問いに答える。

## 提供ツール

データ項目（カラム）:
- `list_datasets()` … ABR の全データセット（物理名・日本語名・項目数）を一覧
- `get_dataset(dataset)` … 指定データセットの全項目定義（物理名/日本語名/型/桁/Key/説明）
- `search_field(query, limit)` … 項目名・日本語名・説明を横断検索（BM25・日本語bigram、関連度順）

ドキュメント:
- `list_documents()` … ドキュメント（解説書・整備方針・利用規約 …）を一覧
- `get_document(document, section)` … 指定ドキュメントの全文、または見出しで指定した節を返す
  （8,000字を超える文書は全文の代わりに節一覧を返すので、`section` で絞る）
- `search_docs(query, limit)` … ドキュメントを節（見出し）単位で横断検索（BM25、関連度順）

保守:
- `reload_index()` … `specs/`・`docs/` を読み直して索引を作り直す。md を再生成した直後に呼ぶ
  （索引は起動時にメモリ上に作るため、呼ばないと新しい md は検索に出てこない）

例:
- `search_field("machiaza_type")` → 町字区分コードの定義とコード値（1:大字・町 2:丁目 …）
- `search_field("住居表示フラグ")` → `rsdt_addr_flg` を持つ全データセット
- `get_dataset("町字フルセット")` → `mt_town_fullset` の全52項目
- `search_docs("地番 レコード件数")` → 公開CSVのレコード件数レポート（全国合計＋都道府県別。例: 地番 約2.1億件）
- `get_document("abr_record_counts")` / `get_document("abr_csv_sizes")` → 公開CSVの件数・サイズ（圧縮＝DL量/展開）の全文
- `search_docs("街区符号 住居番号 道路方式")` → 解説書の街区ID/住居マスター収録基準
- `search_docs("アドレス・ベース・レジストリ 政策効果")` → 整備改善計画の該当節
- `get_document("利用規約")` → 利用規約（PDL1.0・地番マスターの個別制約 等）の全文

## 使い方

依存は `mcp` のみ（Python 3.11+）。仕様ファイルは同梱済みでビルド不要。

同梱の `.devcontainer/`（VS Code / Claude Code）で開くと依存込みの環境が用意され、
`.mcp.json` により Claude Code が `abr` MCP を自動認識する。

DevContainer を使わない場合は Python 3.11+ で:

```
pip install -r requirements.txt
python3 scripts/mcp_server.py     # stdio。起動して即終了しなければOK
```

Claude Code への登録例:

```
claude mcp add abr -- python3 /絶対パス/abr-mcp/scripts/mcp_server.py
```

仕様は同梱の `specs/`、ドキュメントは同梱の `docs/` を索引する（場所は固定）。

リポジトリ外のローカル md（個人メモ等）を**追加**で索引したいときは `ABR_EXTRA_DOCS_DIRS` に
フォルダを指定する（`os.pathsep`＝Linux/macOS は `:` 区切りで複数可）。`docs/` と同形式・同ツールで
扱う。中身は検索時に LLM へ渡る点に留意。

## 生成物の更新

`specs/`・`docs/` の md はすべて公式資料からの**自動生成物**（手動編集しない）。再生成は
Claude Code スキルが担う:

- [`abr-spec-build`](.claude/skills/abr-spec-build/) … データフォーマット xlsx → `specs/…md`
- [`abr-doc-build-web`](.claude/skills/abr-doc-build-web/) … 公式Webページ → `docs/…md`
- [`abr-doc-build-pdf`](.claude/skills/abr-doc-build-pdf/) … 公式PDF資料 → `docs/…md`

ABR が新フォーマット等を公開したら該当スキルで再生成する。生成物と元データの対応は
[SOURCES.md](SOURCES.md) を参照。

## ライセンス

- **コード**（`scripts/`・`.claude/skills/`・設定ファイル）… [MIT License](LICENSE)。
- **同梱データ**（`specs/`・`docs/`）… 本プロジェクトの著作物ではなく、各出典（下記）の公式資料を
  Markdown 化した二次生成物。利用は MIT ではなく各出典の規約（主に
  [公共データ利用規約 第1.0版（PDL1.0）](https://www.digital.go.jp/resources/open_data/public_data_license_v1.0)）
  に従う。詳細は [LICENSE](LICENSE) 末尾の注記と各ファイルの出典（[SOURCES.md](SOURCES.md)）を参照。

## 出典

同梱の `specs/`・`docs/` は、以下の公的機関が公開する資料を加工して作成（編集・加工はzero3kw）:

- 主たる出典: [「アドレス・ベース・レジストリ」（デジタル庁）](https://www.digital.go.jp/policies/base_registry_address/)
- そのほか: 内閣官房、日本学術会議、情報処理推進機構（IPA）、国土交通省、国土地理院、
  e-Gov 法令（総務省）等。生成md ごとの出典（名称・URL・版）は [SOURCES.md](SOURCES.md) に記載。

デジタル庁ABRデータの利用にあたっては
[利用規約](https://www.digital.go.jp/policies/base_registry_address_tos) を確認すること
（地番マスター／地番マスター位置参照は登記所備付地図データ利用規約も別途適用。ただし本リポジトリは
住所レコード実体を含まず仕様・文章のみを収録）。
