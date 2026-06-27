"""PawPal logic layer: backend classes for owners, pets, tasks, and scheduling.

Skeleton generated from diagrams/uml.mmd, with review fixes applied:
relationships between the data classes and the scheduler, a real priority
ordering, partial updates, and input validation.
"""

from dataclasses import dataclass, field
from enum import IntEnum


class Priority(IntEnum):
    """Task priority. Lower value = more important, so it sorts naturally."""

    HIGH = 0
    MEDIUM = 1
    LOW = 2


@dataclass
class Task:
    name: str
    duration: int  # minutes
    priority: Priority
    # Back-reference to the owning pet (fix #2). Excluded from repr/eq to avoid
    # infinite recursion (Pet -> tasks -> task -> pet -> ...).
    pet: "Pet | None" = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        # Validation (fix #6).
        if not self.name:
            raise ValueError("Task name must not be empty")
        if self.duration <= 0:
            raise ValueError("Task duration must be a positive number of minutes")

    def update_details(
        self,
        name: str | None = None,
        duration: int | None = None,
        priority: Priority | None = None,
    ) -> None:
        """Update only the fields that are provided (fix #5)."""
        if name is not None:
            self.name = name
        if duration is not None:
            self.duration = duration
        if priority is not None:
            self.priority = priority

    def display_info(self) -> None:
        """Print a human-readable summary of this task."""
        owner = f" (for {self.pet.name})" if self.pet else ""
        print(f"{self.name}{owner}: {self.duration} min, priority {self.priority.name.lower()}")


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet and set its back-reference (fix #2)."""
        task.pet = self
        if task not in self.tasks:  # avoid duplicates (fix #6)
            self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return this pet's list of tasks."""
        return self.tasks


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        if pet not in self.pets:  # avoid duplicates (fix #6)
            self.pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return this owner's list of pets."""
        return self.pets

    def get_all_tasks(self) -> list[Task]:
        """Flatten every task across all of this owner's pets (fix #1).

        This is the bridge that feeds the Scheduler.
        """
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    def __init__(
        self,
        tasks_to_schedule: list[Task] | None = None,
        available_time: int = 0,  # minutes
    ):
        if available_time < 0:
            raise ValueError("available_time must not be negative")  # validation (fix #6)
        self.tasks_to_schedule = tasks_to_schedule if tasks_to_schedule is not None else []
        self.available_time = available_time

    @classmethod
    def from_owner(cls, owner: Owner, available_time: int) -> "Scheduler":
        """Convenience constructor that pulls all of an owner's tasks (fix #1)."""
        return cls(owner.get_all_tasks(), available_time)

    def sort_tasks(self) -> list[Task]:
        """Sort by priority first, then shorter duration to break ties (fix #3).

        Shorter-first on ties is a greedy choice that lets more tasks fit.
        """
        self.tasks_to_schedule.sort(key=lambda t: (t.priority, t.duration))
        return self.tasks_to_schedule

    def generate_plan(self) -> list[Task]:
        """Build a plan that fits within available_time (fix #4).

        Algorithm: greedy. Walk tasks in sorted order and include each one whose
        duration still fits the remaining budget; skip the rest. Naturally
        handles available_time == 0 (empty plan) and tasks longer than the whole
        budget (always skipped). NOTE: greedy is simple but not guaranteed
        optimal for total time used — swap in a knapsack approach here if you
        need optimal packing.
        """
        plan: list[Task] = []
        remaining = self.available_time
        for task in self.sort_tasks():
            if task.duration <= remaining:
                plan.append(task)
                remaining -= task.duration
        return plan
