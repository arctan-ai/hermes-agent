---
name: arctan-team-knowledge
description: "Arctan product architecture, team repos, services, and domain knowledge. Real-time voice changer with AI noise cancellation and neural voice conversion."
tags: [arctan, architecture, product, team, internal]
triggers:
  - user asks about Arctan product, architecture, services
  - user asks about a specific repo, service, or component
  - user needs context about how Arctan systems work together
  - user asks about deployment, infrastructure, or team workflows
---

# Arctan Team Knowledge

## Product Overview
Arctan builds a **real-time voice changer** desktop application with:
- **AI noise cancellation** (DeepFilterNet)
- **Neural voice conversion** (Beatrice inference library)
- **WebRTC-based** audio streaming via LiveKit
- **Windows-only** desktop client (Tauri v2 + Rust + React)
- Web client variant for browser-based access

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                          │
│  arctan-client (Rust/Tauri desktop)                     │
│  arctan-client-app (TypeScript web + desktop unified)   │
│  client-dashboard (React + FastAPI admin panel)         │
├─────────────────────────────────────────────────────────┤
│                    Gateway Layer                         │
│  console-gateway (Go API gateway + React console)       │
│  livekit-gateway (Go, WebRTC media server)              │
├─────────────────────────────────────────────────────────┤
│                    Service Layer                         │
│  auth-service (Python/Flask, user auth + config)        │
│  db-service (Python, DB lifecycle, Alembic migrations)  │
│  inference-server (Python, voice changer ML models)     │
│  logging-service (Python, metrics + user activities)    │
├─────────────────────────────────────────────────────────┤
│                    Infrastructure                        │
│  audio-driver (C++, Windows WDM virtual audio driver)   │
│  infra-service (Shell, Docker configs for infra)        │
│  hermes-agent (Python, AI agent platform)               │
└─────────────────────────────────────────────────────────┘
```

## Repository Details

### arctan-client (Rust + TypeScript)
- **Purpose**: Desktop voice changer app (Windows-only)
- **Stack**: Tauri v2, Rust backend, React/TypeScript frontend, Jotai state
- **Audio pipeline**: cpal → DeepFilterNet → Beatrice → cpal
- **Key components**: ~21 Rust modules in src-tauri/src/, voice models + gender classifier ONNX
- **Build**: `yarn tauri dev` (dev) / `yarn tauri build` (prod, requires code signing)
- **Dependencies**: Binary deps downloaded via `scripts/download-dependencies.ps1`
- **Known issue**: Audio crackling from spin-wait polling + OS timer granularity (see docs/audio-pipeline-analysis.md)
- **Branch**: main

### arctan-client-app (TypeScript)
- **Purpose**: Unified web + desktop client app
- **Stack**: TypeScript, web + desktop variants
- **Structure**: desktop/, web/, docs/, sample-webrtc-client.html
- **Branch**: main

### audio-driver (C++)
- **Purpose**: Windows WDM virtual audio driver (speaker + microphone endpoints)
- **Stack**: C++, Windows Driver Kit (WDK), WaveRT
- **Key docs**: BUILD.md, CAVEATS.md, TESTING.md, Optimisations.md
- **Signing**: Requires EV certificate + Microsoft Hardware Dashboard submission
- **Known caveats**: Code 10 errors from stale adapter instances, ring buffer sizing
- **Branch**: main

### inference-server (Python)
- **Purpose**: ML inference for voice conversion
- **Stack**: Python, supports CUDA/CPU/DML/ROCm
- **Key files**: voice_changer/, livekit_audio_processor.py, webrtc/
- **Deployment**: Multiple requirements files per platform
- **Branch**: main

### livekit-gateway (Go)
- **Purpose**: WebRTC media server gateway using LiveKit
- **Stack**: Go, LiveKit server, Docker Compose
- **Key files**: server.go, manage-livekit-server.sh, DSCP_CONFIG.md
- **Branch**: main

### console-gateway (Go + TypeScript)
- **Purpose**: API gateway with auth middleware + React admin console
- **Stack**: Go backend (port 8080), Vite React frontend (port 5173)
- **Auth**: Google OAuth (arctan.ai domain), JWT tokens
- **Endpoints**: /api/auth/*, /api/user/*, /api/services/* (proxy)
- **Key docs**: DEVELOPMENT_SETUP.md, DOCKER_SETUP.md, PRODUCTION_DEPLOYMENT.md
- **Branch**: main

### auth-service (Python)
- **Purpose**: User authentication, registration, config management
- **Stack**: Flask, SQLAlchemy, PostgreSQL
- **Endpoints**: /register, /login, /login_v2, /login_v3, /reset_password, /get_server_url
- **Branch**: main

### db-service (Python)
- **Purpose**: Database lifecycle management
- **Stack**: Python, Alembic migrations, PostgreSQL
- **Structure**: apis/, models/, alembic/, scripts/
- **Branch**: master (not main!)

### logging-service (Python)
- **Purpose**: Metrics collection and user activity tracking
- **Stack**: Python, feeds into ClickHouse via PeerDB
- **Key metrics**: CPU, RAM, model latency, ping, packets, jitter, volume, WebRTC stats
- **Docs**: METRICS_SCHEMA_STRATEGY.md, MIGRATION_GUIDE.md, RAM_METRICS_EXPLANATION.md
- **Branch**: main

### client-dashboard (TypeScript + Python)
- **Purpose**: Admin panel for clients
- **Stack**: React Router v7 (SPA) + FastAPI backend + PostgreSQL
- **Deployment**: Docker Compose, supports on-prem and cloud modes
- **Ports**: Frontend 5173 (dev), API 8181
- **Branch**: main

### infra-service (Shell/Docker)
- **Purpose**: Infrastructure configs and deployment scripts
- **Contents**:
  - clickhouse/ — migrations, PeerDB sync setup
  - grafana/ — Loki + Promtail + Prometheus monitoring
  - metabase/ — analytics dashboarding
  - nginx/ — reverse proxy configs + management scripts
  - peerdb/ — Postgres→ClickHouse CDC replication
  - semaphore/ — Ansible automation (deployment tool)
- **Branch**: master (not main!)

### hermes-agent (Python)
- **Purpose**: AI agent platform (this system)
- **Stack**: Python, multi-provider LLM, tools, skills
- **Public repo**: https://github.com/arctan-ai/hermes-agent
- **Branch**: main (arctan/production for deployed)

## Tech Stack Summary
| Layer | Technologies |
|-------|-------------|
| Desktop Client | Rust, Tauri v2, React, TypeScript, Jotai |
| Web Client | TypeScript, WebRTC |
| Audio | C++ (WDM driver), Rust (cpal, DeepFilterNet, Beatrice FFI) |
| ML/Inference | Python, ONNX, CUDA/DML/ROCm, LiveKit |
| API Gateways | Go, Google OAuth, JWT |
| Backend Services | Python, Flask, FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL (primary), ClickHouse (analytics) |
| Data Pipeline | PeerDB (Postgres→ClickHouse CDC) |
| Monitoring | Grafana, Loki, Promtail, Prometheus, Metabase |
| Infrastructure | AWS ECS, Docker Compose, Nginx, Caddy, Semaphore/Ansible |
| CI/CD | GitHub Actions |

## Default Branches
Most repos use `main`. Exceptions:
- **db-service**: `master`
- **infra-service**: `master`
- **hermes-agent** (deployed): `arctan/production`

## Key Domain Concepts
- **Beatrice**: Closed-source C/C++ neural voice conversion library (MSVC static lib)
- **DeepFilterNet**: Open-source AI noise cancellation
- **LiveKit**: WebRTC SFU (Selective Forwarding Unit) for real-time audio
- **PeerDB**: CDC (Change Data Capture) replication from Postgres to ClickHouse
- **WDM/WaveRT**: Windows Driver Model for audio (kernel-mode driver)
- **DSCP**: Differentiated Services Code Point for QoS in network packets
