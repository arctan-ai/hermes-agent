---
name: clickhouse-analytics
description: "Query Arctan's ClickHouse analytics database — user metrics, activities, organizations. Supports curl (HTTP) and Python (clickhouse-connect) access."
tags: [clickhouse, analytics, database, metrics, sql]
triggers:
  - user asks about analytics, metrics, user data, activity data
  - user wants to query the database or run SQL
  - user asks about user counts, call stats, performance metrics
  - user mentions ClickHouse
---

# ClickHouse Analytics DB

## Connection Details
- Host: 172.31.13.161 (private VPC, accessible from Hermes EC2)
- HTTP Port: 8123 | Native Port: 9000
- Credentials stored in env file (CLICKHOUSE_HOST/USER/PASSWORD/DB)
- Database: `analytics`

## Access Methods

### Method 1: curl (quick queries)
```bash
CH_AUTH="admin:Arctan@Very!Secure123"
CH_URL="http://172.31.13.161:8123/"

# Simple query
curl -s "$CH_URL" --user "$CH_AUTH" --data-binary "SELECT count() FROM analytics.metrics"

# Pretty output
curl -s "$CH_URL" --user "$CH_AUTH" --data-binary "SELECT ... FORMAT PrettyCompact"

# JSON output
curl -s "$CH_URL" --user "$CH_AUTH" --data-binary "SELECT ... FORMAT JSON"

# TSV with headers
curl -s "$CH_URL" --user "$CH_AUTH" --data-binary "SELECT ... FORMAT TabSeparatedWithNames"
```

### Method 2: Python (clickhouse-connect)
```python
import clickhouse_connect
client = clickhouse_connect.get_client(
    host='172.31.13.161', port=8123,
    username='admin', password='Arctan@Very!Secure123',
    database='analytics'
)
result = client.query('SELECT count() FROM metrics')
print(result.result_rows)

# DataFrame support
df = client.query_df('SELECT * FROM metrics LIMIT 100')
```

## Database Schema

### analytics.Organizations (42 rows)
| Column | Type |
|--------|------|
| id | Int32 |
| name | String |
| created_at | Nullable(DateTime) |
| updated_at | Nullable(DateTime) |

### analytics.Users (538 rows)
| Column | Type |
|--------|------|
| id | Int32 |
| name | String |
| email | String |
| organization_id | Int32 |
| license_type | Nullable(String) |
| created_at | Nullable(DateTime) |

### analytics.UserConfigs (478 rows)
| Column | Type |
|--------|------|
| id | Int32 |
| user_id | Int32 |
| config | String (JSON) |

### analytics.metrics (~88M rows) — Performance telemetry
| Column | Type | Description |
|--------|------|-------------|
| id | Int32 | |
| user_id | Nullable(Int32) | |
| user_name | Nullable(String) | |
| timestamp | Int64 | Unix ms epoch |
| model_latency | Nullable(Float64) | ML model latency |
| ping | Nullable(Float64) | Network ping |
| cpu | Nullable(Float64) | System CPU % |
| ram | Nullable(Float64) | System RAM % |
| cpu_app | Nullable(Float64) | App CPU % |
| ram_app_heap_usage_percent | Nullable(Float64) | |
| ram_app_rss_bytes | Nullable(Int64) | |
| model_performance_time | Nullable(Float64) | |
| volume | Nullable(Float64) | Audio volume |
| packets_received/sent/lost | Nullable(Int32) | Network stats |
| bytes_received/sent | Nullable(Int32) | |
| jitter | Nullable(Float64) | |
| webrtc_stats | Nullable(String) | JSON blob |

### analytics.user_activities (~27M rows) — User events
| Column | Type | Description |
|--------|------|-------------|
| id | Int32 | |
| user_id | Int32 | |
| activity_type | String | Event type |
| timestamp | Int64 | Unix ms epoch |
| activity_data | String | JSON payload |
| meta | Nullable(String) | |
| created_at | Nullable(DateTime) | |

Activity types (top): generic_activity (26M), call_started (736K), call_ended (706K), APPLICATION_CLOSED (50K), input/output_device_changed, login, logout, streaming_started/stopped, processing_error

### analytics.internal_metrics (~2.9M rows)
| Column | Type |
|--------|------|
| id | Int32 |
| user_id | Int32 |
| timestamp | Int64 |
| metric | String (JSON) |

## Common Queries

### Active users today
```sql
SELECT count(DISTINCT user_id)
FROM analytics.user_activities
WHERE toDate(toDateTime(timestamp/1000)) = today()
```

### Calls per day (last 30 days)
```sql
SELECT toDate(toDateTime(timestamp/1000)) as day, count() as calls
FROM analytics.user_activities
WHERE activity_type = 'call_started'
  AND toDate(toDateTime(timestamp/1000)) >= today() - 30
GROUP BY day ORDER BY day
```

### Average model latency per user (last 24h)
```sql
SELECT user_name, avg(model_latency) as avg_latency, count() as samples
FROM analytics.metrics
WHERE timestamp > toUnixTimestamp(now() - INTERVAL 1 DAY) * 1000
  AND model_latency IS NOT NULL
GROUP BY user_name
ORDER BY avg_latency DESC
```

### User signups by organization
```sql
SELECT o.name as org, count() as users
FROM analytics.Users u
JOIN analytics.Organizations o ON u.organization_id = o.id
WHERE u._peerdb_is_deleted = 0
GROUP BY org ORDER BY users DESC
```

## Data Notes
- Data synced from Postgres via PeerDB (CDC replication)
- `_peerdb_is_deleted` = 1 means soft-deleted, filter these out
- `_peerdb_synced_at` = sync timestamp, `_peerdb_version` for dedup
- Timestamps in metrics/user_activities are Unix ms (divide by 1000 for DateTime)
- ReplacingMergeTree — may have duplicates before merge; use FINAL or latest _peerdb_version

## Pitfalls
- Timestamps are in MILLISECONDS (Int64), not seconds — divide by 1000
- Use `toDateTime(timestamp/1000)` for human-readable dates
- Some early data has epoch-like timestamps from 1970 (bad data)
- Filter `_peerdb_is_deleted = 0` for active records
- For exact counts on ReplacingMergeTree, use `SELECT ... FINAL` (slower)
- The `config` and `metric` columns are JSON strings — use JSONExtract functions
- webrtc_stats is a large JSON blob — extract specific fields, don't SELECT *
