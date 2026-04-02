# 💰 Developer AI Setup: Stop Wasting Tokens

> **Your personal setup. 10 minutes. Saves $50-160/month on your Claude API bill.**
>
> For repo-level context files (AGENTS.md, copilot-instructions, etc), see the separate **[Repository AI Context Setup](repo-ai-context-setup.md)**.

---

## Why You're Burning Money

Every time you start a new Claude session on the same project, Claude rebuilds context from scratch — re-reading files, re-discovering that it's a Tauri app, re-learning that we use Jotai, re-figuring out the audio pipeline. Every. Single. Time.

```
Monday 9am:   "This is a Tauri v2 app with Rust backend..."    50,000 tokens
Monday 2pm:   Claude forgot. Same discovery again.              50,000 tokens
Tuesday 9am:  Claude forgot. Same discovery again.              50,000 tokens
```

**That's ~$55-165/month per person in wasted context tokens.** The fix is personal config files that tell Claude who you are and what you're working on. Takes 10 minutes, lasts forever.

---

## Find Your Tool

| Tool | Jump to |
|------|---------|
| VS Code + Copilot | [Section 1](#1-vs-code--github-copilot) |
| Claude Code (iTerm2) | [Section 2](#2-claude-code-iterm2) |
| OpenCode (Ghostty) | [Section 3](#3-opencode-ghostty) |
| Zed | [Section 4](#4-zed-editor) |

---

## 1. VS Code + GitHub Copilot

### Step 1: Enable Copilot Memory (2 minutes)

Copilot now has persistent memory across sessions. Enable it:

1. Go to **github.com** → **Settings** → **Copilot** → **Features**
2. Toggle **Memory** on

Now tell Copilot things about yourself, and it remembers permanently:

```
"In Arctan repos, we use Jotai for state management, not Redux"
"Our Rust code uses early returns and explicit error handling"
"The beatrice_lib crate is FFI — never modify the C header directly"
"I primarily work on the inference-server and audio pipeline"
```

### Step 2: Configure VS Code Settings (2 minutes)

Add to your VS Code settings (`Cmd+,` → search "copilot"):

```json
{
  "github.copilot.chat.codeGeneration.useInstructionFiles": true
}
```

This tells Copilot to read instruction files from the repos (if the repo owner has added them — see [Repository AI Context Setup](repo-ai-context-setup.md)).

### Step 3: Build Good Habits

| Habit | Why |
|-------|-----|
| Use `@file` to reference code | Avoids pasting — sends the file efficiently |
| Start a new chat for new topics | Old history bloats context and costs tokens |
| Use Sonnet for routine tasks | Opus for complex reasoning, Sonnet for everything else |
| Pin only relevant files | Copilot sends open tab context — fewer tabs = fewer tokens |

### Your Savings

| Action | Effort | Impact |
|--------|--------|--------|
| Enable Copilot Memory | 2 min, once | Preferences persist forever |
| Enable instruction files | 2 min, once | ~40% less context when repos have them |
| Use @file references | Habit | Avoids duplicate content |
| New chat per topic | Habit | Prevents history bloat |

---

## 2. Claude Code (iTerm2)

Claude Code has the best built-in memory system of any tool. You're probably not using it.

### Step 1: Create Your Global CLAUDE.md (2 minutes)

This file is loaded in **every project, every session**, automatically:

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

**Customize the "About Me" section** with your actual role and what you work on.

That's ~400 tokens loaded per session instead of 50,000 tokens of Claude reading random files to figure out the same information.

### Step 2: Start Using /memory (2 seconds per session)

At the end of each work session, type:

```
/memory
```

Claude saves what it learned to a project-level `CLAUDE.md`. Next session, it picks up exactly where you left off.

**Example of what gets saved:**
```
## Session Notes
- The crackling in deep_filter.rs is caused by spin-wait polling with
  sleep() at line 97. Windows thread::sleep has ~15ms granularity,
  causing ring buffer underruns.
- Fix approach: event-based wake-up instead of polling. See PR #47.
- Tests passing on Build 22631 with 48kHz @ 480 hop size.
```

Tomorrow, Claude already knows all of this. Zero re-explaining.

### Step 3: Use /compact and Haiku

When a conversation gets long (20+ exchanges), type `/compact` to summarize history and reclaim context space.

For quick questions:
```bash
claude --model claude-3-5-haiku "What's the syntax for Tauri v2 command handlers?"
```
Haiku costs **1/30th** of Opus. Use it for lookups and simple questions.

### Step 4 (Optional): Install claude-mem

For fully automatic memory — no need to remember to run /memory:

```
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

Restart Claude Code. Now it automatically:
- Captures everything you work on during a session
- Compresses observations into compact summaries
- Injects only what's relevant in future sessions
- Web dashboard at http://localhost:37777

**Start with Steps 1-3.** Add claude-mem later when you want zero-effort memory.

### Your Savings

| Action | Effort | Impact |
|--------|--------|--------|
| Create ~/.claude/CLAUDE.md | 2 min, once | ~70% less context per session |
| Run /memory after sessions | 2 sec each time | Session knowledge persists |
| Use /compact on long chats | 2 sec when needed | Prevents context overflow |
| Use Haiku for simple questions | Habit | 30x cheaper per query |
| Install claude-mem | 5 min, once | ~80% total context reduction |

---

## 3. OpenCode (Ghostty)

OpenCode's killer feature for cost savings: a configurable summarizer model.

### Step 1: Create Your Global Context (2 minutes)

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

## Repos (all in arctan-ai GitHub org)
arctan-client (Rust/Tauri), inference-server (Python/CUDA),
console-gateway (Go), auth-service (Flask), db-service (Alembic),
logging-service (Python), audio-driver (C++ WDM), livekit-gateway (Go),
client-dashboard (React/FastAPI), infra-service (Docker/Shell)

NOTE: db-service and infra-service use 'master' branch, not 'main'.
EOF
```

**Customize the "About Me" section** with what you actually work on.

### Step 2: Set Up a Cheap Summarizer (2 minutes — biggest cost saver)

When your conversation gets long, OpenCode summarizes old messages to fit the context window. By default it uses your primary (expensive) model. Switch summarization to Haiku:

Add this to `~/.config/opencode/config.toml` (or `opencode.toml` in your project):

```toml
[provider.anthropic]
# Uses ANTHROPIC_API_KEY env var automatically

[model.default]
provider = "anthropic"
model = "claude-sonnet-4-20250514"

[model.summarizer]
provider = "anthropic"
model = "claude-3-5-haiku-20241022"
max_tokens = 4000
```

Haiku costs $0.25/M input tokens vs Sonnet's $3/M. **This alone saves 5-10x on long sessions.**

### Step 3: Build Good Habits

| Habit | Why |
|-------|-----|
| Use `/compact` when conversations get long | Shrinks bloated history |
| Use `--prompt "question"` for one-shots | Avoids session overhead entirely |
| Use session forking for experiments | Explore without polluting main session |

### Your Savings

| Action | Effort | Impact |
|--------|--------|--------|
| Create global context.md | 2 min, once | ~70% less context per session |
| Set Haiku as summarizer | 2 min, once | 5-10x cheaper on long sessions |
| Use /compact | 2 sec when needed | Shrinks bloated conversations |
| Use --prompt for one-shots | Habit | Skips session overhead |

---

## 4. Zed Editor

The single biggest token saver in Zed is controlling what context gets sent.

### Step 1: Fix Tab Context (1 minute — biggest saver)

By default, Zed sends the content of **every open tab** to Claude with every message. 15 open files × ~500 lines = massive token waste on every single interaction.

Open Zed settings (`Cmd+,`) and add:

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

Now only tabs you explicitly **pin** get sent as context. Pin the 2-3 files relevant to your current task.

Options:
- `"pinned"` — **recommended**, only pinned tabs sent
- `"none"` — cheapest, no tab context at all
- `"following"` — **default (expensive)**, sends whatever you're looking at

### Step 2: Create Global Rules (2 minutes)

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

**Customize** with your specific focus area.

### Step 3: Build Good Habits

| Habit | Why |
|-------|-----|
| Use `@file` to mention specific files | Sends targeted context, not everything |
| Use `@thread` to reference past conversations | Avoids re-explaining decisions |
| Start new threads for new topics | Prevents old history burning tokens |
| Use inline assist (Ctrl+Enter) on selections | Sends only what you selected |

### Your Savings

| Action | Effort | Impact |
|--------|--------|--------|
| Set tabs to "pinned" | 1 min, once | 50-80% less tab context waste |
| Create global rules.md | 2 min, once | ~70% less per-session context |
| Use @file instead of open tabs | Habit | Targeted context only |
| Start new threads per topic | Habit | Prevents history bloat |

---

## Quick Reference

### What Lives on Your Machine (personal, not in git)

| File | Tool | What to put in it |
|------|------|------------------|
| `~/.claude/CLAUDE.md` | Claude Code | Your role, preferences, Arctan stack knowledge |
| `~/.config/opencode/context.md` | OpenCode | Your role, preferences, stack overview |
| `~/.config/opencode/config.toml` | OpenCode | Cheap summarizer model config |
| `~/.config/zed/rules.md` | Zed | Your coding style, stack knowledge |
| `~/.config/zed/settings.json` | Zed | Tab context = "pinned" |
| GitHub Settings → Copilot → Memory | VS Code | Toggled on (web UI, not a file) |

### What Lives in Your Repos (shared, committed to git)

See **[Repository AI Context Setup](repo-ai-context-setup.md)** for templates.

---

## How Much This Saves

### Per Person Per Month

| What you do | Context tokens/session | Monthly cost |
|-------------|----------------------|-------------|
| Nothing (current state) | ~50,000 | $55-165 |
| Personal config only (this guide) | ~10,000 | $11-33 |
| + repo context files (repo guide) | ~5,000 | $6-17 |
| + claude-mem or /memory habit | ~2,000 | $2-7 |

### Across Our 12-Person Team

| Scenario | Monthly | Annually |
|----------|---------|----------|
| No optimization | $660-1,980 | $7,900-23,800 |
| Full setup (both guides) | $24-84 | $290-1,010 |
| **Savings** | **$636-1,896** | **$6,900-22,700** |

---

## Action Items

### Today (10 minutes)
- [ ] Create your personal global config file (see your tool's section above)
- [ ] **Zed users:** Change tab context to `"pinned"` right now
- [ ] **VS Code users:** Enable Copilot Memory on github.com

### This Week
- [ ] **Claude Code users:** Start ending sessions with `/memory`
- [ ] **OpenCode users:** Add the Haiku summarizer to your config
- [ ] Tell Hermes about yourself: go to [chat.getarctan.com](https://chat.getarctan.com) and say "I'm [name], I work on [area]"

### When You Want Maximum Savings
- [ ] **Claude Code users:** Install claude-mem plugin
- [ ] Make sure your repos have AI context files → **[Repository AI Context Setup](repo-ai-context-setup.md)**

---

*Questions? Ask Hermes at [chat.getarctan.com](https://chat.getarctan.com) or DM @hermesbot on Slack.*
