# ==========================================
# MCP Server: Dice Roller (HTTP)
# ==========================================
# Used by THE_EXAMPLE.py -> Exercise 23 / 24.
# Why it's NOT inside THE_EXAMPLE.py: an MCP server must run as its own program.
# HTTP = unlike stdio, YOU start it first (terminal 1) and leave it running;
# the client connects to it at http://127.0.0.1:8001/mcp.
# Port 8001 (not 8000) so it does not clash with uvicorn THE_EXAMPLE:app, which uses 8000.

# STEP 0: IMPORTS
import secrets
from mcp.server.fastmcp import FastMCP

# STEP 1: CREATE THE SERVER (host/port = where it listens)
mcp = FastMCP("Dice Roller", host="127.0.0.1", port=8001)

# STEP 2: THE TOOL
@mcp.tool()
def roll_dice(n_dice: int) -> list[int]:
    """Roll n_dice six-sided dice and return each result."""
    return [secrets.randbelow(6) + 1 for _ in range(n_dice)]

# STEP 3: RUN IT -> serves on http://127.0.0.1:8001/mcp
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
