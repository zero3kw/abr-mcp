"""mcp_server.py が使うパス解決・表記正規化・検索用トークナイズ。"""

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# ABR データ項目定義書（公式フォーマット仕様の変換物）。specs/ 配下の md を全て読む。
SPECS_DIR = ROOT / 'specs'
# 公式の解説書・利用規約・方針などドキュメント（md）の置き場。
DOCS_DIR = ROOT / 'docs'
# 追加で索引するローカルの md フォルダ（個人メモ等）。os.pathsep 区切りで複数可。
# リポジトリ外を指す想定（同梱せず・コミットせず・手置き）。docs/ と同じ形式で索引する。
EXTRA_DOCS_DIRS = [Path(p) for p in
                   os.environ.get('ABR_EXTRA_DOCS_DIRS', '').split(os.pathsep) if p]

# 全角英数字→半角（検索語・本文を揃える）。記号・かなは対象外。
_FW_ASCII = str.maketrans(
    '０１２３４５６７８９'
    'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ'
    'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ',
    '0123456789'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    'abcdefghijklmnopqrstuvwxyz')


def normalize(text):
    """検索用にテキストを均す。全角英数字→半角、小文字化、空白除去。"""
    return (text or '').translate(_FW_ASCII).lower().replace(' ', '').replace('　', '')


_WORD = re.compile(r'[a-z0-9]+')                       # 英数字（型番・物理名 machiaza_type 等）
_CJK = re.compile(r'[぀-ヿ㐀-鿿々〆ヶ]+')  # かな/漢字の連なり


def tokenize(text):
    """検索語に分解する。英数字は小文字の単語、かな/漢字は連続文字の bigram。
    形態素解析を使わずに表記の部分一致をある程度拾うための簡易トークナイザ。"""
    text = (text or '').lower().translate(_FW_ASCII)
    tokens = _WORD.findall(text)
    for run in _CJK.findall(text):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens += [run[i:i + 2] for i in range(len(run) - 1)]
    return tokens
