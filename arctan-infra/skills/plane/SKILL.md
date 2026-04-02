---
name: plane
description: "Manage Plane.so projects, issues (work items), cycles, modules, and members via REST API. Query, create, update, and analyze project management data using curl."
tags: [plane, project-management, issues, work-items, productivity]
triggers:
  - user mentions Plane, issues, work items, sprints, cycles, modules
  - user asks about project status, task tracking, issue management
  - user wants to create, update, or query Plane work items
---

# Plane.so API Integration

## Environment
Requires these env vars (stored in ~/.hermes/.env):
- `PLANE_API_KEY` — API token from Workspace Settings > API Tokens
- `PLANE_WORKSPACE_SLUG` — workspace slug (e.g. "arctan")
- `PLANE_BASE_URL` — https://api.plane.so/api/v1

## Auth Header
All requests use: `-H "x-api-key: $PLANE_API_KEY" -H "Content-Type: application/json"`

## Quick Reference — Shell Helper
```bash
# Set up variables for a session
export PLANE_API_KEY=$(grep PLANE_API_KEY ~/.hermes/.env | cut -d= -f2)
export PLANE_WS=$(grep PLANE_WORKSPACE_SLUG ~/.hermes/.env | cut -d= -f2)
export PLANE_URL=$(grep PLANE_BASE_URL ~/.hermes/.env | cut -d= -f2)
alias pcurl='curl -s -H "x-api-key: $PLANE_API_KEY" -H "Content-Type: application/json"'
```

## Core Endpoints

### 1. List Projects
```bash
pcurl "$PLANE_URL/workspaces/$PLANE_WS/projects/"
```
Response: `{ "results": [...], "total_count": N }`

### 2. List Issues (Work Items) in a Project
```bash
pcurl "$PLANE_URL/workspaces/$PLANE_WS/projects/<project_id>/issues/?per_page=100"
```
Pagination: response has `next_cursor`, `next_page_results`, `total_count`, `total_pages`.
Use `?cursor=<next_cursor>&per_page=100` for next page.

### 3. Get Single Issue
```bash
pcurl "$PLANE_URL/workspaces/$PLANE_WS/projects/<project_id>/issues/<issue_id>/"
```

### 4. Create Issue
```bash
pcurl -X POST "$PLANE_URL/workspaces/$PLANE_WS/projects/<project_id>/issues/" \
  -d '{
    "name": "Issue title",
    "description_html": "<p>Description</p>",
    "priority": "high",
    "state": "<state_uuid>",
    "assignees": ["<member_uuid>"],
    "labels": ["<label_uuid>"],
    "start_date": "2026-04-01",
    "target_date": "2026-04-15"
  }'
```
Priority values: urgent, high, medium, low, none

### 5. Update Issue (Partial)
```bash
pcurl -X PATCH "$PLANE_URL/workspaces/$PLANE_WS/projects/<project_id>/issues/<issue_id>/" \
  -d '{"priority": "urgent", "state": "<new_state_uuid>"}'
```

### 6. Delete Issue
```bash
pcurl -X DELETE "$PLANE_URL/workspaces/$PLANE_WS/projects/<project_id>/issues/<issue_id>/"
```

### 7. List States (for a project)
```bash
pcurl "$PLANE_URL/workspaces/$PLANE_WS/projects/<project_id>/states/"
```
State groups: backlog, unstarted, started, completed, cancelled

### 8. List Labels
```bash
pcurl "$PLANE_URL/workspaces/$PLANE_WS/projects/<project_id>/labels/"
```

### 9. List Members
```bash
# Workspace members
pcurl "$PLANE_URL/workspaces/$PLANE_WS/members/"
# Project members
pcurl "$PLANE_URL/workspaces/$PLANE_WS/projects/<project_id>/members/"
```

### 10. Cycles
```bash
pcurl "$PLANE_URL/workspaces/$PLANE_WS/projects/<project_id>/cycles/"
```

### 11. Modules
```bash
pcurl "$PLANE_URL/workspaces/$PLANE_WS/projects/<project_id>/modules/"
```

### 12. Issue Activity / Comments
```bash
# Activity log
pcurl "$PLANE_URL/workspaces/$PLANE_WS/projects/<project_id>/issues/<issue_id>/activities/"
# Comments
pcurl "$PLANE_URL/workspaces/$PLANE_WS/projects/<project_id>/issues/<issue_id>/comments/"
# Add comment
pcurl -X POST "$PLANE_URL/workspaces/$PLANE_WS/projects/<project_id>/issues/<issue_id>/comments/" \
  -d '{"comment_html": "<p>My comment</p>"}'
```

## Arctan Workspace — Project Reference
| Identifier   | Name                     | ID                                   |
|-------------|--------------------------|--------------------------------------|
| ENGINEERIN  | Engineering              | f806dcbe-bc32-4a56-a1d0-27925d335545 |
| DATASCIENC  | Data Science             | 88a8b922-43de-46c3-9de8-33c43cf5cb8e |
| CUSTOMERIS  | Customer Issues & Tracks | d769c475-4958-46d3-afb0-db6c2b2c5c76 |
| CUSTOMERON  | Customer Onboarding      | 77e8d5de-950b-4a87-a5ba-c342d0e4bb4c |
| ARCTA       | ARCTAN                   | 46dc1634-69e8-4f98-b6dd-4c97bc674923 |
| BUSINESS    | Business                 | a85ef23b-913d-4f8a-81a7-893cf0f26539 |

## Common Patterns

### Get all issues with their states resolved
```bash
# First get states mapping
pcurl "$PLANE_URL/workspaces/$PLANE_WS/projects/<pid>/states/" | python3 -c "
import json,sys; [print(f'{s[\"id\"]}: {s[\"name\"]} ({s[\"group\"]})') for s in json.load(sys.stdin)['results']]"

# Then list issues with state names
pcurl "$PLANE_URL/workspaces/$PLANE_WS/projects/<pid>/issues/?per_page=100" | python3 -c "
import json,sys; data=json.load(sys.stdin)
for i in data['results']:
    print(f'[{i[\"priority\"]:6s}] {i[\"state_detail\"][\"name\"]:15s} | {i[\"name\"][:60]}')
"
```

### Paginate through all issues
```bash
python3 -c "
import json, subprocess, os
key = '$(grep PLANE_API_KEY ~/.hermes/.env | cut -d= -f2)'
ws = '$(grep PLANE_WORKSPACE_SLUG ~/.hermes/.env | cut -d= -f2)'
base = '$(grep PLANE_BASE_URL ~/.hermes/.env | cut -d= -f2)'
pid = '<project_id>'
cursor = ''
all_issues = []
while True:
    url = f'{base}/workspaces/{ws}/projects/{pid}/issues/?per_page=100'
    if cursor: url += f'&cursor={cursor}'
    r = subprocess.run(['curl','-s','-H',f'x-api-key: {key}','-H','Content-Type: application/json',url], capture_output=True, text=True)
    data = json.loads(r.stdout)
    all_issues.extend(data['results'])
    if not data.get('next_page_results'): break
    cursor = data['next_cursor']
print(f'Total: {len(all_issues)} issues')
"
```

## Pitfalls
- Workspace uses **slug** (string) not UUID in URL paths
- Issue descriptions use `description_html` (HTML format), not plain text
- States and labels must be referenced by UUID — fetch them first
- Assignees is a list of member UUIDs
- PATCH for updates (not PUT) — only send fields you want to change
- API returns 404 for invalid workspace slugs (not 401)
- Pagination uses cursor-based approach, not page numbers
