# Stop Wasting Tokens: AI Memory Setup for Your Workflow

> **10 minutes of setup. Save 60-80% on Claude context costs. Works with every tool we use.**

---

## The Problem

Every time you start a new AI session on the same project, Claude starts from scratch. It re-reads files, re-discovers patterns, re-learns your conventions. You're paying for the same context over and over.

```
Session 1:  "This is a Tauri app with Rust + React..."     50,000 tokens
Session 2:  "This is a Tauri app with Rust + React..."     50,000 tokens  (again)
Session 3:  "This is a Tauri app with Rust + React..."     50,000 tokens  (again)
```

**That's ~$55-165/month per person in wasted context tokens.**

The fix: give Claude persistent context so it doesn't start from zero. How you do it depends on which tool you use.

---

## Find Your Setup

| If you use... | Jump to... |
|--------------|------------|
| **VS Code + Copilot** (with Claude API) | [Section 1](#1-vs-code--github-copilot) |
| **iTerm2 + Claude Code** | [Section 2](#2-claude-code-iterm2) |
| **Ghostty + OpenCode** | [Section 3](#3-opencode-ghostty) |
| **Zed** (with Claude API) | [Section 4](#4-zed-editor) |
| All of the above | [Section 5](#5-the-shared-layer) — do this first! |

---

## 5. The Shared Layer (Do This First — Everyone Benefits)

Before touching your individual tool, we'll add context files to our repos that **every tool reads automatically**. One setup, works everywhere.

### AGENTS.md — The Universal Context File

`AGENTS.md` is a convention that Claude Code, OpenCode, Zed, and Copilot all support. It tells the AI about your project's structure, conventions, and how things work.

**The arctan-client repo already has one!** Check if your repo does too:

```bash
ls AGENTS.md
```

If it doesn't exist, create one. Here's a template:

```markdown
# AGENTS.md

## Project Overview
[What this project does, in 2-3 sentences]

## Tech Stack
[Languages, frameworks, key libraries]

## Project Structure
[Key directories and what they contain]

## Code Conventions
[Naming, style, patterns to follow]

## Common Tasks
[How to build, test, deploy]
```

**Why this works:** Every AI tool reads this file automatically. You write it once, and Claude knows your project in every tool — VS Code, terminal, Zed, everywhere. No more re-explaining.

**Token impact:** A good AGENTS.md is ~500-1000 tokens. It replaces 10,000-50,000 tokens of Claude re-discovering your project by reading random files.

### Commit it to Git

AGENTS.md goes in your repo root. When everyone pulls, everyone gets it:

```bash
git add AGENTS.md
git commit -m "docs: add AGENTS.md for AI context"
git push
```

---

## 1. VS Code + GitHub Copilot

### What You Have
VS Code with GitHub Copilot, using Claude as the model via your API key.

### Built-in Context System

Copilot already has three context features most people don't use:

#### a) Custom Instructions File (5 minutes)

Create `.github/copilot-instructions.md` in your repo root:

```markdown
# Copilot Instructions

## Project
This is [project name] — [brief description].

## Conventions
- [Your coding conventions]
- [Preferred patterns]
- [What to avoid]

## Architecture
- [Key architectural decisions]
- [Important file locations]
```

This file is **automatically included** in every Copilot Chat request. Write it once, forget about it.

#### b) Copilot Memory (2 minutes)

Copilot now has built-in memory (launched April 2025). Enable it:

1. Go to **github.com** → **Settings** → **Copilot** → **Features**
2. Turn on **Memory**
3. Done

Now Copilot remembers your preferences across sessions. You can tell it things like:
- "I prefer functional components in React"
- "Always use early returns in Rust"
- "Our API endpoints follow REST conventions"

It stores these and applies them automatically.

#### c) Scoped Instructions (optional, advanced)

For different file types, create files in `.github/instructions/`:

```
.github/instructions/
  rust-conventions.md     ← applies when editing .rs files
  react-conventions.md    ← applies when editing .tsx files
  testing-guidelines.md   ← applies when editing test files
```

Each file can have a front matter with a glob pattern to scope when it's applied.

### Token Savings Tips

1. **Use `@file` references** instead of pasting code into chat
2. **Start new chats** for unrelated topics (old history burns tokens)
3. **Use Sonnet** for routine tasks, Opus only when you need deep reasoning
4. **Keep instruction files concise** — they load on every request

---

## 2. Claude Code (iTerm2)

### What You Have
Claude Code CLI in iTerm2, using your Anthropic API key.

### Built-in Memory: CLAUDE.md (2 minutes)

Claude Code has the **best** built-in memory system. It uses `CLAUDE.md` files — and you might not be using them.

#### How It Works

Claude Code reads `CLAUDE.md` files from three places:

```
~/.claude/CLAUDE.md          ← Global (all projects)
./CLAUDE.md                  ← Project root (this project)
./src/CLAUDE.md              ← Directory-specific (this folder)
```

#### Quick Setup

**Step 1: Create a global CLAUDE.md**

```bash
mkdir -p ~/.claude
cat > ~/.claude/CLAUDE.md << 'EOF'
# Global Preferences

- I work at Arctan on real-time voice processing
- Prefer concise responses with code examples
- Use early returns and guard clauses
- Always handle errors explicitly
- My timezone is IST
EOF
```

**Step 2: The `/memory` command**

While working in Claude Code, whenever Claude learns something useful, type:

```
/memory
```

Claude will save key observations to your project's CLAUDE.md automatically. Do this at the end of each session — it takes 2 seconds and saves thousands of tokens next time.

**Step 3: Also reads AGENTS.md**

Claude Code automatically reads `AGENTS.md` files too. If you did [Section 5](#5-the-shared-layer), you're already covered.

### claude-mem Plugin (5 minutes — optional, extra savings)

For even more automatic memory, install **claude-mem**:

```
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

Restart Claude Code. Now it:
- Automatically captures what you work on (no /memory needed)
- Compresses observations into tiny summaries
- Injects only relevant context in future sessions
- Has a web dashboard at http://localhost:37777

**claude-mem vs CLAUDE.md:**

| Feature | CLAUDE.md | claude-mem |
|---------|-----------|------------|
| Setup | Built-in, zero install | Plugin, 2 commands |
| How it works | You manually run /memory | Fully automatic |
| What it stores | Key facts you tell it | Everything Claude does |
| Token savings | Good (~60% reduction) | Better (~80% reduction) |
| Recommendation | **Start here** | Add later for max savings |

### Token Savings Tips

1. **Use `/compact`** when conversations get long — it summarizes history
2. **Use Haiku** for simple tasks: `claude --model claude-3-5-haiku "quick question"`
3. **Run `/memory` before ending** each significant session
4. **Keep CLAUDE.md under 2000 tokens** — it loads every session

---

## 3. OpenCode (Ghostty)

### What You Have
OpenCode CLI in Ghostty terminal, using your Anthropic API key.

### Context Files (5 minutes)

OpenCode supports the same AGENTS.md convention plus its own context system:

#### Context File Locations

```
~/.config/opencode/context.md    ← Global (all projects)
.opencode/context.md             ← Project-specific
opencode.md                      ← Alt project-specific
AGENTS.md                        ← Standard convention (auto-read)
```

**Quick Setup:**

```bash
# Global context
mkdir -p ~/.config/opencode
cat > ~/.config/opencode/context.md << 'EOF'
# Coding Preferences

- I work at Arctan on real-time audio/video processing
- Prefer concise, well-tested code
- Always handle errors explicitly
- Use early returns
EOF
```

For project-specific context, create `.opencode/context.md` in your repo root (or just use AGENTS.md from [Section 5](#5-the-shared-layer)).

You can also add custom files in your config:

```toml
# opencode.toml or .opencode/config.toml
[context]
files = [
  "./docs/architecture.md",
  "./CONVENTIONS.md"
]
```

### Use a Cheap Summarizer Model (2 minutes)

OpenCode has a brilliant feature: you can use a **cheaper model** for context summarization. Add this to your config:

```toml
[model.default]
provider = "anthropic"
model = "claude-sonnet-4-20250514"

[model.summarizer]
provider = "anthropic"
model = "claude-3-5-haiku-20241022"
max_tokens = 4000
```

Now when conversations get long, OpenCode uses the cheap Haiku model to summarize old messages instead of the expensive Sonnet/Opus. This alone can cut costs 5-10x on long sessions.

### Token Savings Tips

1. **Use `/compact`** to manually trigger context summarization
2. **Set a cheap summarizer** (Haiku) — see above
3. **Use session forking** for exploring different approaches
4. **Keep context files under 1000 tokens** each
5. **Use `--prompt`** for one-shot questions (avoids session overhead)

---

## 4. Zed Editor

### What You Have
Zed with built-in AI assistant, using your Anthropic API key.

### Rules Files (3 minutes)

Zed uses "rules files" — persistent instructions loaded into every AI interaction.

#### Rules File Locations

```
.zed/rules.md           ← Project rules (in repo root)
.rules                  ← Alt project rules
~/.config/zed/rules.md  ← Global rules (all projects)
AGENTS.md               ← Standard convention (auto-read, scoped by directory)
```

**Quick Setup:**

```bash
# Global rules
cat > ~/.config/zed/rules.md << 'EOF'
# AI Rules

- Be concise and practical
- Show code, not just explanations
- Handle errors explicitly
- Follow existing code patterns in the project
EOF
```

For project-specific rules, create `.zed/rules.md` in your repo root, or use AGENTS.md from [Section 5](#5-the-shared-layer).

### Control Tab Context (biggest token saver)

By default, Zed sends ALL your open tabs as context. This burns tokens fast. Configure it:

```json
// ~/.config/zed/settings.json
{
  "assistant": {
    "context": {
      "tabs": "pinned",    // Only include tabs you explicitly pin
      "rules": true
    }
  }
}
```

Tab context modes:
- `"none"` — **cheapest**, no tab context
- `"pinned"` — **recommended**, only tabs you pin
- `"following"` — most expensive (default), includes whatever you're looking at

### Thread References

Zed doesn't have persistent memory yet, but you can reference past conversations:
- Type `@thread` in chat to search and include previous threads
- This avoids re-explaining decisions you've already discussed

### Token Savings Tips

1. **Set tabs to "pinned"** — biggest single saving
2. **Use `@file` mentions** instead of opening all files as tabs
3. **Start new threads** for new topics
4. **Use inline assist** (Ctrl+Enter) on selections for targeted help
5. **Keep rules files concise** — they load on every interaction

---

## Cheat Sheet: What Goes Where

| File | Who reads it | Where to put it |
|------|-------------|-----------------|
| `AGENTS.md` | Claude Code, OpenCode, Zed, Copilot* | Repo root (commit to git) |
| `CLAUDE.md` | Claude Code only | Repo root + `~/.claude/` |
| `.github/copilot-instructions.md` | VS Code Copilot | Repo root (commit to git) |
| `.opencode/context.md` | OpenCode only | Repo root |
| `.zed/rules.md` | Zed only | Repo root |
| `~/.config/zed/rules.md` | Zed | Home dir (personal) |
| `~/.config/opencode/context.md` | OpenCode | Home dir (personal) |
| `~/.claude/CLAUDE.md` | Claude Code | Home dir (personal) |

\* Copilot reads AGENTS.md via its coding agent feature.

**Pro tip:** Put shared knowledge in `AGENTS.md` (everyone benefits), tool-specific preferences in the tool's own config file.

---

## Expected Savings

### Per Person Per Month

| Scenario | Context Tokens/Session | Monthly Cost |
|----------|----------------------|-------------|
| No optimization | ~50,000 | $55-165 |
| AGENTS.md only | ~15,000 | $17-50 |
| AGENTS.md + tool memory | ~5,000 | $6-17 |
| Full setup (all of the above) | ~2,000 | $2-7 |

### For Our 12-Person Team

| Scenario | Monthly Cost | Annual Savings |
|----------|-------------|---------------|
| No optimization | $660-1,980 | — |
| Full setup | $24-84 | **$6,900-22,700** |

---

## Quick Action Items

**Today (5 minutes):**
- [ ] Check if your repo has AGENTS.md — if not, create one
- [ ] Set up your tool's context/rules file (see your section above)

**This Week (10 minutes):**
- [ ] If you use Claude Code: start using `/memory` at end of sessions
- [ ] If you use VS Code: enable Copilot Memory in GitHub settings
- [ ] If you use Zed: change tab context to "pinned"
- [ ] If you use OpenCode: add a cheap summarizer model to config

**Optional (when you want max savings):**
- [ ] Claude Code users: install claude-mem plugin
- [ ] Create `.github/copilot-instructions.md` for the team's VS Code users
- [ ] Add project-specific rules to your most-used repos

---

*Guide by the Arctan Engineering team — April 2026*
*Questions? Ask Hermes at https://chat.getarctan.com or DM @hermesbot on Slack*
