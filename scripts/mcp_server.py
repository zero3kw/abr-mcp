"""アドレス・ベース・レジストリ（ABR）のデータ定義を参照する MCP サーバ（stdio）。

公式「データフォーマット（仕様確定版）」を変換した specs/ の項目定義 md を読み込み、
ABR 各データセットの項目定義（物理名・日本語名・型・桁・Key・説明とコード値の意味）を
参照できるようにする。住所レコードそのものは扱わない（仕様の参照に特化）。完全オフライン。

データ項目（カラム）の定義に加え、公式のドキュメント（解説書・利用規約・整備方針
など、docs/ 配下の md）も節（見出し）単位で索引化し、横断検索できる。

ツール:
  list_datasets()              ABR の全データセット（mt_pref, mt_town_fullset …）を一覧
  get_dataset(dataset)         指定データセットの全項目定義（表）を返す
  search_field(query, limit)   項目名・日本語名・説明を横断検索（「machiaza_type の意味」等）
  list_documents()             ドキュメント（解説書・利用規約・整備方針 …）を一覧
  get_document(document, ...)  指定ドキュメントの全文、または見出しで指定した節を返す
  search_docs(query, limit)    ドキュメントを節単位で横断検索（「実証事業のスケジュール」等）
"""

import math
import re
import sys
from collections import Counter
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from common import DOCS_DIR, EXTRA_DOCS_DIRS, SPECS_DIR, normalize, tokenize

mcp = FastMCP('abr')


def _parse(text, fallback_id='spec'):
    """仕様md を データセット毎の {id, title, raw, fields[]} に分解する。

    id は見出しの `(物理名)` から採る。物理名が無い見出し（件数レポート等）は fallback_id
    （通常はファイル名）を id にする。
    """
    sections, cur = [], None
    for line in text.splitlines():
        if line.startswith('# '):
            if cur:
                sections.append(cur)
            head = line[2:].strip()
            m = re.search(r'\(([A-Za-z0-9_]+)\)', head)
            ds_id = m.group(1) if m else fallback_id
            title = re.sub(r'^[0-9]+', '', re.sub(r'\([A-Za-z0-9_]+\)', '', head)).strip()
            cur = {'id': ds_id, 'title': title, 'lines': [line], 'fields': []}
        elif cur is not None:
            cur['lines'].append(line)
    if cur:
        sections.append(cur)

    out, seen = [], set()
    for s in sections:
        table = [ln for ln in s['lines'] if ln.lstrip().startswith('|')]
        # 項目定義テーブル（ヘッダに「項目No.」を含む）だけを項目として読む。
        # 件数レポート等の別形式テーブルは項目0個（データセットとしては raw のみ返す）。
        if not (table and '項目No.' in table[0]):
            table = []
        for ln in table[2:]:  # 先頭2行（見出し・区切り）を除く
            cells = [c.strip() for c in ln.strip().strip('|').split('|')]
            if len(cells) >= 8 and cells[0] != '項目No.':
                no, name, jp, typ, ln_, notnull, key, desc = cells[:8]
                s['fields'].append({'no': no, 'name': name, 'jp': jp, 'type': typ,
                                    'len': ln_, 'notnull': notnull, 'key': key, 'desc': desc})
        s['raw'] = '\n'.join(s['lines']).strip()
        if s['id'] in seen:  # 重複見出し（blk_pos 等）は最初の1つだけ
            continue
        seen.add(s['id'])
        out.append(s)
    return out


class BM25:
    """文字bigramトークン上の素朴な BM25。コーパス（項目定義の集合）が小さい前提で全件走査。"""

    def __init__(self, docs, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.N = len(docs)
        self.tf = [Counter(d) for d in docs]
        self.len = [sum(c.values()) for c in self.tf]
        self.avg = (sum(self.len) / self.N) if self.N else 1.0
        df = Counter()
        for c in self.tf:
            df.update(c.keys())
        self.idf = {t: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for t, n in df.items()}

    def search(self, query, top_k):
        q = tokenize(query)
        scored = []
        for i, c in enumerate(self.tf):
            s = 0.0
            for t in q:
                f = c.get(t)
                if f:
                    denom = f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg)
                    s += self.idf.get(t, 0.0) * f * (self.k1 + 1) / denom
            if s > 0:
                scored.append((s, i))
        scored.sort(reverse=True)
        return scored[:top_k]


_HEADING = re.compile(r'^#{2,6}\s')

# これを超える文書は get_document で全文を返さず、節一覧を返して絞らせる。
# 資料1本でコンテキストを使い切らせないため
_MAX_FULL = 8000


def _split_frontmatter(text):
    """先頭の YAML フロントマター（`---` で囲む出典メタ）を {key: value} と本文に分ける。

    Web Clipper / WebFetch どちらで作った md も、source/captured/version 等を機械可読にするため。
    フロントマターが無ければ ({}, 元テキスト) を返す。簡易パーサ（1行 key: value のみ）。
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return {}, text
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            meta = {}
            for ln in lines[1:i]:
                if ':' in ln:
                    k, v = ln.split(':', 1)
                    meta[k.strip()] = v.strip()
            return meta, '\n'.join(lines[i + 1:])
    return {}, text  # 閉じ `---` が無ければ本文扱い


def _parse_doc(path, text):
    """1つのドキュメントmd を {id, title, source, sections[]} に分解する。節は ## 見出し単位。

    先頭のフロントマター（source/captured 等）はメタとして分離し、索引・節本文には載せない。
    本文中の `# ` 行を文書タイトルとし、見出し前の前置きは「（冒頭）」節に入れる。
    """
    meta, body = _split_frontmatter(text)
    doc_id = path.stem
    title = meta.get('title') or path.stem
    sections, cur = [], {'heading': '（冒頭）', 'lines': []}
    for line in body.splitlines():
        if line.startswith('# '):  # 文書タイトル行。本文には含めない
            title = line[2:].strip()
            continue
        if _HEADING.match(line):
            if cur['lines']:
                sections.append(cur)
            cur = {'heading': line.lstrip('#').strip(), 'lines': []}
        else:
            cur['lines'].append(line)
    sections.append(cur)
    for s in sections:
        s['body'] = '\n'.join(s['lines']).strip()
    return {'id': doc_id, 'title': title, 'source': meta.get('source', ''),
            'raw': text.strip(), 'sections': [s for s in sections if s['body']]}


def _load_docs():
    """同梱 docs/ ＋ 外部フォルダ（ABR_EXTRA_DOCS_DIRS）の md を索引対象として読む。

    外部フォルダはローカルの md の置き場（個人メモ等。リポジトリ外想定）。docs/ と同形式で扱う。
    id（ファイル名）が重複したら先に読んだ方を採用し、後続は警告して飛ばす。
    """
    docs, seen = [], set()
    for d in [DOCS_DIR, *EXTRA_DOCS_DIRS]:
        if not d.is_dir():
            continue
        for p in sorted(d.glob('*.md')):
            doc = _parse_doc(p, p.read_text(encoding='utf-8'))
            if doc['id'] in seen:
                sys.stderr.write(f'[abr] id重複のためスキップ: {p}（既出 id={doc["id"]}）\n')
                continue
            seen.add(doc['id'])
            docs.append(doc)
    return docs


def _build():
    """specs/ と docs/ を読み直して索引を作る。起動時と reload_index から呼ぶ。

    項目（カラム単位）と文書（節単位）の2系統を作る。どちらも BM25 は共有。
    """
    global _SECTIONS, _DATASETS, _FIELDS, _INDEX, _DOCS, _DOC_SECTIONS, _DOC_INDEX

    # specs/ 配下の md を全て読む。id（物理名 or ファイル名）が重複したら先に読んだ方を採用。
    # 再生成後に呼ばれても拾えるよう、ここで glob し直す
    _SECTIONS, seen = [], set()
    for p in sorted(SPECS_DIR.glob('*.md')):
        if not p.is_file():
            continue
        for s in _parse(p.read_text(encoding='utf-8'), fallback_id=p.stem):
            if s['id'] in seen:
                continue
            seen.add(s['id'])
            _SECTIONS.append(s)

    # 項目を持つ節＝データセット（list_datasets/get_dataset 対象）。
    # 項目を持たない節（件数・サイズ レポート等）は後段でドキュメント検索の対象に回す。
    _DATASETS = [s for s in _SECTIONS if s['fields']]

    # 各項目（カラム）を1ドキュメントとして BM25 索引化する。
    # 検索対象テキスト = 物理名 + 日本語名 + 説明 + データセットの id/日本語名。
    _FIELDS = [(s, f) for s in _SECTIONS for f in s['fields']]
    _INDEX = BM25([tokenize(' '.join((f['name'], f['jp'], f['desc'], s['id'], s['title'])))
                   for s, f in _FIELDS])

    _DOCS = _load_docs()

    # 仕様mdのうち項目を持たない節（件数・サイズ レポート等）も、節単位でドキュメント検索できる
    # ようにする。これで「地番のレコード数は？」のような自由文を search_docs/get_document で引ける。
    doc_ids = {d['id'] for d in _DOCS}
    for s in _SECTIONS:
        if not s['fields'] and s['id'] not in doc_ids:
            _DOCS.append(_parse_doc(Path(f"{s['id']}.md"), s['raw']))

    # ドキュメントは「節（見出し単位）」を1ドキュメントとして BM25 索引化する。
    _DOC_SECTIONS = [(d, s) for d in _DOCS for s in d['sections']]
    _DOC_INDEX = BM25([tokenize(' '.join((d['title'], s['heading'], s['body'])))
                       for d, s in _DOC_SECTIONS])


_build()


def _resolve(dataset):
    """データセット指定（id でも日本語名でも、部分一致でも）を解決する。"""
    q = normalize(dataset)
    exact = [s for s in _DATASETS if normalize(s['id']) == q]
    if exact:
        return exact, ''
    hit = [s for s in _DATASETS if q in normalize(s['id']) or q in normalize(s['title'])]
    return hit, ''


@mcp.tool()
def list_datasets() -> str:
    """ABR の全データセット（物理名・日本語名・項目数）を一覧する。get_dataset の起点に使う。"""
    if not _DATASETS:
        return f'仕様ファイルが読めません: {SPECS_DIR}'
    return '\n'.join(f'{s["id"]}  {s["title"]}（{len(s["fields"])}項目）' for s in _DATASETS)


@mcp.tool()
def get_dataset(dataset: str) -> str:
    """指定したデータセットの全項目定義（物理名/日本語名/型/桁/Key/説明）を表で返す。

    Args:
        dataset: 物理名か日本語名（部分可）。例:「mt_town_fullset」「町字」「市区町村」
    """
    hits, _ = _resolve(dataset)
    if not hits:
        ids = ', '.join(s['id'] for s in _DATASETS)
        return f'該当データセットなし: {dataset}\n候補: {ids}'
    if len(hits) > 1:
        return ('複数該当しました。一つに絞ってください:\n'
                + '\n'.join(f'- {s["id"]}（{s["title"]}）' for s in hits))
    return hits[0]['raw']


@mcp.tool()
def search_field(query: str, limit: int = 15) -> str:
    """項目（カラム）を物理名・日本語名・説明から横断検索し、関連度（BM25）順に返す。

    日本語は文字bigramで照合するので、語の一部や言い回しの揺れもある程度拾う。
    「machiaza_type とは」「住居表示フラグ はどのデータセットに？」「丁目の英語表記」等に使う。

    Args:
        query: 探したい語。例:「machiaza_type」「住居表示フラグ」「代表点 緯度」「外字」
        limit: 返す件数（既定 15）
    """
    hits = _INDEX.search(query, limit)
    if not hits:
        return f'「{query}」に一致する項目は見つかりませんでした。'
    out = []
    for score, i in hits:
        s, f = _FIELDS[i]
        key = f'[{f["key"]}]' if f['key'] else ''
        out.append(f'{s["id"]}.{f["name"]}（{f["jp"]}） 型:{f["type"]} 桁:{f["len"]} {key}'
                   f'（関連度 {score:.1f}）\n   {f["desc"]}')
    return '\n'.join(out)


def _resolve_doc(document):
    """文書指定（id でも日本語タイトルでも、部分一致でも）を解決する。"""
    q = normalize(document)
    exact = [d for d in _DOCS if normalize(d['id']) == q]
    if exact:
        return exact
    return [d for d in _DOCS if q in normalize(d['id']) or q in normalize(d['title'])]


@mcp.tool()
def list_documents() -> str:
    """ABR 公式のドキュメント（解説書・利用規約・整備方針など）を一覧する。

    データ項目の定義は list_datasets / search_field、文章での解説・背景・規約はこちら。
    """
    if not _DOCS:
        return f'ドキュメントがありません: {DOCS_DIR}'
    return '\n'.join(f'{d["id"]}  {d["title"]}（{len(d["sections"])}節）' for d in _DOCS)


@mcp.tool()
def get_document(document: str, section: str = '') -> str:
    """指定したドキュメントの全文、または見出しで指定した節だけを返す。

    Args:
        document: 文書id か タイトル（部分可）。例:「terms_of_service」「利用規約」「解説書」
        section: 見出し語（部分可）。指定するとその節だけ返す。例:「出典」「スケジュール」
    """
    hits = _resolve_doc(document)
    if not hits:
        ids = ', '.join(d['id'] for d in _DOCS)
        return f'該当ドキュメントなし: {document}\n候補: {ids}'
    if len(hits) > 1:
        return ('複数該当しました。一つに絞ってください:\n'
                + '\n'.join(f'- {d["id"]}（{d["title"]}）' for d in hits))
    d = hits[0]
    if section:
        sq = normalize(section)
        secs = [s for s in d['sections'] if sq in normalize(s['heading'])]
        if not secs:
            heads = ', '.join(s['heading'] for s in d['sections'])
            return f'該当する節なし: {section}\n見出し候補: {heads}'
        return '\n\n'.join(f'## {s["heading"]}\n{s["body"]}' for s in secs)
    if len(d['raw']) > _MAX_FULL:
        heads = '\n'.join(f'- {s["heading"]}（{len(s["body"]):,}文字）' for s in d['sections'])
        return (f'{d["title"]} は {len(d["raw"]):,} 文字あるので全文は返さない。'
                f'section を指定して節ごとに取ること:\n{heads}')
    return d['raw']


@mcp.tool()
def search_docs(query: str, limit: int = 10) -> str:
    """ドキュメント（解説書・利用規約・整備方針など）を節（見出し）単位で横断検索する。

    日本語は文字bigramで照合。「地番マスターの利用規約」「実証事業のスケジュール」
    「街区符号 住居番号 とは」等、文章での解説・背景・手続を探すときに使う。
    項目（カラム）の定義そのものを探すときは search_field を使う。

    Args:
        query: 探したい語・問い。例:「登記所備付地図 利用規約」「共通化の背景」
        limit: 返す件数（既定 10）
    """
    hits = _DOC_INDEX.search(query, limit)
    if not hits:
        return f'「{query}」に一致する記述は見つかりませんでした。'
    out = []
    for score, i in hits:
        d, s = _DOC_SECTIONS[i]
        snippet = ' '.join(s['body'].split())[:140]
        out.append(f'{d["id"]} › {s["heading"]}（関連度 {score:.1f}）\n   {snippet}…')
    return '\n'.join(out)


@mcp.tool()
def reload_index() -> str:
    """specs/ と docs/ を読み直して索引を作り直す。md を再生成した直後に呼ぶ。

    索引は起動時にメモリ上に作るため、これを呼ばない限り新しい md は検索に出てこない。
    stdio サーバは Claude Code から再起動されないので、セッションを続けたまま反映するにはこれを使う。
    """
    _build()
    return (f'{len(_DATASETS)} データセット / {len(_FIELDS)} 項目、'
            f'{len(_DOCS)} 文書 / {len(_DOC_SECTIONS)} 節を読み直した')


if __name__ == '__main__':
    mcp.run()  # 既定で stdio トランスポート
