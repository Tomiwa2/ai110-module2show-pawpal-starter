# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

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

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

```
=== Today's Schedule for Ada ===
[ ] 08:00 Morning walk (for Rex) (30 min) [priority: high]
[ ] 08:15 Feed (for Bella) (10 min) [priority: medium]
[ ] 14:00 Litter change (for Bella) (10 min) [priority: high]
[ ] 14:00 Play fetch (for Rex) (20 min) [priority: medium]
[ ] 14:00 Vet visit (for Rex) (60 min) [priority: low]
[ ] 18:00 Brush coat (for Bella) (15 min) [priority: medium]

--- Conflict check ---
WARNING - conflict for Rex and Bella: 'Morning walk' (08:00) overlaps 'Feed' (08:15).
WARNING - conflict for Bella and Rex: 'Litter change' (14:00) overlaps 'Play fetch' (14:00).
WARNING - conflict for Bella and Rex: 'Litter change' (14:00) overlaps 'Vet visit' (14:00).
WARNING - conflict for Rex's schedule: 'Play fetch' (14:00) overlaps 'Vet visit' (14:00).
```

### Previous output (old format)

```
=== Today's Schedule for Ada ===
[ ] 08:00 Morning walk (for Rex) (30 min) [priority: high]
[ ] 08:15 Feed (for Bella) (10 min) [priority: medium]
[ ] 14:00 Vet visit (for Rex) (60 min) [priority: low]
[ ] 18:00 Brush coat (for Bella) (15 min) [priority: medium]

!! Conflicts detected:
   'Morning walk' (08:00) overlaps 'Feed' (08:15)
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
