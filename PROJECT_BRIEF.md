# EasyCFD Project Brief

日本語名: やさしいCFD
English name: EasyCFD

## One-line summary

EasyCFD is a desktop GUI assistant that helps CFD beginners run their first OpenFOAM simulations through natural language, guided workflow explanations, safe command execution, and visual feedback.

---

## Agent Architecture

EasyCFD uses a **Commander / Worker** agent model:

```
Claude Code (Commander)
  └── Codex MCP Worker (Worker)
```

### Claude Code の役割
- プロジェクト全体の設計判断
- セキュリティクリティカルなコードのレビュー
- Codex への実装タスクの委任
- Codex の出力レビューと修正指示
- テスト失敗時の原因特定と修正

### Codex MCP Worker の役割
- Claude Code から受け取ったタスクの実装
- ボイラープレートコードの生成
- テストコードの生成
- 仕様が明確な実装タスクの実行

### MCP サーバー構成

```
easycfd/
  mcp/
    codex_worker/
      server.py       # MCPサーバー本体
      handlers.py     # タスクハンドラー
      validator.py    # Codex出力の安全性検証
      requirements.txt
```

### MCP サーバーの起動

```bash
# MCPサーバーを起動
python mcp/codex_worker/server.py

# Claude Code の設定（.claude/settings.json）
{
  "mcpServers": {
    "codex-worker": {
      "command": "python",
      "args": ["mcp/codex_worker/server.py"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### Claude Code から Codex を呼び出す流れ

```
Claude Code がタスクを分解
        │
        ▼
MCP経由でCodexにタスクを投げる
  - task: 実装内容の説明
  - context_files: 参照すべきファイルのリスト
  - constraints: 守るべき制約（セキュリティルール等）
        │
        ▼
Codex が実装してファイルを生成
        │
        ▼
MCP validator が出力を検証
  - 危険なコードパターンをチェック
  - ホワイトリスト違反をチェック
        │
        ▼
Claude Code がレビューして承認 or 修正指示
```

### Codex に委任すべきタスク
- ボイラープレートコードの生成
- テストコードの生成
- OpenFOAM テンプレートファイルの生成
- Pydantic スキーマの実装
- ログパーサーの実装

### Claude Code 自身がやるべきタスク
- セキュリティクリティカルなコード（safety.py等）
- 設計判断とアーキテクチャ決定
- Codex の出力レビュー
- テスト失敗時のデバッグ

---

## Project Motivation

OpenFOAM is powerful but has a steep initial learning curve. Beginners must understand case directory structure, dictionary files, meshing commands, solver selection, boundary conditions, terminal commands, residual logs, and mesh errors before running even a simple simulation.

EasyCFD translates this workflow into understandable guided steps. It does not hide CFD — it makes the first encounter approachable.

---

## Target Users

**Primary:**
- Students or self-learners curious about CFD
- OpenFOAM beginners
- People overwhelmed by command-line workflow and case files

**Not the target:**
- Professional CFD engineers needing industrial-grade accuracy
- Full CAD-to-mesh automation users
- Commercial CAE replacement users

---

## Research Framing

**Research question (EN):**
> Can a natural-language GUI assistant reduce the initial workflow barrier for students learning OpenFOAM-based CFD?

**Research question (JA):**
> 自然言語GUIアシスタントは、OpenFOAMを用いたCFD学習における初期ワークフローの障壁を下げられるか？

**Core hypothesis:**
> If beginners can describe simple CFD cases in natural language and see the generated workflow, commands, logs, residuals, and results in a GUI, they can complete first simulations more successfully than with command-line tutorials alone.

---

## Core Design Principle

**Never let the LLM directly execute arbitrary shell commands.**

```
Correct flow:
  User prompt
    -> LLM
    -> structured JSON case plan
    -> validator
    -> template-based OpenFOAM case generation
    -> whitelisted OpenFOAM command runner
    -> log parser / residual monitor
    -> visualization
    -> explanation back to user

Incorrect flow:
  User prompt
    -> LLM
    -> arbitrary shell command  ← 絶対禁止
```

---

## MVP Scope

**Supported cases:**
1. 2D lid-driven cavity flow
2. 2D channel flow

**Supported physics:**
- Incompressible flow
- Simple laminar cases
- Basic steady or transient workflows

**Allowed OpenFOAM commands:**
```python
ALLOWED_COMMANDS = {
    "blockMesh",
    "checkMesh",
    "icoFoam",
    "simpleFoam",
    "postProcess"
}
```

**Initial features:**
- Select or create a case from a template
- Run OpenFOAM commands safely
- Stream logs to the GUI
- Parse residuals from solver logs
- Show residual plot
- Show basic result visualization
- Explain each step in beginner-friendly language
- Run without an API key in sample mode
- Optional LLM mode using OpenAI API or local Ollama

**Out of scope for MVP:**
- Arbitrary CAD import
- snappyHexMesh automation
- High-Reynolds-number validation
- Industrial accuracy claims
- Remote compute clusters
- Unrestricted shell access

---

## Tech Stack

```
Frontend:
  Tauri + React + TypeScript

Backend:
  Python FastAPI

CFD:
  Native OpenFOAM on Ubuntu (MVP)
  Docker runner (later, for Windows support)
  WSL runner (later)

LLM:
  Ollama (local, primary target)
  OpenAI API (optional)
  MockProvider (sample mode, no API key required)

Agent:
  Claude Code (commander)
  Codex via MCP (worker)

Visualization:
  Residual plots from logs (MVP)
  PNG outputs from post-processing
  PyVista / ParaView (later)
```

---

## Repository Structure

```
easycfd/
  AGENTS.md
  CLAUDE.md
  README.md
  PROJECT_BRIEF.md
  easycfd_project_brief.json
  .claude/
    settings.json           # MCP サーバー設定
  mcp/
    codex_worker/
      server.py             # MCPサーバー本体
      handlers.py           # タスクハンドラー
      validator.py          # 出力の安全性検証
      requirements.txt
  apps/
    desktop/                # Tauri + React app
  backend/
    easycfd_core/
      __init__.py
      api/
      cfd/
      llm/
      validation/
      visualization/
    tests/
  templates/
    cavity_2d/
    channel_2d/
  examples/
    prompts/
    cases/
  docs/
    architecture.md
    research-plan.md
    user-study.md
  scripts/
    dev.sh
    check_openfoam.sh
  logs/                     # エージェントの実行ログ
  runs/                     # OpenFOAM ワークスペース
```

---

## Key Abstractions

### OpenFOAMRunner

```python
class OpenFOAMRunner:
    def run_command(self, case_dir: str, command: str) -> dict:
        raise NotImplementedError

class NativeLinuxRunner(OpenFOAMRunner): ...
class DockerRunner(OpenFOAMRunner): ...   # Windows対応用
class WSLRunner(OpenFOAMRunner): ...      # Windows対応用
```

### LLMProvider

```python
class LLMProvider:
    def generate_case_plan(self, user_prompt: str) -> dict:
        raise NotImplementedError
    def explain_log(self, log_text: str) -> str:
        raise NotImplementedError

class MockProvider(LLMProvider): ...      # APIキー不要モード
class OpenAIProvider(LLMProvider): ...
class OllamaProvider(LLMProvider): ...    # ローカルLLM
```

### Case Plan Schema

```json
{
  "case_type": "cavity_2d",
  "physics": {
    "flow": "incompressible",
    "state": "transient",
    "turbulence": "laminar"
  },
  "solver": "icoFoam",
  "geometry": { "width": 1.0, "height": 1.0, "depth": 0.1 },
  "mesh": { "nx": 20, "ny": 20, "nz": 1 },
  "fluid": { "kinematic_viscosity": 0.01 },
  "boundary_conditions": {
    "movingWall": { "U": [1.0, 0.0, 0.0], "p": "zeroGradient" },
    "fixedWalls": { "U": "noSlip", "p": "zeroGradient" },
    "frontAndBack": { "type": "empty" }
  },
  "commands": [
    {"name": "blockMesh"},
    {"name": "checkMesh"},
    {"name": "icoFoam"}
  ]
}
```

---

## Safety Constraints

**Mandatory. Never bypass.**

```python
ALLOWED_COMMANDS = {
    "blockMesh",
    "checkMesh",
    "icoFoam",
    "simpleFoam",
    "postProcess"
}

FORBIDDEN_PATTERNS = [
    "rm", "mv", "chmod", "chown",
    "curl", "wget", "sudo", "python -c",
    ";", "&&", "|", ".."
]
```

- All case generation happens inside `./runs/` or `~/.easycfd/workspaces/`
- Never write outside the configured workspace
- Never trust LLM output — always validate against schema and safety rules
- Never execute arbitrary shell strings
- Never commit secrets

---

## Milestones

### Milestone 0: Repository Bootstrap
- Repo structure, README, AGENTS.md, CLAUDE.md
- `.gitignore`, `.env.example`
- Python package layout, test setup
- **MCP サーバーの基本構造を作成**

### Milestone 1: MCP Codex Worker
- MCPサーバー本体（server.py）の実装
- タスクハンドラーの実装
- Codex出力の安全性検証（validator.py）
- Claude Code から Codex への委任フローのテスト

### Milestone 2: OpenFOAM Runner
- NativeLinuxRunner
- Command whitelist
- Workspace path validation
- Subprocess execution with stdout/stderr capture
- Safety tests

### Milestone 3: Template-based Case Generation
- cavity_2d template
- Dictionary file renderer
- system/, constant/, 0/ directory generation
- Parameter validation

### Milestone 4: Solver Run and Residual Parsing
- Run icoFoam / simpleFoam
- Stream and save logs
- Parse residual history
- Return structured residual data

### Milestone 5: Minimal GUI
- Tauri + React setup
- Case selection screen
- Run button, log panel, residual chart

### Milestone 6: LLM Structured Planning
- MockProvider, OpenAIProvider, OllamaProvider
- JSON schema validation
- Provider settings UI

### Milestone 7: Beginner Explanations
- Solver explanation
- Boundary condition explanation
- Command and error explanation
- Residual plot explanation

---

## First Agent Task

```
Claude Code への最初の指示:

PROJECT_BRIEF.md と AGENTS.md を読んでください。
Milestone 0 と Milestone 1 を実行してください。

具体的には:
1. リポジトリのscaffoldを作成する
2. mcp/codex_worker/server.py を実装する
   - CodexをMCPツールとして登録する
   - タスクを受け取ってCodexに投げる
   - 出力を検証して返す
3. .claude/settings.json にMCPサーバーを登録する
4. backend/easycfd_core/validation/safety.py の実装は
   Codex MCP Worker に委任する
5. テストを実行して確認する

セキュリティクリティカルなコードは自分で実装し、
ボイラープレートはCodexに委任すること。
```

---

## Coding Style

- Simple and readable over clever abstractions
- Python type hints everywhere
- Pydantic for all schemas
- Validate external inputs aggressively
- Tests required for all safety-critical behavior
- Keep OpenFOAM logic isolated from GUI code
- Never let frontend code directly execute shell commands
- Version LLM prompts and schemas in files

---

## Security Reminders

- Do not commit secrets
- Do not expose API keys in logs
- Do not trust LLM output
- Do not run arbitrary shell strings
- Do not allow writes outside the workspace
- Do not claim CFD accuracy without validation
