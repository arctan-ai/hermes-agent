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

# Checklists

Copy into a Plane issue or print out. Two checklists — one for admin, one for each team member.

---

## ✅ Admin Checklist

**You (the admin) own Layer 1 (org) and Layer 2 (repos).** Team members only need to set up their personal dev environment (Layer 3).

### Organization (Layer 1)

- [ ] All team members can sign in at https://chat.getarctan.com with @arctan.ai
- [ ] Open WebUI roles assigned for each person (admin / user)
- [ ] @hermesbot responds in Slack
- [ ] Share the onboarding guide (onboarding-guide.md) with the team
- [ ] Share this guide (token-savings-guide.md) with the team
- [ ] Pin both guides in a Slack channel

### Repositories (Layer 2) — Add AGENTS.md to all repos

The admin pushes AGENTS.md (and optionally copilot-instructions, .zed/rules) to every repo. Templates for all 11 repos are in [Layer 2](#layer-2-repository) above.

| # | Repo | Branch | AGENTS.md | .github/copilot-instructions.md | .zed/rules.md |
|---|------|--------|-----------|--------------------------------|---------------|
| 1 | arctan-client | main | ✅ exists | ☐ | ☐ |
| 2 | arctan-client-app | main | ☐ | ☐ | ☐ |
| 3 | inference-server | main | ☐ | ☐ | ☐ |
| 4 | console-gateway | main | ☐ | ☐ | ☐ |
| 5 | auth-service | main | ☐ | ☐ | ☐ |
| 6 | db-service | **master** | ☐ | ☐ | ☐ |
| 7 | logging-service | main | ☐ | ☐ | ☐ |
| 8 | audio-driver | main | ☐ | ☐ | ☐ |
| 9 | livekit-gateway | main | ☐ | ☐ | ☐ |
| 10 | client-dashboard | main | ☐ | ☐ | ☐ |
| 11 | infra-service | **master** | ☐ | ☐ | ☐ |

**Priority:** AGENTS.md is required for every repo. The other two are nice-to-have for repos where VS Code or Zed are used heavily.

**Verify all repos after pushing:**
```bash
for repo in arctan-client arctan-client-app inference-server console-gateway \
  auth-service db-service livekit-gateway logging-service audio-driver \
  client-dashboard infra-service; do
  echo -n "$repo: "
  gh api repos/arctan-ai/$repo/contents/AGENTS.md --jq '.name' 2>/dev/null || echo "MISSING"
done
```

### Notify Team

- [ ] Send Slack message to team: "AI context files have been added to all repos. Please do your personal dev setup — takes 10 minutes. Guide: [link to this doc, Layer 3]"
- [ ] Follow up after 1 week in standup: "Has everyone set up their AI context files?"

### Ongoing Maintenance

- [ ] Track Claude API spend monthly (OpenRouter dashboard shows per-key usage)
- [ ] When a repo changes significantly (new service, major refactor), update its AGENTS.md
- [ ] Add to PR review culture: "Does this change affect AGENTS.md?"

---

## ✅ Team Member Checklist

**You own your personal dev environment (Layer 3).** The admin has already set up Hermes and pushed context files to all repos. You just need to configure your local tools.

~15 minutes total. Do it once, benefit forever.

### 1. Get Into Hermes (2 minutes)

The shared AI assistant — query data, manage Plane, search the web, ask about any repo.

- [ ] Go to **https://chat.getarctan.com**
- [ ] Sign in with your **@arctan.ai** Google account
- [ ] Select **hermes-agent** from the model dropdown
- [ ] Send: "Hi, I'm [your name], I work on [your repos/area]"
- [ ] Hermes remembers you from now on — no need to re-introduce yourself

### 2. Set Up Your Coding Tool (10 minutes)

**Do only the section for the tool you use:**

#### VS Code + GitHub Copilot

- [ ] Enable Copilot Memory: go to **github.com → Settings → Copilot → Features → Memory on**
- [ ] Enable instruction files in VS Code settings:
  ```json
  { "github.copilot.chat.codeGeneration.useInstructionFiles": true }
  ```
- [ ] Teach Copilot about yourself in a chat session:
  ```
  "I work at Arctan on [your repos]. I prefer [your coding style].
   We use Jotai for React state, Tailwind v4 for styling.
   Beatrice lib is closed-source FFI — never modify C headers directly."
  ```
- [ ] **Habit:** use `@file` references instead of pasting code. Start new chats for new topics.

#### Claude Code (iTerm2)

- [ ] Create your global preferences file:
  ```bash
  mkdir -p ~/.claude
  ```
  Then create `~/.claude/CLAUDE.md` using the template in [Section 3.2](#32-claude-code-iterm2).
- [ ] **Edit the "About Me" line** with your actual name, role, and repos you work on
- [ ] **Habit:** end each work session with `/memory` (2 seconds, saves thousands of tokens next time)
- [ ] **Habit:** use `/compact` when conversations get long
- [ ] **Habit:** use `claude --model claude-3-5-haiku "question"` for quick lookups (30x cheaper)
- [ ] **Optional:** install claude-mem for fully automatic memory:
  ```
  /plugin marketplace add thedotmack/claude-mem
  /plugin install claude-mem
  ```

#### OpenCode (Ghostty)

- [ ] Create your global context file:
  ```bash
  mkdir -p ~/.config/opencode
  ```
  Then create `~/.config/opencode/context.md` using the template in [Section 3.3](#33-opencode-ghostty).
- [ ] **Edit the "About Me" line** with your actual role and repos
- [ ] Set up cheap summarizer — add to `~/.config/opencode/config.toml`:
  ```toml
  [model.summarizer]
  provider = "anthropic"
  model = "claude-3-5-haiku-20241022"
  max_tokens = 4000
  ```
  This saves 5-10x on long sessions (Haiku summarizes old messages instead of Sonnet).
- [ ] **Habit:** use `/compact` when conversations bloat. Use `opencode --prompt "question"` for one-shots.

#### Zed

- [ ] **Do this first (biggest win):** Open settings (`Cmd+,`) and set tab context:
  ```json
  { "assistant": { "context": { "tabs": "pinned", "rules": true } } }
  ```
  This stops Zed from sending every open tab to Claude with every message.
- [ ] Create your global rules:
  ```bash
  cat > ~/.config/zed/rules.md << 'EOF'
  # Arctan AI Rules
  - Concise answers with code examples
  - Early returns, explicit error handling
  - Follow existing patterns in the file
  - Arctan: Tauri v2 (Rust + React), audio: cpal → DeepFilterNet → Beatrice
  - Backend: Python (Flask/FastAPI), Go (gateways/LiveKit)
  - Data: PostgreSQL → PeerDB → ClickHouse
  - db-service and infra-service use 'master', not 'main'
  EOF
  ```
- [ ] **Habit:** use `@file` for specific files, `@thread` to reference past conversations. New thread per topic.

### 3. Pull Latest on Your Repos

The admin has pushed AGENTS.md and other context files to all repos. Pull them:

```bash
cd ~/your-project && git pull
ls AGENTS.md    # should exist now
```

Once pulled, every AI tool reads these files automatically. No action needed from you.

### 4. Verify It's Working

Start a new Claude session on any Arctan project. It should:

- ✅ Know what the project is **without you explaining**
- ✅ Know your coding preferences from your personal config
- ✅ **NOT** spend the first 5 minutes reading random files

If Claude seems lost:
1. Check `ls AGENTS.md` in the repo root
2. Check your personal config file exists (path depends on your tool — see above)
3. For Claude Code: did you run `/memory` in a previous session?
4. Ask Hermes: "My AI tool isn't picking up context files, help me debug"

### 5. Ongoing Habits

These take zero extra time but compound into big savings:

- [ ] **Claude Code users:** Run `/memory` before closing a session (2 seconds)
- [ ] **Everyone:** Start a new chat/thread for each new topic — don't let old history pile up
- [ ] **Quick questions:** Ask Hermes at chat.getarctan.com instead of burning your personal API tokens
- [ ] **Simple lookups:** Use the cheap model (Haiku) when you don't need deep reasoning

---

*Questions? Ask Hermes at [chat.getarctan.com](https://chat.getarctan.com) or DM @hermesbot on Slack.*
