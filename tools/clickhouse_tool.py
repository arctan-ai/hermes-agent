#!/usr/bin/env python3
"""
ClickHouse Analytics Tool - Read-only SQL query access to ClickHouse.

Provides a single tool for executing read-only queries against the
ClickHouse analytics database via the HTTP API using curl subprocess.
"""

import json
import os
import re
import subprocess
import urllib.parse


# ---------------------------------------------------------------------------
# Forbidden SQL keywords (write / DDL / admin operations)
# ---------------------------------------------------------------------------
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "ATTACH", "DETACH", "RENAME", "GRANT", "REVOKE",
    "KILL", "SYSTEM",
]

# Build a single compiled regex: word-boundary match, case-insensitive
_FORBIDDEN_RE = re.compile(
    r"\b(" + "|".join(FORBIDDEN_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# Allowed leading statements
_ALLOWED_RE = re.compile(
    r"^\s*(SELECT|SHOW|DESCRIBE|DESC|EXPLAIN)\b",
    re.IGNORECASE,
)

_LIMIT_RE = re.compile(r"\bLIMIT\s+\d+", re.IGNORECASE)


def _validate_query(query: str) -> str | None:
    """Return an error string if the query is disallowed, else None."""
    if _FORBIDDEN_RE.search(query):
        match = _FORBIDDEN_RE.search(query)
        return f"Blocked: query contains forbidden keyword '{match.group()}'. Only SELECT/SHOW/DESCRIBE/EXPLAIN allowed."
    if not _ALLOWED_RE.match(query):
        return "Blocked: query must start with SELECT, SHOW, DESCRIBE, or EXPLAIN."
    return None


def clickhouse_query_handler(args, **kwargs) -> str:
    """Execute a read-only ClickHouse query via the HTTP API."""

    query = (args.get("query") or "").strip()
    if not query:
        return json.dumps({"error": "No query provided."})

    fmt = (args.get("format") or "table").lower()
    if fmt not in ("table", "json", "csv"):
        fmt = "table"

    limit = args.get("limit", 100)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 100
    limit = max(1, min(limit, 1000))

    # --- Security check ---
    err = _validate_query(query)
    if err:
        return json.dumps({"error": err})

    # Auto-append LIMIT if not present (for SELECT queries)
    if _ALLOWED_RE.match(query) and re.match(r"^\s*SELECT\b", query, re.IGNORECASE):
        if not _LIMIT_RE.search(query):
            # Strip trailing semicolon before appending
            query = query.rstrip().rstrip(";")
            query = f"{query} LIMIT {limit}"

    # --- Build curl command ---
    host = os.environ.get("CLICKHOUSE_HOST", "172.31.13.161")
    port = os.environ.get("CLICKHOUSE_PORT", "8123")
    user = os.environ.get("CLICKHOUSE_USER", "admin")
    password = os.environ.get("CLICKHOUSE_PASSWORD", "")
    database = os.environ.get("CLICKHOUSE_DB", "analytics")

    # Map format to ClickHouse output format
    ch_format_map = {
        "table": "PrettyCompact",
        "json": "JSON",
        "csv": "CSVWithNames",
    }
    ch_format = ch_format_map[fmt]

    # Build URL with query parameters
    params = urllib.parse.urlencode({
        "database": database,
        "default_format": ch_format,
        "max_result_rows": str(limit),
        "readonly": "1",
    })
    url = f"http://{host}:{port}/?{params}"

    cmd = [
        "curl", "-s", "-S",
        "--max-time", "30",
        "--user", f"{user}:{password}",
        "--data-binary", query,
        url,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=35,
        )

        output = result.stdout
        stderr = result.stderr.strip()

        if result.returncode != 0:
            return json.dumps({
                "error": f"curl failed (exit {result.returncode}): {stderr or output}",
            })

        # ClickHouse returns errors as plain text with "Code:" prefix
        if output.startswith("Code:") or "DB::Exception" in output:
            return json.dumps({"error": output.strip()})

        if not output.strip():
            return json.dumps({"result": "(empty result set)", "format": fmt})

        return output

    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Query timed out after 30 seconds."})
    except Exception as e:
        return json.dumps({"error": f"Execution error: {str(e)}"})


# =============================================================================
# OpenAI Function-Calling Schema
# =============================================================================

CLICKHOUSE_QUERY_SCHEMA = {
    "name": "clickhouse_query",
    "description": (
        "Execute a read-only SQL query against the ClickHouse analytics database. "
        "Only SELECT, SHOW, DESCRIBE, and EXPLAIN queries are allowed.\n\n"
        "Available tables and key columns:\n"
        "- analytics.metrics (~88M rows): user_id, timestamp, model_latency, ping, cpu, ram, volume, packets, jitter\n"
        "- analytics.user_activities (~27M rows): user_id, activity_type, timestamp, activity_data\n"
        "- analytics.Users (538 rows): id, name, email, organization_id\n"
        "- analytics.Organizations (42 rows): id, name\n"
        "- analytics.internal_metrics (~3M rows): user_id, timestamp, metric\n\n"
        "Important notes:\n"
        "- Timestamps are Unix milliseconds. Divide by 1000 or use fromUnixTimestamp64Milli() for DateTime.\n"
        "- Filter _peerdb_is_deleted = 0 for active records.\n"
        "- Large tables: always use WHERE clauses and reasonable date ranges to avoid slow queries.\n"
        "- LIMIT is auto-appended if not present in SELECT queries."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "SQL query to execute (SELECT/SHOW/DESCRIBE/EXPLAIN only).",
            },
            "format": {
                "type": "string",
                "enum": ["table", "json", "csv"],
                "description": "Output format. 'table' (default) for human-readable, 'json' for structured data, 'csv' for CSV with headers.",
                "default": "table",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum rows to return (default 100, max 1000). Auto-appended as LIMIT if not in query.",
                "default": 100,
            },
        },
        "required": ["query"],
    },
}


# --- Registry ---
from tools.registry import registry

registry.register(
    name="clickhouse_query",
    toolset="clickhouse",
    schema=CLICKHOUSE_QUERY_SCHEMA,
    handler=clickhouse_query_handler,
    emoji="🏠",
)
