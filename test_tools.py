#!/usr/bin/env python3
"""
Quick test script to call MCP tools directly (bypasses MCP protocol).
Usage: python test_tools.py <tool_name> [args as JSON]

Examples:
    python test_tools.py get_study_info '{"accession": "SRR9990627"}'
    python test_tools.py list_runs '{"study_accession": "SRP123456"}'
    python test_tools.py list_manifests '{}'
"""
import sys
import json

# Import tools directly from main
from main import (
    get_study_info,
    list_runs,
    create_manifest,
    list_manifests,
    approve_manifest,
    import_to_hox,
    get_import_status
)

TOOLS = {
    "get_study_info": get_study_info,
    "list_runs": list_runs,
    "create_manifest": create_manifest,
    "list_manifests": list_manifests,
    "approve_manifest": approve_manifest,
    "import_to_hox": import_to_hox,
    "get_import_status": get_import_status,
}

def main():
    if len(sys.argv) < 2:
        print("Available tools:")
        for name in TOOLS:
            print(f"  - {name}")
        print("\nUsage: python test_tools.py <tool_name> [args as JSON]")
        sys.exit(0)

    tool_name = sys.argv[1]
    if tool_name not in TOOLS:
        print(f"Unknown tool: {tool_name}")
        print(f"Available: {', '.join(TOOLS.keys())}")
        sys.exit(1)

    # Parse args
    args = {}
    if len(sys.argv) > 2:
        args = json.loads(sys.argv[2])

    # Call tool
    result = TOOLS[tool_name](**args)

    # Pretty print if JSON
    try:
        parsed = json.loads(result)
        print(json.dumps(parsed, indent=2))
    except:
        print(result)

if __name__ == "__main__":
    main()
