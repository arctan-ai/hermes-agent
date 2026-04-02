# 💰 Stop Wasting Tokens: AI Memory Setup for Arctan

> **10 minutes of setup. Save 60-80% on Claude context costs. Covers every tool we use.**

---

## Why You Should Care

Every time you open a new Claude session on `arctan-client` or `inference-server`, Claude starts from scratch. It doesn't know it's a Tauri app. It doesn't know the audio pipeline goes `cpal → DeepFilterNet → Beatrice → cpal`. It doesn't know we use Jotai for state management or that `beatrice.lib` is a closed-source MSVC static lib.

So it re-reads files, re-discovers all of this, and charges you tokens for the privilege:

```
Monday morning:  "This is a Tauri v2 app with Rust backend..."   50,000 tokens
Monday afternoon: same thing                                      50,000 tokens
Tuesday morning:  same thing again                                50,000 tokens
```

Over a month, that's **~$55-165 per person** burned on Claude re-learning what it already knew yesterday.

The fix: persistent context files that every tool reads automatically. One-time setup, works forever.

---

## Start Here: The Shared Context File (Everyone, 5 minutes)

Before doing anything tool-specific, do this. It benefits everyone regardless of which tool they use.

### AGENTS.md — One File, Every Tool Reads It

`AGENTS.md` is a convention supported by **Claude Code, OpenCode, Zed, and Copilot**. Put it in a repo root, and every AI tool automatically includes it as context.

**arctan-client already has one.** Here's what it looks like:

```markdown
# AGENTS.md

## Project Overview
Arctan (beatrice-client) is a real-time voice changer desktop app built 
with Tauri v2 (Rust backend + React/TypeScript frontend). The audio 
pipeline chains DeepFilterNet noise cancellation with a closed-source 
Beatrice inference library for neural voice conversion. Windows-only.

## Repository Structure
beatrice-client/             # Cargo workspace root
├── beatrice_lib/            # Rust FFI wrapper around beatrice.lib
├── beatrice-client/
│   ├── src/                 # React frontend (Vite, Tailwind v4, Jotai)
│   ├── src-tauri/src/       # Tauri Rust backend (~21 modules)
│   └── package.json
├── models/                  # Voice models + gender classifier ONNX
├── dependencies/            # onnxruntime.dll
└── scripts/                 # Build/release scripts (PowerShell)

## Build Commands
yarn install
yarn tauri dev      # Development mode
yarn tauri build    # Production build (needs code signing)

## Code Conventions
- Optimize for readability — clear names, short functions, obvious flow
- Use early returns to reduce nesting
- Always handle errors explicitly
- Rust and TypeScript in this repo
```

**Check your repos.** If the one you work on doesn't have an AGENTS.md, create one now. It takes 5 minutes and saves everyone on the team thousands of tokens per day.

Here are starting points for each repo:

<details>
<summary><b>inference-server</b> — click to expand</summary>

```markdown
# AGENTS.md

## Project Overview
Python-based ML inference server for real-time voice conversion. Serves 
Beatrice voice changer models via LiveKit WebRTC integration. Supports 
CUDA, DirectML, ROCm, and CPU inference.

## Key Files
- server/voice_changer/       # Core voice conversion logic
- server/livekit_audio_processor.py  # LiveKit WebRTC audio processing
- server/webrtc/              # WebRTC utilities
- server/settings.py          # Configuration

## Requirements
- requirements-cuda.txt       # GPU (NVIDIA)
- requirements-dml.txt        # GPU (AMD/Intel on Windows)
- requirements-cpu.txt        # CPU fallback
```
</details>

<details>
<summary><b>console-gateway</b> — click to expand</summary>

```markdown
# AGENTS.md

## Project Overview
Go backend API gateway with auth middleware + Vite React frontend console.
Handles Google OAuth (arctan.ai domain), JWT tokens, and proxies requests 
to internal services.

## Structure
server/              # Go API gateway (port 8080)
  internal/auth/     # Authentication service
  internal/gateway/  # API gateway logic
  internal/middleware/ # Auth middleware
client/              # Vite React frontend (port 5173)
  src/components/    # React components
  src/contexts/      # Auth context
  src/services/      # API service layer

## Key Endpoints
GET  /api/auth/google          # Initiate Google OAuth
GET  /api/auth/google/callback # OAuth callback
POST /api/auth/refresh         # Refresh JWT
GET  /api/user/profile         # Get user profile (protected)
*    /api/services/*           # Proxy to internal services (protected)

## Environment
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, JWT_SECRET,
DB_SERVICE_URL (http://localhost:3020)
```
</details>

<details>
<summary><b>auth-service</b> — click to expand</summary>

```markdown
# AGENTS.md

## Project Overview
Flask + SQLAlchemy authentication microservice. User registration, login,
password reset, and user configuration management. Backed by PostgreSQL.

## Key Endpoints
POST /register_v2     # Register (DB)
POST /login_v3        # Login with user config (DB)
POST /reset_password  # Password reset
POST /get_server_url  # Get user's server URL

## Stack
Python, Flask, SQLAlchemy, PostgreSQL, Gunicorn (production)
```
</details>

<details>
<summary><b>db-service</b> — click to expand</summary>

```markdown
# AGENTS.md

## Project Overview
Database lifecycle management service. Handles schema migrations via 
Alembic and provides APIs for database operations.

## Structure
apis/        # API endpoints
models/      # SQLAlchemy models
alembic/     # Migration scripts
scripts/     # Utility scripts

## Stack
Python, Alembic, PostgreSQL
NOTE: Default branch is 'master' (not 'main')
```
</details>

<details>
<summary><b>logging-service</b> — click to expand</summary>

```markdown
# AGENTS.md

## Project Overview
Metrics collection and user activity tracking service. Receives telemetry
from clients and writes to PostgreSQL, which syncs to ClickHouse via PeerDB.

## Key Tables (via ClickHouse)
- metrics: model_latency, ping, cpu, ram, volume, packets, jitter (88M+ rows)
- user_activities: activity_type, timestamp, activity_data (27M+ rows)

## Important
- Timestamps are Unix MILLISECONDS (divide by 1000 for DateTime)
- Filter _peerdb_is_deleted = 0 for active records

## Stack
Python, PostgreSQL → PeerDB CDC → ClickHouse
```
</details>

<details>
<summary><b>audio-driver</b> — click to expand</summary>

```markdown
# AGENTS.md

## Project Overview
Windows WDM virtual audio driver (C++). Exposes speaker + microphone 
endpoints. Uses WaveRT for rendering. Code signing required via EV 
certificate + Microsoft Hardware Dashboard submission.

## Known Caveats
- Code 10 errors from stale adapter instances (m_AdapterInstances left non-zero)
- Ring buffer size: 2 seconds at 48kHz (was 16.9GB due to constant misuse)
- 48kHz only — no runtime format negotiation
- Build requires Windows SDK + WDK

## Build
See BUILD.md. CI builds, then sign locally on Windows with EV cert.
```
</details>

<details>
<summary><b>livekit-gateway</b> — click to expand</summary>

```markdown
# AGENTS.md

## Project Overview
Go-based WebRTC media server gateway using LiveKit. Manages real-time 
audio streams between clients and inference servers.

## Key Files
- server.go             # Main server
- livekit-server/       # LiveKit server binary + config
- livekit-token-server/ # Token generation for client auth

## Stack
Go, LiveKit, Docker Compose
```
</details>

<details>
<summary><b>client-dashboard</b> — click to expand</summary>

```markdown
# AGENTS.md

## Project Overview
Admin panel for managing clients. React Router v7 (SPA) frontend + 
FastAPI backend + PostgreSQL.

## Structure
client/                    # React frontend (port 5173 dev)
client-dashboard-server/   # FastAPI backend (port 8181)

## Deployment
Docker Compose. Supports on-prem (with local Postgres) and cloud modes.
```
</details>

### Commit it

```bash
git add AGENTS.md
git commit -m "docs: add AGENTS.md for AI context"
git push
```

When your teammates pull, they get it too. Every AI tool reads it automatically.

---

## Now Set Up Your Specific Tool

Jump to your section:

| Tool | Section |
|------|---------|
| VS Code + Copilot | [Section 1](#1-vs-code--github-copilot) |
| Claude Code (iTerm2) | [Section 2](#2-claude-code-iterm2) |
| OpenCode (Ghostty) | [Section 3](#3-opencode-ghostty) |
| Zed | [Section 4](#4-zed-editor) |

---

## 1. VS Code + GitHub Copilot

You're using VS Code with Copilot and Claude as the model. Here's how to stop Copilot from wasting your tokens.

### a) Enable Copilot Memory (2 minutes)

Copilot now remembers your preferences across sessions. Turn it on:

1. Go to **github.com** → **Settings** → **Copilot** → **Features**
2. Toggle **Memory** on
3. Done

Now when you tell Copilot things like these, it remembers permanently:
- "In Arctan repos, we use Jotai for state management, not Redux"
- "Our Rust code uses early returns and explicit error handling"
- "The beatrice_lib crate is an FFI wrapper — never modify the C header directly"

### b) Create a Copilot Instructions File (5 minutes)

Create `.github/copilot-instructions.md` in your repo root. Here's one for arctan-client:

```markdown
# Copilot Instructions — arctan-client

## Project
Real-time voice changer desktop app. Tauri v2 (Rust backend, React/TS frontend).
Audio pipeline: cpal → DeepFilterNet (noise cancellation) → Beatrice (voice conversion) → cpal.
Windows-only. The Beatrice library is closed-source (MSVC static lib).

## Rust Conventions
- Edition 2024, resolver 3
- Use early returns and guard clauses
- Handle all errors explicitly (no unwrap in production code)
- Ring buffers are in Source/Utilities/ (C++ driver) and deep_filter.rs (Rust)
- beatrice_lib/ is FFI only — changes require matching C header updates

## TypeScript/React Conventions
- Jotai for state management (not Redux, not Context API)
- Tailwind v4 for styling
- shadcn/ui for components
- Functional components only, prefer named exports

## Build
- `yarn tauri dev` for development
- `yarn tauri build` for production (requires code signing on Windows)
- Dependencies downloaded via scripts/download-dependencies.ps1
```

Create similar files for whichever repos you work in most.

### c) Scoped Instructions (optional)

For different file types, create files in `.github/instructions/`:

```
.github/instructions/
  rust.md          ← loads only when editing .rs files
  react.md         ← loads only when editing .tsx/.jsx files
  tauri-config.md  ← loads only when editing tauri.conf.json
```

Each file has a front matter with a glob pattern:
```markdown
---
applyTo: "**/*.rs"
---
Use early returns. Handle errors with ? operator. No unwrap() in prod code.
```

### Token Savings Summary (VS Code)

| Action | Effort | Savings |
|--------|--------|---------|
| Enable Copilot Memory | 2 min | Remembers preferences forever |
| Create copilot-instructions.md | 5 min | ~40% less context re-reading |
| Add AGENTS.md to repo | 5 min | ~60% less project discovery |
| Use `@file` instead of pasting | Habit | Avoids sending duplicate content |
| Start new chats for new topics | Habit | Prevents ballooning history |

---

## 2. Claude Code (iTerm2)

You're using Claude Code in iTerm2 with your Anthropic API key. Claude Code has the best built-in memory system — you're probably just not using it.

### a) Create Your Global CLAUDE.md (2 minutes)

This is read in every project, every session:

```bash
mkdir -p ~/.claude
cat > ~/.claude/CLAUDE.md << 'EOF'
# Global Preferences — Arctan

## About Me
- I work at Arctan on real-time voice processing
- My timezone is IST

## Coding Style
- Concise responses with code examples
- Early returns and guard clauses
- Always handle errors explicitly
- Prefer showing diffs over full file rewrites

## Arctan Stack
- Desktop client: Tauri v2 (Rust + React/TypeScript)
- Audio: cpal → DeepFilterNet → Beatrice (closed-source C/C++ lib)
- Backend: Python (Flask, FastAPI), Go (gateway, LiveKit)
- DB: PostgreSQL → PeerDB CDC → ClickHouse (analytics)
- Infrastructure: AWS ECS (ap-south-1), Docker, nginx
- Project management: Plane (app.plane.so/arctan)

## Key Repos
- arctan-client: Desktop app (Rust/Tauri, main branch)
- inference-server: ML voice changer (Python, main branch)
- console-gateway: API gateway (Go + React, main branch)
- db-service: DB migrations (Python/Alembic, MASTER branch — not main!)
- infra-service: Docker configs (MASTER branch — not main!)
- audio-driver: Windows WDM driver (C++, main branch)
EOF
```

Now every Claude Code session starts with this context — 400 tokens instead of 50,000 tokens of Claude reading random files.

### b) Use /memory (2 seconds per session, massive savings)

At the end of each significant work session, type:

```
/memory
```

Claude saves key observations about the project to a `CLAUDE.md` in the project root. Next session, it picks up where you left off.

**Example of what /memory saves:**
```
## Session Notes
- The crackling in deep_filter.rs is caused by spin-wait polling with 
  sleep() at line 97. Windows thread::sleep has ~15ms granularity, 
  causing ring buffer underruns.
- Fix approach: event-based wake-up instead of polling. See PR #47.
- Tests passing on Build 22631 with 48kHz @ 480 hop size.
```

Next session, Claude already knows all of this. No re-explaining needed.

### c) Install claude-mem (Optional — 5 minutes)

For fully automatic memory (no need to remember to run /memory):

```
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

Restart Claude Code. Now it automatically:
- Captures everything you work on
- Compresses it into compact summaries
- Injects only relevant context in future sessions
- Provides a web dashboard at http://localhost:37777

**Start with CLAUDE.md + /memory.** Add claude-mem later if you want zero-effort memory.

### d) Use /compact and Haiku

When a conversation gets long (20+ back-and-forth), type `/compact` to summarize the history and free up context space.

For quick questions that don't need the expensive model:
```bash
claude --model claude-3-5-haiku "What's the syntax for Tauri v2 command handlers?"
```

Haiku costs 1/30th of Opus. Use it for simple lookups.

### Token Savings Summary (Claude Code)

| Action | Effort | Savings |
|--------|--------|---------|
| Create ~/.claude/CLAUDE.md | 2 min | ~70% less context per session |
| Run /memory after sessions | 2 sec | Preserves session knowledge |
| Add AGENTS.md to repo | 5 min | ~60% less project discovery |
| Use /compact on long chats | 2 sec | Prevents context overflow |
| Use Haiku for quick questions | Habit | 30x cheaper per query |
| Install claude-mem | 5 min | ~80% total reduction |

---

## 3. OpenCode (Ghostty)

You're using OpenCode in Ghostty with your Anthropic API key. OpenCode's killer feature for cost savings is its configurable summarizer model.

### a) Create Your Global Context (2 minutes)

```bash
mkdir -p ~/.config/opencode
cat > ~/.config/opencode/context.md << 'EOF'
# Arctan Context

## About Me
- I work at Arctan on real-time voice processing
- Prefer concise, tested code with explicit error handling

## Stack Overview
- Desktop: Tauri v2 (Rust + React/TS), Windows-only
- Audio: cpal → DeepFilterNet → Beatrice → cpal
- Backend: Python (Flask/FastAPI), Go (gateways)
- Data: PostgreSQL → PeerDB → ClickHouse
- Infra: AWS ECS ap-south-1, Docker
- PM: Plane (app.plane.so/arctan)

## Repos (all arctan-ai GitHub org)
arctan-client (Rust/Tauri), inference-server (Python/CUDA),
console-gateway (Go), auth-service (Flask), db-service (Alembic),
logging-service (Python), audio-driver (C++ WDM), livekit-gateway (Go),
client-dashboard (React/FastAPI), infra-service (Docker/Shell)

NOTE: db-service and infra-service use 'master' branch, not 'main'.
EOF
```

### b) Set Up a Cheap Summarizer (2 minutes — biggest cost saver)

When your conversation gets long, OpenCode needs to summarize old messages to fit the context window. By default it uses your primary (expensive) model. Switch to Haiku:

```toml
# opencode.toml (in your project root or ~/.config/opencode/config.toml)

[provider.anthropic]
api_key = "sk-ant-..."    # or use ANTHROPIC_API_KEY env var

[model.default]
provider = "anthropic"
model = "claude-sonnet-4-20250514"

[model.summarizer]
provider = "anthropic"
model = "claude-3-5-haiku-20241022"
max_tokens = 4000
```

This alone saves 5-10x on long sessions. Haiku costs $0.25/M input vs Sonnet's $3/M.

### c) Load Extra Context Files

If you want OpenCode to always read specific docs:

```toml
[context]
files = [
  "./docs/audio-pipeline-analysis.md",
  "./CONVENTIONS.md"
]
```

OpenCode also reads `AGENTS.md` files automatically — so if you've added those to your repos, you're already covered.

### Token Savings Summary (OpenCode)

| Action | Effort | Savings |
|--------|--------|---------|
| Create global context.md | 2 min | ~70% less context per session |
| Set Haiku as summarizer | 2 min | 5-10x cheaper on long sessions |
| Add AGENTS.md to repo | 5 min | ~60% less project discovery |
| Use /compact | 2 sec | Shrinks bloated conversations |
| Use --prompt for one-shots | Habit | Avoids session overhead |

---

## 4. Zed Editor

You're using Zed with the built-in AI assistant and your Anthropic API key. The single biggest token saver here is tab context control.

### a) Fix Tab Context (1 minute — biggest saver)

By default, Zed sends the content of **every open tab** to Claude with every message. If you have 15 files open, that's 15 files × ~500 lines = massive token waste.

Fix it now:

Open Zed settings (`Cmd+,` or `~/.config/zed/settings.json`) and add:

```json
{
  "assistant": {
    "context": {
      "tabs": "pinned",
      "rules": true
    }
  }
}
```

Now Zed only sends tabs you explicitly pin. Pin the 2-3 files relevant to your current task, not your entire workspace.

### b) Create Global Rules (2 minutes)

```bash
cat > ~/.config/zed/rules.md << 'EOF'
# Arctan AI Rules

## Style
- Concise, practical answers with code examples
- Early returns and guard clauses
- Handle errors explicitly — no silent failures
- Follow existing patterns in the file

## Stack Knowledge
- Arctan: real-time voice changer (Tauri v2, Rust + React)
- Audio pipeline: cpal → DeepFilterNet → Beatrice → cpal
- Beatrice is a closed-source C/C++ library (MSVC static lib)
- Backend: Python (Flask/FastAPI), Go (gateways/LiveKit)
- DB: PostgreSQL → PeerDB CDC → ClickHouse
- AWS ECS in ap-south-1

## Important
- db-service and infra-service use 'master' branch, not 'main'
- Audio driver is C++ WDM (Windows Driver Kit required)
- Desktop client is Windows-only
EOF
```

### c) Create Project Rules

For repos you work in frequently, add `.zed/rules.md`:

```bash
# In arctan-client repo root:
mkdir -p .zed
cat > .zed/rules.md << 'EOF'
# arctan-client Rules

- This is a Tauri v2 app: Rust backend (src-tauri/) + React frontend (src/)
- Audio pipeline: cpal input → DeepFilterNet → Beatrice → cpal output
- beatrice_lib/ is FFI to closed-source C lib — don't modify headers without matching C changes
- State management: Jotai (not Redux)
- Styling: Tailwind v4 + shadcn/ui
- Build: yarn tauri dev (dev), yarn tauri build (prod, needs signing)
- Known issue: crackling from spin-wait polling in deep_filter.rs
EOF
```

### d) Use @thread for Continuity

Zed doesn't have persistent memory yet (it's coming — [GitHub issue #25282](https://github.com/zed-industries/zed/issues/25282)). Workaround: type `@thread` in the chat to search and include previous threads as context.

### Token Savings Summary (Zed)

| Action | Effort | Savings |
|--------|--------|---------|
| Set tabs to "pinned" | 1 min | 50-80% less tab context waste |
| Create global rules.md | 2 min | ~70% less per-session context |
| Create project .zed/rules.md | 5 min | Project-specific context |
| Add AGENTS.md to repo | 5 min | ~60% less project discovery |
| Use @file instead of open tabs | Habit | Targeted context only |
| Start new threads per topic | Habit | Prevents history bloat |

---

## Quick Reference: What File Goes Where

| File | Tool(s) That Read It | Commit to Git? |
|------|---------------------|---------------|
| `AGENTS.md` | Claude Code, OpenCode, Zed, Copilot | ✅ Yes — shared |
| `CLAUDE.md` | Claude Code | ⚠️ Project root yes, ~/.claude/ no |
| `.github/copilot-instructions.md` | VS Code Copilot | ✅ Yes — shared |
| `.zed/rules.md` | Zed | ✅ Yes — shared |
| `.opencode/context.md` | OpenCode | ✅ Yes — shared |
| `~/.claude/CLAUDE.md` | Claude Code | ❌ Personal |
| `~/.config/zed/rules.md` | Zed | ❌ Personal |
| `~/.config/opencode/context.md` | OpenCode | ❌ Personal |

**Rule:** Shared project knowledge → commit to repo. Personal preferences → home directory.

---

## How Much This Actually Saves

### Per Person Per Month

| What you do | Context tokens/session | Monthly context cost |
|-------------|----------------------|---------------------|
| Nothing (status quo) | ~50,000 | $55-165 |
| Add AGENTS.md to repos | ~15,000 | $17-50 |
| + personal config files | ~5,000 | $6-17 |
| + claude-mem or /memory habit | ~2,000 | $2-7 |

### Across Our 12-Person Team

| Scenario | Monthly | Annually |
|----------|---------|----------|
| No optimization | $660-1,980 | $7,900-23,800 |
| Full setup | $24-84 | $290-1,010 |
| **Savings** | **$636-1,896** | **$6,900-22,700** |

---

## Action Items

### Today (5 minutes)
- [ ] Add AGENTS.md to any repo you work on that doesn't have one yet (use the templates above)
- [ ] Create your personal global config file (see your tool's section)

### This Week
- [ ] **VS Code users:** Enable Copilot Memory in GitHub Settings → Copilot → Features
- [ ] **Claude Code users:** Start running `/memory` at the end of each session
- [ ] **OpenCode users:** Add the cheap Haiku summarizer to your config
- [ ] **Zed users:** Change tab context to `"pinned"` in settings

### Optional (maximum savings)
- [ ] Claude Code users: Install claude-mem plugin
- [ ] Add `.github/copilot-instructions.md` to repos with VS Code users
- [ ] Add `.zed/rules.md` to repos with Zed users

---

*Questions? Ask Hermes at [chat.getarctan.com](https://chat.getarctan.com) or DM @hermesbot on Slack.*

*"How do I set up claude-mem?" — Hermes can walk you through it step by step.*
