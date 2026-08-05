#!/usr/bin/env python3
"""ABR（アドレス・ベース・レジストリ）の公開CSVを取得してレコード数とサイズを集計する（Python標準ライブラリのみ）。

取得方法: DCAT feed（https://dataset.address-br.digital.go.jp/api/feed/dcat-us/1.1.json）から
カテゴリ別 CSV(zip) の URL を引く（zero3kw/jp-address-datasets の方式を参考）。

集計内容: 各CSVについて
  - レコード数 = データ行数（ヘッダ除く）
  - 圧縮サイズ = zip のバイト数（ダウンロード量）
  - 展開サイズ = 解凍後CSVのバイト数
各CSVはファイル名の `prefNN`/`cityNN…` で都道府県が判別できるので、全国合計（カテゴリ別）と
都道府県別の両方を集計する。text（文字）と pos（代表点）の両方。
zip はメモリ上で処理して破棄するので、ファイルはディスクに残さない（保存しない）。

レポートは2本に分けて出力する:
  - abr_record_counts.md … レコード数
  - abr_csv_sizes.md     … CSVサイズ

Usage:
  python3 count_records.py            # 2本を標準出力に続けて表示
  python3 count_records.py specs      # specs/abr_record_counts.md と specs/abr_csv_sizes.md に書き出す
"""
import collections, concurrent.futures as cf, io, json, os, re, sys, urllib.request, zipfile
from datetime import datetime, timezone

FEED_URL = "https://dataset.address-br.digital.go.jp/api/feed/dcat-us/1.1.json"
DIST_HOST = "data.address-br.digital.go.jp"  # feed の配布ドメイン（S3直URLは同じファイルの重複）
PARALLEL = 16

# 全国1ファイルの都道府県マスター（都道府県別表には出さない）
PREF_TEXT = r"/mt_pref/[^/]+\.csv\.zip$"
PREF_POS = r"/mt_pref_pos/[^/]+\.csv\.zip$"

# 都道府県別に並べるカテゴリ (key, 説明, text の feedパス正規表現, pos の feedパス正規表現)
CATS = [
    ("city",   "市区町村",       r"/mt_city/pref/[^/]+\.csv\.zip$",          r"/mt_city_pos/pref/[^/]+\.csv\.zip$"),
    ("town",   "町字（全件）",   r"/mt_town_fullset/pref/[^/]+\.csv\.zip$",  r"/mt_town_pos/pref/[^/]+\.csv\.zip$"),
    ("blk",    "住居表示・街区", r"/mt_rsdtdsp_blk/pref/[^/]+\.csv\.zip$",   r"/mt_rsdtdsp_blk_pos/pref/[^/]+\.csv\.zip$"),
    ("rsdt",   "住居表示・住居", r"/mt_rsdtdsp_rsdt/pref/[^/]+\.csv\.zip$",  r"/mt_rsdtdsp_rsdt_pos/pref/[^/]+\.csv\.zip$"),
    ("parcel", "地番",           r"/mt_parcel/city/[^/]+\.csv\.zip$",        r"/mt_parcel_pos/city/[^/]+\.csv\.zip$"),
]
PREF = [  # JIS X 0401（01〜47）
    ("01","北海道"),("02","青森県"),("03","岩手県"),("04","宮城県"),("05","秋田県"),("06","山形県"),
    ("07","福島県"),("08","茨城県"),("09","栃木県"),("10","群馬県"),("11","埼玉県"),("12","千葉県"),
    ("13","東京都"),("14","神奈川県"),("15","新潟県"),("16","富山県"),("17","石川県"),("18","福井県"),
    ("19","山梨県"),("20","長野県"),("21","岐阜県"),("22","静岡県"),("23","愛知県"),("24","三重県"),
    ("25","滋賀県"),("26","京都府"),("27","大阪府"),("28","兵庫県"),("29","奈良県"),("30","和歌山県"),
    ("31","鳥取県"),("32","島根県"),("33","岡山県"),("34","広島県"),("35","山口県"),("36","徳島県"),
    ("37","香川県"),("38","愛媛県"),("39","高知県"),("40","福岡県"),("41","佐賀県"),("42","長崎県"),
    ("43","熊本県"),("44","大分県"),("45","宮崎県"),("46","鹿児島県"),("47","沖縄県"),
]


def fetch(url, timeout=600, retries=3):
    """URL を取得してバイト列を返す（数回リトライ）。"""
    req = urllib.request.Request(url, headers={"User-Agent": "address-dataset-count"})
    last = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001  一時的なネットワーク失敗はリトライ
            last = e
    raise last


def measure(data):
    """zip バイト列から (データ行数, 解凍後バイト数) を返す。"""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if not names:
            return 0, 0
        body = z.read(names[0])
    nl = body.count(b"\n") + (0 if body.endswith(b"\n") or not body else 1)
    return max(nl - 1, 0), len(body)  # ヘッダ1行を除く / 解凍後サイズ


def fetch_feed_urls():
    d = json.loads(fetch(FEED_URL, timeout=120))
    urls = []
    for ds in d.get("dataset", []):
        for dist in ds.get("distribution", []) or []:
            u = dist.get("accessURL") or dist.get("downloadURL")
            if u and u.endswith(".csv.zip") and DIST_HOST in u:
                urls.append(u)
    return urls


def classify(url):
    """URL を (カテゴリ, pos?, 都道府県コード) に分類。都道府県別の対象外なら None。"""
    for key, _desc, tpat, ppat in CATS:
        is_pos = bool(re.search(ppat, url))
        if is_pos or re.search(tpat, url):
            m = re.search(r"(?:pref|city)(\d\d)\d*\.csv\.zip$", url)
            return (key, is_pos, m.group(1)) if m else None
    return None


def measure_urls(urls):
    """URL 群を取得して (行数, 圧縮バイト, 解凍バイト) の合計を返す。"""
    def one(u):
        data = fetch(u)
        rows, ub = measure(data)
        return rows, len(data), ub
    with cf.ThreadPoolExecutor(max_workers=PARALLEL) as ex:
        res = list(ex.map(one, urls))
    return tuple(sum(c) for c in zip(*res)) if res else (0, 0, 0)


def human(n):
    """バイト数を読みやすい単位に。"""
    n = float(n)
    for u in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024 or u == "TB":
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024


def main():
    feed = fetch_feed_urls()

    # 都道府県マスター（全国1ファイル）: (行数, 圧縮, 解凍)
    pref_t = measure_urls([u for u in feed if re.search(PREF_TEXT, u)])
    pref_p = measure_urls([u for u in feed if re.search(PREF_POS, u)])

    # 都道府県別の各カテゴリ
    tasks = [(u, c) for u in feed if (c := classify(u))]
    rec = collections.defaultdict(int)   # (pos?, pref, cat) -> レコード数
    comp = collections.defaultdict(int)  # -> 圧縮バイト
    unc = collections.defaultdict(int)   # -> 解凍バイト
    done = 0
    def job(item):
        url, (cat, is_pos, pref) = item
        data = fetch(url)
        rows, ub = measure(data)
        return (is_pos, pref, cat, rows, len(data), ub)
    with cf.ThreadPoolExecutor(max_workers=PARALLEL) as ex:
        for is_pos, pref, cat, rows, c, u in ex.map(job, tasks):
            k = (is_pos, pref, cat)
            rec[k] += rows; comp[k] += c; unc[k] += u
            done += 1
            if done % 200 == 0:
                print(f"[INFO] {done}/{len(tasks)} ファイル...", file=sys.stderr)

    def ctot(d, is_pos, key):  # カテゴリ全国合計
        return sum(d[(is_pos, code, key)] for code, _ in PREF)
    def psum(d, is_pos, code):  # 都道府県の全カテゴリ合計
        return sum(d[(is_pos, code, key)] for key, *_ in CATS)

    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")

    # ---- レコード数レポート ----
    R = [f"# ABR 公開CSVレコード数（取得日 {stamp}）", "",
         "ABR 公開CSV の各マスター（都道府県・市区町村・町字・住居表示・地番）のレコード件数（CSVのデータ行数）。"
         "`pos` は代表点行を含むため住所件数とは一致しない。", "",
         "## 全国合計（カテゴリ別）", "",
         "| カテゴリ | 説明 | text レコード数 | pos レコード数 |", "|---|---|---:|---:|",
         f"| `pref` | 都道府県マスター | {pref_t[0]:,} | {pref_p[0]:,} |"]
    tt = pref_t[0]; pt = pref_p[0]
    for key, desc, *_ in CATS:
        t, p = ctot(rec, False, key), ctot(rec, True, key)
        tt += t; pt += p
        R.append(f"| `{key}` | {desc}マスター | {t:,} | {p:,} |")
    R.append(f"| **合計** | | **{tt:,}** | **{pt:,}** |")

    def rec_table(is_pos):
        out = ["| コード | 都道府県 | " + " | ".join(d for _, d, *_ in CATS) + " | 合計 |",
               "|---|---|" + "---:|" * (len(CATS) + 1)]
        grand = 0
        for code, name in PREF:
            vals = [rec[(is_pos, code, key)] for key, *_ in CATS]
            grand += sum(vals)
            out.append(f"| {code} | {name} | " + " | ".join(f"{v:,}" for v in vals) + f" | {sum(vals):,} |")
        tots = [ctot(rec, is_pos, key) for key, *_ in CATS]
        out.append("| **合計** | | " + " | ".join(f"**{v:,}**" for v in tots) + f" | **{grand:,}** |")
        return out

    R += ["", "## text レコード数（都道府県 × カテゴリ）", "",
          "※ 都道府県マスター（pref）は全国1件のため下表には含めない。", ""] + rec_table(False)
    R += ["", "## pos（代表点）レコード数（都道府県 × カテゴリ）", ""] + rec_table(True)

    # ---- CSVサイズレポート ----
    S = [f"# ABR 公開CSVサイズ（取得日 {stamp}）", "",
         "圧縮=zip（ダウンロード量） / 展開=解凍後CSV。", "",
         "## 全国合計（カテゴリ別）", "",
         "| カテゴリ | 説明 | text 圧縮 | text 展開 | pos 圧縮 | pos 展開 |", "|---|---|---:|---:|---:|---:|",
         f"| `pref` | 都道府県マスター | {human(pref_t[1])} | {human(pref_t[2])} | {human(pref_p[1])} | {human(pref_p[2])} |"]
    tc = pref_t[1]; tu = pref_t[2]; pc = pref_p[1]; pu = pref_p[2]
    for key, desc, *_ in CATS:
        a, b = ctot(comp, False, key), ctot(unc, False, key)
        c, d = ctot(comp, True, key), ctot(unc, True, key)
        tc += a; tu += b; pc += c; pu += d
        S.append(f"| `{key}` | {desc}マスター | {human(a)} | {human(b)} | {human(c)} | {human(d)} |")
    S.append(f"| **合計** | | **{human(tc)}** | **{human(tu)}** | **{human(pc)}** | **{human(pu)}** |")

    S += ["", "## 都道府県別（カテゴリ合計）", "",
          "| コード | 都道府県 | text 圧縮 | text 展開 | pos 圧縮 | pos 展開 |", "|---|---|---:|---:|---:|---:|"]
    s = [0, 0, 0, 0]
    for code, name in PREF:
        v = [psum(comp, False, code), psum(unc, False, code), psum(comp, True, code), psum(unc, True, code)]
        for i in range(4):
            s[i] += v[i]
        S.append(f"| {code} | {name} | " + " | ".join(human(x) for x in v) + " |")
    S.append("| **合計** | | " + " | ".join(f"**{human(x)}**" for x in s) + " |")

    records_md = "\n".join(R) + "\n"
    sizes_md = "\n".join(S) + "\n"

    if len(sys.argv) > 1:
        outdir = sys.argv[1]
        with open(os.path.join(outdir, "abr_record_counts.md"), "w", encoding="utf-8") as f:
            f.write(records_md)
        with open(os.path.join(outdir, "abr_csv_sizes.md"), "w", encoding="utf-8") as f:
            f.write(sizes_md)
        print(f"wrote {outdir}/abr_record_counts.md, {outdir}/abr_csv_sizes.md", file=sys.stderr)
    else:
        print(records_md)
        print(sizes_md)


if __name__ == "__main__":
    main()
