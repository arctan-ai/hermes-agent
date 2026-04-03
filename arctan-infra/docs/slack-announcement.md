:robot_face: *Hermes is live — your AI assistant that actually knows Arctan*

It's connected to our Plane boards, ClickHouse analytics (88M+ metrics), AWS infrastructure, and all 11 repos. It remembers you across sessions.

---

:point_right: *Three things you can do right now:*

*1. Chat at <https://chat.getarctan.com|chat.getarctan.com>*
Sign in with your @arctan.ai Google account, pick a model, and start asking. Try:
> _"How many active users made calls this week?"_
> _"What urgent issues are open in Engineering?"_

*2. Use @hermesbot right here in Slack*
DM it or mention it in any channel:
> _@hermesbot Show me daily active users for the last 7 days, grouped by organization_

Use `/model sonnet` or `/model opus` to switch models per-session.

*3. Pull latest on your repos*
We've pushed `AGENTS.md`, `.github/copilot-instructions.md`, and `.zed/rules.md` to all 11 repos. Just `git pull` — your AI tools (Claude Code, OpenCode, Zed, Copilot) will read them automatically.

---

:bulb: *What can Hermes do that your personal Claude can't?*

• _"What's the p95 model latency for ICCS users this week? Compare to last week."_ → runs SQL on ClickHouse
• _"Create an issue in Engineering: 'Investigate AGC regression on build 22631' with high priority, assign to me"_ → creates it in Plane directly

It knows our audio pipeline, PeerDB setup, driver caveats, and every repo's architecture — no re-explaining needed.

---

:zap: *Quick model guide:*
• *Haiku 4.5* — fast answers, simple lookups
• *Sonnet 4.6* — everyday tasks (recommended default)
• *Opus 4.6* — complex reasoning, architecture decisions

---

:book: Full onboarding guide: ask Hermes _"Show me the onboarding guide"_ or check `arctan-infra/docs/onboarding-guide.md`
