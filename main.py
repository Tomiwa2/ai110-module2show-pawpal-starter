"""Temporary testing ground for the PawPal logic layer.

Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler, Priority


def main() -> None:
    # 1. Create an owner.
    owner = Owner("Ada")

    # 2. Create at least two pets and add them to the owner.
    rex = Pet("Rex", "dog")
    bella = Pet("Bella", "cat")
    owner.add_pet(rex)
    owner.add_pet(bella)

    # 3. Add tasks with start times, durations, and priorities.
    rex.add_task(Task("Morning walk", 30, Priority.HIGH, start_time="08:00", frequency="daily"))
    rex.add_task(Task("Vet visit", 60, Priority.LOW, start_time="14:00", frequency="monthly"))
    bella.add_task(Task("Feed", 10, Priority.MEDIUM, start_time="08:15", frequency="daily"))
    bella.add_task(Task("Brush coat", 15, Priority.MEDIUM, start_time="18:00", frequency="weekly"))

    # 4. Build today's routine from the owner's pets.
    scheduler = Scheduler.from_owner(owner)
    plan = scheduler.generate_plan()

    # 5. Print "Today's Schedule".
    print(f"=== Today's Schedule for {owner.name} ===")
    for task in plan:
        task.display_info()

    # 6. Flag any overlapping tasks (the owner can't be in two places at once).
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        print("\n!! Conflicts detected:")
        for a, b in conflicts:
            print(f"   '{a.name}' ({a.start_time}) overlaps '{b.name}' ({b.start_time})")
    else:
        print("\nNo conflicts — the day flows cleanly.")


if __name__ == "__main__":
    main()