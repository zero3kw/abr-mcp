#!/usr/bin/env python3
"""pandoc(gfm) が出す HTML <table> を Markdown に均す（stdin→stdout）。

pandoc は Word の「1セルの罫線囲み（テキストボックス）」や、段落入りセルの表を
HTML <table> として出力する。これを:
  - 単一列（実体はテキストボックス） → 引用（> ...）に
  - 複数列（実体は表）            → GFM パイプ表に
変換して、Markdown として素直に読める／索引しやすい形にする。
"""
import re
import sys
from html.parser import HTMLParser


class _Table(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.row = []
        elif tag in ('td', 'th'):
            self.cell = []
        elif tag in ('p', 'br', 'blockquote', 'li') and self.cell is not None:
            self.cell.append('\n')

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            text = re.sub(r'\n+', '\n', ''.join(self.cell)).strip()
            self.row.append(text)
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def _convert(block):
    p = _Table()
    p.feed(block)
    rows = [r for r in p.rows if any(c.strip() for c in r)]
    if not rows:
        return ''
    ncol = max(len(r) for r in rows)
    if ncol == 1:  # テキストボックス → 引用
        out = []
        for r in rows:
            for line in r[0].split('\n'):
                out.append('> ' + line if line.strip() else '>')
        return '\n'.join(out)
    # 実テーブル → パイプ表（セル内改行は半角スペースに）
    def fmt(c):
        return c.replace('\n', ' ').replace('|', r'\|').strip()
    head = rows[0] + [''] * (ncol - len(rows[0]))
    out = ['| ' + ' | '.join(fmt(c) for c in head) + ' |', '|' + '---|' * ncol]
    for r in rows[1:]:
        r = r + [''] * (ncol - len(r))
        out.append('| ' + ' | '.join(fmt(c) for c in r) + ' |')
    return '\n'.join(out)


def _is_sep(line):
    core = line.strip()
    return bool(re.fullmatch(r'\|[\s:\-|]+\|', core)) and '-' in core


def _pipe_cells(line):
    core = line.strip()
    if core.startswith('|'):
        core = core[1:]
    if core.endswith('|'):
        core = core[:-1]
    return [c.strip() for c in re.split(r'(?<!\\)\|', core)]


def _flatten_single_col_pipe(text):
    """単一列のパイプ表（pandoc が罫線囲み1セルをパイプ表にしたもの）を引用に均す。"""
    lines, out, i = text.split('\n'), [], 0
    is_row = lambda l: l.lstrip().startswith('|') and l.rstrip().endswith('|')
    while i < len(lines):
        if is_row(lines[i]):
            j = i
            while j < len(lines) and is_row(lines[j]):
                j += 1
            block = lines[i:j]
            data = [b for b in block if not _is_sep(b)]
            if data and all(len(_pipe_cells(b)) == 1 for b in data):
                for b in data:
                    c = _pipe_cells(b)[0].replace(r'\|', '|')
                    out.append('> ' + c if c else '>')
            else:
                out.extend(block)
            i = j
        else:
            out.append(lines[i])
            i += 1
    return '\n'.join(out)


text = sys.stdin.read()
# (1) HTML <table>：入れ子に対応するため内側（<table> を含まない）から順に変換。
inner = re.compile(r'<table>(?:(?!<table>).)*?</table>', re.S)
prev = None
while prev != text:
    prev = text
    text = inner.sub(lambda m: _convert(m.group(0)), text)
# 取りこぼした表構造タグが残っていれば最後に除去（保険）。
text = re.sub(r'</?(?:table|colgroup|thead|tbody|tr|th|td)\b[^>]*>', '', text)
text = re.sub(r'<col\b[^>]*/?>', '', text)
# (2) 単一列のパイプ表 → 引用。
text = _flatten_single_col_pipe(text)
sys.stdout.write(text)
