"""PawPal logic layer: backend classes for owners, pets, tasks, and scheduling.

Design:
- Task, Pet, Owner are data objects (dataclasses) that hold state.
- Scheduler is the "brain" for the pet's day: it sorts tasks into a daily
  routine, detects time conflicts, and works with recurring tasks. It never
  reaches into a Pet's internals -- it asks the Owner for a flat task list.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import IntEnum

# How far ahead the next occurrence of a recurring task lands. Only fixed-length
# cycles live here: timedelta has no "months" unit because calendar months vary,
# so "monthly"/"once" tasks are intentionally absent and never auto-repeat.
_FREQUENCY_DELTAS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
}


class Priority(IntEnum):
    """Task priority. Lower value = more important, so it sorts naturally."""

    HIGH = 0
    MEDIUM = 1
    LOW = 2


def _to_minutes(hhmm: str) -> int:
    """Convert a 'HH:MM' clock string into minutes since midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _same_day(a: "Task", b: "Task") -> bool:
    """True if two tasks could land on the same day.

    Both dated -> only when the dates match. If either is undated, it floats to
    "any day" and so is allowed to clash with the other.
    """
    if a.due_date is None or b.due_date is None:
        return True
    return a.due_date == b.due_date


@dataclass
class Task:
    """A single pet-care activity in the daily routine."""

    name: str  # the description, e.g. "Morning walk"
    duration: int  # how long it takes, in minutes
    priority: Priority
    start_time: str | None = None  # "HH:MM" when the task begins (None = unscheduled)
    frequency: str = "daily"  # e.g. "daily", "weekly", "once"
    due_date: date | None = None  # which day this occurrence is for (None = undated)
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

    def next_occurrence(self) -> "Task | None":
        """Build the next-cycle copy of this task, or None if it doesn't repeat.

        Only "daily"/"weekly" tasks recur (see _FREQUENCY_DELTAS). The new task's
        due_date is this occurrence's date plus one cycle; if this task is undated,
        we anchor off today. The copy starts pending and unattached to a pet.
        """
        delta = _FREQUENCY_DELTAS.get(self.frequency)
        if delta is None:
            return None  # "once"/"monthly"/unknown -> no automatic repeat
        base = self.due_date or date.today()
        return Task(
            name=self.name,
            duration=self.duration,
            priority=self.priority,
            start_time=self.start_time,
            frequency=self.frequency,
            due_date=base + delta,
        )

    def mark_complete(self) -> "Task | None":
        """Mark this task done; if it recurs, spawn and attach the next occurrence.

        Returns the newly created next-occurrence Task (already added to the same
        pet), or None for non-recurring tasks.
        """
        self.completed = True
        upcoming = self.next_occurrence()
        if upcoming is not None and self.pet is not None:
            self.pet.add_task(upcoming)
        return upcoming

    def mark_incomplete(self) -> None:
        """Reset to not-done (e.g. for a recurring task's next cycle)."""
        self.completed = False

    def display_info(self) -> None:
        """Print a human-readable summary of this task."""
        when = self.start_time if self.start_time else "--:--"
        status = "x" if self.completed else " "
        owner = f" (for {self.pet.name})" if self.pet else ""
        day = f" on {self.due_date.isoformat()}" if self.due_date else ""
        print(
            f"[{status}] {when}{day} {self.name}{owner} "
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
        """Find every pair of pending tasks whose scheduled times overlap.

        The owner can only do one thing at a time, so overlaps across *any*
        pets count as a conflict. Two tasks only conflict if they fall on the
        same day -- a task dated for tomorrow can't clash with one for today.
        An undated task is treated as "any day" and can clash with either.
        Completed tasks are ignored: they're already done, so they can't clash.
        """
        timed = [
            t
            for t in self.tasks_to_schedule
            if t.start_minutes is not None and not t.completed
        ]
        timed.sort(key=lambda t: t.start_minutes)
        conflicts: list[tuple[Task, Task]] = []
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                # Sorted by start time: once j starts at/after i ends, no later
                # task can overlap i either, so stop scanning this row.
                if timed[j].start_minutes >= timed[i].end_minutes:
                    break
                if _same_day(timed[i], timed[j]) and timed[i].overlaps(timed[j]):
                    conflicts.append((timed[i], timed[j]))
        return conflicts

    def filter_tasks(
        self,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return tasks matching the given filters, in the current order.

        Both filters are optional and combine with AND:
        - completed: keep only done (True) or pending (False) tasks; None = either.
        - pet_name: keep only tasks belonging to this pet (case-insensitive);
          None = any pet.

        With no arguments this returns every task.
        """
        target_pet = pet_name.casefold() if pet_name is not None else None
        return [
            task
            for task in self.tasks_to_schedule
            if (completed is None or task.completed == completed)
            and (
                target_pet is None
                or (task.pet is not None and task.pet.name.casefold() == target_pet)
            )
        ]

    def conflict_warnings(self) -> list[str]:
        """Return a human-readable warning for each scheduling conflict.

        A "lightweight" wrapper over detect_conflicts: it never raises, it just
        builds a friendly message per overlapping pair so the caller can print
        them. An empty list means the day is clear.
        """
        warnings: list[str] = []
        for a, b in self.detect_conflicts():
            same_pet = a.pet is not None and a.pet is b.pet
            who = (
                f"{a.pet.name}'s schedule"
                if same_pet
                else f"{a.pet.name if a.pet else '?'} and {b.pet.name if b.pet else '?'}"
            )
            warnings.append(
                f"WARNING - conflict for {who}: '{a.name}' ({a.start_time}) "
                f"overlaps '{b.name}' ({b.start_time})."
            )
        return warnings

    def generate_plan(self) -> list[Task]:
        """Return today's routine: pending tasks, sorted into the day's order."""
        self.sort_tasks()
        return [task for task in self.tasks_to_schedule if not task.completed]
