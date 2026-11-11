import sys
from pathlib import Path

from launcher.discovery import check, find_phases
from launcher.runners import run_exercise

# ==========================================
# MAIN MENU: Fullstack Web Development with AI 
# ==========================================
# Heres is the menu for the course supaya senang check semua or relearning purposes. 
# Run:    python menu.py
# Check:  python menu.py --check     (lists everything, reports broken paths)
#
# to check the folder is by phase learning, so kalau mau check by folders bole buka 1 1 
# dalam setiap phase folder either contain what been done by weeks or topic 
# ada 3 layers, maybe.. idk, tingu la

# Benny notes: how to add new exercise, section, phase, etc.
# HOW TO ADD AN EXERCISE: open that section's week.toml and add
#   [[exercise]]
#   title = "What it shows in the menu"
#   type  = "html"            # html | react | python | menu | fastapi | fullstack
#   path  = "page.html"       # relative to the folder the week.toml is in
#
#   html      path = the .html file                      -> opens in the browser
#   react     path = the Vite app folder                 -> npm install (once) + npm run dev
#   python    path = the .py file                        -> runs it in its own folder
#   menu      path = a .py file that shows its own menu  -> same as python
#   fastapi   path = backend folder (default "."), app = "main:app", port = 8000,
#             open = "/docs" or a local .html file       -> uvicorn, then opens that page
#   fullstack backend = folder, frontend = folder        -> both together, Ctrl+C stops both
#
# HOW TO ADD A SECTION: make a folder inside a phase and put a week.toml in it.
# HOW TO ADD A PHASE:   make a folder named phase<N>_<name> at the top.

ROOT = Path(__file__).resolve().parent

# Shows a numbered list and returns the item the user picked, or None for back/quit
def pick(title: str, items: list, back_label: str, note: str = ""):
    while True:
        print(f"\n========== {title} ==========")
        if note:
            print(note)
        for number, item in enumerate(items, start=1):
            print(f"{number}. {item['title']}")
        print(f"b. {back_label}")

        choice = input("Pick one: ").strip().lower()
        if choice == "b":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(items):
            return items[int(choice) - 1]
        print("Invalid choice.")

def main():
    while True:
        # Level 1: phase
        phase = pick("Coding is Fun: Course Menu", find_phases(ROOT), "Quit")
        if phase is None:
            break

        # Level 2: section inside that phase
        while True:
            section = pick(phase["title"], phase["sections"], "Back to phases")
            if section is None:
                break

            # Level 3: exercise inside that section
            while True:
                exercise = pick(section["title"], section["exercises"], "Back to sections", section["note"])
                if exercise is None:
                    break
                run_exercise(section["folder"], exercise)

if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(0 if check(ROOT) else 1)
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
