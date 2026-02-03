#!/bin/bash

# Clear any stuck ports from previous runs
lsof -i :6274 -i :6277 -t 2>/dev/null | xargs kill -9 2>/dev/null

# Get absolute path to current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the inspector with ABSOLUTE paths to ensure it can find the python executable
echo "Starting Bio Tools Server..."
echo "Please wait for the browser to open..."

# We use the full path to python and main.py
npx @modelcontextprotocol/inspector "$DIR/.venv/bin/python" "$DIR/main.py"
