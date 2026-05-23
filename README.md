# EasyCFD / やさしいCFD

**Desktop GUI assistant for CFD beginners learning OpenFOAM**

OpenFOAM初心者のための、デスクトップGUIアシスタント

---

## Overview / 概要

EasyCFD is a beginner-friendly desktop application that helps students and self-learners run simple OpenFOAM simulations through guided workflows, safe command execution, logs, residuals, and explanations.

EasyCFDは、学生や独学者がOpenFOAMのシンプルなシミュレーションを実行できるよう、ガイド付きワークフロー、安全なコマンド実行、ログ、残差、説明機能を提供する初心者向けデスクトップアプリケーションです。

---

## Features / 機能

- **Guided Workflows**: Step-by-step simulation setup / ステップバイステップのシミュレーション設定
- **Safe Execution**: Whitelisted OpenFOAM commands only / ホワイトリスト方式の安全なコマンド実行
- **Docker Integration**: No OpenFOAM installation required / OpenFOAMのインストール不要
- **Real-time Logs**: Monitor solver progress / ソルバーの進行状況をモニタリング
- **Residual Plots**: Visualize convergence / 収束状況の可視化
- **Beginner Explanations**: Understand what's happening / 何が起こっているかを理解

---

## Status / 開発状況

**Current Version**: 0.1.0-alpha
**Status**: Active Development / 開発中

This project is in early alpha. Not ready for production use.

このプロジェクトは初期アルファ版です。本番使用には適していません。

---

## Architecture / アーキテクチャ

```
EasyCFD
├── apps/desktop/           # Tauri + React frontend
├── backend/easycfd_core/   # Python backend (FastAPI)
│   ├── api/               # REST API endpoints
│   ├── cfd/               # OpenFOAM runner
│   ├── llm/               # LLM integration (future)
│   └── validation/        # Safety & validation
├── mcp/codex_worker/       # MCP server for code generation
├── templates/             # OpenFOAM case templates
└── tests/                 # Test suite
```

---

## Installation / インストール

**Prerequisites / 必要環境:**
- Python 3.10+
- Docker Desktop
- Node.js 18+ (for frontend development)
- Rust (for Tauri development)

**Setup:**

```bash
# Clone repository
git clone https://github.com/yourusername/EasyCFD.git
cd EasyCFD

# Install Python dependencies
pip install poetry
poetry install

# Copy environment template
cp .env.example .env

# Start Docker OpenFOAM container
docker-compose up -d

# Run backend
poetry run uvicorn backend.easycfd_core.api.main:app --reload

# (Future) Run frontend
cd apps/desktop
npm install
npm run tauri dev
```

---

## Usage / 使い方

**Step 1: Create a new case / 新しいケースを作成**

Select a template (cavity or channel flow) from the GUI.

GUIからテンプレート（キャビティ流れまたはチャネル流れ）を選択します。

**Step 2: Configure parameters / パラメータを設定**

Adjust mesh size, solver settings, etc.

メッシュサイズ、ソルバー設定などを調整します。

**Step 3: Run simulation / シミュレーションを実行**

The app will run blockMesh, solver, and postProcess inside a Docker container.

アプリがDockerコンテナ内でblockMesh、ソルバー、postProcessを実行します。

**Step 4: View results / 結果を表示**

Check logs, residual plots, and visualization.

ログ、残差プロット、可視化を確認します。

---

## Security / セキュリティ

**EasyCFD follows strict security principles:**

- **Whitelist-only commands**: Only `blockMesh`, `checkMesh`, `icoFoam`, `simpleFoam`, `postProcess` are allowed
- **No arbitrary shell execution**: LLM output is structured and validated
- **Workspace isolation**: All runs confined to `./runs/` directory
- **Docker sandboxing**: OpenFOAM runs in isolated containers

**EasyCFDは厳格なセキュリティ原則に従います:**

- **ホワイトリスト方式**: `blockMesh`、`checkMesh`、`icoFoam`、`simpleFoam`、`postProcess`のみ許可
- **任意のシェル実行なし**: LLM出力は構造化され検証されます
- **ワークスペース隔離**: すべての実行は`./runs/`ディレクトリに制限
- **Dockerサンドボックス**: OpenFOAMは隔離されたコンテナ内で実行

---

## Development / 開発

**Run tests:**

```bash
poetry run pytest
```

**Code formatting:**

```bash
poetry run black .
poetry run ruff check .
```

**Type checking:**

```bash
poetry run mypy backend/ mcp/
```

---

## Roadmap / ロードマップ

- [x] Milestone 0: Repository scaffold
- [ ] Milestone 1: MCP Codex Worker
- [ ] Milestone 2: OpenFOAM runner + safety tests
- [ ] Milestone 3: Template-based case generation
- [ ] Milestone 4: Solver run + residual parsing
- [ ] Milestone 5: Minimal GUI (Tauri + React)
- [ ] Milestone 6: LLM structured planning
- [ ] Milestone 7: Beginner explanations

---

## Contributing / 貢献

This is a learning project. Contributions welcome but please follow security guidelines in `CLAUDE.md`.

これは学習プロジェクトです。貢献は歓迎しますが、`CLAUDE.md`のセキュリティガイドラインに従ってください。

---

## License / ライセンス

MIT License

---

## Disclaimer / 免責事項

**This tool is for educational purposes only.** Do not use for industrial CFD or safety-critical applications.

**このツールは教育目的のみです。** 産業用CFDや安全性が重要なアプリケーションには使用しないでください。

---

## Links / リンク

- [Project Brief](PROJECT_BRIEF.md) - Detailed specification / 詳細な仕様
- [Claude Instructions](CLAUDE.md) - Development guidelines / 開発ガイドライン
- [Agent Instructions](AGENTS.md) - MCP worker guidelines / MCPワーカーガイドライン
