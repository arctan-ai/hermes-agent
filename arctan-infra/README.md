# Arctan Hermes Infrastructure

Configuration, custom skills, and deployment files for the Arctan Hermes Agent instance.

## Structure

```
arctan-infra/
├── config/
│   ├── .env.example              # Environment template (no secrets)
│   ├── role_permissions.yaml     # Role-based tool access control
│   └── ORG.md                    # Shared org memory (injected for all users)
├── caddy/
│   └── Caddyfile                 # HTTPS reverse proxy config
├── systemd/
│   └── hermes-gateway.service    # Systemd service for the gateway
├── skills/
│   ├── arctan-team-knowledge/    # Product architecture & repo knowledge
│   ├── clickhouse-analytics/     # ClickHouse DB access & queries
│   └── plane/                    # Plane.so project management API
└── scripts/                      # Deployment/maintenance scripts
```

## Deployment

Server: EC2 t3.large, ap-south-1 (43.204.147.51)
Domain: https://chat.getarctan.com
Branch: arctan/production

### Quick Deploy

```bash
# On the EC2 server
cd ~/.hermes/hermes-agent
git pull origin arctan/production

# Copy config files to their runtime locations
cp arctan-infra/config/role_permissions.yaml ~/.hermes/
cp arctan-infra/caddy/Caddyfile /etc/caddy/Caddyfile
cp arctan-infra/systemd/hermes-gateway.service /etc/systemd/system/

# Copy custom skills
cp -r arctan-infra/skills/* ~/.hermes/skills/productivity/ 2>/dev/null
cp -r arctan-infra/skills/clickhouse-analytics ~/.hermes/skills/data-science/

# Restart services
sudo systemctl daemon-reload
sudo systemctl restart hermes-gateway
sudo systemctl restart caddy
```

## Role Permissions

Edit `config/role_permissions.yaml` to control tool access per Open WebUI role.
Changes are auto-reloaded (no restart needed).

| Role    | Access Level |
|---------|-------------|
| admin   | Full (all tools) |
| user    | Read/query only (no terminal, no file writes) |
| pending | Minimal (web search, skills view, clarify) |

## Secrets

The `.env.example` is a template. Actual secrets are in `~/.hermes/.env` on the
server (not tracked in git). Copy `.env.example` and fill in real values.
