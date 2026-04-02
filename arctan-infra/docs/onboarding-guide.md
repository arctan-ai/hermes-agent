# Arctan AI Assistant — Team Onboarding Guide

> Your team now has access to a shared AI assistant that knows your codebase, can query your databases, manage project issues, and help with research — all through a simple chat interface.

---

## Table of Contents

1. [What Is This?](#1-what-is-this)
2. [Getting Started (2 minutes)](#2-getting-started)
3. [What Can You Do With It?](#3-what-can-you-do-with-it)
4. [Real Examples By Role](#4-real-examples-by-role)
5. [Access Levels](#5-access-levels)
6. [Tips for Getting Better Results](#6-tips-for-getting-better-results)
7. [What It Knows About Arctan](#7-what-it-knows-about-arctan)
8. [Slack Integration](#8-slack-integration)
9. [Privacy & Memory](#9-privacy--memory)
10. [Frequently Asked Questions](#10-frequently-asked-questions)
11. [Cost Analysis: Shared vs Individual AI Agents](#11-cost-analysis-shared-vs-individual-ai-agents)

---

## 1. What Is This?

We've set up **Hermes** — an AI agent that goes beyond a simple chatbot. Unlike ChatGPT or a basic Claude subscription, Hermes can:

- **Take actions**: query databases, search the web, browse websites, look up project issues
- **Remember context**: it remembers your preferences and past conversations across sessions
- **Access our tools**: it's connected to Plane (project management), ClickHouse (analytics database), and AWS (infrastructure)
- **Know our codebase**: it has documentation for all 12 Arctan repositories built into its knowledge base

Think of it as a team member that has read all our docs, has access to our project tracker and analytics, and is available 24/7.

**It is NOT:**
- A replacement for your IDE or coding tools
- An autonomous agent that will deploy code or modify production systems
- A place to share confidential customer data outside of what's already in our systems

---

## 2. Getting Started

### Step 1: Open the Chat Interface

Go to: **https://chat.getarctan.com**

### Step 2: Sign In with Google

Click **"Sign in with Google"** and use your **@arctan.ai** Google account. Only arctan.ai emails are allowed — no personal Gmail accounts.

### Step 3: Start Chatting

That's it. You'll see a chat interface similar to ChatGPT. Select the **hermes-agent** model from the model dropdown (it should be the only one), and start typing.

Your first message could be something like:
> "Hi! I'm [your name], I work on [your area]. What can you help me with?"

The AI will introduce its capabilities and remember who you are for future sessions.

---

## 3. What Can You Do With It?

### 🔍 Research & Web Search
- "Search for the latest papers on real-time voice conversion"
- "What are the best practices for WebRTC audio optimization?"
- "Compare LiveKit vs Janus for our use case"
- "Summarize this article: [paste URL]"

### 📊 Analytics & Data Queries
- "How many active users did we have this week?"
- "Show me call volume trends for the last 30 days"
- "What's the average model latency by organization?"
- "Which organizations have the most users?"
- "Show me user growth month-over-month"

The AI writes and runs SQL queries against our ClickHouse analytics database (88 million+ metrics rows, 27 million+ user activity events).

### ✈️ Project Management (Plane)
- "What are the urgent issues in the Engineering project?"
- "Show me all open issues assigned to me in Data Science"
- "Create a new issue in Engineering: 'Fix audio crackling on Windows 11' with high priority"
- "Update issue ENGINEERIN-42 to mark it as completed"
- "Add a comment to ARCTA-15 saying we need to discuss this in standup"

### ☁️ Infrastructure Queries (AWS)
- "List all ECS services running in production"
- "Show me the EC2 instances in ap-south-1"
- "What's the status of the clickhouse ECS task?"
- "Describe the security groups in our VPC"

(Read-only — the AI cannot modify infrastructure.)

### 📖 Codebase Knowledge
- "Explain the audio pipeline architecture in arctan-client"
- "What does the inference-server do?"
- "How is data synced from Postgres to ClickHouse?"
- "What's the structure of the console-gateway project?"
- "What are the known caveats with the audio driver?"

### 🌐 Web Browsing & Research
- "Browse the ClickHouse documentation and find how to optimize ReplacingMergeTree queries"
- "Go to our competitor's website and summarize their product features"
- "Find the npm package for WebRTC audio processing and check its API"

### 📝 General Assistance
- "Draft an email to the client about the new feature release"
- "Help me write a technical spec for the delta update feature"
- "Translate this error message from Japanese"
- "Create a summary of this meeting transcript: [paste text]"

---

## 4. Real Examples By Role

### For Engineers
```
You: "Show me all high-priority bugs in the Engineering project"

AI: [Uses plane_query tool]
    Found 5 high-priority issues:
    1. ENGINEERIN-23: Refactoring the gender detection logic
    2. ENGINEERIN-31: Audio crackling on specific Realtek drivers
    ...

You: "What's the average model latency over the past 24 hours?"

AI: [Uses clickhouse_query tool]
    Average model latency: 12.3ms
    95th percentile: 28.7ms
    Max: 142ms (user: john@client.com at 14:23)
    ...
```

### For Data Science
```
You: "Show me a breakdown of activity types for the last week"

AI: [Runs SQL query on ClickHouse]
    call_started:    12,450
    call_ended:      12,389
    login:           892
    streaming_started: 234
    ...

You: "Which users have the highest packet loss?"

AI: [Runs SQL query]
    Top 5 by avg packet loss:
    1. user_42 (org: MegaaOpes) — avg 3.2% loss
    ...
```

### For Business / Product
```
You: "How many new users signed up this month vs last month?"

AI: [Queries ClickHouse]
    This month: 47 new users
    Last month: 38 new users
    Growth: +23.7%

You: "Create a Plane issue for Customer Onboarding: 
      'Prepare demo for Acme Corp' with medium priority, 
      due date April 15"

AI: [Uses plane_update tool]
    Created: CUSTOMERON-18 "Prepare demo for Acme Corp"
    Priority: Medium | Due: April 15, 2026
```

### For Everyone
```
You: "I keep getting a CORS error in the console-gateway. 
      What does the documentation say about CORS configuration?"

AI: [Reads from its knowledge base]
    The console-gateway handles CORS in server/internal/middleware/.
    The HTTP_HTTPS_CONFIG.md doc explains that when running behind
    nginx, you should set USE_HTTPS=false and let nginx handle SSL
    termination. CORS headers are configured in...
```

---

## 5. Access Levels

Your access depends on your Open WebUI role (set by an admin):

| Capability | Admin | Team Member | Pending |
|-----------|-------|-------------|---------|
| Web search & browsing | ✅ | ✅ | ✅ |
| View codebase knowledge | ✅ | ✅ | ✅ |
| Query Plane issues | ✅ | ✅ | ✅ |
| Create/update Plane issues | ✅ | ✅ | ❌ |
| Query analytics (ClickHouse) | ✅ | ✅ | ❌ |
| Query AWS infrastructure | ✅ | ✅ | ❌ |
| Browse files on server | ✅ | ✅ | ❌ |
| Personal memory (remembers you) | ✅ | ✅ | ❌ |
| Run terminal commands | ✅ | ❌ | ❌ |
| Write/edit files | ✅ | ❌ | ❌ |
| Create cron jobs (scheduled tasks) | ✅ | ❌ | ❌ |
| Manage skills (modify AI knowledge) | ✅ | ❌ | ❌ |

**Most team members will be "Team Member" (user role)** — this gives you full access to all integrations without being able to modify the server or run arbitrary code.

If you need elevated access, ask an admin to upgrade your role.

---

## 6. Tips for Getting Better Results

### Be Specific
```
❌ "Show me the data"
✅ "Show me daily active users for the last 30 days, broken down by organization"
```

### Give Context
```
❌ "Fix the bug"
✅ "I'm working on ENGINEERIN-23, the gender detection refactor. 
    The current logic in inference-server uses a threshold of 0.5. 
    Help me understand the tradeoffs of changing it to 0.7"
```

### Ask Follow-up Questions
The AI remembers the conversation. You can say:
- "Now filter that to just the top 5"
- "Show me the same thing but for last month"
- "Export that as a CSV format"

### Use Multi-Step Tasks
```
"First, check how many calls had packet loss > 5% last week.
 Then look up which organizations those users belong to.
 Finally, create a Plane issue in Customer Issues with a summary."
```

### Teach It About Yourself
The AI has persistent memory per user. Tell it:
- "I work on the audio driver team"
- "I prefer concise answers with code examples"
- "My timezone is IST"

It will remember these across sessions.

---

## 7. What It Knows About Arctan

The AI has built-in knowledge about our entire stack:

### Repositories It Knows
| Repo | What It Knows |
|------|--------------|
| arctan-client | Tauri desktop app, audio pipeline, Rust + React architecture |
| arctan-client-app | Unified web + desktop client |
| audio-driver | Windows WDM driver, build process, known caveats |
| inference-server | Voice changer ML models, LiveKit integration |
| livekit-gateway | WebRTC media server, Go implementation |
| console-gateway | API gateway, Google OAuth, React console |
| auth-service | Flask auth, user registration, config management |
| db-service | Database migrations, Alembic, PostgreSQL |
| logging-service | Metrics collection, schema strategy |
| client-dashboard | React + FastAPI admin panel |
| infra-service | ClickHouse, Grafana, PeerDB, nginx configs |
| hermes-agent | This AI system itself |

### Databases It Can Query
- **ClickHouse Analytics**: 88M+ performance metrics, 27M+ user activities, 538 users, 42 organizations
- **Plane**: 6 projects (Engineering, Data Science, Customer Issues, Customer Onboarding, ARCTAN, Business)

### It Also Knows
- Audio pipeline internals (crackling root causes, ring buffer optimizations)
- PeerDB CDC setup (how data flows from Postgres to ClickHouse)
- Infrastructure topology (ECS services, security groups, networking)
- Build and deployment processes for each repo

---

## 8. Slack Integration

The AI is also available in Slack as **@hermesbot**. You can:

- DM @hermesbot directly for private conversations
- Mention @hermesbot in a channel for team-visible queries
- Use it in threads for contextual follow-ups

Slack conversations have the same tool access as your Open WebUI role.

---

## 9. Privacy & Memory

### What's Private
- **Your conversations are private.** Other team members cannot see your chat history.
- **Your memory is isolated.** What the AI remembers about you is stored separately from other users.
- **Chat history stays on our server.** Nothing is sent to third parties except the LLM API calls.

### What's Shared
- **Org memory**: There's a shared knowledge base that all users can see (company info, team roster, infrastructure details). Only admins can edit this.
- **Skills/knowledge**: Everyone sees the same codebase knowledge and tool capabilities.
- **LLM API calls**: Your messages are sent to the AI model provider (via OpenRouter → Anthropic) for processing. These providers have data processing agreements and don't use your data for training.

### Data Retention
- Chat sessions are stored on our EC2 server in ap-south-1
- The AI's memory about you persists across sessions until you ask it to forget
- You can say "forget everything you know about me" to wipe your personal memory

---

## 10. Frequently Asked Questions

**Q: Is this ChatGPT?**
No. This is Hermes Agent running Claude (by Anthropic) as the underlying model. Unlike ChatGPT, it can take actions — run queries, browse the web, manage Plane issues. It's also connected to our internal systems.

**Q: Can it write code for me?**
Yes, it can help write, review, and explain code. However, team members (non-admin) cannot run code on the server. Use it for code generation, review, and explanation — then copy the code to your local IDE.

**Q: Can it access my local files?**
No. It runs on our server, not on your computer. It can only access files on the server and query our connected systems (Plane, ClickHouse, AWS).

**Q: Is it safe to paste sensitive code?**
The messages go through OpenRouter to Anthropic for processing. Use the same judgment as you would with any cloud-based AI tool. Don't paste customer PII, API keys, or passwords.

**Q: Can I use it for personal tasks?**
It's set up for work purposes, but occasional personal use (writing an email, quick research) is fine. Don't use it for anything that would be inappropriate at work.

**Q: How do I report issues?**
Message an admin, or create a Plane issue in the ARCTAN project. You can even ask the AI: "Create a Plane issue for a bug I found in the AI assistant".

**Q: Does it make mistakes?**
Yes. AI can hallucinate (make things up). Always verify critical information, especially:
- SQL query results (check the query logic)
- Code suggestions (test before using)
- Factual claims (cross-reference)

**Q: What model is it running?**
Claude Opus 4.6 by Anthropic, routed through OpenRouter. This is the same model available on claude.ai, but with tool-calling capabilities and our custom integrations.

**Q: Can I use it on mobile?**
Yes. The web interface at https://chat.getarctan.com works on mobile browsers. The Slack integration also works on the Slack mobile app.

---

## 11. Cost Analysis: Shared vs Individual AI Agents

### The Question
*Would it be cheaper for each team member to run their own Claude API subscription (via VS Code extensions, local agents, etc.) instead of this shared setup?*

### Current Shared Setup Cost

| Component | Monthly Cost |
|-----------|-------------|
| EC2 t3.large (ap-south-1) | ~$60/mo |
| OpenRouter API (Claude Opus 4.6) | Variable (usage-based) |
| Domain + SSL | Free (Let's Encrypt via Caddy) |
| Open WebUI | Free (open source) |
| Hermes Agent | Free (open source) |
| **Infrastructure total** | **~$60/mo fixed** |

#### API Token Costs (OpenRouter → Claude)
Claude Opus 4.6 via OpenRouter:
- Input: $10/M tokens
- Output: $30/M tokens

A typical interaction (ask a question, AI uses 1-2 tools, returns answer):
- ~2,000 input tokens (your message + system prompt + tool schemas)
- ~1,000 output tokens (AI response + tool calls)
- **Cost per interaction: ~$0.05**

Estimated usage per team member per day: 20-40 interactions
- **Per person per day: $1.00 - $2.00**
- **Per person per month: $20 - $40**

For a 12-person team:
- **Monthly API cost: $240 - $480**
- **Total (infra + API): $300 - $540/mo**

### Individual Setup Cost (Everyone Runs Their Own)

Each person running Claude directly (e.g., via Cursor, Claude Code, VS Code + Claude API):

| Component | Monthly Cost Per Person |
|-----------|----------------------|
| Claude API (direct via Anthropic) | Same token pricing |
| OR Claude Pro subscription | $20/mo (limited usage) |
| OR Cursor Pro | $20/mo (includes some AI usage) |
| Additional API usage beyond limits | $20-60/mo |
| **Per person total** | **$20 - $80/mo** |

For a 12-person team:
- **Monthly cost: $240 - $960/mo**
- No shared context, no tool integrations

### The Real Comparison

| Factor | Shared Hermes | Individual Agents |
|--------|--------------|-------------------|
| **Monthly cost (12 people)** | $300-540 | $240-960 |
| **Access to Plane issues** | ✅ Built-in | ❌ Manual copy-paste |
| **Access to analytics DB** | ✅ Direct SQL | ❌ None |
| **Access to AWS infra** | ✅ Read-only queries | ❌ None |
| **Codebase knowledge** | ✅ All 12 repos indexed | ❌ Only what's open in IDE |
| **Cross-session memory** | ✅ Remembers preferences | ⚠️ Depends on tool |
| **Shared org knowledge** | ✅ Everyone gets it | ❌ Each person starts from zero |
| **Web browsing & research** | ✅ Full browser automation | ⚠️ Limited in most tools |
| **Admin control & visibility** | ✅ Role-based permissions | ❌ No central control |
| **Works on mobile** | ✅ Web + Slack | ❌ IDE-only |
| **Code execution in IDE** | ❌ Not in your IDE | ✅ Native IDE integration |

### Key Insight: They're Complementary, Not Competing

The shared Hermes setup and individual IDE agents serve **different purposes**:

**Use Hermes for:**
- Querying data ("How many users last week?")
- Project management ("Show me urgent issues")
- Research ("Compare these two libraries")
- Cross-team knowledge ("How does the auth service work?")
- Quick questions on mobile or Slack
- Tasks that need our integrations

**Use your local IDE agent (Cursor, Claude Code, etc.) for:**
- Writing code with full repo context
- Debugging with stack traces
- Refactoring large files
- Running tests locally
- Anything that needs your local filesystem

### Recommendation

**Run both.** The shared setup costs ~$25-45/person/month for capabilities that no individual setup can replicate (database access, project management, shared knowledge). It's an org-wide multiplier, not a per-seat replacement.

For coding specifically, individual IDE tools may still be better since they have direct access to your local files and can run code. But for everything else — research, analytics, project management, quick questions, team knowledge — the shared setup is both cheaper and more capable.

### Break-Even Analysis

The shared setup pays for itself if it saves each team member **just 15-20 minutes per week** on tasks like:
- Looking up analytics data (vs. writing SQL manually or asking someone)
- Searching through Plane issues (vs. clicking through the UI)
- Answering "how does X work?" questions (vs. reading docs/code)
- Drafting emails, specs, or summaries

At an average engineering cost of $30-50/hour, 20 minutes/week × 12 people = 4 hours/week = **$120-200/week saved** — well above the $75-135/week cost.

---

## Getting Help

- **Chat**: Ask the AI itself — "What can you do?" or "Help me with..."
- **Slack**: DM @hermesbot or mention it in a channel
- **Admin**: Reach out to your admin for access issues or role changes
- **Bugs**: Create a Plane issue in the ARCTAN project

---

*Last updated: April 2026*
*Setup maintained by the Engineering team*
*Powered by Hermes Agent + Claude Opus 4.6*
