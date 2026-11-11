# ==========================================
# MCP Server: Postgres (stdio, READ-ONLY)
# ==========================================
# Used by THE_EXAMPLE.py -> Exercise 25.
# Why it's NOT inside THE_EXAMPLE.py: an MCP server must run as its own program.
# stdio = the client launches it automatically; you never start it yourself.

# STEP 0: IMPORTS
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from mcp.server.fastmcp import FastMCP

# STEP 1: SHARED STUFF
# load_dotenv() searches UPWARD from this file, so it finds mcp/backend/.env first.
# That's where DATABASE_URL must be (postgresql+psycopg://user:pass@host:5432/books_db).
load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])  # just a recipe; it connects on first use

mcp = FastMCP("Postgres")

# STEP 2: THE TOOLS
@mcp.tool()
def list_tables() -> list[str]:
    """List the names of all tables in the public schema."""
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        ))
        return [row[0] for row in rows]

@mcp.tool()
def run_query(sql: str) -> list[dict]:
    """Run a read-only SQL query (SELECT) and return up to 50 rows."""
    with engine.connect() as conn:
        # Must be the FIRST statement of the transaction: Postgres will now reject
        # INSERT / UPDATE / DELETE / DROP, so the AI can look but never change data.
        conn.exec_driver_sql("SET TRANSACTION READ ONLY")
        rows = conn.exec_driver_sql(sql).mappings().fetchmany(50)
        return [dict(row) for row in rows]

# STEP 3: RUN IT
if __name__ == "__main__":
    mcp.run(transport="stdio")
