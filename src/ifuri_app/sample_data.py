# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

from __future__ import annotations

import copy
import platform
import socket
import uuid

DEFAULT_FLOW = """flow:
  id: local-review-and-share
  group: dev-ops

do:
  - mcp://filesystem/list:
      path: ./project
  - llm://local/qwen/analyze:
      input: file://project-summary
  - agent://code-reviewer/run
  - ifuri://office-node.local/services/browser/open:
      url: https://ifuri.com
"""

DEFAULT_WORKSPACE = {
    "version": 1,
    "node": {
        "id": "",
        "name": "",
        "role": "host",
        "port": 8765,
        "public": False,
    },
    "urisys": {
        "endpoint": "http://127.0.0.1:8790",
        "role": "client",
        "examples_root": "",
    },
    "groups": [
        {
            "id": "dev-ops",
            "name": "DevOps flows",
            "description": "Grouped uri2flow tasks for local automation.",
            "flows": [
                {
                    "id": "local-review-and-share",
                    "name": "Local review and remote browser",
                    "filename": "local-review-and-share.uri.flow.yaml",
                    "text": DEFAULT_FLOW,
                    "updated_at": "",
                }
            ],
        },
        {
            "id": "office",
            "name": "Office workflows",
            "description": "Examples for office, browser, mail and agent actions.",
            "flows": [],
        },
    ],
    "services": [
        {"name": "Local filesystem MCP", "scheme": "mcp", "uri": "mcp://filesystem/list", "scope": "private", "enabled": True},
        {"name": "Code reviewer agent", "scheme": "agent", "uri": "agent://code-reviewer/run", "scope": "private", "enabled": True},
        {"name": "Local LLM", "scheme": "llm", "uri": "llm://local/qwen/analyze", "scope": "private", "enabled": True},
        {"name": "Browser operator", "scheme": "browser", "uri": "browser://chrome/page/open", "scope": "shared", "enabled": True},
        {"name": "Shell dry-run", "scheme": "shell", "uri": "shell://local/echo", "scope": "private", "enabled": True},
        {"name": "ifURI peer call", "scheme": "ifuri", "uri": "ifuri://peer.local/api/uri/call", "scope": "shared", "enabled": True},
    ],
    "peers": [],
    "events": [],
}


def default_workspace() -> dict:
    data = copy.deepcopy(DEFAULT_WORKSPACE)
    data["node"]["id"] = f"ifuri-{uuid.uuid4().hex[:8]}"
    hostname = socket.gethostname() or platform.node() or "local"
    data["node"]["name"] = f"{hostname}.ifuri"
    return data
