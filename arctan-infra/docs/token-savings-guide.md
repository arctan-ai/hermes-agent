# 💰 Arctan AI Token Savings Guide

> **Reduce org-wide Claude API costs by 60-80%. Three layers: organization, repository, developer.**

Every time someone at Arctan starts a new Claude session, Claude re-discovers the same things — it's a Tauri app, the audio pipeline is `cpal → DeepFilterNet → Beatrice → cpal`, we use Jotai not Redux, `db-service` uses `master` not `main`. Every session, every person, every day.

At ~50,000 tokens per context rebuild × 5 sessions/day × 12 people, that's **~$660-1,980/month wasted on re-learning**.

This guide has three layers of fixes. Each builds on the previous:

| Layer | Who does it | How often | Impact |
|-------|------------|-----------|--------|
| [Organization](#layer-1-organization) | Admin (once) | One-time | Sets the foundation |
| [Repository](#layer-2-repository) | Repo owner (per repo) | One-time per repo | Biggest per-token savings |
| [Developer](#layer-3-developer) | Each person | One-time + habits | Personal optimization |

**Combined savings: $6,900-22,700/year across the team.**

---

# Layer 1: Organization

*Done once by an admin. Takes 10 minutes. Benefits every person and every tool.*

## 1.1 Shared AI Assistant (Already Done ✅)

Hermes is deployed at [chat.getarctan.com](https://chat.getarctan.com) with Plane, ClickHouse, and AWS integrations. See the [Onboarding Guide](onboarding-guide.md) for details.

This eliminates tokens spent on questions like "How many active users this week?" or "What are the urgent issues in Engineering?" — Hermes answers them directly without anyone burning personal API tokens.

## 1.2 AGENTS.md Convention

We're adopting `AGENTS.md` as the standard AI context file across all Arctan repos. It's read automatically by **Claude Code, OpenCode, Zed, and GitHub Copilot** — every tool our team uses.

**Decision:** Every Arctan repo must have an `AGENTS.md` in its root. Templates for all 12 repos are in [Layer 2](#layer-2-repository).

## 1.3 Branch Naming Gotcha

Two repos use `master` instead of `main`. This trips up Claude constantly (it assumes `main`), wasting tokens on failed git operations and corrections. Every `AGENTS.md` and context file should call this out:

- `db-service` → **master**
- `infra-service` → **master**
- All other repos → **main**

---

# Layer 2: Repository

*Done once per repo by whoever owns it. Takes ~10 minutes per repo. Every developer on that repo benefits permanently.*

## What to Add Per Repo

| File | Who benefits | Priority |
|------|-------------|----------|
| `AGENTS.md` | Everyone (Claude Code, OpenCode, Zed, Copilot) | **Required** |
| `.github/copilot-instructions.md` | VS Code + Copilot users | Recommended |
| `.zed/rules.md` | Zed users | Nice to have |

`AGENTS.md` is the priority — it covers the most tools with a single file. The others are additive.

## AGENTS.md for Every Repo

Copy the one for your repo, paste it as `AGENTS.md` in the repo root, commit, push. Done.

---

### arctan-client ✅ Already exists

Current AGENTS.md covers project overview, repo structure, build commands, audio pipeline architecture, naming conventions, and error handling patterns. No action needed.

---

### arctan-client-app

```markdown
# AGENTS.md

## Project Overview
Unified repository for Arctan Client web and desktop app. TypeScript-based,
with separate web/ and desktop/ directories sharing common code.

## Structure
desktop/                    # Electron/desktop variant
web/                        # Web browser variant
docs/                       # Documentation
sample-webrtc-client.html   # WebRTC test client

## Stack
TypeScript, WebRTC
```

---

### inference-server

```markdown
# AGENTS.md

## Project Overview
Python ML inference server for real-time voice conversion. Serves Beatrice
voice changer models via LiveKit WebRTC. Supports CUDA, DirectML, ROCm, CPU.

## Structure
server/
├── voice_changer/              # Core voice conversion logic
├── livekit_audio_processor.py  # LiveKit WebRTC audio processing
├── webrtc/                     # WebRTC utilities
├── settings.py                 # Configuration
├── mods/                       # Model modules
├── restapi/                    # REST API endpoints
└── data/                       # Model data

## Platform Requirements
requirements-cuda.txt           # NVIDIA GPU
requirements-dml.txt            # AMD/Intel GPU (Windows)
requirements-rocm.txt           # AMD GPU (Linux)
requirements-cpu.txt            # CPU fallback

## Running
python server/main.py
```

---

### console-gateway

```markdown
# AGENTS.md

## Project Overview
Go backend API gateway with auth middleware + Vite React frontend console.
Google OAuth (arctan.ai domain), JWT tokens, proxies to internal services.

## Structure
server/                     # Go API gateway (port 8080)
├── internal/auth/          # Google OAuth + JWT
├── internal/gateway/       # Routing logic
├── internal/middleware/     # Auth middleware
├── main.go
client/                     # Vite React frontend (port 5173)
├── src/components/
├── src/contexts/           # Auth context
├── src/services/           # API service layer

## Key Endpoints
GET  /api/auth/google               # Initiate Google OAuth
GET  /api/auth/google/callback      # OAuth callback
POST /api/auth/refresh              # Refresh JWT
GET  /api/user/profile              # Protected — user profile
*    /api/services/*                # Protected — proxy to internal services

## Environment
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, JWT_SECRET,
DB_SERVICE_URL (http://localhost:3020)

## Development
cd server && go run main.go
cd client && npm install && npm run dev

## Important
- USE_HTTPS=false when behind nginx/Caddy (SSL termination at proxy)
- See HTTP_HTTPS_CONFIG.md and PRODUCTION_DEPLOYMENT.md
```

---

### auth-service

```markdown
# AGENTS.md

## Project Overview
Flask + SQLAlchemy authentication microservice. User registration, login,
password reset, user config management. PostgreSQL backend.

## Key Endpoints
POST /register_v2           # Register (DB)
POST /login_v3              # Login with user config (DB)
POST /reset_password        # Password reset
POST /get_server_url        # Get user's inference server URL

## Structure
main.py                     # Flask app entry
models/                     # SQLAlchemy models

## Stack
Python, Flask, SQLAlchemy, PostgreSQL, Gunicorn (prod)

## Running
python main.py (dev) | bash start.sh (prod)
```

---

### db-service

```markdown
# AGENTS.md

## Project Overview
Database lifecycle management. PostgreSQL schema migrations via Alembic,
REST APIs for DB operations.

## Structure
main.py             # Entry point
apis/               # REST endpoints
models/             # SQLAlchemy ORM models
alembic/            # Migration scripts
scripts/            # Utilities

## Stack
Python, Alembic, SQLAlchemy, PostgreSQL

## ⚠️ Default branch is 'master' (not 'main')
```

---

### logging-service

```markdown
# AGENTS.md

## Project Overview
Metrics collection and user activity tracking. Receives client telemetry,
writes to PostgreSQL, replicated to ClickHouse via PeerDB CDC for analytics.

## Key Tables (in ClickHouse)
- metrics (~88M rows): model_latency, ping, cpu, ram, cpu_app,
  ram_app_heap_usage_percent, ram_app_rss_bytes, volume, packets_received/sent/lost,
  bytes_received/sent, jitter, webrtc_stats
- user_activities (~27M rows): user_id, activity_type, timestamp, activity_data
- Users (538): id, name, email, organization_id, license_type
- Organizations (42): id, name

## ⚠️ Data Gotchas
- Timestamps are Unix MILLISECONDS → divide by 1000: toDateTime(timestamp/1000)
- Filter _peerdb_is_deleted = 0 for active records (PeerDB soft-deletes)
- ReplacingMergeTree may have dupes before merge — use FINAL for exact counts

## Key Docs
METRICS_SCHEMA_STRATEGY.md  # Why flat columns vs nested JSON
MIGRATION_GUIDE.md          # Adding new metric columns
RAM_METRICS_EXPLANATION.md  # Heap% vs RSS bytes

## Stack
Python, PostgreSQL → PeerDB CDC → ClickHouse
```

---

### audio-driver

```markdown
# AGENTS.md

## Project Overview
Windows WDM virtual audio driver (C++). Speaker + microphone endpoints via
WaveRT. Virtual device — no physical hardware. Requires code signing via EV
certificate + Microsoft Hardware Dashboard submission.

## Structure
Source/                         # C++ driver code
├── Utilities/audio_ring_buffer.cpp  # Ring buffer (performance-critical)
Package/                        # Installer files
scripts/                        # Build, sign, installer scripts

## Build & Release
1. Build: CI or Build.ps1 locally
2. Sign: SignDriver.ps1 (EV cert on Windows)
3. Submit: CreateSubmissionPackage.ps1 → Microsoft Hardware Dashboard
4. Package: BuildInstaller.ps1 with Microsoft-signed driver
See BUILD.md for full guide.

## ⚠️ Known Caveats (details in CAVEATS.md)
- Code 10 errors: m_AdapterInstances stuck non-zero from previous install
- Ring buffer was 16.9GB (!), fixed to 2s. See Optimisations.md for 50ms target.
- 48kHz only — no runtime format negotiation
- Dual-endpoint: speaker + mic share one CAdapterCommon

## Testing
See TESTING.md for pre-ship checklist.

## Stack
C++, WDK, WaveRT, Inno Setup. Requires Visual Studio + MSVC + Windows SDK.
```

---

### livekit-gateway

```markdown
# AGENTS.md

## Project Overview
Go WebRTC media server gateway using LiveKit. Real-time audio streams
between Arctan clients and inference servers.

## Structure
server.go                   # Main gateway server
livekit-server/             # LiveKit server binary + config
livekit-token-server/       # Token generation for client auth
DSCP_CONFIG.md              # QoS packet marking

## Key Scripts
manage-livekit-server.sh    # Start/stop LiveKit
add-inference-server.sh     # Register inference server
check-participants.sh       # Active room participants

## Stack
Go, LiveKit SFU, Docker Compose
```

---

### client-dashboard

```markdown
# AGENTS.md

## Project Overview
Admin panel for managing Arctan clients/organizations. React Router v7
(SPA) frontend + FastAPI backend + PostgreSQL.

## Structure
client/                         # React frontend (port 5173 dev)
client-dashboard-server/        # FastAPI backend (port 8181)

## Deployment
Docker Compose — on-prem (docker-compose.onprem.yml, includes Postgres)
or cloud (docker-compose.cloud.yml, external Postgres).

## Stack
React Router v7, TypeScript, Tailwind CSS, FastAPI, PostgreSQL
```

---

### infra-service

```markdown
# AGENTS.md

## Project Overview
Infrastructure configs and deployment scripts for Arctan self-hosted services.

## Structure
clickhouse/         # DB setup, migrations, pg-clickhouse-sync-plan.md
grafana/            # Grafana + Loki + Promtail + Prometheus (docker-compose)
metabase/           # Analytics dashboards (docker-compose)
nginx/              # Reverse proxy configs, nginx-manager.sh
peerdb/             # Postgres → ClickHouse CDC (PeerDB v0.36.9, 6 containers)
semaphore/          # Ansible automation (deployment tool)

## ⚠️ Default branch is 'master' (not 'main')
```

---

### Copilot Instructions (for repos with VS Code users)

If your repo has VS Code + Copilot users, also add `.github/copilot-instructions.md`. Example for arctan-client:

```markdown
# Copilot Instructions — arctan-client

## Project
Real-time voice changer. Tauri v2 (Rust + React/TS). Audio: cpal →
DeepFilterNet → Beatrice → cpal. Windows-only. Beatrice is closed-source.

## Rust
Edition 2024, resolver 3. Early returns, guard clauses, no unwrap() in prod.
beatrice_lib/ is FFI — C header and Rust wrapper must change together.

## TypeScript/React
Jotai for state (not Redux). Tailwind v4 + shadcn/ui. Named exports.

## Build
yarn tauri dev | yarn tauri build (needs code signing)
```

### Zed Rules (for repos with Zed users)

Add `.zed/rules.md` with a condensed version of AGENTS.md. Example:

```markdown
# arctan-client
Tauri v2: Rust (src-tauri/) + React (src/). Audio: cpal → DeepFilterNet → Beatrice.
beatrice_lib is FFI to closed-source C lib. Jotai for state. Tailwind v4 + shadcn/ui.
Known: crackling from spin-wait polling in deep_filter.rs.
```

### Scoped Copilot Instructions (optional, advanced)

For arctan-client, you can scope instructions by file type in `.github/instructions/`:

`.github/instructions/rust.md`:
```markdown
---
applyTo: "**/*.rs"
---
Early returns. Error propagation with ?. No unwrap() in production.
beatrice_lib changes require matching C header updates.
Ring buffer code is performance-critical — avoid allocations in hot paths.
```

`.github/instructions/react.md`:
```markdown
---
applyTo: "**/*.tsx,**/*.jsx"
---
Jotai atoms for state. Tailwind v4 for styling. shadcn/ui components.
Functional components, named exports. No class components.
```

---

### Repo Setup Progress

| Repo | AGENTS.md | .github/copilot-instructions | .zed/rules | Owner | Status |
|------|-----------|------------------------------|------------|-------|--------|
| arctan-client | ✅ | ❌ | ❌ | | |
| arctan-client-app | ❌ | ❌ | ❌ | | |
| inference-server | ❌ | ❌ | ❌ | | |
| console-gateway | ❌ | ❌ | ❌ | | |
| auth-service | ❌ | ❌ | ❌ | | |
| db-service | ❌ | ❌ | ❌ | | |
| logging-service | ❌ | ❌ | ❌ | | |
| audio-driver | ❌ | ❌ | ❌ | | |
| livekit-gateway | ❌ | ❌ | ❌ | | |
| client-dashboard | ❌ | ❌ | ❌ | | |
| infra-service | ❌ | ❌ | ❌ | | |

---

# Layer 3: Developer

*Done once per person. Takes 10 minutes. Your personal AI preferences on your machine.*

This is where each team member configures their specific tool. These files live on **your laptop** — they're not committed to git. They contain your personal preferences, role, and working style.

**Jump to your tool:**

| Tool | Section |
|------|---------|
| VS Code + Copilot | [3.1](#31-vs-code--github-copilot) |
| Claude Code (iTerm2) | [3.2](#32-claude-code-iterm2) |
| OpenCode (Ghostty) | [3.3](#33-opencode-ghostty) |
| Zed | [3.4](#34-zed-editor) |

---

## 3.1 VS Code + GitHub Copilot

### Enable Copilot Memory (2 minutes)

1. Go to **github.com** → **Settings** → **Copilot** → **Features**
2. Toggle **Memory** on

Then tell Copilot about yourself in a chat session:
```
"I work at Arctan primarily on [inference-server / audio-driver / etc].
I prefer concise code with explicit error handling and early returns.
We use Jotai for state management in React, not Redux."
```

Copilot stores this and applies it to every future session.

### Enable Instruction File Reading (1 minute)

In VS Code settings, ensure this is on:
```json
{
  "github.copilot.chat.codeGeneration.useInstructionFiles": true
}
```

This tells Copilot to read the `.github/copilot-instructions.md` files from Layer 2.

### Habits That Save Tokens

- **Use `@file` references** instead of pasting code into chat
- **Start new chats** for unrelated topics — old history burns tokens
- **Use Sonnet** for routine tasks, **Opus** only for complex reasoning

---

## 3.2 Claude Code (iTerm2)

### Create Your Global CLAUDE.md (2 minutes)

```bash
mkdir -p ~/.claude
cat > ~/.claude/CLAUDE.md << 'EOF'
# Global Preferences — Arctan

## About Me
- I work at Arctan primarily on [YOUR REPOS HERE]
- My timezone is IST

## Coding Style
- Concise responses with code examples
- Early returns and guard clauses
- Always handle errors explicitly
- Prefer diffs over full file rewrites

## Arctan Stack
- Desktop: Tauri v2 (Rust + React/TypeScript), Windows-only
- Audio: cpal → DeepFilterNet → Beatrice (closed-source C/C++ lib)
- Backend: Python (Flask, FastAPI), Go (gateway, LiveKit)
- Data: PostgreSQL → PeerDB CDC → ClickHouse
- Infra: AWS ECS ap-south-1, Docker
- PM: Plane (app.plane.so/arctan)
- db-service and infra-service use 'master' branch, not 'main'
EOF
```

**Edit the "About Me" line** with the repos you actually work on.

### Use /memory After Sessions (2 seconds each time)

At the end of each work session, type `/memory`. Claude saves what it learned to the project's CLAUDE.md. Next session, zero re-explaining:

```
Before /memory:  "So this is a Tauri app, and the crackling..."  50,000 tokens
After /memory:   Claude already knows. Straight to work.          2,000 tokens
```

### Use /compact and Haiku

- `/compact` when conversations get long — summarizes history
- `claude --model claude-3-5-haiku "quick question"` — Haiku is **30x cheaper** than Opus

### Install claude-mem (Optional, 5 minutes)

For fully automatic memory:
```
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```
Restart Claude Code. Now it captures and compresses context automatically. Web dashboard at http://localhost:37777.

**Start with CLAUDE.md + /memory.** Add claude-mem when you want zero-effort.

---

## 3.3 OpenCode (Ghostty)

### Create Your Global Context (2 minutes)

```bash
mkdir -p ~/.config/opencode
cat > ~/.config/opencode/context.md << 'EOF'
# Arctan Context

## About Me
- I work at Arctan primarily on [YOUR REPOS HERE]
- Prefer concise, tested code with explicit error handling

## Stack
- Desktop: Tauri v2 (Rust + React/TS), Windows-only
- Audio: cpal → DeepFilterNet → Beatrice → cpal
- Backend: Python (Flask/FastAPI), Go (gateways/LiveKit)
- Data: PostgreSQL → PeerDB → ClickHouse
- Infra: AWS ECS ap-south-1, Docker
- db-service and infra-service use 'master', not 'main'
EOF
```

### Set Up Cheap Summarizer (2 minutes — biggest single saver)

When conversations get long, OpenCode summarizes old messages. By default it uses your expensive primary model. Switch to Haiku:

Add to `~/.config/opencode/config.toml`:

```toml
[model.default]
provider = "anthropic"
model = "claude-sonnet-4-20250514"

[model.summarizer]
provider = "anthropic"
model = "claude-3-5-haiku-20241022"
max_tokens = 4000
```

Haiku costs $0.25/M tokens vs Sonnet's $3/M. **5-10x savings on long sessions.**

### Habits

- `/compact` when conversations bloat
- `opencode --prompt "question"` for one-shot questions (skips session overhead)
- Session forking for experiments

---

## 3.4 Zed Editor

### Fix Tab Context (1 minute — biggest saver in Zed)

Zed sends **every open tab** as context by default. 15 files open = 15 files sent with every message.

Open settings (`Cmd+,`) and add:

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

Now only **pinned tabs** are sent. Pin the 2-3 files you're actually working on.

### Create Global Rules (2 minutes)

```bash
cat > ~/.config/zed/rules.md << 'EOF'
# Arctan AI Rules

## Style
- Concise answers with code examples
- Early returns, explicit error handling
- Follow existing patterns in the file

## Stack
- Arctan: real-time voice changer (Tauri v2, Rust + React)
- Audio: cpal → DeepFilterNet → Beatrice (closed-source C/C++)
- Backend: Python (Flask/FastAPI), Go (gateways/LiveKit)
- Data: PostgreSQL → PeerDB CDC → ClickHouse
- Infra: AWS ECS ap-south-1
- db-service and infra-service use 'master', not 'main'
EOF
```

### Habits

- `@file` to reference specific files instead of opening them as tabs
- `@thread` to reference past conversations (avoids re-explaining)
- New thread for each new topic

---

# Summary: What Goes Where

### On your machine (personal, Layer 3)

| File | Tool | Content |
|------|------|---------|
| `~/.claude/CLAUDE.md` | Claude Code | Your role, preferences, Arctan stack |
| `~/.config/opencode/context.md` | OpenCode | Your role, preferences, stack |
| `~/.config/opencode/config.toml` | OpenCode | Cheap summarizer model |
| `~/.config/zed/rules.md` | Zed | Your coding style, stack |
| `~/.config/zed/settings.json` | Zed | Tab context → "pinned" |
| GitHub Settings → Copilot Memory | VS Code | Toggle on (web UI) |

### In each repo (shared, Layer 2)

| File | Tools | Content |
|------|-------|---------|
| `AGENTS.md` | All tools | Project overview, structure, conventions |
| `.github/copilot-instructions.md` | VS Code Copilot | Coding instructions |
| `.github/instructions/*.md` | VS Code Copilot | Per-file-type rules |
| `.zed/rules.md` | Zed | Condensed project rules |

### Org-wide (Layer 1)

| System | Purpose |
|--------|---------|
| Hermes at chat.getarctan.com | Shared AI for data/PM/research (no personal tokens) |
| AGENTS.md convention | Standard context file across all repos |

---

# Cost Impact

| Layer | Tokens saved/session/person | Monthly savings (12 people) |
|-------|----------------------------|-----------------------------|
| Layer 1 (Hermes) | Offloads non-coding queries entirely | ~$100-300 |
| Layer 2 (Repo files) | 30,000 → 5,000 tokens/session | ~$300-900 |
| Layer 3 (Developer) | 5,000 → 2,000 tokens/session | ~$200-600 |
| **Combined** | **50,000 → 2,000 tokens/session** | **$636-1,896/mo** |
| **Annual savings** | | **$6,900-22,700** |

---

# Action Items

### This Week — Admin
- [ ] Share this guide with the team
- [ ] Assign repo owners in the [progress table](#repo-setup-progress) above
- [ ] Verify Hermes is accessible to all team members

### This Week — Repo Owners
- [ ] Add `AGENTS.md` to your repo(s) using the templates above
- [ ] Add `.github/copilot-instructions.md` if your repo has VS Code users
- [ ] Commit and push

### This Week — Every Developer
- [ ] Create your personal config file (see [Layer 3](#layer-3-developer), your tool)
- [ ] **Zed users:** Set tabs to `"pinned"` — do this right now, biggest instant win
- [ ] **VS Code users:** Enable Copilot Memory at github.com
- [ ] **Claude Code users:** Create `~/.claude/CLAUDE.md` and start using `/memory`
- [ ] **OpenCode users:** Add Haiku summarizer to config

### Later — For Maximum Savings
- [ ] Claude Code users: install claude-mem plugin
- [ ] Add scoped `.github/instructions/*.md` to high-traffic repos

---

*Questions? Ask Hermes at [chat.getarctan.com](https://chat.getarctan.com) or DM @hermesbot on Slack.*
