# MCPサーバーセットアップ手順

MCPサーバー（Claude Code ⇔ OpenAI Codex連携）を動かすための手順です。

## 必要なもの

1. Python 3.10+（✅ 既にインストール済み: Python 3.13.3）
2. pip（Pythonパッケージマネージャー）
3. 仮想環境（venv）
4. OpenAI APIキー

---

## セットアップ手順

### 1. 必要なパッケージをインストール（sudo必要）

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv
```

**理由：** Debian/UbuntuのPython 3.13は、システム保護のため外部パッケージインストールを制限しています。仮想環境を使う必要があります。

---

### 2. 仮想環境を作成

```bash
cd /home/teru_26_2/webapp/EasyCFD
python3 -m venv .venv
```

これで `.venv/` ディレクトリができます。

---

### 3. 仮想環境を有効化

```bash
source .venv/bin/activate
```

プロンプトが `(.venv)` になればOK。

---

### 4. 依存関係をインストール

```bash
pip install openai mcp
```

または：

```bash
pip install -r mcp/codex_worker/requirements.txt
```

---

### 5. OpenAI APIキーを設定

```bash
cp .env.example .env
nano .env  # または vim/code で編集
```

`.env`ファイルに以下を追加：

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**APIキーの取得：**
1. https://platform.openai.com/api-keys
2. アカウント作成/ログイン
3. "Create new secret key"
4. コピーして `.env` に貼り付け

**料金：**
- GPT-4: $0.03/1K tokens (input), $0.06/1K tokens (output)
- 1回のコード生成 ≈ $0.05-0.10
- クレジットカード登録必要（最低$5チャージ）

---

### 6. MCPサーバー設定を更新

`.claude/settings.json` を修正（既に設定済み）：

```json
{
  "mcpServers": {
    "codex-worker": {
      "command": "/home/teru_26_2/webapp/EasyCFD/.venv/bin/python3",
      "args": ["-m", "mcp.codex_worker.server"],
      "cwd": "/home/teru_26_2/webapp/EasyCFD"
    }
  }
}
```

**重要：** `"command"` を仮想環境のpythonに変更する必要があります。

---

### 7. 動作確認

```bash
# 仮想環境が有効化されていることを確認
source .venv/bin/activate

# openaiがインポートできるか確認
python3 -c "import openai; print('✅ OpenAI OK')"

# mcpがインポートできるか確認
python3 -c "import mcp; print('✅ MCP OK')"
```

両方とも `✅ OK` と出ればインストール成功。

---

### 8. Claude Codeを再起動

Claude Codeを再起動して、`.claude/settings.json` を読み込ませます。

---

### 9. テスト実行

Claude Code内で：

```
codex_workerツールを使って、簡単なPydanticスキーマを生成してください
```

と指示すると、MCPサーバー経由でOpenAI GPT-4がコード生成します。

---

## トラブルシューティング

### Q: "No module named 'openai'" エラー

**A:** 仮想環境が有効化されていないか、インストールされていません。

```bash
source .venv/bin/activate
pip install openai mcp
```

### Q: "OPENAI_API_KEY not found" エラー

**A:** `.env` ファイルを作成して、APIキーを設定してください。

### Q: MCPサーバーが起動しない

**A:** `.claude/settings.json` の `"command"` が正しい仮想環境のPythonを指しているか確認：

```bash
ls -la /home/teru_26_2/webapp/EasyCFD/.venv/bin/python3
```

このファイルが存在すればOK。

---

## アーキテクチャ

```
あなた
  ↓
Claude Code (Sonnet 4.5) = 司令官
  ├─ 設計判断
  ├─ セキュリティレビュー
  ├─ コード品質チェック
  └─ 最終承認

  ↓ MCP Tool: codex_worker

MCP Server (mcp/codex_worker/server.py)
  ├─ タスク受信
  ├─ OpenAI API呼び出し
  └─ Validator実行（セキュリティチェック）

  ↓ OpenAI API

OpenAI GPT-4 = 作業員
  ├─ Pydanticスキーマ生成
  ├─ テストコード生成
  ├─ OpenFOAMテンプレート生成
  └─ ボイラープレート生成

  ↓ Generated Code

Validator (validator.py)
  ├─ shell=True? → NG
  ├─ eval()? → NG
  └─ Path traversal? → NG

  ↓ Validated Code

Claude Code = レビュアー
  ├─ Codexの出力をレビュー
  └─ 承認 or 修正指示
```

---

## まとめ

1. ✅ `sudo apt install python3-pip python3-venv` （sudoパスワード必要、1回のみ）
2. ✅ `python3 -m venv .venv` （仮想環境作成）
3. ✅ `source .venv/bin/activate` （有効化）
4. ✅ `pip install openai mcp` （依存関係）
5. ✅ `.env` にAPIキー設定
6. ✅ `.claude/settings.json` 修正（仮想環境のpython指定）
7. ✅ Claude Code再起動
8. ✅ テスト実行

これで Claude ⇔ Codex の完全自律実行が可能になります！
