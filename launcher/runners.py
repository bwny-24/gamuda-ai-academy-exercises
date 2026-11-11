import shutil, socket, subprocess, sys, threading, time, webbrowser
from pathlib import Path

# ==========================================
# RUNNERS: how each kind of exercise is opened/started
# ==========================================
# Most exercises are NOT Python (HTML pages, React apps, FastAPI servers), so the
# menu can't just call a function. Each "type" in a week.toml maps to one runner here.
#
# Stop a running app/server with Ctrl+C: you go back to the menu instead of crashing.

DEFAULT_APP = "main:app"  # uvicorn's "<file>:<variable>": the `app` object inside main.py

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
    print(f"\n> {' '.join(str(part) for part in cmd)}   (in {folder})")
    print("Press Ctrl+C to stop and go back to the menu.\n")
    try:
        subprocess.run(cmd, cwd=folder)
    except KeyboardInterrupt:
        print("\nStopped.")

# ==========================================
# Python scripts (including scripts that show their own menu)
# ==========================================
def run_python(script: Path):
    if not script.exists():
        print(f"Can't find {script}")
        return
    # cwd = the script's own folder, so its .env, PDFs, images are found
    # exactly as if you ran it yourself. sys.executable = same venv as this menu.
    try:
        subprocess.run([sys.executable, script.name], cwd=script.parent)
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
    if not (app_folder / "package.json").exists():
        print(f"Can't find a React app (package.json) in {app_folder}")
        return None
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
def fastapi_command(app: str = DEFAULT_APP, port: int = 8000):
    # sys.executable -m uvicorn = uvicorn from the SAME venv as this menu
    return [sys.executable, "-m", "uvicorn", app, "--reload", "--port", str(port)]

def _open_when_server_is_up(target: str, port: int):
    # The server needs a few seconds to start; opening the browser too early shows an error page.
    def wait_then_open():
        for _ in range(60):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.5).close()
            except OSError:
                time.sleep(0.5)
            else:
                webbrowser.open(target)
                return
    threading.Thread(target=wait_then_open, daemon=True).start()

def run_fastapi(backend_folder: Path, app: str = DEFAULT_APP, port: int = 8000, open_target: str = ""):
    if not backend_folder.exists():
        print(f"Can't find {backend_folder}")
        return
    print(f"API docs (Swagger UI): http://127.0.0.1:{port}/docs")
    if open_target:
        _open_when_server_is_up(open_target, port)
    run_command(fastapi_command(app, port), backend_folder)

# ==========================================
# Full-stack: backend in the background + frontend in front, both stop on Ctrl+C
# ==========================================
def run_fullstack(backend_folder: Path, frontend_folder: Path, app: str = DEFAULT_APP, port: int = 8000):
    if not backend_folder.exists():
        print(f"Can't find {backend_folder}")
        return
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

# ==========================================
# week.toml "type" -> runner
# ==========================================
# Each entry: the keys that type needs in week.toml (checked by `python menu.py --check`).
EXERCISE_TYPES = {
    "html": ["path"],
    "react": ["path"],
    "python": ["path"],
    "menu": ["path"],
    "fastapi": [],
    "fullstack": ["backend", "frontend"],
}

def _fastapi_open_target(section_dir: Path, exercise: dict, port: int) -> str:
    # open = "/docs"            -> a page served by the API itself
    # open = "frontend/x.html"  -> a local HTML file that calls the API
    target = exercise.get("open", "")
    if not target:
        return ""
    if target.startswith("/"):
        return f"http://127.0.0.1:{port}{target}"
    return (section_dir / target).as_uri()

def run_exercise(section_dir: Path, exercise: dict):
    kind = exercise.get("type")
    port = exercise.get("port", 8000)
    app = exercise.get("app", DEFAULT_APP)

    if kind == "html":
        open_page(section_dir / exercise["path"], exercise.get("section", ""))
    elif kind == "react":
        run_react_app(section_dir / exercise["path"])
    elif kind in ("python", "menu"):
        run_python(section_dir / exercise["path"])
    elif kind == "fastapi":
        run_fastapi(section_dir / exercise.get("path", "."), app, port,
                    _fastapi_open_target(section_dir, exercise, port))
    elif kind == "fullstack":
        run_fullstack(section_dir / exercise["backend"], section_dir / exercise["frontend"], app, port)
    else:
        print(f"Unknown type '{kind}' in week.toml. Use one of: {', '.join(EXERCISE_TYPES)}")
