#!/bin/bash
# Backup Hermes config (without secrets) to the infra repo
set -e

INFRA_DIR=~/hermes-infra

# Copy non-secret configs
cp /etc/caddy/Caddyfile "$INFRA_DIR/caddy/Caddyfile"
cp ~/hermes/setup.md "$INFRA_DIR/docs/setup.md"

# Create sanitized config.yaml (strip API keys)
sed 's/api_key: .*/api_key: REDACTED/g' ~/.hermes/config.yaml > "$INFRA_DIR/hermes-config.yaml.example"

echo "Configs backed up to $INFRA_DIR"
echo "Remember to commit and push:"
echo "  cd $INFRA_DIR && git add -A && git commit -m 'update configs' && git push"
