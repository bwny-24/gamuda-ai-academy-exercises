import shutil, subprocess, sys, webbrowser
from pathlib import Path

# ==========================================
# LAUNCH HELPERS: shared by every week's exercises.py
# ==========================================
# Most exercises are NOT Python (HTML pages, React apps, FastAPI servers), so the
# week menus can't just call a function. These helpers open/start them for you.
#
# How a week's exercises.py uses this file (it lives 2 folders up, in lesson/):
#     sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
#     from launch import open_page, run_react_app, run_fastapi
#
# Stop a running app/server with Ctrl+C: you go back to the menu instead of crashing.

# ==========================================
# HTML pages -> open in the browser
# ==========================================
def open_page(page: Path, section: str = ""):
    if not page.exists():
        print(f"Can't find {page}")
        return
    url = page.as_uri() + (f"#{section}" if section else "")
    print(f"Opening {url}")
    # (Some Windows setups drop the #part for local files; then just scroll to the section.)
    webbrowser.open(url)

# ==========================================
# Run a terminal command until Ctrl+C
# ==========================================
def run_command(cmd: list, folder: Path):
    print(f"\n> {' '.join(cmd)}   (in {folder})")
    print("Press Ctrl+C to stop and go back to the menu.\n")
    try:
        subprocess.run(cmd, cwd=folder)
    except KeyboardInterrupt:
        print("\nStopped.")

# ==========================================
# React (Vite) apps -> npm install (first time) + npm run dev
# ==========================================
def _npm():
    # On Windows npm is "npm.cmd"; shutil.which finds the right one on any OS
    npm = shutil.which("npm")
    if npm is None:
        print("npm not found. Install Node.js from https://nodejs.org and reopen the terminal.")
    return npm

def _npm_install_if_needed(app_folder: Path, npm: str) -> bool:
    if (app_folder / "node_modules").exists():
        return True
    # node_modules isn't in git (too big), so a fresh copy needs this once
    print(f"First run: installing packages in {app_folder.name} (takes a minute)...")
    return subprocess.run([npm, "install"], cwd=app_folder).returncode == 0

def react_dev_command(app_folder: Path):
    """Returns the npm command that starts the Vite dev server, or None if it can't."""
    npm = _npm()
    if npm is None or not _npm_install_if_needed(app_folder, npm):
        return None
    # "--" passes --open to Vite: it opens the browser at http://localhost:5173 by itself
    return [npm, "run", "dev", "--", "--open"]

def run_react_app(app_folder: Path):
    cmd = react_dev_command(app_folder)
    if cmd:
        run_command(cmd, app_folder)

# ==========================================
# FastAPI -> uvicorn
# ==========================================
def fastapi_command(app: str = "main:app", port: int = 8000):
    # sys.executable -m uvicorn = uvicorn from the SAME venv as this menu
    return [sys.executable, "-m", "uvicorn", app, "--reload", "--port", str(port)]

def run_fastapi(backend_folder: Path, app: str = "main:app", port: int = 8000):
    print(f"API docs (Swagger UI): http://127.0.0.1:{port}/docs")
    run_command(fastapi_command(app, port), backend_folder)

# ==========================================
# Full-stack: backend in the background + frontend in front, both stop on Ctrl+C
# ==========================================
def run_fullstack(backend_folder: Path, frontend_folder: Path, app: str = "main:app", port: int = 8000):
    front_cmd = react_dev_command(frontend_folder)
    if front_cmd is None:
        return
    print(f"Starting backend: http://127.0.0.1:{port}/docs")
    backend = subprocess.Popen(fastapi_command(app, port), cwd=backend_folder)
    try:
        run_command(front_cmd, frontend_folder)
    finally:
        backend.terminate()  # stop the backend too when the frontend stops
        backend.wait()
        print("Backend stopped.")
