:wave: *Hey team — we've shipped something that's going to change how you work day-to-day.*

We built an AI assistant called *Hermes* that's wired directly into our systems — Plane, ClickHouse, AWS, and all 11 repos. It's not another ChatGPT. It *knows Arctan* — the codebase, the data, the projects, and it remembers who you are.

:point_right: *Here's what this means in practice:*

Instead of opening ClickHouse, writing SQL, and figuring out the right table:
> _"How many active users made calls this week, broken down by organization?"_
Done. It writes the query, runs it, gives you the answer.

Instead of switching to Plane, searching, creating, filling fields:
> _"Create an issue in Engineering: 'AGC regression on build 22631' with high priority, assign to me"_
Created. Link back. 5 seconds.

Instead of asking around "hey does anyone know how the PeerDB sync works":
> _"Explain how data flows from Postgres to ClickHouse through PeerDB. I'm seeing a delay."_
It knows. It's read every repo, every doc, every config.

---

:rocket: *Getting started takes 2 minutes:*

*1.* Go to <https://chat.getarctan.com|chat.getarctan.com> → sign in with your *@arctan.ai* Google account
*2.* Pick a model from the dropdown (start with *Sonnet 4.6* for everyday use)
*3.* Say hello — tell it your name and what you work on. It'll remember you from now on.

That's it. You're in.

:speech_balloon: *Or use it right here in Slack* — DM @hermesbot or mention it in any channel. Use `/model` to switch between models.

---

:muscle: *How this boosts your workflow over time:*

• *Week 1:* You stop context-switching to Plane, ClickHouse, and docs. Data questions that took 10 minutes now take 10 seconds.
• *Week 2:* It knows your preferences, your repos, your style. Answers get sharper. You start chaining tasks — _"Check packet loss for ICCS users last week → find which orgs → create a Plane issue summarizing it."_
• *Week 3+:* It becomes your first stop for anything Arctan — research, drafting, debugging context, cross-repo questions. The team's collective knowledge is always one message away.

---

:wrench: *One more thing — your local AI tools just got smarter too.*

We've pushed context files (`AGENTS.md`, `.github/copilot-instructions.md`, `.zed/rules.md`) to all 11 repos. Just `git pull` on your projects — Claude Code, OpenCode, Zed, and VS Code Copilot will automatically pick them up. No more spending the first 5 minutes of every session re-explaining what Arctan is.

---

:zap: *Model cheat sheet:*
• *Haiku 4.5* — instant answers, quick lookups
• *Sonnet 4.5 / 4.6* — everyday workhorse (start here)
• *Opus 4.5 / 4.6* — deep reasoning, architecture decisions, complex debugging

:book: Full guide: <https://chat.getarctan.com|ask Hermes> _"Show me the onboarding guide"_ — or check `arctan-infra/docs/onboarding-guide.md`

Questions? Just ask Hermes. Seriously — that's what it's for. :slightly_smiling_face:
