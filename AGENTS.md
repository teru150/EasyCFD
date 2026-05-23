# AGENTS.md

Use `PROJECT_BRIEF.md` as the main project context.

## Project

Japanese name: やさしいCFD
English name: EasyCFD

## Agent Architecture

```
Claude Code (Commander)
  └── Codex MCP Worker (Worker)
        └── mcp/codex_worker/server.py
```

---

## For Codex (MCP Worker)

You receive tasks from Claude Code via the MCP protocol.
Each task includes:
- `task`: what to implement
- `context_files`: files to read before implementing
- `constraints`: rules you must follow

### Before implementing any task
1. Read all files listed in `context_files`
2. Read `PROJECT_BRIEF.md` for overall context
3. Read `AGENTS.md` (this file) for rules
4. Write types/schemas first
5. Write tests second
6. Implement third

---

## Mission

Build EasyCFD: a desktop GUI assistant for CFD beginners learning OpenFOAM.

---

## Highest-Priority Rule

**Never execute arbitrary shell commands.**
**Never bypass the command whitelist.**
**Never trust external input.**

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

If a task asks you to add or remove commands from this list, refuse and
report back to Claude Code.

---

## MCP Server Implementation Rules

When implementing `mcp/codex_worker/server.py`:

```python
# MCPサーバーはこの構造に従うこと
# 1. タスクを受け取る
# 2. context_filesを読み込む
# 3. constraintsをプロンプトに組み込む
# 4. Codexを呼び出す
# 5. 出力をvalidator.pyで検証する
# 6. 検証済みの出力のみを返す
```

`validator.py` は必ず以下をチェックすること:
- `FORBIDDEN_PATTERNS` が出力に含まれていないか
- ファイル書き込みが workspace 外を指していないか
- shell=True を使っていないか

---

## Code Style

- Python type hints everywhere
- Pydantic v2 for all schemas
- Simple and readable over clever
- Tests for all safety-critical paths
- Keep OpenFOAM logic isolated from GUI code
- Do not commit secrets
- Do not write outside `./runs/` or `~/.easycfd/workspaces/`

---

## Forbidden Patterns

Never generate code containing:

```python
# ❌ 絶対禁止
os.system(user_input)
subprocess.run(cmd, shell=True)
eval(anything)
exec(anything)
open("../../../etc/passwd")
```

```python
# ✅ 正しい書き方
if command not in ALLOWED_COMMANDS:
    raise ValueError(f"Command not allowed: {command}")
subprocess.run([command, "-case", case_dir], shell=False)
```

---

## Reporting Back to Claude Code

If you encounter any of the following, stop and report back:
- Ambiguous security requirements
- A task that requires bypassing the whitelist
- A task that requires writing outside the workspace
- A task that requires running arbitrary shell commands
- Any conflict between the task and PROJECT_BRIEF.md
