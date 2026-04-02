# Arctan Hermes Infrastructure

Configuration and setup for the Arctan team's Hermes Agent deployment.

## Architecture

```
chat.getarctan.com
      │ HTTPS (Caddy auto-SSL)
      ▼
  Open WebUI (Docker, port 3000)
      │ HTTP + X-OpenWebUI-User-* headers
      ▼
  Hermes Gateway (port 8642)
      ├── API Server (Open WebUI backend)
      ├── Slack (@hermesbot in Arctan workspace)
      ├── Webhook listener (port 8644)
      └── Cron scheduler
```

## Components

| Component | Location | Managed by |
|-----------|----------|------------|
| Hermes Agent | `~/.hermes/hermes-agent/` | git (arctan-ai/hermes-agent, branch: arctan/production) |
| Hermes config | `~/.hermes/config.yaml` | this repo (template) |
| Hermes secrets | `~/.hermes/.env` | NOT tracked (secrets) |
| Open WebUI | Docker container `open-webui` | `docker/docker-compose.yml` |
| Caddy | `/etc/caddy/Caddyfile` | `caddy/Caddyfile` |
| Setup plan | `docs/setup.md` | this repo |

## Quick Reference

```bash
# Hermes
hermes gateway status          # check gateway
hermes gateway restart         # restart after config changes
cd ~/.hermes/hermes-agent && git log --oneline -5  # check deployed version

# Open WebUI
docker ps                      # check container
docker logs open-webui --tail 20  # check logs
docker restart open-webui      # restart

# Caddy (HTTPS)
sudo systemctl status caddy    # check
sudo systemctl restart caddy   # restart
cat /etc/caddy/Caddyfile       # config

# Update Hermes from upstream
cd ~/.hermes/hermes-agent
git fetch upstream
git checkout main && git merge upstream/main
git checkout arctan/production && git rebase main
git push origin arctan/production --force-with-lease
hermes gateway restart
```

## Secrets (not tracked)

These live in `~/.hermes/.env` and must be set manually:
- `ANTHROPIC_API_KEY` or `OPENROUTER_API_KEY`
- `API_SERVER_KEY`
- `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`
- `SLACK_HOME_CHANNEL`
- `GITHUB_TOKEN`
