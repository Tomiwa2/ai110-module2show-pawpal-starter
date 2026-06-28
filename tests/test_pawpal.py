"""Tests for the PawPal logic layer."""

import os
import sys
from datetime import date, timedelta

# Make pawpal_system.py (one directory up) importable when running pytest.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Owner, Pet, Task, Priority, Scheduler


def test_mark_complete_changes_status():
    """Calling mark_complete() flips a task from incomplete to complete."""
    task = Task("Morning walk", 30, Priority.HIGH)
    assert task.completed is False  # starts incomplete

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet increases that pet's task count by one."""
    pet = Pet("Rex", "dog")
    assert len(pet.get_tasks()) == 0  # starts empty

    pet.add_task(Task("Feed", 10, Priority.MEDIUM))

    assert len(pet.get_tasks()) == 1


# --- Sorting correctness ---------------------------------------------------


def test_sort_tasks_returns_chronological_order():
    """sort_tasks() orders timed tasks by clock time, earliest first."""
    afternoon = Task("Vet visit", 60, Priority.LOW, start_time="14:00")
    morning = Task("Morning walk", 30, Priority.HIGH, start_time="08:00")
    midday = Task("Feed", 10, Priority.MEDIUM, start_time="09:30")
    scheduler = Scheduler([afternoon, morning, midday])  # deliberately out of order

    ordered = scheduler.sort_tasks()

    assert [t.start_time for t in ordered] == ["08:00", "09:30", "14:00"]


def test_sort_tasks_breaks_ties_by_priority():
    """Two tasks at the same time sort by priority (HIGH before LOW)."""
    low = Task("Play fetch", 20, Priority.LOW, start_time="14:00")
    high = Task("Litter change", 10, Priority.HIGH, start_time="14:00")
    scheduler = Scheduler([low, high])

    ordered = scheduler.sort_tasks()

    assert [t.name for t in ordered] == ["Litter change", "Play fetch"]


def test_sort_tasks_places_unscheduled_last():
    """Tasks with no start_time sort after every timed task."""
    timed = Task("Morning walk", 30, Priority.HIGH, start_time="08:00")
    unscheduled = Task("Buy food", 15, Priority.HIGH)  # no start_time
    scheduler = Scheduler([unscheduled, timed])

    ordered = scheduler.sort_tasks()

    assert ordered == [timed, unscheduled]


# --- Recurrence logic ------------------------------------------------------


def test_mark_complete_daily_creates_next_day_occurrence():
    """Completing a daily task spawns a pending copy dated one day later."""
    pet = Pet("Rex", "dog")
    today = date.today()
    task = Task("Morning walk", 30, Priority.HIGH, frequency="daily", due_date=today)
    pet.add_task(task)

    upcoming = task.mark_complete()

    assert upcoming is not None
    assert upcoming.due_date == today + timedelta(days=1)
    assert upcoming.completed is False  # next occurrence starts pending
    assert upcoming in pet.get_tasks()  # auto-attached to the same pet


def test_mark_complete_once_does_not_repeat():
    """A 'once' task never auto-creates a follow-up occurrence."""
    pet = Pet("Bella", "cat")
    task = Task("Vet visit", 60, Priority.LOW, frequency="once")
    pet.add_task(task)

    upcoming = task.mark_complete()

    assert upcoming is None
    assert len(pet.get_tasks()) == 1  # no extra task added


# --- Conflict detection ----------------------------------------------------


def test_detect_conflicts_flags_duplicate_times():
    """Two pending tasks at the exact same start time are flagged as a conflict."""
    a = Task("Litter change", 10, Priority.HIGH, start_time="14:00")
    b = Task("Play fetch", 20, Priority.MEDIUM, start_time="14:00")
    scheduler = Scheduler([a, b])

    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    pair = conflicts[0]
    assert a in pair and b in pair  # both tasks named in the conflicting pair


def test_detect_conflicts_ignores_touching_boundary():
    """Back-to-back tasks that only touch at the boundary do not conflict."""
    first = Task("Morning walk", 30, Priority.HIGH, start_time="08:00")  # 08:00-08:30
    second = Task("Feed", 15, Priority.MEDIUM, start_time="08:30")  # 08:30-08:45
    scheduler = Scheduler([first, second])

    assert scheduler.detect_conflicts() == []


def test_detect_conflicts_ignores_completed_tasks():
    """A completed task can't clash with a pending one."""
    done = Task("Walk", 30, Priority.HIGH, start_time="14:00", completed=True)
    pending = Task("Play", 20, Priority.LOW, start_time="14:00")
    scheduler = Scheduler([done, pending])

    assert scheduler.detect_conflicts() == []


# --- Next available slot ---------------------------------------------------


def test_next_available_slot_empty_day_returns_day_start():
    """With nothing booked, the first free slot is the start of the day."""
    scheduler = Scheduler([])

    assert scheduler.find_next_available_slot(30, day_start="08:00") == "08:00"


def test_next_available_slot_finds_gap_between_tasks():
    """A task fits in the gap between two booked tasks when it's big enough."""
    morning = Task("Walk", 30, Priority.HIGH, start_time="08:00")  # 08:00-08:30
    later = Task("Vet", 30, Priority.LOW, start_time="10:00")  # 10:00-10:30
    scheduler = Scheduler([morning, later])

    # 08:30-10:00 is a 90-min gap; a 60-min task slots in at 08:30.
    assert scheduler.find_next_available_slot(60, day_start="08:00") == "08:30"


def test_next_available_slot_skips_gap_that_is_too_small():
    """A gap smaller than the duration is skipped for the next viable one."""
    first = Task("Walk", 30, Priority.HIGH, start_time="08:00")  # 08:00-08:30
    second = Task("Feed", 30, Priority.MEDIUM, start_time="09:00")  # 09:00-09:30
    scheduler = Scheduler([first, second])

    # The 08:30-09:00 gap is only 30 min, too small for a 45-min task, so the
    # next free slot is after the second task ends, at 09:30.
    assert scheduler.find_next_available_slot(45, day_start="08:00") == "09:30"


def test_next_available_slot_returns_none_when_day_is_full():
    """When nothing fits before day_end, the search returns None."""
    task = Task("All day", 60, Priority.HIGH, start_time="08:00")  # 08:00-09:00
    scheduler = Scheduler([task])

    # Only 08:00-09:00 window, fully booked -> no room for a 30-min task.
    assert scheduler.find_next_available_slot(30, day_start="08:00", day_end="09:00") is None


def test_next_available_slot_ignores_completed_and_unscheduled():
    """Completed tasks free their slot and unscheduled tasks block nothing."""
    done = Task("Walk", 60, Priority.HIGH, start_time="08:00", completed=True)
    floating = Task("Buy food", 30, Priority.LOW)  # no start_time
    scheduler = Scheduler([done, floating])

    # The completed task doesn't block, so the day is wide open at 08:00.
    assert scheduler.find_next_available_slot(60, day_start="08:00") == "08:00"


def test_next_available_slot_is_date_aware():
    """A task dated for another day doesn't block the requested date."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    booked_tomorrow = Task(
        "Vet", 120, Priority.HIGH, start_time="08:00", due_date=tomorrow
    )
    scheduler = Scheduler([booked_tomorrow])

    # Searching today, tomorrow's booking is irrelevant -> 08:00 is free.
    assert scheduler.find_next_available_slot(60, day_start="08:00", on_date=today) == "08:00"


# --- Persistence (save/load JSON) ------------------------------------------


def _sample_owner() -> Owner:
    """An owner with two pets, varied priorities, dates, and a completed task."""
    owner = Owner("Ada")
    rex = Pet("Rex", "dog")
    bella = Pet("Bella", "cat")
    owner.add_pet(rex)
    owner.add_pet(bella)
    rex.add_task(
        Task("Morning walk", 30, Priority.HIGH, start_time="08:00",
             frequency="daily", due_date=date(2026, 6, 28))
    )
    done = Task("Refill water", 5, Priority.LOW, completed=True)  # undated, unscheduled
    bella.add_task(done)
    return owner


def test_save_and_load_round_trip_preserves_data(tmp_path):
    """Saving then loading reproduces the owner's pets and tasks exactly."""
    path = str(tmp_path / "data.json")
    _sample_owner().save_to_json(path)

    loaded = Owner.load_from_json(path)

    assert loaded is not None
    assert loaded.name == "Ada"
    assert [p.name for p in loaded.get_pets()] == ["Rex", "Bella"]

    walk = loaded.get_pets()[0].get_tasks()[0]
    assert walk.priority is Priority.HIGH        # IntEnum survives the round trip
    assert walk.due_date == date(2026, 6, 28)    # date survives as well
    assert walk.start_time == "08:00"
    assert walk.completed is False


def test_load_restores_pet_back_reference(tmp_path):
    """The Task.pet link (never serialized) is rebuilt on load."""
    path = str(tmp_path / "data.json")
    _sample_owner().save_to_json(path)

    loaded = Owner.load_from_json(path)

    rex = loaded.get_pets()[0]
    walk = rex.get_tasks()[0]
    assert walk.pet is rex  # back-reference restored via Pet.add_task()


def test_load_from_missing_file_returns_none(tmp_path):
    """Loading before anything has been saved returns None (clean first run)."""
    missing = str(tmp_path / "does_not_exist.json")

    assert Owner.load_from_json(missing) is None