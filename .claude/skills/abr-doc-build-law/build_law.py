#!/usr/bin/env python3
"""e-Gov 法令API（v2）から条文を逐語抽出して docs/ 用 Markdown 断片を出力する。

e-Gov の法令ページ（laws.e-gov.go.jp/law/<lawId>）は JS レンダリングのため
defuddle では本文を取れない。法令は API v2 の JSON 法令ツリーから取得する。

使い方:
    python3 build_law.py <lawId> --articles 3,11
    python3 build_law.py <lawId> --keyword 公的基礎情報データベース

オプション:
    --articles  抽出する条番号をカンマ区切りで指定（本則 MainProvision のみ対象）
    --keyword   その語を含む条だけを抽出（--articles と併用すると AND ではなく
                articles 優先。どちらも未指定なら全条）

出力(stdout):
    1) 「# META」ブロック … 版の識別に使うメタ（revision_id・改正法・施行日 等）。
       これを見て docs md のフロントマター version と冒頭の抽出方針を人が書く。
    2) 「# BODY」ブロック … 各条の `## 第x条（見出し）` 以下の Markdown 断片。
       これをフロントマター＋`# タイトル`＋抽出方針の後ろに貼る。

依存は標準ライブラリ＋curl のみ（実行時の MCP には不要・変換時だけ使う）。
"""
import argparse
import json
import subprocess
import sys

API = "https://laws.e-gov.go.jp/api/2/law_data/{law_id}"


def fetch(law_id: str) -> dict:
    url = API.format(law_id=law_id)
    out = subprocess.run(
        ["curl", "-sL", url], capture_output=True, text=True, check=True
    ).stdout
    data = json.loads(out)
    if data.get("law_full_text") is None:
        sys.exit(f"law_full_text が空。lawId を確認: {law_id}")
    return data


def find_tag(node, tag, first_only=False, _acc=None):
    """ツリーから tag のノードを収集（出現順）。"""
    acc = [] if _acc is None else _acc
    if isinstance(node, dict):
        if node.get("tag") == tag:
            acc.append(node)
            if first_only:
                return acc
        for v in node.values():
            find_tag(v, tag, first_only, acc)
            if first_only and acc:
                return acc
    elif isinstance(node, list):
        for x in node:
            find_tag(x, tag, first_only, acc)
            if first_only and acc:
                return acc
    return acc


def leaf_text(node) -> str:
    """ノード配下の文字列リーフを連結（Sentence 等の本文取り出し用）。"""
    parts = []

    def rec(n):
        if isinstance(n, dict):
            for v in n.values():
                rec(v)
        elif isinstance(n, list):
            for x in n:
                rec(x)
        elif isinstance(n, str):
            parts.append(n)

    rec(node.get("children", []))
    return "".join(parts).strip()


def children(node, tag):
    return [
        c
        for c in node.get("children", [])
        if isinstance(c, dict) and c.get("tag") == tag
    ]


def sentences(container) -> str:
    """ParagraphSentence/ItemSentence 等の直下 Sentence を連結。"""
    return "".join(leaf_text(s) for s in find_tag(container, "Sentence"))


def render_item(item, indent="") -> list:
    """Item（号）と入れ子の Subitem を Markdown 行に。"""
    title = ""
    t = find_tag(item, "ItemTitle", first_only=True)
    if t:
        title = leaf_text(t[0])
    body = ""
    sent = children(item, "ItemSentence")
    if sent:
        body = sentences(sent[0])
    lines = [f"{indent}{title}　{body}".rstrip()]
    # 一段だけ Subitem1 を拾う（必要十分。深い入れ子はまれ）
    for sub in children(item, "Subitem1"):
        st = ""
        stt = find_tag(sub, "Subitem1Title", first_only=True)
        if stt:
            st = leaf_text(stt[0])
        ssent = children(sub, "Subitem1Sentence")
        sbody = sentences(ssent[0]) if ssent else ""
        lines.append(f"{indent}　{st}　{sbody}".rstrip())
    return lines


def render_article(art) -> str:
    title = ""
    cap = ""
    tt = find_tag(art, "ArticleTitle", first_only=True)
    if tt:
        title = leaf_text(tt[0])
    ct = find_tag(art, "ArticleCaption", first_only=True)
    if ct:
        cap = leaf_text(ct[0])
    head = f"## {title}{cap}".rstrip()
    blocks = [head]
    for i, para in enumerate(children(art, "Paragraph")):
        pnum = ""
        pn = find_tag(para, "ParagraphNum", first_only=True)
        if pn:
            pnum = leaf_text(pn[0])
        psent = children(para, "ParagraphSentence")
        ptext = sentences(psent[0]) if psent else ""
        # 第1項は番号を付けない（条文慣行）。第2項以降は全角番号を前置。
        prefix = "" if (i == 0 or not pnum) else f"{pnum}　"
        blocks.append(f"{prefix}{ptext}".strip())
        for item in children(para, "Item"):
            blocks.extend(render_item(item))
    return "\n\n".join(b for b in blocks if b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("law_id")
    ap.add_argument("--articles", default="", help="例: 3,11")
    ap.add_argument("--keyword", default="")
    args = ap.parse_args()

    data = fetch(args.law_id)
    ri = data["revision_info"]
    li = data["law_info"]
    ft = data["law_full_text"]

    main_prov = find_tag(ft, "MainProvision", first_only=True)
    if not main_prov:
        sys.exit("MainProvision が見つからない")
    arts = find_tag(main_prov[0], "Article")

    want = [a.strip() for a in args.articles.split(",") if a.strip()]
    selected = []
    seen = set()
    for art in arts:
        num = art.get("attr", {}).get("Num")
        if num in seen:  # 本則内の重複番号は先勝ち
            continue
        md = None
        if want:
            if num in want:
                md = render_article(art)
        elif args.keyword:
            md = render_article(art)
            if args.keyword not in md:
                md = None
        else:
            md = render_article(art)
        if md:
            selected.append((num, md))
            seen.add(num)

    print("# META")
    print(f"law_id: {li.get('law_id')}")
    print(f"law_num: {li.get('law_num')}")
    print(f"title: {ri.get('law_title')}")
    print(f"revision_id: {ri.get('law_revision_id')}")
    print(f"current_revision_status: {ri.get('current_revision_status')}")
    print(f"amendment_law_num: {ri.get('amendment_law_num')}")
    print(f"amendment_promulgate_date: {ri.get('amendment_promulgate_date')}")
    print(f"amendment_enforcement_date: {ri.get('amendment_enforcement_date')}")
    print(f"source: https://laws.e-gov.go.jp/law/{li.get('law_id')}")
    print(f"selected_articles: {[n for n, _ in selected]}")
    print()
    print("# BODY")
    for _, md in selected:
        print(md)
        print()


if __name__ == "__main__":
    main()
