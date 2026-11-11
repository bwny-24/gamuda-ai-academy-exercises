import subprocess, sys
from pathlib import Path

# ==========================================
# MAIN MENU: Fullstack Web Development with AI (all weeks)
# ==========================================
# Run:  python lesson/menu.py
#
# 3 levels:  Phase  ->  Section (a week/topic)  ->  Exercise
#   - Levels 1 and 2 are here.
#   - Level 3 (the exercises) is in each section's own menu file
#     (phase1_web fundamentals/week 1/exercises.py, phase4_genai and agentic/ai/THE_EXAMPLE.py, ...).
# Non-Python exercises (HTML, React, FastAPI) are opened/started by lesson/launch.py.
# Picking a section starts that file as its own program, inside its own folder,
# so its .env, PDFs, HTML pages etc. are found exactly as if you ran it yourself.
#
# Folders on disk follow the same idea:
#   lesson/phaseN_<name>/week N/...   (AI stays in one folder: phase4_genai and agentic/ai)

LESSON_DIR = Path(__file__).resolve().parent

# HOW TO ADD A SECTION:
#   find its phase below and add:  "key": ("Description", "path/to/menu_file.py")
#   path is relative to lesson/.  None = not built yet (shows "coming soon")
PHASES = {
    "1": ("Phase 1 : Web Fundamentals", {
        "1": ("Week 1 : Web Fundamentals (HTML & CSS)", "phase1_web fundamentals/week 1/exercises.py"),
        "2": ("Week 2 : JavaScript Essentials", "phase1_web fundamentals/week 2/exercises.py"),
        "3": ("Week 3 : Design & Version Control (Figma, Git)", None),
    }),
    "2": ("Phase 2 : React Development & State", {
        "1": ("Week 3 : React Core", "phase2_react/week 3/exercises.py"),
        "2": ("Week 4 : State, Hooks & A34PIs", "phase2_react/week 4/exercises.py"),
        "3": ("Week 5 : Advanced React", None),
    }),
    "3": ("Phase 3 : Backend Integration & Cloud Services", {
        "1": ("Week 5 : Backend Foundations (FastAPI)", None),
        "2": ("Week 6 : Full-Stack Integration & Serverless", "phase3_backend and cloud/week 6/exercises.py"),
        "3": ("Week 7 : Cloud Infrastructure & Deployment", None),
        "4": ("Week 9-10 : Cloud Security, Data & Observability", None),
    }),
    "4": ("Phase 4 : Generative AI & Agentic Systems", {
        # Kept together in one file: all these exercises use AI and share helpers
        "1": ("Week 7-9 : GenAI, RAG & Agents (AI)", "phase4_genai and agentic/ai/THE_EXAMPLE.py"),
        "2": ("Introduction to Computer Vision (OpenCV)", "phase4_genai and agentic/computerVision/exercises.py"),
    }),
}

def run_section(menu_file: str):
    script = LESSON_DIR / menu_file
    # cwd = the section's own folder, sys.executable = same Python/venv as this menu
    if not script.exists():
        print(f"Can't find {script}. Was the folder renamed? Update PHASES in menu.py.")
        return
    try:
        subprocess.run([sys.executable, script.name], cwd=script.parent)
    except KeyboardInterrupt:
        pass  # Ctrl+C stopped an app/server: just come back to the menu

# Shows a numbered list and returns the key the user picked, or None for back/quit
def pick(title: str, options: dict, back_label: str):
    while True:
        print(f"\n========== {title} ==========")
        for key, (description, value) in options.items():
            print(f"{key}. {description}{'' if value else '  (coming soon)'}")
        print(f"b. {back_label}")

        choice = input("Pick one: ").strip().lower()
        if choice == "b":
            return None
        if choice in options:
            return choice
        print("Invalid choice.")

if __name__ == "__main__":
    while True:
        # Level 1: phase
        phase_key = pick("Coding is Fun: Course Menu", PHASES, "Quit")
        if phase_key is None:
            break
        phase_title, sections = PHASES[phase_key]

        # Level 2: section inside that phase
        while True:
            section_key = pick(phase_title, sections, "Back to phases")
            if section_key is None:
                break
            description, menu_file = sections[section_key]
            if menu_file is None:
                print(f"{description} is not built yet.")
                continue
            # Level 3: the section's own exercise menu
            run_section(menu_file)
