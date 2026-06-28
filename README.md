# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## ✨ Features

PawPal+ turns a flat list of pet-care tasks into a conflict-checked daily plan.
The scheduling algorithms all live in `pawpal_system.py`:

- **Sorting by time** — `Scheduler.sort_tasks()` orders the day by start time
  (computed as minutes since midnight, so `"9:30"` and `"09:30"` sort correctly),
  using task **priority** (HIGH → MEDIUM → LOW) only to break ties. Unscheduled
  tasks (no start time) always sort last.
- **Daily plan generation** — `Scheduler.generate_plan()` returns today's routine:
  the sorted task list with completed tasks dropped.
- **Conflict warnings** — `Scheduler.detect_conflicts()` finds every pair of
  pending, timed tasks whose ranges overlap — even across different pets, since
  the owner can't be in two places at once. It is **date-aware** (a task dated for
  tomorrow can't clash with one for today) and uses a sweep-line early-exit for
  efficiency. `conflict_warnings()` turns each conflict into a readable message.
- **Daily / weekly recurrence** — completing a recurring task with
  `Task.mark_complete()` auto-creates its next occurrence (`+1 day` for daily,
  `+1 week` for weekly) and attaches it to the same pet. `"once"`/`"monthly"`
  tasks don't auto-repeat.
- **Filtering** — `Scheduler.filter_tasks()` filters by completion status and/or
  pet name (case-insensitive); the two filters combine with AND.
- **Input validation** — tasks reject empty names and non-positive durations at
  construction time.

See [System Design (UML)](#-system-design-uml) for how these classes fit together
and [Smarter Scheduling](#-smarter-scheduling) for per-method detail.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

See the [Demo Walkthrough](#-demo-walkthrough) below for full, up-to-date sample
output from `python main.py` (the sorted plan, filters, recurrence, and conflict
check).

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

### What the tests cover

The suite (`tests/test_pawpal.py`) exercises the core scheduling logic:

- **Data objects** — adding a task to a pet increases its task count; `mark_complete()` flips a task's status.
- **Sorting correctness** — timed tasks come back in chronological order, ties are broken by priority (HIGH first), and unscheduled tasks sort last.
- **Recurrence logic** — completing a `daily` task spawns a pending copy dated one day later and auto-attaches it to the same pet, while a `once` task never repeats.
- **Conflict detection** — two pending tasks at the exact same time are flagged, back-to-back tasks that only touch at the boundary are not, and completed tasks are ignored.

### Sample test output

```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Ire\Desktop\Codepath AI 110\ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 10 items

tests\test_pawpal.py ..........                                          [100%]

============================= 10 passed in 0.09s ==============================
```

### Confidence Level

⭐⭐⭐⭐☆ (4/5)

All 10 tests pass, covering the three highest-risk areas — sorting, recurrence, and conflict detection — including their key edge cases (same-time conflicts, touching boundaries, `once` tasks). The fourth star reflects solid coverage of the critical paths; the fifth is held back because some behaviors are not yet tested: `filter_tasks()`, date-aware conflicts (today vs. tomorrow), cross-pet conflict warnings, undated recurring tasks, and input validation (empty names, non-positive durations).

## 📐 System Design (UML)

The class diagram below reflects the final implementation in `pawpal_system.py`.
Source: [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd).

![PawPal+ UML class diagram](diagrams/uml_final.png)

The PNG is generated from the Mermaid source. After editing `uml_final.mmd`,
re-export it with the [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli)
(requires Node.js):

```bash
npx @mermaid-js/mermaid-cli -i diagrams/uml_final.mmd -o diagrams/uml_final.png -b white
```

## 📐 Smarter Scheduling

All scheduling logic lives in `pawpal_system.py`. Below is each feature we
implemented and the method that powers it.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks()` | Orders the day by start time, with `Priority` as a tie-breaker; unscheduled tasks sort last. |
| Filtering | `Scheduler.filter_tasks()` | Filters by completion status and/or pet name (case-insensitive); the two filters combine with AND. |
| Conflict detection | `Scheduler.detect_conflicts()`, `Scheduler.conflict_warnings()`, `Task.overlaps()`, `_same_day()` | Finds overlapping timed tasks across any pets and returns either pairs or printable warnings. |
| Recurring tasks | `Task.mark_complete()`, `Task.next_occurrence()` | Completing a daily/weekly task auto-creates its next occurrence on the next date. |

### Sorting behavior — `Scheduler.sort_tasks()`

Sorts the task list in place using a tuple key `(start_minutes is None,
start_minutes or 0, priority)`. This puts **timed tasks before unscheduled
ones**, orders timed tasks by clock time, and uses `Priority` (HIGH=0 first)
only to break ties. Sorting on minutes-since-midnight (via the `start_minutes`
property) rather than the raw `"HH:MM"` string keeps it correct even for
non-zero-padded times. `Scheduler.generate_plan()` calls this and then drops
completed tasks to produce today's routine.

### Filtering behavior — `Scheduler.filter_tasks()`

Returns the tasks matching optional filters:

- `completed` — `True` for done tasks, `False` for pending, `None` to ignore.
- `pet_name` — keep only one pet's tasks (case-insensitive, `None` for any pet).

Both are optional and combine with AND, so `filter_tasks()` returns everything,
`filter_tasks(pet_name="Rex")` returns just Rex's tasks, and
`filter_tasks(completed=False, pet_name="Bella")` returns Bella's pending tasks.

### Conflict detection — `Scheduler.detect_conflicts()` / `conflict_warnings()`

Because the owner can't be in two places at once, any two **pending, timed**
tasks whose ranges overlap — even across different pets — count as a conflict.
`Task.overlaps()` does the time-range math, and the `_same_day()` helper makes
detection date-aware so tomorrow's recurring task can't clash with today's.
`detect_conflicts()` returns the raw `(Task, Task)` pairs (sorted by start time,
with a sweep-line early exit), while `conflict_warnings()` is a lightweight
wrapper that turns each pair into a printable warning string and never raises.

### Recurring task logic — `Task.mark_complete()` / `next_occurrence()`

Tasks carry a `frequency` (`"daily"`, `"weekly"`, etc.) and an optional
`due_date`. When a recurring task is completed, `mark_complete()` calls
`next_occurrence()`, which uses `datetime.timedelta` to compute the next date
(`+1 day` for daily, `+1 week` for weekly) and returns a fresh, pending copy
that is automatically attached to the same pet. `"once"`/`"monthly"` tasks don't
auto-repeat (`timedelta` has no calendar-month unit).

## 📸 Demo Walkthrough

PawPal+ has two front ends over the same scheduling engine: a **Streamlit UI**
(`app.py`) for interactive use and a **CLI script** (`main.py`) that exercises
every feature end to end.

### Main UI features (Streamlit)

Run `streamlit run app.py`. The app lets a user:

- **Add an owner and pets** — enter the owner's name, then add pets by name and
  species (`Owner.add_pet` / `Pet`).
- **Add tasks to a pet** — give each task a title, duration, priority, start time,
  and the pet it belongs to (`Pet.add_task`).
- **Browse and filter tasks** — the task table is sorted into the day's order, with
  dropdowns to filter by pet and by status (All / Pending / Done) via
  `Scheduler.filter_tasks()`.
- **Complete tasks** — mark a task done; if it's daily/weekly, the next occurrence
  is created automatically and the app reports its date (`Task.mark_complete()`).
- **Generate the daily schedule** — produce a sorted plan and a conflict report.

### Example workflow

1. Enter the owner's name (e.g. *Ada*).
2. **Add a pet** → *Rex (dog)*; add a second → *Bella (cat)*.
3. **Schedule tasks** → e.g. *Morning walk* for Rex at 08:00 (high priority,
   daily), *Feed* for Bella at 08:15, and a couple of 14:00 tasks.
4. Click **Generate schedule** → PawPal+ shows **Today's Schedule** sorted by time.
5. Read the **conflict report** — overlapping tasks are flagged with a suggestion.
6. Back in the task list, **mark *Morning walk* complete** → its next-day
   occurrence appears automatically.

### Key Scheduler behaviors shown

- **Sorting by time** — tasks entered out of order come back in chronological
  order, with priority breaking ties at the same time.
- **Completion filtering** — a pre-completed task is hidden from "Today's Schedule"
  but still visible under the "Done" filter.
- **Conflict warnings** — same-time tasks across different pets are flagged (the
  owner can't be in two places at once).
- **Daily recurrence** — completing the daily walk auto-creates tomorrow's copy.

### Sample CLI output (`python main.py`)

The CLI runs the full scenario above and prints each stage:

```
--- Tasks as entered (out of order) ---
[ ] 14:00 on 2026-06-28 Vet visit (for Rex) (60 min) [priority: low]
[ ] 08:00 on 2026-06-28 Morning walk (for Rex) (30 min) [priority: high]
[ ] 14:00 on 2026-06-28 Play fetch (for Rex) (20 min) [priority: medium]
[x] 07:30 on 2026-06-28 Refill water (for Rex) (5 min) [priority: high]
[ ] 18:00 on 2026-06-28 Brush coat (for Bella) (15 min) [priority: medium]
[ ] 08:15 on 2026-06-28 Feed (for Bella) (10 min) [priority: medium]
[ ] 14:00 on 2026-06-28 Litter change (for Bella) (10 min) [priority: high]

=== Today's Schedule for Ada ===
[ ] 08:00 on 2026-06-28 Morning walk (for Rex) (30 min) [priority: high]
[ ] 08:15 on 2026-06-28 Feed (for Bella) (10 min) [priority: medium]
[ ] 14:00 on 2026-06-28 Litter change (for Bella) (10 min) [priority: high]
[ ] 14:00 on 2026-06-28 Play fetch (for Rex) (20 min) [priority: medium]
[ ] 14:00 on 2026-06-28 Vet visit (for Rex) (60 min) [priority: low]
[ ] 18:00 on 2026-06-28 Brush coat (for Bella) (15 min) [priority: medium]

--- Filter: only Rex's tasks ---
[x] 07:30 on 2026-06-28 Refill water (for Rex) (5 min) [priority: high]
[ ] 08:00 on 2026-06-28 Morning walk (for Rex) (30 min) [priority: high]
[ ] 14:00 on 2026-06-28 Play fetch (for Rex) (20 min) [priority: medium]
[ ] 14:00 on 2026-06-28 Vet visit (for Rex) (60 min) [priority: low]

--- Filter: completed tasks ---
[x] 07:30 on 2026-06-28 Refill water (for Rex) (5 min) [priority: high]

--- Filter: pending tasks ---
[ ] 08:00 on 2026-06-28 Morning walk (for Rex) (30 min) [priority: high]
[ ] 08:15 on 2026-06-28 Feed (for Bella) (10 min) [priority: medium]
[ ] 14:00 on 2026-06-28 Litter change (for Bella) (10 min) [priority: high]
[ ] 14:00 on 2026-06-28 Play fetch (for Rex) (20 min) [priority: medium]
[ ] 14:00 on 2026-06-28 Vet visit (for Rex) (60 min) [priority: low]
[ ] 18:00 on 2026-06-28 Brush coat (for Bella) (15 min) [priority: medium]

--- Completing 'Morning walk' (daily) ---
Auto-created next occurrence due: 2026-06-29
Rex's tasks now (note the new pending walk for tomorrow):
[x] 07:30 on 2026-06-28 Refill water (for Rex) (5 min) [priority: high]
[x] 08:00 on 2026-06-28 Morning walk (for Rex) (30 min) [priority: high]
[ ] 08:00 on 2026-06-29 Morning walk (for Rex) (30 min) [priority: high]
[ ] 14:00 on 2026-06-28 Play fetch (for Rex) (20 min) [priority: medium]
[ ] 14:00 on 2026-06-28 Vet visit (for Rex) (60 min) [priority: low]

--- Conflict check ---
WARNING - conflict for Bella and Rex: 'Litter change' (14:00) overlaps 'Play fetch' (14:00).
WARNING - conflict for Bella and Rex: 'Litter change' (14:00) overlaps 'Vet visit' (14:00).
WARNING - conflict for Rex's schedule: 'Play fetch' (14:00) overlaps 'Vet visit' (14:00).
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
