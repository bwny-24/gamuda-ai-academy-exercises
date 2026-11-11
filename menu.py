import sys
from pathlib import Path

from launcher.discovery import check, find_phases
from launcher.runners import run_exercise

# ==========================================
# MAIN MENU: Fullstack Web Development with AI (all weeks)
# ==========================================
# Run:    python menu.py
# Check:  python menu.py --check     (lists everything, reports broken paths)
#
# 3 levels:  Phase  ->  Section (a week/topic)  ->  Exercise
# Nothing is listed in this file. The menu is built from the folders:
#
#   phase<N>_<name>/                 a phase      (optional phase.toml = nicer title)
#       <section>/                   a week/topic (must contain week.toml)
#           week.toml                title + the list of exercises
#
# Weeks 1-4 have one folder per week. From week 5 on the course mixes topics,
# so those are grouped by topic instead (books_crud, ai, computer_vision).
#
# HOW TO ADD AN EXERCISE: open that section's week.toml and add
#
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
