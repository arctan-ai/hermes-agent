#!/usr/bin/env python3
"""
Plane Tool Module - Plane.so Project Management Integration

Provides tools to query and update Plane.so project management data
via the Plane API. Uses curl subprocess calls for HTTP requests.

Tools:
- plane_query: Query projects, issues, cycles, modules, states, labels, members
- plane_update: Create/update issues and add comments
"""

import json
import os
import subprocess
from typing import Any, Dict, Optional


# =============================================================================
# Configuration
# =============================================================================

PLANE_BASE_URL = os.environ.get("PLANE_BASE_URL", "https://api.plane.so/api/v1")
PLANE_API_KEY = os.environ.get("PLANE_API_KEY", "")
PLANE_WORKSPACE_SLUG = os.environ.get("PLANE_WORKSPACE_SLUG", "")

# Known project name -> ID mapping for quick resolution
PROJECT_MAP = {
    "engineering": "f806dcbe-bc32-4a56-a1d0-27925d335545",
    "data science": "88a8b922-43de-46c3-9de8-33c43cf5cb8e",
    "customer issues & tracks": "d769c475-4958-46d3-afb0-db6c2b2c5c76",
    "customer onboarding": "77e8d5de-950b-4a87-a5ba-c342d0e4bb4c",
    "arctan": "46dc1634-69e8-4f98-b6dd-4c97bc674923",
    "business": "a85ef23b-913d-4f8a-81a7-893cf0f26539",
}


def _resolve_project_id(project: str) -> Optional[str]:
    """
    Resolve a project name or ID to a project UUID.
    Supports case-insensitive exact match and partial match.
    If it looks like a UUID already, return as-is.
    """
    if not project:
        return None

    # If it looks like a UUID, return directly
    if len(project) == 36 and project.count("-") == 4:
        return project

    project_lower = project.strip().lower()

    # Exact match
    if project_lower in PROJECT_MAP:
        return PROJECT_MAP[project_lower]

    # Partial match
    matches = [(name, pid) for name, pid in PROJECT_MAP.items() if project_lower in name]
    if len(matches) == 1:
        return matches[0][1]
    elif len(matches) > 1:
        # Return first match but prefer exact starts
        starts = [(n, p) for n, p in matches if n.startswith(project_lower)]
        if starts:
            return starts[0][1]
        return matches[0][1]

    return None


def _get_project_name(project_id: str) -> str:
    """Get project name from ID, or return the ID if not found."""
    for name, pid in PROJECT_MAP.items():
        if pid == project_id:
            return name.title()
    return project_id


def _api_call(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
    """
    Make an API call to Plane using curl subprocess.
    Returns parsed JSON response or error dict.
    """
    if not PLANE_API_KEY:
        return {"error": "PLANE_API_KEY environment variable not set"}
    if not PLANE_WORKSPACE_SLUG:
        return {"error": "PLANE_WORKSPACE_SLUG environment variable not set"}

    url = f"{PLANE_BASE_URL}/workspaces/{PLANE_WORKSPACE_SLUG}/{endpoint}"

    # Add query params
    if params:
        query_parts = []
        for k, v in params.items():
            if v is not None:
                query_parts.append(f"{k}={v}")
        if query_parts:
            url += "?" + "&".join(query_parts)

    cmd = [
        "curl", "-s", "-X", method.upper(),
        "-H", f"X-API-Key: {PLANE_API_KEY}",
        "-H", "Content-Type: application/json",
        "-w", "\n%{http_code}",
        url,
    ]

    if data and method.upper() in ("POST", "PUT", "PATCH"):
        cmd.extend(["-d", json.dumps(data)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout.strip()

        # Split response body and status code
        lines = output.rsplit("\n", 1)
        if len(lines) == 2:
            body, status_code = lines
        else:
            body = output
            status_code = "0"

        try:
            status_int = int(status_code)
        except ValueError:
            status_int = 0

        if status_int >= 400:
            try:
                err_body = json.loads(body)
            except (json.JSONDecodeError, ValueError):
                err_body = body
            return {"error": f"HTTP {status_int}", "detail": err_body}

        if not body or body.strip() == "":
            return {"success": True, "status": status_int}

        try:
            return json.loads(body)
        except (json.JSONDecodeError, ValueError):
            return {"raw_response": body, "status": status_int}

    except subprocess.TimeoutExpired:
        return {"error": "Request timed out after 30 seconds"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


# =============================================================================
# Formatting Helpers
# =============================================================================

def _format_project(p: Dict) -> str:
    lines = []
    lines.append(f"  Project: {p.get('name', 'Unknown')}")
    lines.append(f"  ID: {p.get('id', 'N/A')}")
    if p.get('description'):
        lines.append(f"  Description: {p['description'][:120]}")
    lines.append(f"  Identifier: {p.get('identifier', 'N/A')}")
    lines.append(f"  Network: {'Public' if p.get('network') == 2 else 'Private'}")
    return "\n".join(lines)


def _format_issue(issue: Dict) -> str:
    lines = []
    seq = issue.get('sequence_id', '')
    proj_id = issue.get('project', '')
    identifier = issue.get('project_detail', {}).get('identifier', '')
    issue_label = f"{identifier}-{seq}" if identifier and seq else issue.get('id', 'N/A')[:8]

    lines.append(f"  [{issue_label}] {issue.get('name', 'Untitled')}")
    lines.append(f"  ID: {issue.get('id', 'N/A')}")

    priority = issue.get('priority', 'none')
    state_detail = issue.get('state_detail', {})
    state_name = state_detail.get('name', issue.get('state', 'Unknown'))
    lines.append(f"  Priority: {priority}  |  State: {state_name}")

    assignee_details = issue.get('assignee_details', [])
    if assignee_details:
        names = [a.get('display_name', a.get('email', '?')) for a in assignee_details]
        lines.append(f"  Assignees: {', '.join(names)}")

    label_details = issue.get('label_details', [])
    if label_details:
        label_names = [l.get('name', '?') for l in label_details]
        lines.append(f"  Labels: {', '.join(label_names)}")

    if issue.get('start_date'):
        lines.append(f"  Start: {issue['start_date']}")
    if issue.get('target_date'):
        lines.append(f"  Due: {issue['target_date']}")

    if issue.get('description_stripped'):
        desc = issue['description_stripped'][:200]
        lines.append(f"  Description: {desc}")

    return "\n".join(lines)


def _format_cycle(c: Dict) -> str:
    lines = []
    lines.append(f"  Cycle: {c.get('name', 'Untitled')}")
    lines.append(f"  ID: {c.get('id', 'N/A')}")
    if c.get('start_date'):
        lines.append(f"  Start: {c['start_date']}  |  End: {c.get('end_date', 'N/A')}")
    lines.append(f"  Status: {c.get('status', 'N/A')}")
    return "\n".join(lines)


def _format_module(m: Dict) -> str:
    lines = []
    lines.append(f"  Module: {m.get('name', 'Untitled')}")
    lines.append(f"  ID: {m.get('id', 'N/A')}")
    if m.get('start_date'):
        lines.append(f"  Start: {m['start_date']}  |  End: {m.get('target_date', 'N/A')}")
    lines.append(f"  Status: {m.get('status', 'N/A')}")
    return "\n".join(lines)


def _format_state(s: Dict) -> str:
    return f"  [{s.get('group', '?')}] {s.get('name', '?')} (ID: {s.get('id', 'N/A')[:8]}...)"


def _format_label(l: Dict) -> str:
    color = l.get('color', '')
    return f"  {l.get('name', '?')} (ID: {l.get('id', 'N/A')[:8]}...) {color}"


def _format_member(m: Dict) -> str:
    member = m.get('member', m)
    display = member.get('display_name', member.get('email', '?'))
    role_map = {5: 'Guest', 10: 'Viewer', 15: 'Member', 20: 'Admin'}
    role = role_map.get(m.get('role', 0), str(m.get('role', '?')))
    return f"  {display} ({role}) - ID: {member.get('id', 'N/A')[:8]}..."


# =============================================================================
# Query Handler
# =============================================================================

def plane_query_handler(args: Dict[str, Any], **kwargs) -> str:
    """Query Plane data: projects, issues, cycles, modules, states, labels, members."""
    resource = args.get("resource", "projects").lower()
    project = args.get("project")
    filters = args.get("filters", {})
    issue_id = args.get("issue_id")
    page = args.get("page", 1)
    per_page = args.get("per_page", 50)

    # Resources that don't need a project
    if resource == "projects":
        resp = _api_call("GET", "projects/", params={"page": page, "per_page": per_page})
        if "error" in resp:
            return f"Error: {resp['error']}\n{resp.get('detail', '')}"

        results = resp.get("results", resp if isinstance(resp, list) else [])
        if not results:
            return "No projects found."

        output = [f"=== Projects ({len(results)}) ===\n"]
        for p in results:
            output.append(_format_project(p))
            output.append("")
        return "\n".join(output)

    # All other resources need a project
    if not project:
        return "Error: 'project' parameter is required for querying " + resource

    project_id = _resolve_project_id(project)
    if not project_id:
        available = ", ".join(n.title() for n in PROJECT_MAP.keys())
        return f"Error: Could not resolve project '{project}'. Available: {available}"

    project_name = _get_project_name(project_id)

    if resource == "issues":
        if issue_id:
            # Get single issue
            resp = _api_call("GET", f"projects/{project_id}/issues/{issue_id}/")
            if "error" in resp:
                return f"Error: {resp['error']}\n{resp.get('detail', '')}"
            return f"=== Issue Detail ({project_name}) ===\n\n{_format_issue(resp)}"

        # Build filter params
        params = {"page": page, "per_page": per_page, "expand": "assignees,labels,state"}
        if filters:
            if filters.get("priority"):
                params["priority"] = filters["priority"]
            if filters.get("state"):
                params["state"] = filters["state"]
            if filters.get("assignee"):
                params["assignees"] = filters["assignee"]
            if filters.get("label"):
                params["labels"] = filters["label"]
            if filters.get("target_date"):
                params["target_date"] = filters["target_date"]
            if filters.get("created_by"):
                params["created_by"] = filters["created_by"]

        resp = _api_call("GET", f"projects/{project_id}/issues/", params=params)
        if "error" in resp:
            return f"Error: {resp['error']}\n{resp.get('detail', '')}"

        results = resp.get("results", resp if isinstance(resp, list) else [])
        total = resp.get("total_count", len(results))
        total_pages = resp.get("total_pages", 1)

        if not results:
            return f"No issues found in {project_name} with the given filters."

        output = [f"=== Issues in {project_name} (showing {len(results)} of {total}, page {page}/{total_pages}) ===\n"]
        for issue in results:
            output.append(_format_issue(issue))
            output.append("")

        if total_pages > page:
            output.append(f"[Page {page} of {total_pages} — use page={page+1} to see more]")
        return "\n".join(output)

    elif resource == "cycles":
        resp = _api_call("GET", f"projects/{project_id}/cycles/", params={"page": page, "per_page": per_page})
        if "error" in resp:
            return f"Error: {resp['error']}\n{resp.get('detail', '')}"

        results = resp.get("results", resp if isinstance(resp, list) else [])
        if not results:
            return f"No cycles found in {project_name}."

        output = [f"=== Cycles in {project_name} ({len(results)}) ===\n"]
        for c in results:
            output.append(_format_cycle(c))
            output.append("")
        return "\n".join(output)

    elif resource == "modules":
        resp = _api_call("GET", f"projects/{project_id}/modules/", params={"page": page, "per_page": per_page})
        if "error" in resp:
            return f"Error: {resp['error']}\n{resp.get('detail', '')}"

        results = resp.get("results", resp if isinstance(resp, list) else [])
        if not results:
            return f"No modules found in {project_name}."

        output = [f"=== Modules in {project_name} ({len(results)}) ===\n"]
        for m in results:
            output.append(_format_module(m))
            output.append("")
        return "\n".join(output)

    elif resource == "states":
        resp = _api_call("GET", f"projects/{project_id}/states/")
        if "error" in resp:
            return f"Error: {resp['error']}\n{resp.get('detail', '')}"

        results = resp.get("results", resp if isinstance(resp, list) else [])
        if not results:
            return f"No states found in {project_name}."

        output = [f"=== States in {project_name} ({len(results)}) ===\n"]
        for s in results:
            output.append(_format_state(s))
        return "\n".join(output)

    elif resource == "labels":
        resp = _api_call("GET", f"projects/{project_id}/labels/")
        if "error" in resp:
            return f"Error: {resp['error']}\n{resp.get('detail', '')}"

        results = resp.get("results", resp if isinstance(resp, list) else [])
        if not results:
            return f"No labels found in {project_name}."

        output = [f"=== Labels in {project_name} ({len(results)}) ===\n"]
        for l in results:
            output.append(_format_label(l))
        return "\n".join(output)

    elif resource == "members":
        resp = _api_call("GET", f"projects/{project_id}/members/")
        if "error" in resp:
            return f"Error: {resp['error']}\n{resp.get('detail', '')}"

        results = resp.get("results", resp if isinstance(resp, list) else [])
        if not results:
            return f"No members found in {project_name}."

        output = [f"=== Members in {project_name} ({len(results)}) ===\n"]
        for m in results:
            output.append(_format_member(m))
        return "\n".join(output)

    else:
        return f"Error: Unknown resource '{resource}'. Valid: projects, issues, cycles, modules, states, labels, members"


# =============================================================================
# Update Handler
# =============================================================================

def plane_update_handler(args: Dict[str, Any], **kwargs) -> str:
    """Create or update Plane issues, or add comments."""
    action = args.get("action", "create").lower()
    project = args.get("project")
    issue_id = args.get("issue_id")
    data = args.get("data", {})

    if not project:
        return "Error: 'project' parameter is required."

    project_id = _resolve_project_id(project)
    if not project_id:
        available = ", ".join(n.title() for n in PROJECT_MAP.keys())
        return f"Error: Could not resolve project '{project}'. Available: {available}"

    project_name = _get_project_name(project_id)

    if action == "create":
        # Build issue payload
        payload = {}
        field_map = {
            "name": "name",
            "description_html": "description_html",
            "priority": "priority",
            "state": "state",
            "assignees": "assignees",
            "labels": "labels",
            "start_date": "start_date",
            "target_date": "target_date",
            "parent": "parent",
            "estimate_point": "estimate_point",
        }
        for data_key, api_key in field_map.items():
            if data_key in data:
                payload[api_key] = data[data_key]

        if "name" not in payload:
            return "Error: 'name' is required in data for creating an issue."

        resp = _api_call("POST", f"projects/{project_id}/issues/", data=payload)
        if "error" in resp:
            return f"Error creating issue: {resp['error']}\n{resp.get('detail', '')}"

        issue_name = resp.get("name", "Untitled")
        new_id = resp.get("id", "unknown")
        seq = resp.get("sequence_id", "")
        identifier = resp.get("project_detail", {}).get("identifier", "")
        label = f"{identifier}-{seq}" if identifier and seq else new_id[:8]

        return (
            f"Issue created successfully in {project_name}!\n\n"
            f"  [{label}] {issue_name}\n"
            f"  ID: {new_id}\n"
            f"  Priority: {resp.get('priority', 'none')}\n"
        )

    elif action == "update":
        if not issue_id:
            return "Error: 'issue_id' is required for updating an issue."

        payload = {}
        field_map = {
            "name": "name",
            "description_html": "description_html",
            "priority": "priority",
            "state": "state",
            "assignees": "assignees",
            "labels": "labels",
            "start_date": "start_date",
            "target_date": "target_date",
            "parent": "parent",
            "estimate_point": "estimate_point",
        }
        for data_key, api_key in field_map.items():
            if data_key in data:
                payload[api_key] = data[data_key]

        if not payload:
            return "Error: No fields to update. Provide fields in 'data'."

        resp = _api_call("PATCH", f"projects/{project_id}/issues/{issue_id}/", data=payload)
        if "error" in resp:
            return f"Error updating issue: {resp['error']}\n{resp.get('detail', '')}"

        issue_name = resp.get("name", "Untitled")
        updated_fields = ", ".join(payload.keys())
        return (
            f"Issue updated successfully in {project_name}!\n\n"
            f"  Issue: {issue_name}\n"
            f"  ID: {issue_id}\n"
            f"  Updated fields: {updated_fields}\n"
        )

    elif action == "comment":
        if not issue_id:
            return "Error: 'issue_id' is required for adding a comment."

        comment_html = data.get("comment_html", "")
        if not comment_html:
            return "Error: 'comment_html' is required in data for adding a comment."

        payload = {"comment_html": comment_html}
        resp = _api_call("POST", f"projects/{project_id}/issues/{issue_id}/comments/", data=payload)
        if "error" in resp:
            return f"Error adding comment: {resp['error']}\n{resp.get('detail', '')}"

        return (
            f"Comment added successfully!\n\n"
            f"  Issue ID: {issue_id}\n"
            f"  Project: {project_name}\n"
            f"  Comment ID: {resp.get('id', 'unknown')}\n"
        )

    else:
        return f"Error: Unknown action '{action}'. Valid: create, update, comment"


# =============================================================================
# Check function
# =============================================================================

def check_plane_requirements() -> bool:
    """Check if Plane API credentials are configured."""
    return bool(os.environ.get("PLANE_API_KEY")) and bool(os.environ.get("PLANE_WORKSPACE_SLUG"))


# =============================================================================
# OpenAI Function-Calling Schemas
# =============================================================================

PLANE_QUERY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "plane_query",
        "description": (
            "Query Plane.so project management data. Retrieve projects, issues, cycles, "
            "modules, states, labels, or members. Supports filtering issues by priority, "
            "state, assignee, and label. Supports pagination.\n\n"
            "Available projects: Engineering, Data Science, Customer Issues & Tracks, "
            "Customer Onboarding, ARCTAN, Business.\n\n"
            "Examples:\n"
            "- List all projects: resource='projects'\n"
            "- List issues: resource='issues', project='Engineering'\n"
            "- Filter issues: resource='issues', project='Engineering', filters={priority: 'urgent'}\n"
            "- Get single issue: resource='issues', project='Engineering', issue_id='<uuid>'\n"
            "- List states: resource='states', project='Engineering'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "resource": {
                    "type": "string",
                    "enum": ["projects", "issues", "cycles", "modules", "states", "labels", "members"],
                    "description": "Type of resource to query."
                },
                "project": {
                    "type": "string",
                    "description": "Project name (partial match supported) or project UUID. Required for all resources except 'projects'."
                },
                "filters": {
                    "type": "object",
                    "description": "Filters for issue queries. Keys: priority (none|low|medium|high|urgent), state (state UUID), assignee (member UUID), label (label UUID), target_date, created_by.",
                    "properties": {
                        "priority": {"type": "string", "description": "Filter by priority: none, low, medium, high, urgent"},
                        "state": {"type": "string", "description": "Filter by state UUID"},
                        "assignee": {"type": "string", "description": "Filter by assignee member UUID"},
                        "label": {"type": "string", "description": "Filter by label UUID"},
                        "target_date": {"type": "string", "description": "Filter by target date"},
                        "created_by": {"type": "string", "description": "Filter by creator UUID"}
                    }
                },
                "issue_id": {
                    "type": "string",
                    "description": "Specific issue UUID to retrieve details for."
                },
                "page": {
                    "type": "integer",
                    "description": "Page number for paginated results (default: 1).",
                    "default": 1
                },
                "per_page": {
                    "type": "integer",
                    "description": "Results per page (default: 50, max: 100).",
                    "default": 50
                }
            },
            "required": ["resource"]
        }
    }
}

PLANE_UPDATE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "plane_update",
        "description": (
            "Create or update Plane.so issues, or add comments.\n\n"
            "Actions:\n"
            "- create: Create a new issue. Requires 'data.name'.\n"
            "- update: Update an existing issue. Requires 'issue_id'.\n"
            "- comment: Add a comment to an issue. Requires 'issue_id' and 'data.comment_html'.\n\n"
            "Available projects: Engineering, Data Science, Customer Issues & Tracks, "
            "Customer Onboarding, ARCTAN, Business.\n\n"
            "Data fields: name, description_html, priority (none|low|medium|high|urgent), "
            "state (UUID), assignees (list of UUIDs), labels (list of UUIDs), "
            "start_date (YYYY-MM-DD), target_date (YYYY-MM-DD), comment_html."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "update", "comment"],
                    "description": "Action to perform."
                },
                "project": {
                    "type": "string",
                    "description": "Project name (partial match supported) or project UUID."
                },
                "issue_id": {
                    "type": "string",
                    "description": "Issue UUID (required for update and comment actions)."
                },
                "data": {
                    "type": "object",
                    "description": "Fields for the issue or comment.",
                    "properties": {
                        "name": {"type": "string", "description": "Issue title"},
                        "description_html": {"type": "string", "description": "Issue description in HTML"},
                        "priority": {
                            "type": "string",
                            "enum": ["none", "low", "medium", "high", "urgent"],
                            "description": "Issue priority"
                        },
                        "state": {"type": "string", "description": "State UUID"},
                        "assignees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of assignee member UUIDs"
                        },
                        "labels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of label UUIDs"
                        },
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                        "target_date": {"type": "string", "description": "Target/due date (YYYY-MM-DD)"},
                        "comment_html": {"type": "string", "description": "Comment text in HTML (for comment action)"}
                    }
                }
            },
            "required": ["action", "project"]
        }
    }
}


# =============================================================================
# Registry
# =============================================================================

from tools.registry import registry

registry.register(
    name="plane_query",
    toolset="plane",
    schema=PLANE_QUERY_SCHEMA,
    handler=plane_query_handler,
    check_fn=check_plane_requirements,
    emoji="✈️",
)

registry.register(
    name="plane_update",
    toolset="plane",
    schema=PLANE_UPDATE_SCHEMA,
    handler=plane_update_handler,
    check_fn=check_plane_requirements,
    emoji="✈️",
)
