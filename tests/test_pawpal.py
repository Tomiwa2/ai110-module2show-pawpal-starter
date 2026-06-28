"""Tests for the PawPal logic layer."""

import os
import sys

# Make pawpal_system.py (one directory up) importable when running pytest.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, Task, Priority


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