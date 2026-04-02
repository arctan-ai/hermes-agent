# Save Money on Claude: Install claude-mem

> **One-time setup. 2 minutes. Saves ~60-80% on Claude token costs for coding.**

---

## The Problem You Don't Know You Have

Every time you start a new Claude Code session to work on the same project, Claude starts with **zero memory** of what you did before. So you end up re-explaining:

- "This is a Tauri app with Rust backend and React frontend..."
- "The audio pipeline flows from cpal → DeepFilterNet → Beatrice..."
- "The bug was in deep_filter.rs, line 97..."

Each time, Claude reads your files again, rebuilds context, and burns through tokens — **just to get back to where you left off yesterday**.

This is like hiring a contractor who gets amnesia every evening and needs a full re-briefing every morning.

**The cost of this:**
```
Without memory:  ~50,000 tokens to rebuild context per session
                 × 5 sessions/day
                 × 22 working days
                 = 5.5 million wasted tokens/month
                 = ~$55-165/month burned on re-explaining
                   (per person!)
```

---

## The Fix: claude-mem

**claude-mem** is a plugin for Claude Code that gives Claude persistent memory.

After you install it:
1. Claude remembers what you worked on yesterday
2. It remembers the bugs you fixed, decisions you made, patterns you followed
3. It compresses everything into tiny summaries (not raw file dumps)
4. Next session, it loads only what's relevant — in ~2,000 tokens instead of 50,000

```
With claude-mem:  ~2,000 tokens of compressed context per session
                  (instead of 50,000)
                  
                  That's a 96% reduction in context setup cost.
```

**It's free, open-source, and used by 44,000+ developers.**

---

## Install It (2 minutes)

### Prerequisites

You need **Claude Code** installed. If you don't have it yet:
```bash
npm install -g @anthropic-ai/claude-code
```

You also need **Node.js 18+** (you probably already have this).

### Step 1: Open Claude Code

Open your terminal and start Claude Code in any project:
```bash
cd your-project
claude
```

### Step 2: Install the Plugin

Inside the Claude Code session, type these two commands:

```
/plugin marketplace add thedotmack/claude-mem
```

Then:

```
/plugin install claude-mem
```

### Step 3: Restart Claude Code

Exit (`Ctrl+C` or type `/exit`) and start Claude Code again:

```bash
claude
```

**That's it. You're done.**

---

## What Happens Now (You Don't Need to Do Anything)

From this point on, claude-mem works **automatically in the background**:

### During Your Session
- claude-mem quietly watches what Claude does (file edits, tool calls, decisions)
- It captures key observations without slowing anything down
- You won't notice any difference in how you use Claude

### When You End a Session
- claude-mem compresses everything Claude learned into concise summaries
- These are stored locally on your machine (in a SQLite database)
- Nothing is sent anywhere — it's all local

### When You Start a New Session
- claude-mem automatically loads relevant compressed context
- Claude "remembers" your project, recent work, and decisions
- You can jump straight into productive work — no re-explaining needed

### What It Looks Like

**Before claude-mem:**
```
You: "I'm working on the audio pipeline in arctan-client. 
      The issue is crackling when..."
[30 minutes of Claude re-reading files and rebuilding context]
[50,000 tokens spent just getting oriented]
```

**After claude-mem:**
```
You: "Continue fixing the crackling issue"
Claude: "I see from our previous session that we identified the 
         spin-wait polling in deep_filter.rs line 97 as the root 
         cause. We were implementing the event-based approach. 
         Let me pick up where we left off..."
[2,000 tokens of compressed context — straight to work]
```

---

## Useful Commands (Optional — You Don't Need These to Get Started)

Once claude-mem is running, you have a few optional tools:

### Search Your Memory
Inside a Claude Code session:
```
/mem-search "audio pipeline crackling fix"
```
This searches across all your past sessions for relevant context.

### View the Memory Dashboard
Open in your browser while Claude Code is running:
```
http://localhost:37777
```
This shows a real-time view of what claude-mem has stored.

### Mark Something as Private
If you're working with sensitive data you don't want stored:
```
<private>
This API key is sk-abc123...
</private>
```
Anything inside `<private>` tags won't be saved to memory.

---

## How Much Money Does This Actually Save?

### Per Person

| Metric | Without claude-mem | With claude-mem |
|--------|-------------------|-----------------|
| Context tokens per session | ~50,000 | ~2,000 |
| Sessions per day | 5 | 5 |
| Monthly context tokens | 5.5M | 220K |
| Monthly context cost (Claude) | $55-165 | $2-7 |
| **Monthly savings** | — | **$50-160** |

### For Our 12-Person Team

| Metric | Without | With | Savings |
|--------|---------|------|---------|
| Monthly context tokens | 66M | 2.6M | 63.4M tokens |
| Monthly context cost | $660-1,980 | $26-78 | **$634-1,902** |
| Annual savings | — | — | **$7,600-22,800** |

> **Note:** These are estimates for the context re-building cost only. You'll still spend tokens on the actual coding work — claude-mem just eliminates the wasteful "getting Claude up to speed" cost that you pay every single session.

### The Hidden Benefit: Speed

Beyond cost, claude-mem makes sessions **faster**. Instead of spending the first 5-10 minutes of each session waiting for Claude to re-orient, you start productive work immediately. That's 25-50 minutes saved per day per person.

---

## FAQ

**Q: Does it slow down Claude Code?**
No. It runs in the background and doesn't affect Claude's response time.

**Q: Where is the data stored?**
Locally on your machine. Nothing is sent to any external server.

**Q: Does it work with our Arctan repos?**
Yes. It works with any project. It's especially useful for complex codebases like arctan-client (Rust + React) where context setup is expensive.

**Q: Can I use it alongside the Hermes AI assistant?**
Yes. They serve different purposes:
- **claude-mem + Claude Code** = coding with persistent memory (local, in your IDE)
- **Hermes** = queries, analytics, project management, research (shared, in browser/Slack)

**Q: What if I switch between projects?**
claude-mem stores memory per project directory. Each project gets its own memory.

**Q: Can I delete the memory if needed?**
Yes. The memory is stored in `.claude-mem/` in your project directory. Delete it to start fresh.

**Q: Does it work on Mac and Windows?**
Yes. Anywhere Claude Code runs, claude-mem works.

**Q: Is it safe for production codebases?**
Yes. It only stores summaries of observations — not your actual source code. Use `<private>` tags for sensitive content.

---

## Troubleshooting

### "Plugin not found"
Make sure you run both commands in order:
```
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```
Then restart Claude Code.

### "Worker not starting"
Check that Node.js 18+ is installed:
```bash
node --version
# Should be v18.0.0 or higher
```

### "Memory not loading in new sessions"
Make sure you're starting Claude Code from the same project directory. Memory is per-project.

### Still having issues?
Ask the Hermes AI assistant on https://chat.getarctan.com:
> "I'm having trouble with claude-mem, it says [error message]. How do I fix it?"

---

## Summary

| What | Details |
|------|---------|
| **What to install** | claude-mem plugin for Claude Code |
| **How long** | 2 minutes |
| **Effort** | Zero after install (fully automatic) |
| **Token savings** | ~60-80% on context setup costs |
| **Money saved** | ~$50-160/person/month |
| **Speed improvement** | 5-10 minutes saved per session |
| **Privacy** | All data stored locally, nothing shared |

**Install it today. Your future self (and your API bill) will thank you.**

---

*Guide by the Arctan Engineering team — April 2026*
*Questions? Ask Hermes at https://chat.getarctan.com or DM @hermesbot on Slack*
