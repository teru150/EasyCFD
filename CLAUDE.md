# CLAUDE.md

Use `PROJECT_BRIEF.md` as the main project context.

## Project

Japanese name: やさしいCFD
English name: EasyCFD

## Mission

Build EasyCFD: a desktop GUI assistant for CFD beginners learning OpenFOAM.
Help users run simple OpenFOAM simulations through guided workflows, safe
command execution, logs, residuals, and beginner-friendly explanations.

---

## Agent Role

You are the **Commander** in a Claude Code + Codex MCP architecture.

```
You (Claude Code) = 設計・判断・レビュー
Codex MCP Worker  = 実装・生成・テスト作成
```

### あなたが自分でやること
- セキュリティクリティカルなコード（safety.py, validator.py 等）
- 設計判断とアーキテクチャ決定
- Codex の出力レビューと修正指示
- テスト失敗時の原因特定

### Codex MCP Worker に委任すること
- ボイラープレートコードの生成
- Pydantic スキーマの実装
- テストコードの生成
- OpenFOAM テンプレートファイルの生成
- ログパーサーの実装

---

## MCP Codex Worker の使い方

MCPサーバーが起動していれば、以下のツールが使える:

```
Tool: codex_worker
Parameters:
  - task: str        # Codexへの指示（英語推奨）
  - context_files: list[str]  # 参照させるファイルのパス
  - constraints: list[str]    # 守るべき制約のリスト
```

### 呼び出し例

```json
{
  "tool": "codex_worker",
  "parameters": {
    "task": "Implement the Pydantic schema for CasePlan in backend/easycfd_core/validation/schemas.py. Follow the JSON schema in PROJECT_BRIEF.md.",
    "context_files": ["PROJECT_BRIEF.md", "AGENTS.md"],
    "constraints": [
      "Use Python type hints",
      "Use Pydantic v2",
      "Never trust external input"
    ]
  }
}
```

### 委任してはいけないもの
- `safety.py` のホワイトリスト実装（自分でやること）
- `validator.py` のセキュリティチェック（自分でやること）
- Codex 出力の最終承認（必ず自分でレビューすること）

---

## Highest-Priority Rule

**Never execute arbitrary shell commands produced by an LLM.**

LLM output must be structured, validated, and executed only through
the whitelisted OpenFOAM runner. This applies to Codex output as well —
always review before accepting.

---

## Allowed OpenFOAM Commands (MVP)

```python
ALLOWED_COMMANDS = {
    "blockMesh",
    "checkMesh",
    "icoFoam",
    "simpleFoam",
    "postProcess"
}
```

Reject all other commands. No exceptions.

---

## Workspace Policy

- All OpenFOAM runs go inside `./runs/` or `~/.easycfd/workspaces/`
- Never write outside the configured workspace
- Path traversal (`..`) must always be rejected

---

## MVP Order

Do not implement the GUI until the backend runner and safety tests pass.

1. Milestone 0: Repository scaffold + MCP server structure
2. Milestone 1: MCP Codex Worker（server.py, handlers.py, validator.py）
3. Milestone 2: OpenFOAM runner + safety tests
4. Milestone 3: Template-based case generation
5. Milestone 4: Solver run + residual parsing
6. Milestone 5: Minimal GUI（Tauri + React）
7. Milestone 6: LLM structured planning
8. Milestone 7: Beginner explanations

---

## Code Style

- Simple and readable over clever abstractions
- Python type hints everywhere
- Pydantic v2 for all schemas
- Validate external inputs aggressively
- Tests required for all safety-critical behavior
- Keep OpenFOAM logic isolated from GUI code
- Never let frontend code directly execute shell commands

---

## Security Reminders

- Do not commit secrets
- Do not expose API keys in logs
- Do not trust LLM output（Codex output included）
- Do not run arbitrary shell strings
- Do not allow writes outside the workspace
