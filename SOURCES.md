# 同梱データの出典対応表

このリポジトリ同梱の Markdown は、すべてデジタル庁ほかの公式資料を変換した二次生成物です。
将来の更新・再生成のため、生成物と元データ（URL・形式・版）の対応を以下に記録します。

- 出典トップ: デジタル庁「アドレス・ベース・レジストリ」
  <https://www.digital.go.jp/policies/base_registry_address>
- URL が長い資料アセットは `BASE = https://www.digital.go.jp` を補って記載しています。
- 生成物（specs/・docs/）は**手編集しない**。再生成手順は各スキル（`abr-spec-build` /
  `abr-doc-build-web` / `abr-doc-build-pdf`）に従う。版・取得日を変えたら、この表も合わせて直す。

## データ項目定義（specs/）

| 生成md | 元データ（名称） | 形式 | 版/更新日 | 取得元URL | 生成スキル |
|---|---|---|---|---|---|
| [specs/20240115_policies_base_registry_format_01.md](specs/20240115_policies_base_registry_format_01.md) | データフォーマット（仕様確定版） | Excel(xlsx) | 2024-01-15 | `BASE`/assets/contents/node/basic_page/field_ref_resources/3d996df3-f87c-4439-b474-c0fbbf3ddad8/31267348/20240115_policies_base_registry_format_01.xlsx | `abr-spec-build` |

## ドキュメント（docs/）

| 生成md | 元データ（名称） | 形式 | 版/更新日 | 取得日 | 取得元URL | 生成スキル |
|---|---|---|---|---|---|---|
| [docs/abr_data_manual.md](docs/abr_data_manual.md) | データ解説書（試験公開版） | PDF | 2022-04-18（試験公開版） | 2026-06-29 | `BASE`/assets/contents/node/basic_page/field_ref_resources/3d996df3-f87c-4439-b474-c0fbbf3ddad8/d010b173/20220422_policies_base_registry_manual_01.pdf | `abr-doc-build-pdf` |
| [docs/development_improvement_plan.md](docs/development_improvement_plan.md) | 公的基礎情報データベース整備改善計画（概要） | PDF | 2025-06-13（閣議決定） | 2026-06-29 | `BASE`/assets/contents/node/basic_page/field_ref_resources/816ebeda-f081-4b18-b593-20fd12eb19a9/6e8cdb91/20250613_plan_for_development_and_improvement_of_public_basic_information_database_outline_03.pdf | `abr-doc-build-pdf` |
| [docs/standardization_address_system.md](docs/standardization_address_system.md) | 住所・所在地情報管理システムの共通化 | Webページ(HTML) | 参照時点 | 2026-06-29 | <https://www.digital.go.jp/policies/base_registry_address/standardization> | `abr-doc-build-web` |
| [docs/terms_of_service.md](docs/terms_of_service.md) | アドレス・ベース・レジストリ データの利用規約 | Webページ(HTML) | 2026-05-29（最終更新） | 2026-06-29 | <https://www.digital.go.jp/policies/base_registry_address_tos> | `abr-doc-build-web` |
| [docs/abr_future_policy_2026.md](docs/abr_future_policy_2026.md) | アドレス・ベース・レジストリの今後の方針について（第5回ベース・レジストリ推進有識者会合 資料3） | PDF | 2026-03（第5回ベース・レジストリ推進有識者会合 資料3） | 2026-06-29 | `BASE`/assets/contents/node/basic_page/field_ref_resources/38114226-507b-4df1-b94a-def9acbae0b5/1647c887/20260330_base-registry-advisory-board_5th_outline_03.pdf | `abr-doc-build-pdf` |

## 関連法令・標準（docs/・項目定義の根拠）

ABR の項目定義・コード値が依拠する一次資料（法令条文・外部標準）。デジタル庁ABR以外の公的機関が出典。

| 生成md | 元データ（名称） | 形式 | 版/更新日 | 取得日 | 取得元URL | 生成スキル |
|---|---|---|---|---|---|---|
| [docs/law_jukyo_hyoji.md](docs/law_jukyo_hyoji.md) | 住居表示に関する法律（昭和37法119） | 法令(e-Gov) | 最終改正 平成二十六年五月三十日法律第四十二号 | 2026-06-29 | <https://laws.e-gov.go.jp/law/337AC0000000119> | `abr-doc-build-law` |
| [docs/law_chihojichi.md](docs/law_chihojichi.md) | 地方自治法 第260条（町・字関連） | 法令(e-Gov) | 参照時点 | 2026-06-29 | <https://laws.e-gov.go.jp/law/322AC0000000067> | `abr-doc-build-law` |
| [docs/law_fudosan_toki_kisoku.md](docs/law_fudosan_toki_kisoku.md) | 不動産登記規則（地番区域＝第97/98条等） | 法令(e-Gov) | 参照時点 | 2026-06-29 | <https://laws.e-gov.go.jp/law/417M60000010018> | `abr-doc-build-law` |
| [docs/location_reference.md](docs/location_reference.md) | 位置参照情報 データ仕様（国交省ISJ） | Webページ(HTML) | 製品仕様書 第1.2版 | 2026-06-29 | <https://nlftp.mlit.go.jp/isj/data.html> | `abr-doc-build-web` |
| [docs/imi_address.md](docs/imi_address.md) | IMI共通語彙基盤 住所型 | Webページ(HTML) | コア語彙 2.4.2 | 2026-06-29 | <https://imi.go.jp/ns/core/Core242.html> | `abr-doc-build-web` |
| [docs/place_name_english.md](docs/place_name_english.md) | 地名等の英語表記規程（国土地理院） | PDF | 改正 令和8年国地達第5号（制定 平28国地達10） | 2026-06-29 | <https://www.gsi.go.jp/common/000138865.pdf> | `abr-doc-build-pdf` |

## ベース・レジストリ制度の根拠（docs/）

ABR を含むベース・レジストリ制度の法的・政策的根拠（指定告示・基本法・手続法・改正）。

| 生成md | 元データ（名称） | 形式 | 版/更新日 | 取得日 | 取得元URL | 生成スキル |
|---|---|---|---|---|---|---|
| [docs/designation_br_2021.md](docs/designation_br_2021.md) | ベース・レジストリの指定について（令和3・内閣官房IT総合戦略室決定） | PDF | 2021-05-26 | 2026-06-29 | <https://cio.go.jp/sites/default/files/uploads/documents/SpecifyingBaseRegistry.pdf> | `abr-doc-build-pdf` |
| [docs/designation_br_2023.md](docs/designation_br_2023.md) | ベース・レジストリの指定について（令和5デジタル庁告示第12号） | PDF | 令和5年デジタル庁告示第12号 | 2026-06-29 | `BASE`/assets/contents/node/basic_page/field_ref_resources/816ebeda-f081-4b18-b593-20fd12eb19a9/3c12f761/20230815_policies_base_registry_manual_01.pdf | `abr-doc-build-pdf` |
| [docs/digital_law_amendment_2024.md](docs/digital_law_amendment_2024.md) | デジタル社会形成基本法等の一部を改正する法律 概要（令和6法46） | PDF | 令和6年法律第46号 | 2026-06-29 | `BASE`/assets/contents/node/basic_page/field_ref_resources/423e67de-d520-4d46-8260-54b4f3125544/631a3d4b/20240305_laws_law_outline_01.pdf | `abr-doc-build-pdf` |
| [docs/law_digital_basic.md](docs/law_digital_basic.md) | デジタル社会形成基本法（ベース・レジストリ関連条＝第31/34/39条） | 法令(e-Gov) | 令和6年法律第46号改正後（令和7-04-01施行） | 2026-06-29 | <https://laws.e-gov.go.jp/law/503AC0000000035> | `abr-doc-build-law` |
| [docs/law_digital_procedure.md](docs/law_digital_procedure.md) | デジタル手続法（公的基礎情報DB関連条＝第1/19/20条） | 法令(e-Gov) | 参照時点（令和6法46改正の溶け込み版） | 2026-06-29 | <https://laws.e-gov.go.jp/law/414AC0000000151> | `abr-doc-build-law` |
| [docs/law_npb.md](docs/law_npb.md) | 独立行政法人国立印刷局法（ベース・レジストリ関連条＝第3/11条） | 法令(e-Gov) | 令和6法46改正の溶け込み版（2025-04-01施行・現行） | 2026-06-29 | <https://laws.e-gov.go.jp/law/414AC0000000041> | `abr-doc-build-law` |

## 背景・周辺資料（docs/）

ABR の背景・経緯を補う二次資料（講演資料・学術見解）。定義の根拠ではなく文脈の参照用。

| 生成md | 元データ（名称） | 形式 | 版/更新日 | 取得日 | 取得元URL | 生成スキル |
|---|---|---|---|---|---|---|
| [docs/abr_promotion_2022.md](docs/abr_promotion_2022.md) | アドレス・ベース・レジストリの推進について（平本健二・デジタル庁、SCJシンポ講演） | PDF | 2022-12-18 | 2026-06-29 | <https://www.scj.go.jp/ja/event/pdf3/321-s-1218-t3.pdf> | `abr-doc-build-pdf` |
| [docs/place_name_issue_abr.md](docs/place_name_issue_abr.md) | 地名問題の総合的解決に向けて（日本学術会議 見解・**ABR関連部分のみ抜粋**） | PDF | 2026-04-13 | 2026-06-29 | <https://www.scj.go.jp/ja/info/kohyo/pdf2/kohyo-26-k260413.pdf> | `abr-doc-build-pdf` |
| [docs/npb_br_operations.md](docs/npb_br_operations.md) | 国立印刷局が取り組むデータ整備（ベース・レジストリ運用業務） | PDF | 参照時点（令和7年度） | 2026-06-29 | <https://www.ipa.go.jp/digital/data/miraikaigi/rcu1hd000000marp-att/npb_base_registry_operations.pdf> | `abr-doc-build-pdf` |
| [docs/dp_address_master_2021.md](docs/dp_address_master_2021.md) | ベース・レジストリとしての住所・所在地マスターデータ整備について（政府CIO補佐官 ディスカッションペーパー） | docx | 2021-05 | 2026-06-29 | ローカル提供（dp2021_03.docx） | `abr-doc-build-word` |
| [docs/land_br_institutional_issues_2023.md](docs/land_br_institutional_issues_2023.md) | 土地系ベース・レジストリと制度的課題について（デジタル臨時行政調査会 作業部会 提出資料） | PDF | 2023-03-28（デジタル臨時行政調査会 作業部会 提出資料） | 2026-06-29 | `BASE`/assets/contents/node/basic_page/field_ref_resources/7e954fba-2ee1-432b-aac8-e5312fb72bb4/7236d1ff/20230328_meeting_administrative_research_working_group_02.pdf | `abr-doc-build-pdf` |

## 未取り込み（必要になったら追加）

| 候補 | 形式 | 取得元URL/所在 | メモ |
|---|---|---|---|
| データフォーマット（2025年6月版） | Excel | 出典トップに「公開準備中」 | 公開されたら `abr-spec-build` で specs を再生成 |
| データ解説書（2025年6月版） | PDF | 出典トップに「公開準備中」 | 公開されたら docs/abr_data_manual.md を差し替え |
| JIS X 0401 / 0402（都道府県・市区町村コード） | 規格 | JSAで有料・全文フリー入手不可 | コード体系の定義。位置参照情報の仕様・解説書の記述で代替している |
| 公的基礎情報データベース整備改善計画（案・改訂） | PDF | 第6回ベース・レジストリ推進有識者会合（2026-06-11）資料1/2 | 既収録 development_improvement_plan.md（2025-06-13閣議決定）の改訂作業中の案。確定・閣議決定されたら差し替え |
| 公式FAQ | — | ABRページに該当なし | 所在が判明したら追加 |
