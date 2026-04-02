# PostgreSQL to ClickHouse Migration & Real-Time Sync

Step-by-step guide using the recommended path: **PeerDB** for managed CDC, with **Debezium + Kafka** as the scale-out alternative.

---

## Current Progress

| Component | Status | Details |
|-----------|--------|---------|
| **AWS RDS PostgreSQL** | ✅ Exists | Production database `analytics` on RDS PG 17.4 |
| **ClickHouse (ECS)** | ✅ Running | `production-clickhouse.production:8123` |
| **ClickHouse `analytics` DB** | ✅ Created | Database ready |
| **Target tables in ClickHouse** | ✅ Created | Organizations, Users, UserConfigs, internal_metrics, metrics, user_activities (PeerDB-compatible schema) |
| **RDS logical replication** | ✅ Enabled | `wal_level=logical` after reboot |
| **Replication user** | ✅ Created | `replicator` with `rds_replication` + table ownership via `analytics_admin` |
| **PeerDB (ECS)** | ✅ Deployed | Task at `172.31.13.157:9900`, 4096MB memory, 2 vCPU |
| **PostgreSQL Peer** | ✅ Created | `postgres_source` → analytics DB |
| **ClickHouse Peer** | ✅ Created | `clickhouse_target` → analytics DB |
| **CDC Mirror** | ✅ Running | `pg_to_ch_mirror` — initial snapshot complete, real-time CDC active |

### Mirror Details

- **Mirror name:** `pg_to_ch_mirror`
- **Replication slot:** `peerflow_slot_pg_to_ch_mirror` (logical, active)
- **Publication:** `peerflow_pub_pg_to_ch_mirror`
- **S3 staging:** `s3://production-peerdb-staging/staging`
- **Created:** 2026-03-17
- **Users.password column:** Excluded via PeerDB `exclude` syntax

### Tables Synced

| PostgreSQL Table | ClickHouse Table | Engine | PG Rows | CH Rows | Notes |
|------------------|------------------|--------|---------|---------|-------|
| `public.Organizations` | `Organizations` | ReplacingMergeTree(_peerdb_version) | 42 | 42 | ✅ Exact match |
| `public.Users` | `Users` | ReplacingMergeTree(_peerdb_version) | 538 | 538 | ✅ `password` column excluded |
| `public.UserConfigs` | `UserConfigs` | ReplacingMergeTree(_peerdb_version) | 478 | 480 | ✅ CDC active |
| `public.internal_metrics` | `internal_metrics` | ReplacingMergeTree(_peerdb_version) | 2.62M | 2.62M | ✅ CDC active |
| `public.metrics` | `metrics` | ReplacingMergeTree(_peerdb_version) | 73.74M | 73.74M | ✅ CDC active |
| `public.user_activities` | `user_activities` | ReplacingMergeTree(_peerdb_version) | 19.46M | 19.46M | ✅ CDC active |

### Connection Details

| Service | Endpoint | Credentials |
|---------|----------|-------------|
| ClickHouse HTTP | `http://production-clickhouse.production:8123` | `admin` / `xxxxx` |
| ClickHouse Native | `production-clickhouse.production:9000` | `admin` / `xxxxx` |
| PostgreSQL (RDS) | `user-metrics.cfskyamq4opy.ap-south-1.rds.amazonaws.com` | `replicator` / `xxxxx` |
| PeerDB SQL | `172.31.13.157:9900` | `peerdb` / `xxxxx` |
| PeerDB UI | `http://172.31.13.157:3000` | — |

### Completed Steps

1. ~~Configure PostgreSQL~~ - ✅ Logical replication enabled, replicator user created
2. ~~Identify tables to sync~~ - ✅ 6 tables
3. ~~Create ClickHouse tables~~ - ✅ Migrations `002_rename_tables_for_peerdb.sql` + `003_add_user_activities.sql` applied
4. ~~Deploy PeerDB~~ - ✅ ECS task with 4096MB memory
5. ~~Create peers~~ - ✅ postgres_source + clickhouse_target
6. ~~Create CDC mirror~~ - ✅ Initial snapshot complete, real-time CDC running
7. ~~Validate row counts~~ - ✅ All tables match (2026-03-17)

---

## Prerequisites

- AWS RDS PostgreSQL 12+ with logical replication enabled
- ClickHouse on ECS (production-clickhouse.production)
- Docker & Docker Compose (for PeerDB / Debezium)

---

## Phase 1: Prepare AWS RDS PostgreSQL for Logical Replication

### Step 1: Enable logical replication on RDS

> **Note:** RDS doesn't allow direct access to `postgresql.conf`. Use **Parameter Groups** instead.

**Option A: Via AWS Console**
1. Go to **RDS** → **Parameter Groups**
2. Create a new parameter group (or modify existing) for your PostgreSQL version
3. Set `rds.logical_replication` = `1`
4. Apply the parameter group to your RDS instance
5. **Reboot** the instance (required for this parameter)

**Option B: Via AWS CLI**

```bash
# Create parameter group (if needed) - adjust family for your PG version
aws rds create-db-parameter-group \
  --db-parameter-group-name pg-logical-replication \
  --db-parameter-group-family postgres15 \
  --description "Enable logical replication for CDC"

# Set the parameter
aws rds modify-db-parameter-group \
  --db-parameter-group-name pg-logical-replication \
  --parameters "ParameterName=rds.logical_replication,ParameterValue=1,ApplyMethod=pending-reboot"

# Apply to your RDS instance (replace with your instance ID)
aws rds modify-db-instance \
  --db-instance-identifier YOUR_RDS_INSTANCE_ID \
  --db-parameter-group-name pg-logical-replication

# Reboot to apply changes
aws rds reboot-db-instance --db-instance-identifier YOUR_RDS_INSTANCE_ID
```

**Verify after reboot:**
```sql
SHOW wal_level;              -- Should return 'logical'
SHOW max_replication_slots;  -- Should be > 0 (RDS default: 10)
SHOW max_wal_senders;        -- Should be > 0 (RDS default: 10)
```

### Step 2: Create a replication user ✅ DONE

Connect to your RDS instance as the master user and run:

```sql
-- Create user WITHOUT REPLICATION attribute (RDS doesn't allow this directly)
CREATE ROLE replicator WITH LOGIN PASSWORD 'Arctan@bng123456';

-- Grant rds_replication role (this is what RDS uses for logical replication)
GRANT rds_replication TO replicator;

-- Grant access to public schema
GRANT USAGE ON SCHEMA public TO replicator;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO replicator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO replicator;
```

> **Note:** On RDS, the `rds_replication` role provides logical replication access, not the native PostgreSQL `REPLICATION` attribute.
```

### Step 3: Ensure tables have primary keys

ClickHouse CDC requires primary keys for update/delete tracking:

```sql
-- Find tables without primary keys
SELECT t.table_name
FROM information_schema.tables t
LEFT JOIN information_schema.table_constraints c
  ON t.table_name = c.table_name AND c.constraint_type = 'PRIMARY KEY'
WHERE t.table_schema = 'public'
  AND t.table_type = 'BASE TABLE'
  AND c.constraint_name IS NULL;
```

Add primary keys to any tables that are missing them before proceeding.

---

## Phase 2: Prepare ClickHouse

### Step 4: Create the target database ✅ DONE

```sql
CREATE DATABASE analytics;
```

> **Completed**: Database `analytics` created on 2026-03-15

### Step 5: Create target tables in ClickHouse ✅ DONE

#### Organizations (dimension table with updates)

```sql
CREATE TABLE analytics.organizations (
    id UInt64,
    name String,
    created_at DateTime,
    updated_at DateTime,
    _version UInt64 DEFAULT toUnixTimestamp(now())
) ENGINE = ReplacingMergeTree(_version)
ORDER BY id;
```

#### Users (dimension table with updates)

```sql
CREATE TABLE analytics.users (
    id UInt64,
    name String,
    email String,
    organization_id UInt64,
    license_type Nullable(String),
    created_at DateTime,
    updated_at DateTime,
    _version UInt64 DEFAULT toUnixTimestamp(now())
) ENGINE = ReplacingMergeTree(_version)
ORDER BY id;
```

#### UserConfigs (dimension table with updates)

```sql
CREATE TABLE analytics.user_configs (
    id UInt64,
    user_id UInt64,
    config String,  -- JSON stored as String
    created_at DateTime,
    updated_at DateTime,
    _version UInt64 DEFAULT toUnixTimestamp(now())
) ENGINE = ReplacingMergeTree(_version)
ORDER BY id;
```

#### InternalMetrics (high-volume, append-only)

```sql
CREATE TABLE analytics.internal_metrics (
    id UInt64,
    user_id UInt64,
    timestamp Int64,
    metric String  -- JSON stored as String
) ENGINE = MergeTree()
ORDER BY (user_id, timestamp)
PARTITION BY toYYYYMM(toDateTime(timestamp / 1000));
```

#### Metrics (high-volume, append-only)

```sql
CREATE TABLE analytics.metrics (
    id UInt64,
    user_id UInt64 DEFAULT 0,  -- Can't use Nullable in ORDER BY
    user_name Nullable(String),
    timestamp Int64,
    model_latency Nullable(Float64),
    ping Nullable(Float64),
    cpu Nullable(Float64),
    ram Nullable(Float64),
    cpu_app Nullable(Float64),
    ram_app_heap_usage_percent Nullable(Float64),
    ram_app_rss_bytes Nullable(Int64),
    model_performance_time Nullable(Float64),
    volume Nullable(Float64),
    packets_received Nullable(Int32),
    packets_sent Nullable(Int32),
    packets_lost Nullable(Int32),
    bytes_received Nullable(Int32),
    bytes_sent Nullable(Int32),
    jitter Nullable(Float64),
    webrtc_stats Nullable(String),  -- JSON stored as String
    outbound_audio_level Nullable(Float64),
    inbound_audio_level Nullable(Float64)
) ENGINE = MergeTree()
ORDER BY (user_id, timestamp)
PARTITION BY toYYYYMM(toDateTime(timestamp / 1000));
```

> **Note:** For high-volume tables (metrics, internal_metrics), we use `MergeTree` without versioning since they are append-only. Partitioning by month helps with query performance and data retention.

> **Completed**: All 5 tables created on 2026-03-16. Migration: `migrations/001_create_analytics_tables.sql`

---

## Phase 3A: Sync with PeerDB (Recommended)

### Step 6: Deploy PeerDB on ECS

```bash
cd /home/ubuntu/infra-service/peerdb

# Deploy to ECS
./deploy.sh up

# Check status
./deploy.sh status

# Get PeerDB endpoints
./deploy.sh ip
```

PeerDB UI will be available at `http://<TASK_IP>:3000`.

> **Files:** See `/home/ubuntu/infra-service/peerdb/` for ECS task definition and deployment scripts.

### Step 7: Create the PostgreSQL peer (RDS) ✅ DONE

Via PeerDB SQL interface (`psql -h <TASK_IP> -p 9900 -U peerdb -d peerdb`):

```sql
CREATE PEER postgres_source FROM POSTGRES WITH (
    host = 'user-metrics.cfskyamq4opy.ap-south-1.rds.amazonaws.com',
    port = 5432,
    database = 'analytics',
    user = 'replicator',
    password = 'xxxxx'
);
```

> **Note:** Database must be `analytics` (not `postgres`) since tables live there.

### Step 8: Create the ClickHouse peer ✅ DONE

```sql
CREATE PEER clickhouse_target FROM CLICKHOUSE WITH (
    host = 'production-clickhouse.production',
    port = 9000,
    database = 'analytics',
    user = 'admin',
    password = 'xxxxx',
    s3_path = 's3://production-peerdb-staging/staging'
);
```

### Step 9: Create a mirror (initial snapshot + ongoing CDC) ✅ DONE

```sql
CREATE MIRROR pg_to_ch_mirror
FROM postgres_source TO clickhouse_target
WITH TABLE MAPPING (
  public.Organizations:Organizations,
  {
    from: public.Users,
    to: Users,
    exclude: [password]
  },
  public.UserConfigs:UserConfigs,
  public.internal_metrics:internal_metrics,
  public.metrics:metrics
)
WITH (
  do_initial_copy = true,
  snapshot_num_rows_per_partition = 500000,
  snapshot_max_parallel_workers = 4,
  snapshot_staging_path = 's3://production-peerdb-staging/staging'
);
```

> **Key notes:**
> - Do NOT double-quote table names (PeerDB handles case-sensitivity)
> - Do NOT prefix destination tables with database name (PeerDB adds `analytics.` prefix as literal text otherwise)
> - Use JSON-like `{ from:, to:, exclude: [] }` syntax to exclude columns (e.g., `password` from Users)
> - S3 staging required for ClickHouse snapshot (uses VPC Gateway Endpoint)

PeerDB will:
1. Take an initial snapshot of the selected tables (parallelized, 500K rows per partition)
2. Create a logical replication slot (`peerflow_slot_pg_to_ch_mirror`) in PostgreSQL
3. Create a publication (`peerflow_pub_pg_to_ch_mirror`) for the 5 tables
4. Stream all inserts, updates, and deletes to ClickHouse continuously

### Step 10: Monitor the mirror ✅ DONE

```bash
# Check mirror status in PeerDB catalog
PGPASSWORD="peerdb_secure_password_123" psql -h <RDS_HOST> -U peerdb -d peerdb \
  -c "SELECT name, flow_status, status FROM flows WHERE name = 'pg_to_ch_mirror';"

# Check replication slot health
PGPASSWORD="<password>" psql -h <RDS_HOST> -U replicator -d analytics \
  -c "SELECT slot_name, active, restart_lsn, confirmed_flush_lsn FROM pg_replication_slots;"

# Compare row counts
curl -s "http://production-clickhouse.production:8123/?user=admin&password=<password>&database=analytics" \
  --data-binary "SELECT name, total_rows FROM system.tables WHERE database = 'analytics' FORMAT PrettyCompact"
```

---

## Phase 3B: Sync with Debezium + Kafka (Alternative for Scale)

Use this path if you already have Kafka or need fine-grained control.

### Step 6b: Deploy Kafka + Debezium

```yaml
# docker-compose.yml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on: [zookeeper]
    ports: ["9092:9092"]
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  debezium:
    image: debezium/connect:2.4
    depends_on: [kafka]
    ports: ["8083:8083"]
    environment:
      BOOTSTRAP_SERVERS: kafka:9092
      GROUP_ID: 1
      CONFIG_STORAGE_TOPIC: debezium_configs
      OFFSET_STORAGE_TOPIC: debezium_offsets
      STATUS_STORAGE_TOPIC: debezium_statuses
```

```bash
docker compose up -d
```

### Step 7b: Register the PostgreSQL connector (RDS)

```bash
curl -X POST http://localhost:8083/connectors -H "Content-Type: application/json" -d '{
  "name": "pg-rds-source",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "YOUR_RDS_INSTANCE.xxxxxx.ap-south-1.rds.amazonaws.com",
    "database.port": "5432",
    "database.user": "replicator",
    "database.password": "your_secure_password",
    "database.dbname": "your_db",
    "topic.prefix": "pg",
    "table.include.list": "public.Organizations,public.Users,public.UserConfigs,public.internal_metrics,public.metrics",
    "plugin.name": "pgoutput",
    "snapshot.mode": "initial",
    "slot.name": "debezium_slot",
    "publication.name": "debezium_pub"
  }
}'
```

> **Note:** For RDS, use `pgoutput` as the plugin (native PostgreSQL logical decoding).

### Step 8b: Create ClickHouse Kafka engine tables

Connect to ClickHouse: `curl 'http://production-clickhouse.production:8123/' --user 'admin:xxxxx' -d "QUERY"`

For each table, create a Kafka source table and a materialized view. Example for `metrics`:

```sql
-- Kafka source for metrics
CREATE TABLE analytics.kafka_metrics (
    before String,
    after String,
    op String
) ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'pg.public.metrics',
    kafka_group_name = 'ch_metrics_consumer',
    kafka_format = 'JSONEachRow';

-- Materialized view to process CDC events into the target table
CREATE MATERIALIZED VIEW analytics.mv_metrics TO analytics.metrics AS
SELECT
    JSONExtractUInt(after, 'id') AS id,
    JSONExtractUInt(after, 'user_id') AS user_id,
    JSONExtractString(after, 'user_name') AS user_name,
    JSONExtractInt(after, 'timestamp') AS timestamp,
    JSONExtractFloat(after, 'model_latency') AS model_latency,
    JSONExtractFloat(after, 'ping') AS ping,
    JSONExtractFloat(after, 'cpu') AS cpu,
    JSONExtractFloat(after, 'ram') AS ram,
    JSONExtractFloat(after, 'cpu_app') AS cpu_app,
    JSONExtractFloat(after, 'ram_app_heap_usage_percent') AS ram_app_heap_usage_percent,
    JSONExtractInt(after, 'ram_app_rss_bytes') AS ram_app_rss_bytes,
    JSONExtractFloat(after, 'model_performance_time') AS model_performance_time,
    JSONExtractFloat(after, 'volume') AS volume,
    JSONExtractInt(after, 'packets_received') AS packets_received,
    JSONExtractInt(after, 'packets_sent') AS packets_sent,
    JSONExtractInt(after, 'packets_lost') AS packets_lost,
    JSONExtractInt(after, 'bytes_received') AS bytes_received,
    JSONExtractInt(after, 'bytes_sent') AS bytes_sent,
    JSONExtractFloat(after, 'jitter') AS jitter,
    JSONExtractString(after, 'webrtc_stats') AS webrtc_stats,
    JSONExtractFloat(after, 'outbound_audio_level') AS outbound_audio_level,
    JSONExtractFloat(after, 'inbound_audio_level') AS inbound_audio_level
FROM analytics.kafka_metrics
WHERE op IN ('c', 'u', 'r');  -- create, update, read (snapshot)
```

Example for `users` (with ReplacingMergeTree for updates):

```sql
-- Kafka source for users
CREATE TABLE analytics.kafka_users (
    before String,
    after String,
    op String
) ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'pg.public.Users',
    kafka_group_name = 'ch_users_consumer',
    kafka_format = 'JSONEachRow';

-- Materialized view for users
CREATE MATERIALIZED VIEW analytics.mv_users TO analytics.users AS
SELECT
    JSONExtractUInt(after, 'id') AS id,
    JSONExtractString(after, 'name') AS name,
    JSONExtractString(after, 'email') AS email,
    JSONExtractUInt(after, 'organization_id') AS organization_id,
    JSONExtractString(after, 'license_type') AS license_type,
    parseDateTimeBestEffort(JSONExtractString(after, 'created_at')) AS created_at,
    parseDateTimeBestEffort(JSONExtractString(after, 'updated_at')) AS updated_at,
    toUnixTimestamp(now()) AS _version
FROM analytics.kafka_users
WHERE op IN ('c', 'u', 'r');
```

### Step 9b: Handle deletes (optional)

For dimension tables (users, organizations), add soft delete support:

```sql
ALTER TABLE analytics.users ADD COLUMN is_deleted UInt8 DEFAULT 0;

-- Separate MV for deletes
CREATE MATERIALIZED VIEW analytics.mv_users_deletes TO analytics.users AS
SELECT
    JSONExtractUInt(before, 'id') AS id,
    '' AS name, '' AS email, 0 AS organization_id, '' AS license_type,
    now() AS created_at, now() AS updated_at,
    toUnixTimestamp(now()) AS _version,
    1 AS is_deleted
FROM analytics.kafka_users
WHERE op = 'd';
```

Query with dedup:

```sql
SELECT * FROM analytics.users FINAL WHERE is_deleted = 0;
```

> **Note:** For append-only tables (metrics, internal_metrics), deletes are typically not needed.

---

## Phase 4: Validate the Migration

### Step 11: Compare row counts

```bash
# PostgreSQL
psql -c 'SELECT 
  (SELECT COUNT(*) FROM "Organizations") AS organizations,
  (SELECT COUNT(*) FROM "Users") AS users,
  (SELECT COUNT(*) FROM "UserConfigs") AS user_configs,
  (SELECT COUNT(*) FROM internal_metrics) AS internal_metrics,
  (SELECT COUNT(*) FROM metrics) AS metrics;'

# ClickHouse
curl 'http://production-clickhouse.production:8123/' \
  --user 'admin:xxxxx' \
  -d "SELECT 
    (SELECT COUNT(*) FROM analytics.organizations FINAL) AS organizations,
    (SELECT COUNT(*) FROM analytics.users FINAL) AS users,
    (SELECT COUNT(*) FROM analytics.user_configs FINAL) AS user_configs,
    (SELECT COUNT(*) FROM analytics.internal_metrics) AS internal_metrics,
    (SELECT COUNT(*) FROM analytics.metrics) AS metrics"
```

### Step 12: Spot-check data consistency

```sql
-- PostgreSQL
SELECT id, name, email, organization_id FROM "Users" ORDER BY id LIMIT 10;

-- ClickHouse
SELECT id, name, email, organization_id FROM analytics.users FINAL ORDER BY id LIMIT 10;
```

### Step 13: Checksum comparison for critical tables

```sql
-- PostgreSQL (Users table)
SELECT md5(string_agg(md5(ROW(id, name, email)::text), '' ORDER BY id))
FROM "Users";

-- ClickHouse (equivalent)
SELECT lower(hex(MD5(groupArray(hash))))
FROM (
    SELECT MD5(concat(toString(id), name, email)) AS hash
    FROM analytics.users FINAL
    ORDER BY id
);
```

---

## Phase 5: Optimize for Production

### Step 14: Tune ClickHouse for query performance

```sql
-- Add projections for common query patterns on metrics
ALTER TABLE analytics.metrics ADD PROJECTION metrics_by_user (
    SELECT * ORDER BY user_id, timestamp
);
ALTER TABLE analytics.metrics MATERIALIZE PROJECTION metrics_by_user;

-- Add skip indices for filtered columns
ALTER TABLE analytics.users ADD INDEX idx_org_id organization_id TYPE set(100) GRANULARITY 4;
ALTER TABLE analytics.users MATERIALIZE INDEX idx_org_id;
```

### Step 15: Set up TTL if you don't need old data in ClickHouse

```sql
-- Keep metrics for 1 year, then auto-delete
ALTER TABLE analytics.metrics MODIFY TTL toDateTime(timestamp / 1000) + INTERVAL 365 DAY;

-- Keep internal_metrics for 90 days
ALTER TABLE analytics.internal_metrics MODIFY TTL toDateTime(timestamp / 1000) + INTERVAL 90 DAY;
```

### Step 16: Monitor replication lag

For PeerDB:
```sql
SELECT * FROM peerdb.mirror_stats;
```

For Debezium:
```bash
# Check consumer lag
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group ch_metrics_consumer --describe
```

Set up alerts if lag exceeds your SLA (e.g., > 30 seconds).

### Step 17: Back up the replication slot

If the replication slot is dropped or PostgreSQL is restored from a non-logical backup, you'll need to re-snapshot. Plan for this:

- For PeerDB: drop and recreate the mirror
- For Debezium: delete and recreate the connector with `"snapshot.mode": "initial"`

---

## Quick Reference: Which Path to Choose

| Scenario | Recommendation |
|---|---|
| Fastest setup, few tables | PeerDB |
| Already running Kafka | Debezium + Kafka |
| Need sub-second latency | Debezium + Kafka (tuned) |
| Minimal infrastructure | ClickHouse `MaterializedPostgreSQL` engine |
| One-time migration, no sync | `PostgreSQL` engine + `INSERT AS SELECT` |
