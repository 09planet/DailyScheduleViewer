#!/bin/bash
# ダブルクリックで実行。初回のみ vault 外に専用 venv を自動作成し、
# 以降はその venv の python で today_schedule.py を実行する（activate 不要）。

# コード本体の場所（= この .command がある Obsidian vault 内のフォルダ）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# venv は vault の外に置く（同期に巻き込まないため）
VENV_DIR="$HOME/.venvs/daily-schedule-viewer"

# 初回のみ: venv 作成 & 依存インストール
if [ ! -x "$VENV_DIR/bin/python3" ]; then
  echo "初回セットアップ中… 専用の Python 環境を作成します（少し時間がかかります）"
  python3 -m venv "$VENV_DIR" || { echo "venv の作成に失敗しました"; exit 1; }
  "$VENV_DIR/bin/python3" -m pip install --upgrade pip
  "$VENV_DIR/bin/python3" -m pip install pyobjc-framework-EventKit \
    || { echo "パッケージのインストールに失敗しました"; exit 1; }
  echo "セットアップ完了。"
  echo
fi

# venv の python で実行（activate 不要）
"$VENV_DIR/bin/python3" "$SCRIPT_DIR/today_schedule.py"

DEBUG=false  # デバッグ時は true にするとEnter待ちになる
echo
if [ "$DEBUG" = "true" ]; then
  read -rp "Enterキーを押すと閉じます..."
fi
