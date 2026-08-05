FROM python:3.13-slim

# git/curl/ca-certificates は取得用。以下は doc-build 系スキルの変換時のみ使う（MCP実行時は不要）:
#   nodejs/npm … abr-doc-build-web（defuddle を npx 実行）
#   poppler-utils … abr-doc-build-pdf（PDFのテキスト抽出・描画）
#   pandoc … abr-doc-build-word（docx→md 変換）
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends git curl ca-certificates nodejs npm poppler-utils pandoc \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# 依存（mcp のみ）をシステムの Python に入れる。
# scripts/ や specs/ は実行時に volume マウントするため COPY しない。
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
