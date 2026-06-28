"""Tests for the PawPal logic layer."""

import os
import sys
from datetime import date, timedelta

# Make pawpal_system.py (one directory up) importable when running pytest.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, Task, Priority, Scheduler


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