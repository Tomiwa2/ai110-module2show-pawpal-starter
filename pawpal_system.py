"""PawPal logic layer: backend classes for owners, pets, tasks, and scheduling.

Skeleton generated from diagrams/uml.mmd. Method bodies are stubs to be
implemented.
"""

from dataclasses import dataclass, field


@dataclass
class Task:
    name: str
    duration: int  # minutes
    priority: str

    def update_details(self, name: str, duration: int, priority: str) -> None:
        """Update this task's name, duration, and/or priority."""
        ...

    def display_info(self) -> None:
        """Print a human-readable summary of this task."""
        ...


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        ...

    def get_tasks(self) -> list[Task]:
        """Return this pet's list of tasks."""
        ...


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        ...

    def get_pets(self) -> list[Pet]:
        """Return this owner's list of pets."""
        ...


class Scheduler:
    def __init__(
        self,
        tasks_to_schedule: list[Task] | None = None,
        available_time: int = 0,  # minutes
    ):
        self.tasks_to_schedule = tasks_to_schedule if tasks_to_schedule is not None else []
        self.available_time = available_time

    def sort_tasks(self) -> list[Task]:
        """Order tasks_to_schedule (e.g. by priority/duration) and return them."""
        ...

    def generate_plan(self) -> list[Task]:
        """Build a plan of tasks that fits within available_time and return it."""
        ...
