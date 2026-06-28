"""Presentation helpers for the PawPal CLI.

This module is the *view* layer for `main.py`: it turns plain `Task` objects
into friendly terminal output — emojis per task type, color-coded priority and
status, and aligned tables — without putting any of that styling inside the
logic layer (`pawpal_system.py`).

Two third-party-free niceties plus one optional dependency:
- ANSI color codes (stdlib only) drive the color-coding, and degrade to plain
  text when output isn't a TTY or `NO_COLOR` is set.
- `tabulate` (optional) renders the schedule as a grid; if it isn't installed
  we fall back to a hand-aligned table so the CLI still runs.
"""

import os
import sys

from pawpal_system import Priority, Task

# tabulate is optional: the schedule table is nicer with it, but we keep a
# dependency-free fallback so `python main.py` never crashes on a fresh setup.
try:
    from tabulate import tabulate

    _HAS_TABULATE = True
except ImportError:  # pragma: no cover - exercised only without the dep
    _HAS_TABULATE = False


# --- ANSI color handling --------------------------------------------------

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_COLORS = {
    "red": "\033[31m",
    "yellow": "\033[33m",
    "green": "\033[32m",
    "cyan": "\033[36m",
    "grey": "\033[90m",
}


def _color_enabled() -> bool:
    """Only emit ANSI codes when it's safe: a real TTY and no NO_COLOR opt-out."""
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


# Windows 10+ terminals understand ANSI escapes once virtual-terminal
# processing is on; this no-op os.system call flips it on for legacy consoles.
# We also force UTF-8 so the emojis below don't choke the default cp1252 console.
if os.name == "nt":  # pragma: no cover - platform-specific
    os.system("")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

_USE_COLOR = _color_enabled()


def _paint(text: str, *styles: str) -> str:
    """Wrap text in the given ANSI styles (color names or _BOLD/_DIM), no-op if disabled."""
    if not _USE_COLOR or not styles:
        return text
    codes = "".join(_COLORS.get(style, style) for style in styles)
    return f"{codes}{text}{_RESET}"


# --- Task type emojis ------------------------------------------------------

# Keyword -> emoji, checked in order so more specific words win (e.g. "water"
# before a generic "feed"). The task's name is matched case-insensitively.
_TASK_EMOJIS = [
    (("walk", "stroll"), "🐕"),
    (("water", "refill", "hydra"), "💧"),
    (("feed", "food", "meal", "breakfast", "dinner"), "🍽️"),
    (("vet", "meds", "medicine", "pill", "shot", "vaccin"), "💊"),
    (("brush", "groom", "coat", "bath", "nail", "trim"), "🛁"),
    (("play", "fetch", "toy", "enrich", "train"), "🎾"),
    (("litter", "clean", "scoop", "cage"), "🧹"),
    (("sleep", "nap", "bed"), "😴"),
]
_DEFAULT_EMOJI = "📋"


def task_emoji(task: Task) -> str:
    """Pick an emoji for a task by scanning its name for known keywords."""
    name = task.name.casefold()
    for keywords, emoji in _TASK_EMOJIS:
        if any(word in name for word in keywords):
            return emoji
    return _DEFAULT_EMOJI


# --- Status + priority indicators -----------------------------------------

# Priority -> (emoji, ANSI color). HIGH screams in red, LOW relaxes in green.
_PRIORITY_STYLE = {
    Priority.HIGH: ("🔴", "red"),
    Priority.MEDIUM: ("🟡", "yellow"),
    Priority.LOW: ("🟢", "green"),
}


def status_icon(task: Task) -> str:
    """Green ✅ for done, dim ⏳ for still-pending."""
    if task.completed:
        return _paint("✅ done", "green")
    return _paint("⏳ todo", "grey")


def priority_label(priority: Priority) -> str:
    """Color-coded '<emoji> <name>' badge for a task's priority."""
    emoji, color = _PRIORITY_STYLE[priority]
    return _paint(f"{emoji} {priority.name.lower()}", color)


def format_task_line(task: Task) -> str:
    """One friendly, color-coded line for a single task (drop-in for display_info)."""
    when = task.start_time if task.start_time else "--:--"
    day = f" on {task.due_date.isoformat()}" if task.due_date else ""
    owner = f" for {task.pet.name}" if task.pet else ""
    name = _paint(f"{task_emoji(task)} {task.name}", _BOLD)
    meta = _paint(f"({task.duration} min){owner}{day}", "grey")
    return f"{status_icon(task)}  {_paint(when, 'cyan')}  {name} {meta}  {priority_label(task.priority)}"


# --- Tables ----------------------------------------------------------------

_TABLE_HEADERS = ["Status", "Time", "Task", "Pet", "Duration", "Priority"]


def _table_row(task: Task) -> list[str]:
    """Build the per-task cells used by both the tabulate and fallback tables."""
    when = task.start_time if task.start_time else "--:--"
    day = f"\n{task.due_date.isoformat()}" if task.due_date else ""
    return [
        status_icon(task),
        f"{_paint(when, 'cyan')}{_paint(day, 'grey')}",
        f"{task_emoji(task)} {task.name}",
        task.pet.name if task.pet else "-",
        f"{task.duration} min",
        priority_label(task.priority),
    ]


def tasks_table(tasks: list[Task]) -> str:
    """Render a list of tasks as a grid.

    Uses `tabulate` for a clean bordered grid when it's installed, and a
    hand-aligned fallback table otherwise so the CLI works with zero extra deps.
    """
    rows = [_table_row(task) for task in tasks]
    if not rows:
        return _paint("(no tasks)", "grey")
    if _HAS_TABULATE:
        return tabulate(rows, headers=_TABLE_HEADERS, tablefmt="rounded_grid")
    return _fallback_table(_TABLE_HEADERS, rows)


def _visible_len(cell: str) -> int:
    """Length of a cell ignoring ANSI codes and newlines, for fallback alignment."""
    first_line = cell.split("\n")[0]
    while "\033[" in first_line:
        start = first_line.index("\033[")
        end = first_line.index("m", start)
        first_line = first_line[:start] + first_line[end + 1 :]
    return len(first_line)


def _fallback_table(headers: list[str], rows: list[list[str]]) -> str:
    """Minimal aligned table used when `tabulate` isn't available."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], _visible_len(cell))

    def fmt(cells: list[str]) -> str:
        padded = []
        for i, cell in enumerate(cells):
            first_line = cell.split("\n")[0]
            pad = widths[i] - _visible_len(cell)
            padded.append(first_line + " " * pad)
        return " | ".join(padded)

    sep = "-+-".join("-" * w for w in widths)
    lines = [fmt(headers), sep] + [fmt(row) for row in rows]
    return "\n".join(lines)
