# 📦 Repository AI Context Setup

> **For repo owners / tech leads.** Add these files to your repos so every developer's AI tool has instant project context. One-time setup per repo, benefits the entire team.

---

## What This Does

When a developer opens any Arctan repo in Claude Code, OpenCode, Zed, or VS Code, their AI tool automatically reads context files from the repo. Without these files, Claude spends 50,000+ tokens re-discovering the project structure every session. With them, it needs ~500 tokens.

**One person sets it up per repo. Everyone benefits permanently.**

---

## Which Files to Add

| File | Tools That Read It | Purpose |
|------|-------------------|---------|
| `AGENTS.md` | Claude Code, OpenCode, Zed, Copilot | Project overview, structure, conventions |
| `.github/copilot-instructions.md` | VS Code Copilot | Copilot-specific coding instructions |
| `.github/instructions/*.md` | VS Code Copilot | Per-file-type scoped instructions |
| `.zed/rules.md` | Zed | Zed-specific project rules |
| `.opencode/context.md` | OpenCode | OpenCode-specific project context |

**At minimum, add `AGENTS.md`.** It covers the most tools with a single file. Add the others if your team uses those specific tools.

---

## AGENTS.md Templates (Copy-Paste Ready)

`AGENTS.md` goes in the repo root. `arctan-client` already has one — the rest need them.

### arctan-client ✅ (already exists)

The current AGENTS.md covers: project overview, repo structure, build commands, audio pipeline architecture, naming conventions, error handling patterns.

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

### inference-server

```markdown
# AGENTS.md

## Project Overview
Python-based ML inference server for real-time voice conversion. Serves
Beatrice voice changer models via LiveKit WebRTC integration. Supports
CUDA, DirectML, ROCm, and CPU inference.

## Structure
server/
├── voice_changer/              # Core voice conversion logic
├── livekit_audio_processor.py  # LiveKit WebRTC audio processing
├── webrtc/                     # WebRTC utilities
├── settings.py                 # Configuration
├── mods/                       # Model modules
├── restapi/                    # REST API endpoints
└── data/                       # Model data

## Requirements (platform-specific)
requirements-cuda.txt           # GPU (NVIDIA)
requirements-dml.txt            # GPU (AMD/Intel on Windows)
requirements-rocm.txt           # GPU (AMD on Linux)
requirements-cpu.txt            # CPU fallback

## Running
python server/main.py
```

### console-gateway

```markdown
# AGENTS.md

## Project Overview
Go backend API gateway with authentication/authorization middleware and a
Vite React frontend console application. Handles Google OAuth for the
arctan.ai domain, JWT token management, and proxies requests to internal
services (auth-service, db-service, etc).

## Structure
server/                     # Go API gateway (port 8080)
├── internal/
│   ├── auth/               # Authentication service (Google OAuth, JWT)
│   ├── config/             # Configuration management
│   ├── gateway/            # API gateway routing logic
│   └── middleware/         # Auth middleware (JWT validation)
├── go.mod
└── main.go
client/                     # Vite React frontend (port 5173)
├── src/
│   ├── components/         # React components
│   ├── contexts/           # Auth context (Google OAuth state)
│   └── services/           # API service layer
├── package.json
└── vite.config.ts

## Key Endpoints
### Public
GET  /health                        # Health check
GET  /api/auth/google               # Initiate Google OAuth
GET  /api/auth/google/callback      # OAuth callback
POST /api/auth/refresh              # Refresh JWT token

### Protected (require Authorization header)
GET  /api/user/profile              # User profile
POST /api/user/logout               # Logout
*    /api/services/*                # Proxy to internal services

## Environment Variables
PORT, ENVIRONMENT, JWT_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
GOOGLE_REDIRECT_URL, DB_SERVICE_URL (http://localhost:3020)

## Development
cd server && go run main.go         # Backend
cd client && npm install && npm run dev  # Frontend

## Important
- HTTP mode (USE_HTTPS=false) recommended when behind nginx/Caddy
- SSL termination handled by reverse proxy, not the Go server
- See HTTP_HTTPS_CONFIG.md and PRODUCTION_DEPLOYMENT.md for details
```

### auth-service

```markdown
# AGENTS.md

## Project Overview
Flask + SQLAlchemy authentication microservice. Handles user registration,
login (multiple versions for backward compat), password reset, and user
configuration management. Backed by PostgreSQL.

## Key Endpoints
POST /register_v2           # Register new user (DB)
POST /login_v3              # Login with user config return (DB)
POST /reset_password        # Password reset
POST /get_server_url        # Get user's assigned inference server URL

## Structure
main.py                     # Flask app entry point
models/                     # SQLAlchemy models (User, Config, etc)
requirements.txt            # Dependencies
setup_auth_service.sh       # Creates .env and initial data files

## Stack
Python, Flask, SQLAlchemy, PostgreSQL, Gunicorn (production)

## Running
python main.py              # Development
bash start.sh               # Production (Gunicorn)
```

### db-service

```markdown
# AGENTS.md

## Project Overview
Database lifecycle management service. Handles PostgreSQL schema migrations
via Alembic and provides REST APIs for database operations.

## Structure
main.py                     # Entry point
apis/                       # REST API endpoints
models/                     # SQLAlchemy ORM models
alembic/                    # Migration scripts and config
alembic.ini                 # Alembic configuration
scripts/                    # Utility scripts

## Stack
Python, Alembic, SQLAlchemy, PostgreSQL

## ⚠️ IMPORTANT: Default branch is 'master' (not 'main')
```

### logging-service

```markdown
# AGENTS.md

## Project Overview
Metrics collection and user activity tracking service. Receives telemetry
data from Arctan clients (performance metrics, user events) and writes to
PostgreSQL. Data is replicated to ClickHouse via PeerDB CDC for analytics.

## Key Tables (reflected in ClickHouse)
- metrics (~88M rows): model_latency, ping, cpu, ram, cpu_app,
  ram_app_heap_usage_percent, ram_app_rss_bytes, volume, packets_received,
  packets_sent, packets_lost, bytes_received, bytes_sent, jitter, webrtc_stats
- user_activities (~27M rows): user_id, activity_type, timestamp, activity_data
- Users (538 rows): id, name, email, organization_id, license_type
- Organizations (42 rows): id, name

## ⚠️ Data Gotchas
- Timestamps in metrics/user_activities are Unix MILLISECONDS (Int64)
  → divide by 1000 for DateTime: toDateTime(timestamp/1000)
- Filter _peerdb_is_deleted = 0 for active records (PeerDB soft deletes)
- ReplacingMergeTree may have duplicates before merge — use FINAL for exact counts

## Key Files
main.py / main-v2.py       # Service entry points
models/                     # Data models
utils/                      # Utility functions

## Docs
METRICS_SCHEMA_STRATEGY.md  # Why we use flat columns vs nested JSON
MIGRATION_GUIDE.md          # How to add new metric columns
RAM_METRICS_EXPLANATION.md  # Why we track both heap% and RSS bytes

## Stack
Python, PostgreSQL → PeerDB CDC → ClickHouse
```

### audio-driver

```markdown
# AGENTS.md

## Project Overview
Windows WDM (Windows Driver Model) virtual audio driver written in C++.
Exposes a speaker and microphone endpoint pair using WaveRT rendering.
The driver creates a "virtual audio device" — no physical hardware needed.

## Structure
Source/                     # All C++ driver source code
├── Utilities/
│   └── audio_ring_buffer.cpp  # Ring buffer (key performance file)
Package/                    # Installer files
scripts/                    # Build, sign, and installer scripts
ArctanAudioDriver.sln       # Visual Studio solution

## Build & Release Workflow
1. Build via CI (GitHub Actions) or locally (Build.ps1)
2. Sign locally with EV certificate (SignDriver.ps1)
3. Submit to Microsoft Hardware Dashboard (CreateSubmissionPackage.ps1)
4. Get Microsoft-signed driver back → package installer (BuildInstaller.ps1)
See BUILD.md for full guide.

## ⚠️ Known Caveats (see CAVEATS.md for details)
- Code 10 / STATUS_DEVICE_BUSY: caused by m_AdapterInstances left non-zero
  from previous driver instance. Uninstall fully before reinstalling.
- Ring buffer was allocating ~16.9GB (!) due to constant misuse. Fixed to
  2 seconds (RING_BUFFER_DURATION_SECONDS = 2). See Optimisations.md for
  further reduction to 50ms.
- 48kHz only — driver does not support runtime sample rate negotiation.
- Dual-endpoint topology: speaker + mic are separate filter instances
  sharing one CAdapterCommon.

## Testing Checklist
See TESTING.md — covers clean install, upgrade, uninstall, multi-endpoint,
HLK pre-submission checks.

## Stack
C++, Windows Driver Kit (WDK), WaveRT, Inno Setup (installer)
Requires: Visual Studio with MSVC, Windows SDK, code signing certificate
```

### livekit-gateway

```markdown
# AGENTS.md

## Project Overview
Go-based WebRTC media server gateway using LiveKit. Manages real-time
audio streams between Arctan desktop/web clients and inference servers.

## Structure
server.go                   # Main gateway server
livekit-server/             # LiveKit server binary + configuration
livekit-token-server/       # Token generation service for client auth
docker-compose.yml          # Local development setup
api-server-compose.yml      # API server variant
DSCP_CONFIG.md              # QoS/DSCP packet marking configuration

## Key Scripts
manage-livekit-server.sh    # Start/stop LiveKit server
manage-api-server.sh        # Start/stop API server
add-inference-server.sh     # Register a new inference server
check-participants.sh       # Check active room participants

## Stack
Go, LiveKit SFU, Docker Compose
```

### client-dashboard

```markdown
# AGENTS.md

## Project Overview
Full-stack admin panel for managing Arctan clients and organizations.
React Router v7 (SPA mode) frontend with FastAPI Python backend.

## Structure
client/                     # React frontend (port 5173 dev)
├── src/
│   ├── components/         # React components
│   ├── routes/             # Route definitions
│   └── services/           # API service layer
client-dashboard-server/    # FastAPI backend (port 8181)
├── main.py                 # FastAPI entry point
├── models/                 # Pydantic/SQLAlchemy models
└── requirements.txt

## Deployment
Docker Compose with two modes:
- docker-compose.yml + docker-compose.onprem.yml  → on-premise (includes Postgres)
- docker-compose.yml + docker-compose.cloud.yml   → cloud (external Postgres)

## Stack
React Router v7, TypeScript, Tailwind CSS, FastAPI, PostgreSQL
```

### infra-service

```markdown
# AGENTS.md

## Project Overview
Infrastructure configuration and deployment scripts for Arctan's
self-hosted services. Contains Docker Compose files, configs, and
setup scripts for all supporting infrastructure.

## Structure
clickhouse/                 # ClickHouse database setup
├── migrations/             # Schema migration scripts
├── pg-clickhouse-sync-plan.md  # PeerDB CDC replication plan
└── setup.md                # Installation guide
grafana/                    # Monitoring stack
├── docker-compose.yml      # Grafana + Loki + Promtail + Prometheus
├── prometheus.yml          # Metrics scraping config
└── loki-config.yml         # Log aggregation config
metabase/                   # Analytics dashboarding
├── docker-compose.yml
nginx/                      # Reverse proxy
├── nginx-manager.sh        # nginx management script
├── sites-available/        # Site configurations
└── QUICK_START.md
peerdb/                     # Postgres → ClickHouse CDC replication
├── docker-compose.yml      # PeerDB v0.36.9 (6 containers)
├── deploy.sh               # ECS deployment script
└── README.md
semaphore/                  # Ansible automation (deployment tool)
├── docker-compose.yml

## ⚠️ IMPORTANT: Default branch is 'master' (not 'main')
```

---

## Also Add Tool-Specific Files (Optional)

If your team uses specific tools on a repo, add these too:

### .github/copilot-instructions.md (for VS Code + Copilot users)

Example for arctan-client:

```markdown
# Copilot Instructions — arctan-client

## Project
Real-time voice changer desktop app. Tauri v2 (Rust backend, React/TS frontend).
Audio pipeline: cpal → DeepFilterNet → Beatrice (voice conversion) → cpal.
Windows-only. Beatrice is a closed-source MSVC static lib.

## Rust Conventions
- Edition 2024, resolver 3
- Early returns and guard clauses, no unwrap() in production code
- beatrice_lib/ is FFI only — C header changes require matching Rust updates
- Ring buffers: Source/Utilities/ (C++ driver) and deep_filter.rs (Rust)

## TypeScript/React Conventions
- Jotai for state management (not Redux)
- Tailwind v4 + shadcn/ui for styling/components
- Functional components, named exports

## Build
yarn tauri dev (development) | yarn tauri build (production, needs code signing)
```

### .github/instructions/*.md (scoped by file type)

```
.github/instructions/rust.md:
---
applyTo: "**/*.rs"
---
- Early returns, ? operator for error propagation, no unwrap() in prod
- beatrice_lib changes require matching C header updates
- Ring buffer code is performance-critical — avoid allocations in hot paths

.github/instructions/react.md:
---
applyTo: "**/*.tsx,**/*.jsx"
---
- Jotai atoms for state (not Redux, not Context API)
- Tailwind v4 for styling, shadcn/ui for components
- Functional components only, named exports
```

### .zed/rules.md (for Zed users)

```markdown
# arctan-client Rules
- Tauri v2: Rust backend (src-tauri/) + React frontend (src/)
- Audio: cpal → DeepFilterNet → Beatrice → cpal
- beatrice_lib/ is FFI to closed-source C lib — don't modify headers alone
- State: Jotai | Styling: Tailwind v4 + shadcn/ui
- Known issue: crackling from spin-wait polling in deep_filter.rs
```

### .opencode/context.md (for OpenCode users)

Same content as AGENTS.md is usually sufficient. OpenCode reads AGENTS.md automatically, so this is only needed for OpenCode-specific instructions.

---

## Commit Checklist

For each repo, add and push:

```bash
# Required
git add AGENTS.md
# Optional — add whichever your team uses
git add .github/copilot-instructions.md
git add .github/instructions/
git add .zed/rules.md
git add .opencode/context.md

git commit -m "docs: add AI context files (AGENTS.md + tool configs)"
git push
```

---

## Status Tracker

| Repo | AGENTS.md | copilot-instructions | .zed/rules | Owner |
|------|-----------|---------------------|------------|-------|
| arctan-client | ✅ exists | ❌ | ❌ | |
| arctan-client-app | ❌ | ❌ | ❌ | |
| inference-server | ❌ | ❌ | ❌ | |
| console-gateway | ❌ | ❌ | ❌ | |
| auth-service | ❌ | ❌ | ❌ | |
| db-service | ❌ | ❌ | ❌ | |
| logging-service | ❌ | ❌ | ❌ | |
| audio-driver | ❌ | ❌ | ❌ | |
| livekit-gateway | ❌ | ❌ | ❌ | |
| client-dashboard | ❌ | ❌ | ❌ | |
| infra-service | ❌ | ❌ | ❌ | |

Fill in the owner column and track progress. Each repo takes ~10 minutes.

---

*All templates above are ready to copy-paste. Customize the details for your repo, commit, push, done.*
