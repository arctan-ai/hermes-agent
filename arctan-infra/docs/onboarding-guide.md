# 🎧 Arctan AI Workflow Guide

> We've connected an AI assistant to our Plane boards, analytics database, AWS infrastructure, and all 12 repos. Here's how to use it — and how to stop wasting money on your individual Claude sessions.

---

## Table of Contents

**Part 1: The Shared AI Assistant (Hermes)**
1. [What We Built](#1-what-we-built)
2. [Get In (2 minutes)](#2-get-in)
3. [Day-to-Day Usage: What To Ask It](#3-day-to-day-usage)
4. [Arctan-Specific Examples](#4-arctan-specific-examples)
5. [What It Knows About Our Stack](#5-what-it-knows-about-our-stack)
6. [Using It From Slack](#6-using-it-from-slack)
7. [Access Levels & Permissions](#7-access-levels--permissions)

**Part 2: Your Individual AI Tools**
8. [How Hermes Fits With Your Coding Tools](#8-how-hermes-fits-with-your-coding-tools)
9. [Stop Wasting Tokens: Per-Tool Setup](#9-stop-wasting-tokens)
10. [The Shared Context File: AGENTS.md](#10-the-shared-context-file)

**Part 3: Reference**
11. [Tips for Better Results](#11-tips-for-better-results)
12. [Privacy, Memory & Data](#12-privacy-memory--data)
13. [Cost Breakdown](#13-cost-breakdown)
14. [FAQ](#14-faq)

---

# Part 1: The Shared AI Assistant

## 1. What We Built

We deployed an AI assistant called **Hermes** that every Arctan team member can use through a web chat or Slack. Unlike ChatGPT or a personal Claude subscription, this assistant is wired into our actual systems:

| System | What the AI can do |
|--------|-------------------|
| **Plane** (all 6 projects) | Query issues, create new issues, update status, add comments |
| **ClickHouse** (88M+ metrics) | Run SQL queries on user activity, call data, performance metrics |
| **AWS** (production-cluster) | Check ECS services, EC2 instances, security groups (read-only) |
| **All 12 repos** | Answer questions about architecture, conventions, known bugs |
| **Web** | Search, browse sites, read documentation, summarize articles |

It also has **persistent memory** — it remembers who you are, what you work on, and your preferences across sessions. Each person's memory is private and isolated.

**Think of it this way:**
- ChatGPT knows the internet but nothing about Arctan
- Your local Claude Code knows the files open in your terminal but nothing about our Plane boards or analytics
- **Hermes knows Arctan** — the codebase, the data, the projects, and you

---

## 2. Get In

### Step 1: Go to [chat.getarctan.com](https://chat.getarctan.com)

### Step 2: Click "Sign in with Google"
Use your **@arctan.ai** account. Personal Gmail won't work.

### Step 3: Pick the model
Select **hermes-agent** from the dropdown at the top. It should be the only model available.

### Step 4: Say hello
Type something like:

> "Hey, I'm [your name]. I work on [your team/project]. What can you help me with?"

The AI will introduce itself and remember you. From now on, it knows your name and context.

**That's it. You're in.**

---

## 3. Day-to-Day Usage

Here's what you'll actually use this for on a typical day at Arctan:

### 🔎 "What's going on?"
> "Show me all urgent and high-priority issues in the Engineering project"

> "How many calls did our users make yesterday?"

> "What's the status of the ClickHouse ECS service?"

### ✏️ "I need to update something"
> "Create a new issue in Engineering: 'Investigate Realtek driver compatibility on Windows 11' with high priority, assign it to me"

> "Add a comment to ENGINEERIN-23 saying 'Tested on Build 22631, crackling still present at 48kHz'"

> "Move DATASCIENC-7 to completed"

### 📊 "I need data"
> "Show me daily active users for the last 30 days, grouped by organization"

> "What's the average model latency for ICCS users this week? Compare it to last week"

> "How many users have packet loss above 5%? Which organizations are they from?"

> "Show me signup growth month over month for the last 6 months"

### 🤔 "How does this work?"
> "Explain the audio pipeline in arctan-client. I need to understand the flow from cpal input to Beatrice output"

> "What are the known caveats with the audio driver? I'm about to start testing on a new build"

> "How does PeerDB sync data from Postgres to ClickHouse? I'm seeing a delay in the analytics"

> "What's the structure of the console-gateway project? I need to add a new API endpoint"

### 🔬 "I need research"
> "Search for the latest WebRTC audio processing libraries for noise cancellation. Compare alternatives to DeepFilterNet"

> "Go to the ClickHouse docs and find how to optimize queries on ReplacingMergeTree tables — we have duplicates in the metrics table"

> "Find the LiveKit SDK docs for Go and summarize the room management API"

### 📝 "I need content"
> "Draft a release notes email for the v2.1 desktop client update. The key changes are: AGC improvement, new Beatrice model support, and the ring buffer fix"

> "Write a tech spec outline for adding delta updates to the client app"

> "Summarize this meeting transcript and create Plane issues for each action item: [paste text]"

---

## 4. Arctan-Specific Examples

These are real queries you can run right now using actual Arctan data:

### Engineering Team

```
You: "What issues are open in Engineering with urgent or high priority?"

Hermes: Found 8 issues:
  [urgent] ENGINEERIN-12: Automatic Gain Control
  [urgent] ENGINEERIN-14: Record After Gain
  [high]   ENGINEERIN-23: Refactoring the gender detection logic
  [high]   ENGINEERIN-27: Delta Update feature
  ...
```

```
You: "What's the average model latency for the last 24 hours, 
      broken down by the top 5 users?"

Hermes: [Runs SQL on ClickHouse]
  ┌─user_name───────┬─avg_latency─┬─samples──┐
  │ user_alpha       │      18.4ms │   12,450 │
  │ user_beta        │      14.2ms │    8,321 │
  │ user_gamma       │      12.7ms │   15,672 │
  │ user_delta       │      11.9ms │    9,543 │
  │ user_epsilon     │      10.1ms │   11,234 │
  └──────────────────┴─────────────┴──────────┘
```

### Data Science Team

```
You: "How many distinct users made calls each day this week?"

Hermes: [Runs SQL on ClickHouse]
  Mon: 142 users (2,341 calls)
  Tue: 156 users (2,567 calls)
  Wed: 148 users (2,412 calls)
  Thu: 161 users (2,689 calls)
  Fri: 139 users (2,198 calls)
  Total unique: 203 users, 12,207 calls
```

```
You: "Show me the distribution of activity types this month"

Hermes: [Runs SQL]
  generic_activity:    2,145,000  (94.2%)
  call_started:           62,400  (2.7%)
  call_ended:             61,200  (2.7%)
  APPLICATION_CLOSED:      4,100  (0.2%)
  login:                     380  (0.02%)
  ...
```

### Business / Product Team

```
You: "How many organizations do we have, and what's the user 
      distribution across the top 10?"

Hermes: [Queries ClickHouse]
  42 organizations total, 538 users.
  Top 10:
    ICCS:           146 users (27.1%)
    MegaaOpes:       78 users (14.5%)
    Grassroots:      52 users (9.7%)
    Goalcryst:       41 users (7.6%)
    Value Logistics:  38 users (7.1%)
    Arctan.ai:       23 users (4.3%)
    ...
```

```
You: "Create an issue in Customer Onboarding: 'Prepare onboarding 
      deck for ValueLogistics pilot' with medium priority, due April 15"

Hermes: Created CUSTOMERON-19
  Title: Prepare onboarding deck for ValueLogistics pilot
  Priority: Medium
  Due: 2026-04-15
  URL: https://app.plane.so/arctan/...
```

### Infrastructure / DevOps

```
You: "What ECS services are running in production? Show task status"

Hermes: [Queries AWS]
  production-cluster:
    production-clickhouse:  1/1 running (FARGATE, 2 vCPU, 4GB)
    production-peerdb:      1/1 running (FARGATE)
```

```
You: "What's the private IP of the ClickHouse container?"

Hermes: [Queries AWS ECS]
  Task: a26ff891...
  Private IP: 172.31.13.161
  AZ: ap-south-1b
  Status: RUNNING
```

---

## 5. What It Knows About Our Stack

Hermes has indexed documentation from every Arctan repo. You don't need to tell it what our product is — it already knows.

### Architecture Knowledge

```
Client Layer
├── arctan-client          Tauri v2 desktop app (Rust + React)
│                          Audio: cpal → DeepFilterNet → Beatrice → cpal
├── arctan-client-app      Unified web + desktop (TypeScript)
└── client-dashboard       Admin panel (React + FastAPI)

Gateway Layer
├── console-gateway        API gateway (Go) + React console, Google OAuth
└── livekit-gateway        WebRTC media server (Go + LiveKit)

Service Layer
├── auth-service           User auth + config (Flask + PostgreSQL)
├── db-service             DB lifecycle + migrations (Alembic)
├── inference-server       Voice changer ML models (Python, CUDA/DML)
└── logging-service        Metrics → ClickHouse (Python)

Infrastructure
├── audio-driver           Windows WDM virtual audio driver (C++)
├── infra-service          Docker configs: ClickHouse, Grafana, PeerDB, nginx
└── hermes-agent           This AI system (Python)
```

### Detailed Reference Docs Loaded
- **Audio pipeline analysis** — crackling root causes, ring buffer optimizations
- **Audio driver caveats** — Code 10 errors, buffer sizing, HLK testing
- **PeerDB CDC setup** — how Postgres data flows to ClickHouse
- **AGENTS.md** — coding standards for arctan-client

### Database Schema (ClickHouse)

| Table | Rows | What's In It |
|-------|------|-------------|
| `metrics` | 88M+ | model_latency, ping, cpu, ram, volume, packets, jitter, webrtc_stats |
| `user_activities` | 27M+ | activity_type (call_started, call_ended, login, etc), timestamps |
| `Users` | 538 | name, email, organization_id, license_type |
| `Organizations` | 42 | name, created_at |
| `internal_metrics` | 3M+ | JSON metric blobs |

### Plane Projects

| Project | Identifier | Use For |
|---------|-----------|---------|
| Engineering | ENGINEERIN | Core product development |
| Data Science | DATASCIENC | ML models, data pipeline |
| Customer Issues & Tracks | CUSTOMERIS | Client-reported issues |
| Customer Onboarding | CUSTOMERON | New client onboarding tasks |
| ARCTAN | ARCTA | General company tasks |
| Business | BUSINESS | Business development |

---

## 6. Using It From Slack

Hermes is also **@hermesbot** in Slack.

**DM it** for private questions:
> @hermesbot How many active users this week?

**Mention it in a channel** for team-visible answers:
> @hermesbot What are the urgent issues in Engineering?

**Use threads** for follow-ups — it keeps context within the thread.

Same capabilities, same access level. Use whichever is faster — the browser chat or Slack.

---

## 7. Access Levels & Permissions

Your access is set by an admin based on your Open WebUI role:

| What you can do | Admin | Team Member | New Signup |
|----------------|-------|-------------|------------|
| Search the web, browse sites | ✅ | ✅ | ✅ |
| Ask about our codebase | ✅ | ✅ | ✅ |
| Query Plane issues | ✅ | ✅ | ✅ |
| Create/update Plane issues | ✅ | ✅ | ❌ |
| Query ClickHouse analytics | ✅ | ✅ | ❌ |
| Query AWS infrastructure | ✅ | ✅ | ❌ |
| Personal memory | ✅ | ✅ | ❌ |
| Run shell commands on server | ✅ | ❌ | ❌ |
| Write/edit files on server | ✅ | ❌ | ❌ |
| Create scheduled tasks | ✅ | ❌ | ❌ |

**You'll be added as "Team Member"** — full access to all integrations, no ability to modify the server.

Need more access? Ask an admin.

---

# Part 2: Your Individual AI Tools

## 8. How Hermes Fits With Your Coding Tools

You already use AI for coding. Here's how Hermes complements — not replaces — that:

| Task | Use Hermes | Use Your Coding Tool |
|------|-----------|---------------------|
| "How many active users this week?" | ✅ queries ClickHouse | ❌ can't access our DB |
| "Create an issue in Plane" | ✅ creates it directly | ❌ you'd do it manually |
| "How does the auth-service work?" | ✅ knows all 12 repos | ⚠️ only knows open files |
| "Refactor this Rust function" | ❌ can't edit your files | ✅ edits in your IDE |
| "Debug this stack trace" | ❌ can't run your code | ✅ runs locally |
| "Find a WebRTC library" | ✅ searches + browses web | ⚠️ limited in most tools |
| "Quick question from my phone" | ✅ web + Slack | ❌ need your laptop |

**Rule of thumb:**
- **Hermes** = organization-level questions, data, project management, research
- **Your tool** = hands-on coding, debugging, refactoring

---

## 9. Stop Wasting Tokens

Every time you start a new session in Claude Code, OpenCode, Zed, or VS Code, Claude rebuilds context from scratch. That's ~50,000 tokens wasted per session just getting oriented.

**The fix takes 5-10 minutes and saves $50-160/person/month.**

We have a detailed per-tool guide:

👉 **[Token Savings Guide](claude-mem-setup-guide.md)**

Quick summary of what to do for each tool:

### VS Code + Copilot
1. Enable **Copilot Memory** in GitHub Settings → Copilot → Features
2. Create `.github/copilot-instructions.md` in each repo with project context
3. Set tab context to "pinned" or "none" to avoid sending all open files

### Claude Code (iTerm2)
1. Create `~/.claude/CLAUDE.md` with your global preferences
2. Run `/memory` at the end of each session (2 seconds, saves thousands of tokens next time)
3. Optional: install **claude-mem** plugin for fully automatic memory

### OpenCode (Ghostty)
1. Create `~/.config/opencode/context.md` with your global preferences
2. Add a cheap summarizer model (Haiku) to your config for context compression
3. Use `/compact` to shrink long conversations

### Zed
1. Create `~/.config/zed/rules.md` with your global preferences
2. Change tab context to `"pinned"` in settings (stop sending all open tabs)
3. Use `@thread` to reference previous conversations instead of re-explaining

---

## 10. The Shared Context File

**This is the single highest-impact thing the team can do together.**

`AGENTS.md` is a file in the root of a repo that every AI tool reads automatically — Claude Code, OpenCode, Zed, and Copilot all support it. It tells the AI about the project's architecture, conventions, and gotchas.

**arctan-client already has one.** If your repo doesn't, create one:

```markdown
# AGENTS.md

## Project Overview
[What this service does in 2-3 sentences]

## Tech Stack
[Language, framework, key libraries]

## Structure
[Key directories and what they contain]

## Conventions
[Naming, error handling, patterns]

## Build & Run
[How to build, test, run locally]

## Known Gotchas
[Things that trip people up]
```

Commit it to git. Everyone who pulls gets it. Every AI tool reads it automatically.

**Token impact:** One 500-token file replaces 10,000-50,000 tokens of Claude re-discovering your project structure by reading random files. That's a **95% reduction** in context setup cost.

---

# Part 3: Reference

## 11. Tips for Better Results

### Be specific
```
❌  "Show me the data"
✅  "Show me daily active users for the last 30 days, grouped by organization, 
     sorted by user count descending"
```

### Give Arctan context
```
❌  "Fix the bug"
✅  "I'm working on ENGINEERIN-23, the gender detection refactor in inference-server. 
     The threshold is currently 0.5. What are the tradeoffs of changing it to 0.7?"
```

### Chain tasks together
```
"Check how many calls had packet loss > 5% last week. 
 Find which organizations those users belong to. 
 Create a Plane issue in Customer Issues summarizing the problem."
```

### Teach it about you
Tell it things once — it remembers forever:
- "I work on the audio driver and inference server"
- "I prefer short answers with code examples"
- "When I ask about metrics, default to the last 7 days"

### Follow up naturally
It remembers the conversation:
- "Now show just the top 5"
- "Filter that to only ICCS users"
- "Plot that as a markdown table"

---

## 12. Privacy, Memory & Data

**Your conversations are private.** No one else can see your chat history or what the AI remembers about you.

**Your memory is isolated.** What it learns about your preferences is stored separately per user on our EC2 server in ap-south-1.

**LLM calls go through OpenRouter → Anthropic.** They don't use your data for training. Use the same judgment as with any cloud AI tool — don't paste customer PII, API keys, or passwords.

**Shared knowledge is read-only.** There's an org-wide knowledge base (company info, codebase architecture) that everyone can access but only admins can edit.

**You can reset your memory** anytime: just say "forget everything you know about me."

---

## 13. Cost Breakdown

### Shared Hermes Setup

| Component | Monthly Cost |
|-----------|-------------|
| EC2 t3.large (ap-south-1) | ~$60 |
| Claude API via OpenRouter | ~$240-480 (usage-based, 12 people) |
| Open WebUI + Caddy + Hermes | Free (open source) |
| **Total** | **~$300-540/mo (~$25-45/person)** |

### Your Individual Coding Tools

| Tool | Typical Monthly Cost |
|------|---------------------|
| VS Code + Copilot (Claude) | $10-39 subscription + API usage |
| Claude Code (iTerm2) | ~$20-60 (API usage) |
| OpenCode (Ghostty) | ~$20-60 (API usage) |
| Zed (Claude API) | ~$20-60 (API usage) |

### With Token Optimization (see [Token Savings Guide](claude-mem-setup-guide.md))

| Scenario | Monthly per person | Annual team savings |
|----------|-------------------|-------------------|
| No optimization | $20-80 | — |
| With AGENTS.md + tool memory | $5-20 | **$7,000-22,000** |

### Why Both Are Worth It

Hermes gives you capabilities no local tool can match — querying ClickHouse, managing Plane, searching AWS, accessing cross-repo knowledge. Your local tools give you hands-on coding that Hermes can't do. Together they cover everything.

The shared setup pays for itself if it saves each person **15-20 minutes per week** on data lookups, issue management, or knowledge questions. At engineering rates, that's $120-200/week saved across the team.

---

## 14. FAQ

**Q: How is this different from ChatGPT or Claude.ai?**
It's connected to our internal systems. ChatGPT can't query our ClickHouse database or create Plane issues. Hermes can, because we've built custom tools that integrate with our actual infrastructure.

**Q: Should I stop using Claude Code / OpenCode / Zed / VS Code for coding?**
No. Keep using them for coding. Use Hermes for everything else — data queries, project management, research, codebase questions, content drafting.

**Q: Can it see my local files?**
No. It runs on our EC2 server, not your laptop. It can access server files and query connected systems (Plane, ClickHouse, AWS), but not your local machine.

**Q: Is it safe to paste code?**
Messages go through OpenRouter to Anthropic for processing. Use the same judgment as with any cloud AI tool — don't paste customer PII, credentials, or secrets.

**Q: Can I use it on my phone?**
Yes. Both [chat.getarctan.com](https://chat.getarctan.com) and the Slack @hermesbot work on mobile.

**Q: It gave me wrong data. What do I do?**
AI can hallucinate. For data queries, ask it to show the SQL it ran — then verify the logic. For code suggestions, always test before using. For factual claims, cross-reference.

**Q: How do I report a bug in Hermes itself?**
Ask it: "Create a Plane issue in the ARCTAN project: '[describe the bug]'". Or message an admin directly.

**Q: What model is it running?**
Claude Opus 4.6 by Anthropic, routed through OpenRouter.

**Q: I'm stuck. What should I try first?**
Just ask it: "What can you help me with?" — it'll list its capabilities. Or try one of the examples from [Section 3](#3-day-to-day-usage).

---

## Getting Help

| Channel | When to use |
|---------|------------|
| Ask Hermes itself | "What can you do?" or "Help me with..." |
| Slack @hermesbot | Quick questions from any channel |
| Your admin | Access issues, role changes |
| Plane (ARCTAN project) | Bug reports, feature requests |

---

*Last updated: April 2026 · Powered by Hermes Agent + Claude Opus 4.6*
