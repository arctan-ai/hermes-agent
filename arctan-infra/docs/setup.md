# Hermes as Central Operations Hub for Arctan.ai

## The Vision

Self-hosted Hermes on EC2, connected to all your tools (GitHub, AWS, Plane, databases, etc.), exposed via Open WebUI so the entire Arctan team can interact with a single AI agent that knows your codebase, infra, project state, and business context.

Think of it as: **your startup's AI ops brain** — one place where anyone on the team can ask questions, trigger workflows, and get context-aware answers about anything happening across your systems.

---

## Will This Actually Work? Honest Assessment

### What Works Well (HIGH VALUE)

1. **Single knowledge layer across tools**
   - Ask "what's the status of the accent reduction feature?" and it pulls from Plane issues, GitHub PRs, and deployment state — no context switching
   - New team members get instant onboarding: "explain our infra architecture" or "how does the Krisp pipeline work?"

2. **Multi-user via Open WebUI**
   - Open WebUI supports user accounts, login, and separate chat histories
   - Each person gets their own conversations but shares the same Hermes backend
   - Role-based access can be layered on top

3. **Ops automation**
   - "Deploy the latest accent-demo to dev-inference-server-1"
   - "What's our AWS bill looking like this month? Any GPU instances we can shut down?"
   - "Create a Plane issue for the WebRTC latency bug, assign to Abhishek, link the relevant GitHub commit"

4. **Cron jobs for proactive monitoring**
   - Daily AWS cost summary to Telegram/Slack
   - Alert if GPU instances run past 14hrs/day
   - Weekly sprint summary from Plane

### What's Tricky (MANAGE EXPECTATIONS)

1. **Shared memory vs per-user context**
   - Hermes memory is per-profile, not per-user. All Open WebUI users hit the same Hermes instance, so memory is shared
   - Good: everyone benefits from accumulated knowledge
   - Bad: one person's correction affects everyone
   - Mitigation: Use skills for team knowledge (stable), memory for Hermes's own learnings

2. **Security & permissions**
   - Hermes runs with ONE set of credentials (your AWS keys, GitHub token, etc.)
   - Any Open WebUI user can potentially ask it to delete EC2 instances or push to main
   - Mitigation: Use Hermes's security config (tirith_enabled, website_blocklist), restrict dangerous commands, and limit who gets Open WebUI accounts
   - Consider: read-only credentials for some integrations

3. **Concurrent usage**
   - Hermes processes one request at a time per gateway instance
   - With 3-5 people using it simultaneously, there could be queuing
   - Mitigation: API server handles concurrent requests but they share the LLM rate limit

4. **Cost**
   - Every query hits Anthropic/OpenRouter API — with a team of 5, expect $200-500/month in LLM costs
   - EC2 instance cost on top (t3.medium or similar, ~$30/month)
   - Worth it? If it saves each person 30min/day of context switching, absolutely

---

## Architecture

```
                    ┌──────────────┐
                    │  Open WebUI  │
                    │  (Docker)    │
                    │  port 3000   │
                    └──────┬───────┘
                           │ HTTP (OpenAI-compatible API)
                           ▼
                    ┌──────────────┐
                    │   Hermes     │
                    │   Gateway    │
                    │  port 8642   │
                    │  (API Server)│
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌───────────┐   ┌───────────┐   ┌───────────┐
    │  Telegram  │   │   Cron    │   │  Webhooks │
    │  (alerts)  │   │  (scheduled│   │  (Plane,  │
    │            │   │   tasks)  │   │  GitHub)  │
    └───────────┘   └───────────┘   └───────────┘
          │
          │         INTEGRATIONS
          │    ┌─────────────────────┐
          ├───►│ GitHub (repos, PRs)  │
          ├───►│ AWS (infra, costs)   │
          ├───►│ Plane (issues, sprints│
          ├───►│ PostgreSQL/DB        │
          ├───►│ EC2 instances (SSH)  │
          └───►│ Slack/Discord (opt)  │
               └─────────────────────┘
```

---

## Implementation Plan

### Phase 1: Infrastructure (Day 1-2)

- [ ] **Provision EC2 instance**
  - Type: t3.medium (2 vCPU, 4GB RAM) — enough for Hermes + Open WebUI
  - Region: ap-south-1 (same as your other infra)
  - Storage: 50GB gp3
  - Security group: ports 22 (SSH), 3000 (Open WebUI), 8642 (Hermes API — internal only)

- [ ] **Install Hermes on EC2**
  ```
  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
  hermes setup
  ```

- [ ] **Install Docker + Open WebUI on EC2**
  ```
  # Docker
  curl -fsSL https://get.docker.com | sh

  # Open WebUI pointed at Hermes
  docker run -d --name open-webui \
    --add-host=host.docker.internal:host-gateway \
    -p 3000:8080 \
    -e OPENAI_API_BASE_URL=http://host.docker.internal:8642/v1 \
    -e OPENAI_API_KEY=your-hermes-api-key \
    -e WEBUI_AUTH=true \
    -v open-webui:/app/backend/data \
    --restart always \
    ghcr.io/open-webui/open-webui:main
  ```

- [ ] **Set up HTTPS (important for team access)**
  - Use Caddy or nginx reverse proxy with Let's Encrypt
  - Point a subdomain: ai.arctan.ai → EC2 public IP
  - Caddy auto-handles SSL:
    ```
    ai.arctan.ai {
        reverse_proxy localhost:3000
    }
    ```

- [ ] **Configure Hermes gateway as a systemd service**
  ```
  hermes gateway install
  hermes gateway start
  ```

### Phase 2: Integrations (Day 3-5)

- [ ] **GitHub integration**
  - Generate a GitHub Personal Access Token (fine-grained, repo scope)
  - Add to ~/.hermes/.env: GITHUB_TOKEN=ghp_xxxxx
  - Team can now: "show open PRs", "review PR #42", "create branch for bug fix"

- [ ] **AWS integration**
  - Configure AWS CLI with SSO or IAM credentials on the EC2
  - Hermes uses terminal to run aws cli commands
  - Consider: create a read-only IAM role for safety, separate write role for approved ops
  - Team can now: "what EC2 instances are running?", "show today's costs"

- [ ] **Plane integration (app.plane.so)**
  - Get Plane API key from workspace settings
  - Add to ~/.hermes/.env: PLANE_API_KEY=xxx, PLANE_WORKSPACE=arctan
  - Build a Hermes skill that wraps the Plane API:
    - List/create/update issues
    - View sprint progress
    - Search by assignee, label, status
  - OR: find/build an MCP server for Plane
  - Team can now: "create issue for WebRTC bug, priority high", "what's assigned to me this sprint?"

- [ ] **Database access**
  - Install psql/mysql client on EC2
  - Store connection strings in ~/.hermes/.env
  - Hermes runs queries via terminal
  - IMPORTANT: use a read-only DB user for safety, separate write user for specific ops
  - Team can now: "how many active users this week?", "show latest error logs from DB"

- [ ] **SSH to other EC2 instances**
  - Copy SSH keys to the Hermes EC2
  - Hermes can SSH into dev-inference-server-1, etc.
  - Team can now: "check if the accent demo server is running", "tail the logs on inference server"

### Phase 3: Knowledge Base & Skills (Day 5-7)

- [ ] **Create team knowledge skills**
  These are Hermes skills that load context about your company:

  - `arctan-infra` — documents your AWS setup, instance naming, SSH access patterns
  - `arctan-codebase` — repo structure, key services, how to deploy
  - `arctan-plane-workflow` — how your team uses Plane (sprint cycles, labels, workflow)
  - `accent-product` — the Krisp pipeline, WebRTC flow, how accent reduction works

- [ ] **Set up CLAUDE.md / project context files in repos**
  - When Hermes clones a repo, it reads CLAUDE.md for project context
  - Add these to your key repos so Hermes understands them instantly

- [ ] **Configure Hermes memory with team facts**
  - Company info, team members, common workflows
  - This persists across all sessions

### Phase 4: Automation & Monitoring (Week 2)

- [ ] **Cron jobs**
  - Daily: AWS cost summary → Telegram channel
  - Daily: Open Plane issues aging >7 days → Telegram alert
  - Weekly: Sprint progress summary
  - Monitoring: GPU instance uptime check (flag if >14hrs/day)

- [ ] **Webhooks (if Plane/GitHub support outbound webhooks)**
  - GitHub PR opened → Hermes auto-reviews code
  - Plane issue moved to "Done" → Hermes checks if PR is merged
  - Build failures → Hermes investigates and posts findings

- [ ] **Open WebUI customization**
  - Create preset prompts/templates for common tasks:
    "Daily standup helper", "Create Plane issue", "Check infra status"
  - Set up model presets if using multiple models

### Phase 5: Team Onboarding (Week 2)

- [ ] **Create Open WebUI accounts for each team member**
  - Admin creates accounts at ai.arctan.ai
  - Each person gets their own chat history

- [ ] **Write a team guide**
  - What you can ask Hermes
  - Example prompts for common workflows
  - What NOT to do (destructive operations, sensitive data in prompts)

- [ ] **Set up security guardrails**
  - Enable tirith (policy engine) for dangerous commands
  - Restricted commands list (no rm -rf, no force push to main, no instance termination without approval)
  - Audit log: all Hermes sessions are saved and searchable

---

## Cost Estimate (Monthly)

| Item                     | Cost        |
|--------------------------|-------------|
| EC2 t3.medium            | ~$30        |
| LLM API (Anthropic)      | $200-500    |
| Domain/SSL               | ~$0 (Let's Encrypt) |
| Plane (if self-hosted)   | Free        |
| **Total**                | **$230-530/month** |

To reduce LLM costs:
- Use smart model routing (cheap model for simple queries, Claude for complex ones)
- Set up credential pools with multiple providers
- Use OpenRouter for model variety and cost optimization

---

## What This Replaces / Consolidates

| Before (context switching)          | After (single Hermes interface)           |
|-------------------------------------|-------------------------------------------|
| Open AWS Console → check costs      | "What's our AWS spend this month?"        |
| Open GitHub → review PRs            | "Review the latest PR on accent-demo"     |
| Open Plane → check sprint           | "What's left in this sprint?"             |
| SSH into server → check logs        | "Any errors on the inference server?"     |
| Ask colleague for context           | "How does the Krisp pipeline work?"       |
| Write deployment scripts            | "Deploy accent-demo to staging"           |
| Morning standup prep                | "Summarize what changed yesterday"        |

---

## Per-Employee Personalization via Open WebUI

### The Goal
Each Arctan employee gets their own Open WebUI account. Hermes recognizes who is talking and maintains per-user memory (preferences, context, past conversations) while sharing common organizational knowledge.

### How It Works (Architecture)

```
  Employee A (browser)──┐
  Employee B (browser)──┤   Open WebUI          Hermes API Server
  Employee C (browser)──┼──►(port 3000)────────►(port 8642)
                        │   sends headers:       reads headers:
                        │   X-OpenWebUI-User-Id  → per-user memory
                        │   X-OpenWebUI-User-Name→ personalized greeting
                        │   X-OpenWebUI-User-Email
                        │   X-OpenWebUI-User-Role→ permission level
```

### Layer 1: Open WebUI Config (Easy — just env vars)

Open WebUI can forward user identity headers to backends.
Set this in your Open WebUI Docker config:

```bash
docker run -d --name open-webui \
  --add-host=host.docker.internal:host-gateway \
  -p 3000:8080 \
  -e OPENAI_API_CONFIGS='{"hermes":{"url":"http://host.docker.internal:8642/v1","key":"your-hermes-api-key","enable_forward_user_info":true}}' \
  -e WEBUI_AUTH=true \
  -v open-webui:/app/backend/data \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

Key setting: `"enable_forward_user_info": true`

This makes every request to Hermes include:
- `X-OpenWebUI-User-Name: Alice`
- `X-OpenWebUI-User-Id: abc-123-def`
- `X-OpenWebUI-User-Email: alice@arctan.ai`
- `X-OpenWebUI-User-Role: admin`

### Layer 2: Hermes API Server Modification (Needs code changes)

Currently Hermes API server (`gateway/platforms/api_server.py`) ignores these
headers. It needs to be patched to:

1. **Read user identity from headers** in the `/v1/chat/completions` handler
2. **Route to per-user memory files** instead of global MEMORY.md/USER.md
3. **Include user identity in system prompt** so Hermes knows who it's talking to
4. **Per-user session isolation** so conversations don't leak between employees

Proposed changes to `api_server.py`:

```python
# In the chat completions handler, extract user info:
user_id = request.headers.get("X-OpenWebUI-User-Id", "default")
user_name = request.headers.get("X-OpenWebUI-User-Name", "Unknown")
user_email = request.headers.get("X-OpenWebUI-User-Email", "")
user_role = request.headers.get("X-OpenWebUI-User-Role", "user")

# Use per-user memory directory:
# ~/.hermes/memories/users/<user_id>/MEMORY.md
# ~/.hermes/memories/users/<user_id>/USER.md

# Inject user context into system prompt:
# "You are speaking with {user_name} ({user_email}), role: {user_role}"
```

### Layer 3: Shared vs Personal Knowledge

```
  SHARED (everyone sees):           PER-USER (only that person):
  ├── Skills (arctan-infra, etc.)   ├── Memory (preferences, style)
  ├── Common memory (company facts) ├── Session history
  ├── Tools (GitHub, AWS, etc.)     ├── User profile
  └── Cron jobs, webhooks           └── Corrections & learnings
```

How to implement:
- **Shared knowledge** → Hermes skills (loaded for all users)
- **Shared memory** → Global MEMORY.md (company facts, conventions)
- **Per-user memory** → `~/.hermes/memories/users/<user_id>/USER.md`
  Stores: name, role, team, preferences, past corrections
- **Per-user sessions** → Keyed by user_id in session store

### Layer 4: Role-Based Permissions (Optional)

Map Open WebUI roles to Hermes capabilities:

| Role    | Can Do                                    | Cannot Do                    |
|---------|-------------------------------------------|------------------------------|
| admin   | Everything — deploy, delete, modify infra | -                            |
| user    | Read data, create issues, ask questions   | Deploy, delete, modify infra |
| viewer  | Read-only queries                         | Any write operations         |

Implementation: Check `X-OpenWebUI-User-Role` header and adjust the system
prompt to restrict tool usage accordingly.

### Implementation Steps

- [ ] **Step 1**: Set up Open WebUI with `enable_forward_user_info: true`
- [ ] **Step 2**: Patch Hermes `api_server.py` to read X-OpenWebUI-User-* headers
- [ ] **Step 3**: Create per-user memory directory structure
- [ ] **Step 4**: Modify memory_tool.py to support per-user memory paths
- [ ] **Step 5**: Add user identity injection into system prompt builder
- [ ] **Step 6**: Test with 2-3 Open WebUI accounts
- [ ] **Step 7**: Add role-based permission enforcement
- [ ] **Step 8**: Create team onboarding accounts

### Alternative: Open WebUI Pipe Function (No Hermes Code Changes)

If modifying Hermes source is too risky, use an Open WebUI Pipe Function as
a middleware layer:

```python
class Pipe:
    """Hermes proxy with per-user context injection."""
    def __init__(self):
        self.type = "pipe"
        self.name = "Hermes (Personalized)"

    async def pipe(self, body: dict, __user__: dict) -> str:
        user_name = __user__.get("name", "User")
        user_email = __user__.get("email", "")
        user_role = __user__.get("role", "user")

        # Prepend user context to the system message
        user_context = f"[User: {user_name} | Email: {user_email} | Role: {user_role}]"
        if body["messages"] and body["messages"][0]["role"] == "system":
            body["messages"][0]["content"] = user_context + "\n" + body["messages"][0]["content"]
        else:
            body["messages"].insert(0, {"role": "system", "content": user_context})

        # Forward to Hermes API
        import requests
        r = requests.post(
            "http://host.docker.internal:8642/v1/chat/completions",
            json=body,
            headers={
                "Authorization": "Bearer your-hermes-key",
                "X-OpenWebUI-User-Id": __user__.get("id", ""),
                "X-OpenWebUI-User-Name": user_name,
            },
            stream=body.get("stream", False),
        )
        return r.json()
```

This gives you user-aware prompts WITHOUT modifying Hermes source. Downside:
per-user memory still requires Hermes-side changes.

---

## Risks & Mitigations

| Risk                                  | Mitigation                                    |
|---------------------------------------|-----------------------------------------------|
| Team member runs destructive command  | tirith policies, read-only creds where possible, command allowlist |
| LLM costs spiral                      | Set usage alerts, use cheap models for simple queries, rate limits in Open WebUI |
| Single point of failure               | Hermes gateway auto-restarts (systemd), Docker restart policy for Open WebUI |
| API keys exposed via prompt injection | Don't put keys in system prompts, use .env, restrict Open WebUI to internal/VPN |
| Hermes hallucinates wrong info        | Skills with verified team knowledge, encourage "check with Hermes then verify" culture |
| Stale knowledge                       | Cron jobs that refresh context, regular skill updates |

---

## Verdict: Is It Worth It?

**YES, for a small team (3-10 people) at Arctan's stage.**

The highest value comes from:
1. **Eliminating context switching** — one interface for everything
2. **Institutional memory** — Hermes remembers decisions, architecture, workflows even as team changes
3. **Automation** — cost monitoring, code review, sprint tracking on autopilot
4. **Onboarding** — new hires can ask Hermes anything instead of interrupting senior devs

Start with Phase 1-2 (infra + core integrations), get yourself using it daily, then expand to the team. Don't try to boil the ocean — each integration you add compounds the value.

---

## Next Steps (Immediate)

1. Decide: new EC2 instance or reuse an existing one?
2. Decide: which integrations are highest priority? (GitHub + AWS + Plane seems right)
3. Decide: domain for Open WebUI (ai.arctan.ai? hermes.arctan.ai?)
4. I can start building the Plane API skill right now on your current setup
