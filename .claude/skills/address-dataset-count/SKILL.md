---
name: address-dataset-count
description: ABR（アドレス・ベース・レジストリ）の公開CSVを取得して、レコード数とCSVサイズを都道府県×カテゴリ別に集計する。町字・住居表示・地番など各マスターの件数・サイズ（text/posの両方）を実測したいときに使う。abr-mcp 本体（仕様・文章の参照）とは別系統の運用ヘルパで、住所レコードはカウント時のみ一時取得し保存しない。
---

# address-dataset-count

ABR の公開CSVを**出典元から実際に取得して、レコード数と CSVサイズを数える**スキル。

- 取得元: DCAT feed `https://dataset.address-br.digital.go.jp/api/feed/dcat-us/1.1.json` 経由で各カテゴリの CSV(zip)
- 集計: **レコード数**（CSVのデータ行数＝ヘッダ除く）、**圧縮サイズ**（zip＝DL量）、**展開サイズ**（解凍後CSV）
- zip はメモリ上で処理して破棄。大きなファイルはディスクに残さない（保存しない）

## 前提

- `python3` のみ（標準ライブラリだけ）。curl/jq/unzip/duckdb は不要（取得=`urllib`、zip展開=`zipfile`、JSON=`json`）。
- 出力は集計表のみ。**住所レコード自体は保存しない**（abr-mcp は住所レコードを扱わない方針）。

## 数えるカテゴリ（全カテゴリ固定）

| key | 説明 | 規模感 |
|---|---|---|
| `pref` | 都道府県マスター | 極小（47件） |
| `city` | 市区町村マスター | 小（約1,900件） |
| `town` | 町字マスター（`mt_town_fullset`） | 中（数十万件） |
| `blk` | 住居表示・街区マスター | 中 |
| `rsdt` | 住居表示・住居マスター | 大（数千万件） |
| `parcel` | 地番マスター | 特大（億単位） |

各カテゴリで text（文字）と代表点（pos）の両方を集計する。
`rsdt`/`parcel` を含む全件取得なので、ダウンロードは圧縮で数GB（展開すると数十GB相当）になる。

## 出力（2ファイルに分割）

| ファイル | 内容 |
|---|---|
| `abr_record_counts.md` | レコード数（全国合計＋都道府県×カテゴリ、text/pos） |
| `abr_csv_sizes.md` | CSVサイズ（全国合計＋都道府県別、圧縮/展開、text/pos） |

## 手順

```bash
# specs/ に2ファイルを書き出す
python3 .claude/skills/address-dataset-count/count_records.py specs

# 引数なしなら2本を標準出力に続けて表示
python3 .claude/skills/address-dataset-count/count_records.py
```

MCPサーバは `specs/` 配下の md を全て読む。レポートは項目定義テーブル（ヘッダに「項目No.」）を
持たないため**項目0個のデータセット**として扱われ、`list_datasets()` に出て
`get_dataset("abr_record_counts")` / `get_dataset("abr_csv_sizes")` で全文を取得できる
（項目が無いので `search_field` の項目検索は汚さない）。

## メモ

- 行カウントは「改行数 − ヘッダ1行」。ABR の CSV はレコード内改行が無い前提（住所処理用の素データ）。
- `pos`（代表点）は1住所単位に複数の代表点行を持つ場合があり（`blk_pos` は代表点座標が主キー）、行数＝住所件数ではない。住所件数が要るときは主キーで distinct する。
- 件数・サイズは出典の更新で変動する。表は取得日つきで残すこと。
