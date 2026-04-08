# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 세션 시작 시

- `WORKPLAN_OFFCODE_PHASE1.md`를 먼저 읽고 현재 진행 상태를 파악한 후 시작
- "정리해" 또는 "기록해" → `cleanup` 스킬 실행 (히스토리 기록, 아카이브, git 관리, 문서 통합)

## Gist 소통 채널

- **URL**: https://gist.github.com/imejaim/75d56fbe2b712b35f593d5965da67b9b
- **용도**: 사내 환경(윈도우/리눅스)과 VDI 간 디버깅 소통 채널
- **소통 규칙**:
  1. gist 문서 본문 = 현재 상태 요약 (맨 위에 번호붙인 한줄 상태, 아래에 상세 내용)
  2. 코부장이 회장님에게 할 일을 **댓글**로 요청
  3. 회장님이 결과를 **댓글**로 회신
  4. 코부장이 결과를 분석 → **문서 본문에 통합 정리** + 다음 할 일을 **댓글**로 요청
  5. 반복하여 디버깅 완료까지 진행
- **명령**: "gist 확인해" → gist 댓글 확인 후 분석 및 문서 업데이트

## Workspace Overview

This workspace contains development clones of two related open-source projects (plus their zip archives and a `memo.txt` with upstream GitHub URLs):

| Directory | Project | Upstream |
|-----------|---------|----------|
| `opencode-dev/` | **OpenCode** — open-source AI coding agent (TUI + web + desktop) | `anomalyco/opencode` |
| `oh-my-openagent-dev/` | **oh-my-opencode (OmO)** — OpenCode plugin for multi-agent orchestration | `code-yeongyu/oh-my-openagent` |

OmO is a plugin **for** OpenCode. It adds agents (Sisyphus, Hephaestus, Prometheus, etc.), 52 lifecycle hooks, 26 tools, skill/command/MCP systems, and Claude Code compatibility.

## Build & Development

Both projects use **Bun only** (1.3+). Never use npm/yarn.

### OpenCode (`opencode-dev/`)

```bash
bun install                              # install deps (from repo root)
bun dev                                  # run TUI (equivalent to `opencode`)
bun dev <directory>                      # run TUI against a specific dir
bun dev serve                            # headless API server (port 4096)
bun dev web                              # server + web interface
bun run --cwd packages/app dev           # web app dev server
bun run --cwd packages/desktop tauri dev # native desktop app (requires Rust)
```

**Default branch is `dev`**, not `main`. Use `dev` or `origin/dev` for diffs.

### oh-my-opencode (`oh-my-openagent-dev/`)

```bash
bun install           # install deps
bun run build         # ESM + declarations + JSON schema
bun run typecheck     # tsc --noEmit
bun test              # bun test suite
bun run build:schema  # rebuild config schema only
bun run clean         # rm -rf dist
```

Test local plugin in OpenCode by pointing `opencode.json` plugin entry to `file:///absolute/path/to/oh-my-opencode/dist/index.js`.

## Testing

### OpenCode

```bash
cd packages/opencode && bun test               # run tests (NEVER from repo root)
cd packages/opencode && bun test --timeout 30000
bun turbo typecheck                             # typecheck all packages (from root)
cd packages/opencode && bun run typecheck       # typecheck with tsgo
```

Tests **cannot** run from repo root — there's a guard (`do-not-run-tests-from-root`). Always `cd` into the package directory.

### oh-my-opencode

```bash
bun test                  # all tests
bun run typecheck         # tsc --noEmit
```

Tests use `bun:test`, co-located `*.test.ts` files, given/when/then style. CI splits mock-heavy tests into separate processes automatically.

## Architecture

### OpenCode — Monorepo (Turborepo + Bun workspaces)

Key packages:
- `packages/opencode` — core business logic, server, TUI (SolidJS + opentui)
- `packages/app` — shared web UI (SolidJS)
- `packages/desktop` — Tauri native desktop wrapper
- `packages/desktop-electron` — Electron desktop variant
- `packages/console` — admin console (app + core with Drizzle DB migrations)
- `packages/plugin` — `@opencode-ai/plugin` SDK
- `packages/sdk` — generated SDK (regenerate with `./packages/sdk/js/script/build.ts`)

OpenCode core uses **Effect** heavily. Key patterns:
- `Effect.gen(function* () { ... })` for composition
- `Effect.fn("Domain.method")` for named/traced effects
- `Schema.TaggedErrorClass` for typed errors
- `makeRuntime` for services, `InstanceState` for per-directory state
- Drizzle schema in `src/**/*.sql.ts`, migrations via `bun drizzle-kit`

### oh-my-opencode — Plugin architecture

Entry: `src/index.ts` → `loadPluginConfig()` → `createManagers()` → `createTools()` → `createHooks()` → `createPluginInterface()`

Key directories:
- `src/agents/` — 11 agent definitions (factory pattern: `createXXXAgent`)
- `src/hooks/` — 52 lifecycle hooks (3 tiers: Core + Continuation + Skill)
- `src/tools/` — 26 tools (factory pattern: `createXXXTool`)
- `src/features/` — 19 feature modules (background-agent, skill-loader, tmux, etc.)
- `src/config/` — Zod v4 schema system, JSONC config
- `src/mcp/` — 3 built-in remote MCPs (websearch/Exa, context7, grep_app)
- `src/cli/` — Commander.js CLI (install, doctor, run)

Config: JSONC with multi-level merge (project → user → defaults), snake_case keys.

## Style Guide (shared across both projects)

- **No `any`**, no `@ts-ignore`, no `@ts-expect-error`
- **No `try`/`catch`** where avoidable; prefer `.catch(...)` or Effect error handling
- **No `else`** — use early returns
- **No unnecessary destructuring** — use dot notation
- **`const` over `let`** — use ternaries or early returns instead of reassignment
- **Single-word names** preferred for variables/functions; multi-word only when needed for clarity
- **Inline** values used only once (no intermediate variables)
- **Bun APIs** preferred (`Bun.file()`, etc.)
- Rely on **type inference**; avoid explicit annotations unless required for exports
- Functional array methods (`flatMap`, `filter`, `map`) over `for` loops

### OpenCode-specific

- Drizzle schema: snake_case field names (no column name strings needed)
- PR titles: conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`) with optional scope

### oh-my-opencode-specific

- File/directory naming: kebab-case
- Module structure: `index.ts` barrel exports, no catch-all files (`utils.ts`, `helpers.ts` banned)
- 200 LOC soft limit per file
- Relative imports within module, barrel imports across modules
- No path aliases (`@/`) — relative imports only
- Dual package: `oh-my-opencode` + `oh-my-openagent` published simultaneously
- Logger writes to `/tmp/oh-my-opencode.log`
- Never commit unless explicitly requested; never run `bun publish` directly
