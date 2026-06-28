"""PawPal logic layer: backend classes for owners, pets, tasks, and scheduling.

Design:
- Task, Pet, Owner are data objects (dataclasses) that hold state.
- Scheduler is the "brain" for the pet's day: it sorts tasks into a daily
  routine, detects time conflicts, and works with recurring tasks. It never
  reaches into a Pet's internals -- it asks the Owner for a flat task list.
"""

from dataclasses import dataclass, field
from enum import IntEnum


class Priority(IntEnum):
    """Task priority. Lower value = more important, so it sorts naturally."""

    HIGH = 0
    MEDIUM = 1
    LOW = 2


def _to_minutes(hhmm: str) -> int:
    """Convert a 'HH:MM' clock string into minutes since midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


@dataclass
class Task:
    """A single pet-care activity in the daily routine."""

    name: str  # the description, e.g. "Morning walk"
    duration: int  # how long it takes, in minutes
    priority: Priority
    start_time: str | None = None  # "HH:MM" when the task begins (None = unscheduled)
    frequency: str = "daily"  # e.g. "daily", "weekly", "once"
    completed: bool = False  # completion status
    # Back-reference to the owning pet. Excluded from repr/eq to avoid infinite
    # recursion (Pet -> tasks -> task -> pet -> ...).
    pet: "Pet | None" = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate the task's name and duration after initialization."""
        if not self.name:
            raise ValueError("Task name must not be empty")
        if self.duration <= 0:
            raise ValueError("Task duration must be a positive number of minutes")

    @property
    def start_minutes(self) -> int | None:
        """Start time as minutes since midnight, or None if unscheduled."""
        return _to_minutes(self.start_time) if self.start_time else None

    @property
    def end_minutes(self) -> int | None:
        """End time as minutes since midnight, or None if unscheduled."""
        start = self.start_minutes
        return start + self.duration if start is not None else None

    def overlaps(self, other: "Task") -> bool:
        """True if this task's time range collides with another's."""
        if self.start_minutes is None or other.start_minutes is None:
            return False  # an unscheduled task can't conflict
        return self.start_minutes < other.end_minutes and other.start_minutes < self.end_minutes

    def update_details(
        self,
        name: str | None = None,
        duration: int | None = None,
        priority: Priority | None = None,
        start_time: str | None = None,
        frequency: str | None = None,
    ) -> None:
        """Update only the fields that are provided; leave the rest untouched."""
        if name is not None:
            self.name = name
        if duration is not None:
            if duration <= 0:
                raise ValueError("Task duration must be a positive number of minutes")
            self.duration = duration
        if priority is not None:
            self.priority = priority
        if start_time is not None:
            self.start_time = start_time
        if frequency is not None:
            self.frequency = frequency

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Reset to not-done (e.g. for a recurring task's next cycle)."""
        self.completed = False

    def display_info(self) -> None:
        """Print a human-readable summary of this task."""
        when = self.start_time if self.start_time else "--:--"
        status = "x" if self.completed else " "
        owner = f" (for {self.pet.name})" if self.pet else ""
        print(
            f"[{status}] {when} {self.name}{owner} "
            f"({self.duration} min) [priority: {self.priority.name.lower()}]"
        )


@dataclass
class Pet:
    """A single pet and the care tasks attached to it."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet and set its back-reference."""
        task.pet = self
        if task not in self.tasks:  # avoid duplicates
            self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return this pet's list of tasks."""
        return self.tasks


@dataclass
class Owner:
    """An owner who manages multiple pets and exposes all of their tasks."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        if pet not in self.pets:  # avoid duplicates
            self.pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return this owner's list of pets."""
        return self.pets

    def get_all_tasks(self) -> list[Task]:
        """Flatten every task across all of this owner's pets.

        This is the single bridge the Scheduler uses to get data, so the
        Scheduler never has to know how pets store their tasks.
        """
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """The 'brain': sorts the day, detects conflicts, manages recurring tasks."""

    def __init__(self, tasks_to_schedule: list[Task] | None = None):
        """Create a scheduler over an optional starting list of tasks."""
        self.tasks_to_schedule = tasks_to_schedule if tasks_to_schedule is not None else []

    @classmethod
    def from_owner(cls, owner: Owner) -> "Scheduler":
        """Build a Scheduler straight from an Owner's tasks.

        The Owner gathers its own data; the Scheduler just receives the list.
        """
        return cls(owner.get_all_tasks())

    def sort_tasks(self) -> list[Task]:
        """Order the day by start time, then priority for tasks without a time.

        Unscheduled tasks (no start_time) sort after timed ones.
        """
        self.tasks_to_schedule.sort(
            key=lambda t: (t.start_minutes is None, t.start_minutes or 0, t.priority)
        )
        return self.tasks_to_schedule

    def detect_conflicts(self) -> list[tuple[Task, Task]]:
        """Find every pair of tasks whose scheduled times overlap.

        The owner can only do one thing at a time, so overlaps across *any*
        pets count as a conflict.
        """
        timed = [t for t in self.tasks_to_schedule if t.start_minutes is not None]
        timed.sort(key=lambda t: t.start_minutes)
        conflicts: list[tuple[Task, Task]] = []
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                if timed[i].overlaps(timed[j]):
                    conflicts.append((timed[i], timed[j]))
        return conflicts

    def generate_plan(self) -> list[Task]:
        """Return today's routine: pending tasks, sorted into the day's order."""
        self.sort_tasks()
        return [task for task in self.tasks_to_schedule if not task.completed]
