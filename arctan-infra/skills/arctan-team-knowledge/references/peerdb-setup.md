# PeerDB on AWS ECS

CDC (Change Data Capture) from PostgreSQL to ClickHouse using PeerDB v0.36.9.

## Architecture

Deployed as a single ECS task (EC2 launch type, awsvpc networking) with 6 containers:

| Container | Purpose | Port | Essential |
|-----------|---------|------|-----------|
| temporal | Workflow orchestration (auto-setup:1.29) | 7233 | yes |
| flow-api | Main API server | 8112, 8113 | yes |
| flow-worker | Processes CDC events | — | yes |
| flow-snapshot-worker | Snapshot processing | — | yes |
| peerdb-server | PeerDB gRPC server | 9090 | yes |
| peerdb-ui | Web interface | 3000 | no |

**Startup order:** temporal (must be HEALTHY) → flow-api → flow-worker, flow-snapshot-worker, peerdb-server → peerdb-ui

**Backend:** RDS PostgreSQL (`user-metrics.cfskyamq4opy.ap-south-1.rds.amazonaws.com`) hosts both PeerDB catalog and Temporal databases (`peerdb`, `temporal_visibility`).

## Deployment

```bash
# Push images to ECR (only needed when upgrading versions)
./push-images-to-ecr.sh

# Deploy or update the service
./deploy.sh up

# Check status
./deploy.sh status

# Get task IP for connecting
./deploy.sh ip

# View logs (default: flow-api)
./deploy.sh logs [container-name]

# Stop the service (scale to 0)
./deploy.sh stop

# Delete the service
./deploy.sh down
```

## Files

| File | Purpose |
|------|---------|
| `ecs-task-definition.json` | ECS task definition (source of truth for deployed config) |
| `deploy.sh` | Deployment script (register task def, create/update service) |
| `docker-compose.yml` | Local testing only |
| `push-images-to-ecr.sh` | Pull images from GHCR/DockerHub and push to ECR |
| `.env` | Environment variables sourced by deploy.sh |
| `temporal-config/production.yaml` | Temporal dynamic config |

## Key Configuration Notes

- **BIND_ON_IP=0.0.0.0**: Temporal must bind on all interfaces (ECS awsvpc gives each task its own ENI)
- **TEMPORAL_BROADCAST_ADDRESS=127.0.0.1**: Single-node temporal must broadcast localhost, not the ENI IP, to prevent stale membership records in `cluster_membership` table when tasks restart with new IPs
- **Health check**: Uses `temporal operator cluster health --address 127.0.0.1:7233` with a 120s start period to allow temporal schema migration to complete
- All inter-container communication uses `localhost` (shared network namespace in ECS task)

## Troubleshooting

If temporal fails to start or other containers never launch:
1. Check temporal logs: `./deploy.sh logs temporal`
2. If you see dial errors to old IPs, stale entries exist in the `cluster_membership` table in the `peerdb` database on RDS — delete them
3. Health check must target `127.0.0.1:7233`, not just `localhost` (temporal binds after a delay)
