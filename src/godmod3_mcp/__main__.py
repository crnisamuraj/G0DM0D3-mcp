#!/usr/bin/env python
"""Shim to run the G0DM0D3 MCP server as a module."""

import sys

from godmod3_mcp.server import main

if __name__ == "__main__":
    sys.exit(main())
