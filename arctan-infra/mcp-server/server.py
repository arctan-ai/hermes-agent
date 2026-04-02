#!/usr/bin/env python3
"""Arctan Infrastructure MCP Server — exposes internal tools via StreamableHTTP."""

import json
import os
import re
import subprocess
import glob
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
load_dotenv("/home/ubuntu/.hermes/.env")

PORT = int(os.environ.get("ARCTAN_MCP_PORT", "8643"))
AUTH_TOKEN = os.environ.get("ARCTAN_MCP_TOKEN", "")

# ---------------------------------------------------------------------------
# Plane constants
# ---------------------------------------------------------------------------
PLANE_API_KEY = os.environ.get("PLANE_API_KEY", "")
PLANE_WORKSPACE = os.environ.get("PLANE_WORKSPACE_SLUG", "arctan")
PLANE_BASE = os.environ.get("PLANE_BASE_URL", "https://api.plane.so/api/v1")

PROJECT_NAME_TO_ID = {
    "Engineering": "f806dcbe-bc32-4a56-a1d0-27925d335545",
    "Data Science": "88a8b922-43de-46c3-9de8-33c43cf5cb8e",
    "Customer Issues & Tracks": "d769c475-4958-46d3-afb0-db6c2b2c5c76",
    "Customer Onboarding": "77e8d5de-950b-4a87-a5ba-c342d0e4bb4c",
    "ARCTAN": "46dc1634-69e8-4f98-b6dd-4c97bc674923",
    "Business": "a85ef23b-913d-4f8a-81a7-893cf0f26539",
}
PROJECT_ID_SET = set(PROJECT_NAME_TO_ID.values())

# ---------------------------------------------------------------------------
# ClickHouse constants
# ---------------------------------------------------------------------------
CH_HOST = os.environ.get("CLICKHOUSE_HOST", "172.31.13.161")
CH_PORT = os.environ.get("CLICKHOUSE_PORT", "8123")
CH_USER = os.environ.get("CLICKHOUSE_USER", "admin")
CH_PASS = os.environ.get("CLICKHOUSE_PASSWORD", "")
CH_DB = os.environ.get("CLICKHOUSE_DB", "analytics")

DANGEROUS_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|ATTACH|DETACH|RENAME|OPTIMIZE|KILL|SYSTEM)\b",
    re.IGNORECASE,
)
ALLOWED_SQL = re.compile(r"^\s*(SELECT|SHOW|DESCRIBE|DESC|EXPLAIN|WITH)\b", re.IGNORECASE)

# ---------------------------------------------------------------------------
# AWS whitelist
# ---------------------------------------------------------------------------
AWS_WHITELIST: dict[str, set[str]] = {
    "ecs": {"list-clusters", "list-services", "list-tasks", "describe-services", "describe-tasks", "describe-task-definition"},
    "ec2": {"describe-instances", "describe-security-groups"},
    "s3": {"ls", "list-buckets"},
    "cloudwatch": {"get-metric-data", "list-metrics"},
    "logs": {"describe-log-groups", "filter-log-events"},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_project(name_or_id: Optional[str]) -> Optional[str]:
    """Resolve a project name or ID to the UUID."""
    if not name_or_id:
        return None
    if name_or_id in PROJECT_ID_SET:
        return name_or_id
    # Case-insensitive lookup
    for name, pid in PROJECT_NAME_TO_ID.items():
        if name.lower() == name_or_id.lower():
            return pid
    # Partial match
    for name, pid in PROJECT_NAME_TO_ID.items():
        if name_or_id.lower() in name.lower():
            return pid
    return name_or_id  # pass through, let API error


def _plane_curl(method: str, path: str, data: Optional[dict] = None) -> str:
    """Call Plane API via curl and return formatted output."""
    url = f"{PLANE_BASE}/workspaces/{PLANE_WORKSPACE}/{path}"
    cmd = [
        "curl", "-s", "-X", method, url,
        "-H", f"X-API-Key: {PLANE_API_KEY}",
        "-H", "Content-Type: application/json",
    ]
    if data:
        cmd += ["-d", json.dumps(data)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return f"Error: curl failed — {result.stderr}"
    try:
        parsed = json.loads(result.stdout)
        return _format_json(parsed)
    except json.JSONDecodeError:
        return result.stdout[:5000]


def _format_json(obj, indent: int = 0) -> str:
    """Format JSON into human-readable text."""
    if isinstance(obj, list):
        if not obj:
            return "(empty list)"
        lines = []
        for i, item in enumerate(obj[:50]):  # cap at 50 items
            lines.append(f"\n--- [{i+1}] ---")
            lines.append(_format_json(item, indent))
        if len(obj) > 50:
            lines.append(f"\n... and {len(obj)-50} more items")
        return "\n".join(lines)
    elif isinstance(obj, dict):
        lines = []
        # Handle paginated results
        if "results" in obj and isinstance(obj["results"], list):
            meta_keys = {k: v for k, v in obj.items() if k != "results"}
            if meta_keys:
                lines.append("Metadata: " + ", ".join(f"{k}={v}" for k, v in meta_keys.items()))
            lines.append(_format_json(obj["results"], indent))
            return "\n".join(lines)
        for k, v in obj.items():
            prefix = "  " * indent
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.append(_format_json(v, indent + 1))
            else:
                lines.append(f"{prefix}{k}: {v}")
        return "\n".join(lines)
    else:
        return str(obj)


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp_server = FastMCP("arctan", host="0.0.0.0", port=PORT)


@mcp_server.tool()
def plane_query(
    resource: str,
    project: Optional[str] = None,
    filters: Optional[dict] = None,
    issue_id: Optional[str] = None,
) -> str:
    """Query Plane.so projects and issues.

    Args:
        resource: One of: projects, issues, cycles, modules, states, labels, members
        project: Project name (e.g. 'Engineering') or UUID. Required for issues/cycles/modules/states/labels.
        filters: Optional dict of query filters (passed as URL params).
        issue_id: Optional issue UUID to fetch a specific issue.
    """
    resource = resource.lower().strip()
    valid = {"projects", "issues", "cycles", "modules", "states", "labels", "members"}
    if resource not in valid:
        return f"Invalid resource '{resource}'. Must be one of: {', '.join(sorted(valid))}"

    if resource == "projects":
        return _plane_curl("GET", "projects/")

    if resource == "members":
        return _plane_curl("GET", "members/")

    project_id = _resolve_project(project)
    if not project_id:
        return f"Project is required for '{resource}'. Available: {', '.join(PROJECT_NAME_TO_ID.keys())}"

    if resource == "issues" and issue_id:
        return _plane_curl("GET", f"projects/{project_id}/issues/{issue_id}/")

    path = f"projects/{project_id}/{resource}/"

    if filters:
        qs = "&".join(f"{k}={v}" for k, v in filters.items())
        path += f"?{qs}"

    return _plane_curl("GET", path)


@mcp_server.tool()
def plane_update(
    action: str,
    project: str,
    issue_id: Optional[str] = None,
    data: Optional[dict] = None,
) -> str:
    """Create or update Plane.so issues, or add comments.

    Args:
        action: One of: create, update, comment
        project: Project name (e.g. 'Engineering') or UUID.
        issue_id: Required for 'update' and 'comment' actions.
        data: Dict with issue fields (name, description, state, priority, etc.) or comment body.
    """
    action = action.lower().strip()
    if action not in ("create", "update", "comment"):
        return "Action must be one of: create, update, comment"

    project_id = _resolve_project(project)
    if not project_id:
        return f"Could not resolve project '{project}'. Available: {', '.join(PROJECT_NAME_TO_ID.keys())}"

    if not data:
        return "Data dict is required."

    if action == "create":
        return _plane_curl("POST", f"projects/{project_id}/issues/", data)
    elif action == "update":
        if not issue_id:
            return "issue_id is required for update."
        return _plane_curl("PATCH", f"projects/{project_id}/issues/{issue_id}/", data)
    elif action == "comment":
        if not issue_id:
            return "issue_id is required for comment."
        return _plane_curl("POST", f"projects/{project_id}/issues/{issue_id}/comments/", data)
    return "Unknown action."


@mcp_server.tool()
def clickhouse_query(
    query: str,
    format: str = "table",
    limit: int = 100,
) -> str:
    """Execute read-only SQL on the ClickHouse analytics database.

    Security: Only SELECT, SHOW, DESCRIBE, and EXPLAIN queries are allowed.
    Connection uses readonly=1 mode.

    Known tables in 'analytics' database (run SHOW TABLES for current list):
      - events, sessions, users, page_views, conversions, funnel_events, etc.

    Args:
        query: SQL query string (SELECT/SHOW/DESCRIBE/EXPLAIN only).
        format: Output format — 'table' (Pretty), 'json' (JSONEachRow), or 'csv'.
        limit: Max rows to return (default 100, max 1000).
    """
    query = query.strip().rstrip(";")

    # Security checks
    if DANGEROUS_SQL.search(query):
        return "BLOCKED: Only read-only queries (SELECT/SHOW/DESCRIBE/EXPLAIN) are allowed."
    if not ALLOWED_SQL.match(query):
        return "BLOCKED: Query must start with SELECT, SHOW, DESCRIBE, or EXPLAIN."

    limit = max(1, min(limit, 1000))

    # Auto-append LIMIT if SELECT and no LIMIT present
    if re.match(r"^\s*SELECT\b", query, re.IGNORECASE) and not re.search(r"\bLIMIT\s+\d+", query, re.IGNORECASE):
        query += f" LIMIT {limit}"

    fmt_map = {"table": "PrettyCompact", "json": "JSONEachRow", "csv": "CSVWithNames"}
    ch_format = fmt_map.get(format, "PrettyCompact")

    url = f"http://{CH_HOST}:{CH_PORT}/"
    cmd = [
        "curl", "-s", "--max-time", "30",
        url,
        "--data-urlencode", f"query={query} FORMAT {ch_format}",
        "-u", f"{CH_USER}:{CH_PASS}",
        "-d", f"database={CH_DB}",
        "-d", "readonly=1",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        if result.returncode != 0:
            return f"ClickHouse error: {result.stderr}"
        output = result.stdout
        if not output.strip():
            return "(no results)"
        # Truncate very large results
        if len(output) > 15000:
            output = output[:15000] + "\n... (truncated)"
        return output
    except subprocess.TimeoutExpired:
        return "Error: Query timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


@mcp_server.tool()
def aws_query(
    service: str,
    command: str,
    args: Optional[dict] = None,
    region: str = "ap-south-1",
) -> str:
    """Execute safe read-only AWS CLI commands.

    Whitelisted services and commands:
      - ecs: list-clusters, list-services, list-tasks, describe-services, describe-tasks, describe-task-definition
      - ec2: describe-instances, describe-security-groups
      - s3: ls, list-buckets
      - cloudwatch: get-metric-data, list-metrics
      - logs: describe-log-groups, filter-log-events

    Args:
        service: AWS service (ecs, ec2, s3, cloudwatch, logs).
        command: Subcommand from whitelist above.
        args: Optional dict of CLI arguments (e.g. {"--cluster": "my-cluster"}).
        region: AWS region (default ap-south-1).
    """
    service = service.lower().strip()
    command = command.lower().strip()

    if service not in AWS_WHITELIST:
        return f"Service '{service}' not allowed. Allowed: {', '.join(sorted(AWS_WHITELIST.keys()))}"
    if command not in AWS_WHITELIST[service]:
        return f"Command '{command}' not allowed for {service}. Allowed: {', '.join(sorted(AWS_WHITELIST[service]))}"

    cmd = ["aws", service, command, "--region", region, "--output", "json"]
    if args:
        for k, v in args.items():
            key = k if k.startswith("--") else f"--{k}"
            if v is None or v is True:
                cmd.append(key)
            else:
                cmd.extend([key, str(v)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return f"AWS CLI error:\n{result.stderr}"
        try:
            parsed = json.loads(result.stdout)
            return _format_json(parsed)
        except json.JSONDecodeError:
            return result.stdout[:10000] if result.stdout else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: AWS CLI timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


@mcp_server.tool()
def codebase_knowledge(
    query: str,
    repo: Optional[str] = None,
) -> str:
    """Query Arctan's indexed codebase documentation and architecture knowledge.

    Searches through internal documentation about Arctan's services, repos,
    architecture, and team knowledge.

    Args:
        query: What to search for (e.g. 'how does auth work', 'frontend deployment', 'database schema').
        repo: Optional specific repo name to focus search on.
    """
    base = Path("/home/ubuntu/.hermes/skills/productivity/arctan-team-knowledge")
    if not base.exists():
        return "Knowledge base not found at expected path."

    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))

    results = []

    # Gather all .md files
    files = list(base.glob("*.md")) + list(base.glob("references/*.md"))

    for fpath in files:
        try:
            content = fpath.read_text(errors="ignore")
        except Exception:
            continue

        # If repo filter, check filename or content
        if repo:
            repo_lower = repo.lower()
            if repo_lower not in fpath.name.lower() and repo_lower not in content[:500].lower():
                continue

        # Score by keyword matches
        content_lower = content.lower()
        score = sum(1 for w in query_words if w in content_lower)
        # Bonus for words in first 500 chars (title/header area)
        header = content_lower[:500]
        score += sum(0.5 for w in query_words if w in header)

        if score > 0:
            results.append((score, fpath.name, content))

    if not results:
        return f"No matching documentation found for '{query}'." + (
            f" (filtered to repo '{repo}')" if repo else ""
        )

    # Sort by score descending, return top matches
    results.sort(key=lambda x: -x[0])

    output_parts = []
    total_chars = 0
    for score, fname, content in results[:5]:
        # Extract relevant sections
        chunk = _extract_relevant(content, query_words)
        if total_chars + len(chunk) > 12000:
            chunk = chunk[:max(500, 12000 - total_chars)]
        output_parts.append(f"=== {fname} (relevance: {score:.1f}) ===\n{chunk}")
        total_chars += len(chunk)
        if total_chars > 12000:
            break

    return "\n\n".join(output_parts)


def _extract_relevant(content: str, query_words: set, context_lines: int = 5) -> str:
    """Extract sections of content most relevant to query words."""
    lines = content.split("\n")
    if len(lines) <= 30:
        return content

    # Find lines containing query words
    matching_indices = set()
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(w in line_lower for w in query_words):
            for j in range(max(0, i - context_lines), min(len(lines), i + context_lines + 1)):
                matching_indices.add(j)

    if not matching_indices:
        # Return first 40 lines as overview
        return "\n".join(lines[:40])

    # Also include header lines (starting with #)
    for i, line in enumerate(lines):
        if line.startswith("#"):
            matching_indices.add(i)

    sorted_idx = sorted(matching_indices)
    result = []
    prev = -2
    for idx in sorted_idx:
        if idx > prev + 1:
            result.append("...")
        result.append(lines[idx])
        prev = idx

    return "\n".join(result)


# ---------------------------------------------------------------------------
# Auth Middleware
# ---------------------------------------------------------------------------

from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Reject requests without a valid Bearer token.

    Skips auth if ARCTAN_MCP_TOKEN is empty (allows unauthenticated local dev).
    """

    async def dispatch(self, request, call_next):
        if not AUTH_TOKEN:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header == f"Bearer {AUTH_TOKEN}":
            return await call_next(request)

        return JSONResponse(
            {"error": "Unauthorized — set Authorization: Bearer <ARCTAN_MCP_TOKEN>"},
            status_code=401,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    app = mcp_server.streamable_http_app()
    app.add_middleware(BearerAuthMiddleware)

    auth_status = "enabled (token required)" if AUTH_TOKEN else "DISABLED (no ARCTAN_MCP_TOKEN set)"
    print(f"Starting Arctan MCP server on port {PORT}... Auth: {auth_status}")

    uvicorn.run(app, host="0.0.0.0", port=PORT)
