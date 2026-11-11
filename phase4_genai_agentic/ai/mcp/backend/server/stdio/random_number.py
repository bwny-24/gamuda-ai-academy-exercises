# ==========================================
# MCP Server: Random Number (stdio)
# ==========================================
# Used by THE_EXAMPLE.py -> Exercise 23 / 24.
# Why it's NOT inside THE_EXAMPLE.py: an MCP server must run as its own program.
# stdio = it talks through stdin/stdout, so you never start it yourself;
# the client (Exercise 23) launches it automatically as a child process.

# STEP 0: IMPORTS
import random
from mcp.server.fastmcp import FastMCP

# STEP 1: CREATE THE SERVER
mcp = FastMCP("Random Number")

# STEP 2: THE TOOL
# The docstring + type hints are what the AI reads to decide when/how to call it.
@mcp.tool()
def get_number(low: int = 1, high: int = 100) -> int:
    """Return a random whole number between low and high."""
    return random.randint(low, high)

# STEP 3: RUN IT
if __name__ == "__main__":
    mcp.run(transport="stdio")
