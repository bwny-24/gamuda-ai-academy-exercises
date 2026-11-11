import tomllib
from pathlib import Path

from launcher.runners import EXERCISE_TYPES

# ==========================================
# DISCOVERY: the menu is built from the folders, not from a hand-written list
# ==========================================
#   phase folder   = any folder at the top named  phase<N>_<name>
#   section folder = any folder inside a phase that contains a week.toml
#   exercises      = the [[exercise]] entries inside that week.toml
# Rename or add a folder and the menu follows; there is no path list to keep in sync.

SECTION_FILE = "week.toml"
PHASE_FILE = "phase.toml"   # optional: only holds a nicer title for the phase

def _read_toml(file: Path) -> dict:
    try:
        return tomllib.loads(file.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        print(f"Skipping {file}: {error}")
        return {}

def _title_from_folder(folder: Path) -> str:
    # "phase4_genai_agentic" -> "Phase4 Genai Agentic"
    return folder.name.replace("_", " ").title()

def find_phases(root: Path) -> list[dict]:
    phases = []
    for folder in sorted(root.glob("phase*")):
        if not folder.is_dir():
            continue
        sections = find_sections(folder)
        if not sections:
            continue
        phase_file = folder / PHASE_FILE
        info = _read_toml(phase_file) if phase_file.exists() else {}
        phases.append({
            "title": info.get("title", _title_from_folder(folder)),
            "folder": folder,
            "sections": sections,
        })
    return phases

def find_sections(phase_folder: Path) -> list[dict]:
    sections = []
    for section_file in sorted(phase_folder.glob(f"*/{SECTION_FILE}")):
        info = _read_toml(section_file)
        if not info:
            continue
        sections.append({
            "title": info.get("title", _title_from_folder(section_file.parent)),
            "note": info.get("note", ""),
            "folder": section_file.parent,
            "exercises": info.get("exercise", []),
        })
    return sections

# ==========================================
# python menu.py --check  -> lists everything and reports broken entries
# ==========================================
PATH_KEYS = ("path", "backend", "frontend")

def _problems_with(section: dict, exercise: dict) -> list[str]:
    kind = exercise.get("type")
    if kind not in EXERCISE_TYPES:
        return [f"unknown type '{kind}'"]
    problems = [f"missing '{key}'" for key in EXERCISE_TYPES[kind] if key not in exercise]
    for key in PATH_KEYS:
        if key in exercise and not (section["folder"] / exercise[key]).exists():
            problems.append(f"{key} not found: {exercise[key]}")
    target = exercise.get("open", "")
    if target and not target.startswith("/") and not (section["folder"] / target).exists():
        problems.append(f"open not found: {target}")
    return problems

def check(root: Path) -> bool:
    """Prints the whole menu tree. Returns True when every entry points at something real."""
    all_good = True
    for phase in find_phases(root):
        print(phase["title"])
        for section in phase["sections"]:
            print(f"  {section['title']}   [{section['folder'].relative_to(root).as_posix()}]")
            for exercise in section["exercises"]:
                problems = _problems_with(section, exercise)
                status = "ok" if not problems else "PROBLEM: " + "; ".join(problems)
                print(f"    - {exercise.get('title', '(no title)')}  ({exercise.get('type')})  {status}")
                all_good = all_good and not problems
    return all_good
