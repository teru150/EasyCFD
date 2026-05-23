#!/bin/bash
# MCPサーバーセットアップスクリプト

set -e  # エラーで停止

echo "🚀 EasyCFD MCP Server Setup"
echo "================================"
echo ""

# 現在のディレクトリを確認
if [ ! -f "PROJECT_BRIEF.md" ]; then
    echo "❌ Error: このスクリプトはEasyCFDプロジェクトのルートディレクトリで実行してください"
    exit 1
fi

echo "📍 Current directory: $(pwd)"
echo ""

# Step 1: システムパッケージチェック
echo "Step 1: システムパッケージの確認"
echo "--------------------------------"

if ! command -v pip3 &> /dev/null; then
    echo "⚠️  pip3が見つかりません"
    echo "以下のコマンドを実行してください:"
    echo ""
    echo "  sudo apt update"
    echo "  sudo apt install -y python3-pip python3-venv"
    echo ""
    read -p "今すぐ実行しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt update
        sudo apt install -y python3-pip python3-venv
    else
        echo "❌ 中止しました。手動でインストールしてから再実行してください。"
        exit 1
    fi
else
    echo "✅ pip3: $(pip3 --version)"
fi

echo ""

# Step 2: 仮想環境作成
echo "Step 2: 仮想環境の作成"
echo "--------------------------------"

if [ -d ".venv" ]; then
    echo "⚠️  .venv/ は既に存在します"
    read -p "削除して再作成しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        python3 -m venv .venv
        echo "✅ 仮想環境を再作成しました"
    else
        echo "ℹ️  既存の仮想環境を使用します"
    fi
else
    python3 -m venv .venv
    echo "✅ 仮想環境を作成しました: .venv/"
fi

echo ""

# Step 3: 依存関係インストール
echo "Step 3: 依存関係のインストール"
echo "--------------------------------"

source .venv/bin/activate

echo "📦 openai と mcp をインストール中..."
pip install --upgrade pip
pip install openai mcp

echo "✅ 依存関係をインストールしました"
echo ""

# Step 4: .envファイル作成
echo "Step 4: 環境変数ファイルの作成"
echo "--------------------------------"

if [ -f ".env" ]; then
    echo "ℹ️  .env ファイルは既に存在します"
else
    cp .env.example .env
    echo "✅ .env ファイルを作成しました"
fi

echo ""
echo "⚠️  OPENAI_API_KEYを設定してください:"
echo ""
echo "  nano .env"
echo ""
echo "または:"
echo ""
echo "  export OPENAI_API_KEY=sk-proj-your-key-here"
echo ""

# Step 5: .claude/settings.json更新
echo "Step 5: Claude Code設定の更新"
echo "--------------------------------"

VENV_PYTHON="$(pwd)/.venv/bin/python3"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Error: 仮想環境のPythonが見つかりません: $VENV_PYTHON"
    exit 1
fi

echo "仮想環境のPython: $VENV_PYTHON"

# settings.jsonをバックアップ
if [ -f ".claude/settings.json" ]; then
    cp .claude/settings.json .claude/settings.json.backup
    echo "✅ 既存の設定をバックアップしました: .claude/settings.json.backup"
fi

# 新しいsettings.jsonを作成
cat > .claude/settings.json << EOF
{
  "mcpServers": {
    "codex-worker": {
      "command": "$VENV_PYTHON",
      "args": ["-m", "mcp.codex_worker.server"],
      "cwd": "$(pwd)",
      "env": {
        "PYTHONPATH": "$(pwd)"
      }
    }
  }
}
EOF

echo "✅ .claude/settings.json を更新しました"
echo ""

# Step 6: 動作確認
echo "Step 6: 動作確認"
echo "--------------------------------"

echo "openaiモジュールのテスト..."
if .venv/bin/python3 -c "import openai; print('✅ OpenAI SDK imported successfully')" 2>/dev/null; then
    :
else
    echo "❌ openaiモジュールのインポートに失敗しました"
    exit 1
fi

echo "mcpモジュールのテスト..."
if .venv/bin/python3 -c "import mcp; print('✅ MCP SDK imported successfully')" 2>/dev/null; then
    :
else
    echo "❌ mcpモジュールのインポートに失敗しました"
    exit 1
fi

echo ""
echo "================================"
echo "✅ セットアップ完了！"
echo "================================"
echo ""
echo "次のステップ:"
echo ""
echo "1. OpenAI APIキーを設定:"
echo "   nano .env"
echo ""
echo "2. Claude Codeを再起動"
echo ""
echo "3. テスト実行:"
echo "   Claude Code内で「codex_workerツールを使ってテスト」と指示"
echo ""
echo "詳細: SETUP_MCP.md を参照"
echo ""
