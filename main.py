"""Temporary testing ground for the PawPal logic layer.

Run with:  python main.py
"""

from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler, Priority


def main() -> None:
    # 1. Create an owner.
    owner = Owner("Ada")

    # Anchor every task to today so a completed daily task's next occurrence
    # lands cleanly on *tomorrow* and can't be mistaken for a same-day conflict.
    today = date.today()

    # 2. Create at least two pets and add them to the owner.
    rex = Pet("Rex", "dog")
    bella = Pet("Bella", "cat")
    owner.add_pet(rex)
    owner.add_pet(bella)

    # 3. Add tasks deliberately OUT OF ORDER (late times first, mixed pets) so
    #    we can prove the scheduler sorts them back into the day's real order.
    bella.add_task(Task("Brush coat", 15, Priority.MEDIUM, start_time="18:00", frequency="weekly", due_date=today))
    rex.add_task(Task("Vet visit", 60, Priority.LOW, start_time="14:00", frequency="monthly", due_date=today))
    rex.add_task(Task("Morning walk", 30, Priority.HIGH, start_time="08:00", frequency="daily", due_date=today))
    bella.add_task(Task("Feed", 10, Priority.MEDIUM, start_time="08:15", frequency="daily", due_date=today))
    # Two tasks at the EXACT same time on different pets -> the owner can't be in
    # two places at once, so this must be flagged as a conflict.
    rex.add_task(Task("Play fetch", 20, Priority.MEDIUM, start_time="14:00", frequency="daily", due_date=today))
    bella.add_task(Task("Litter change", 10, Priority.HIGH, start_time="14:00", frequency="daily", due_date=today))
    # An already-completed task, to show the completion filter working.
    done_task = Task("Refill water", 5, Priority.HIGH, start_time="07:30", frequency="daily", due_date=today)
    done_task.mark_complete()
    rex.add_task(done_task)

    # 4. Build today's routine from the owner's pets.
    scheduler = Scheduler.from_owner(owner)

    # Show the unsorted order first, to make the sort visible.
    print("--- Tasks as entered (out of order) ---")
    for task in scheduler.tasks_to_schedule:
        task.display_info()

    # 5. Sort and print "Today's Schedule" (pending tasks, in time order).
    plan = scheduler.generate_plan()
    print(f"\n=== Today's Schedule for {owner.name} ===")
    for task in plan:
        task.display_info()

    # 6. Demonstrate the filtering methods on the now-sorted task list.
    print("\n--- Filter: only Rex's tasks ---")
    for task in scheduler.filter_tasks(pet_name="Rex"):
        task.display_info()

    print("\n--- Filter: completed tasks ---")
    for task in scheduler.filter_tasks(completed=True):
        task.display_info()

    print("\n--- Filter: pending tasks ---")
    for task in scheduler.filter_tasks(completed=False):
        task.display_info()

    # 6b. Complete a recurring task and watch the next occurrence appear.
    walk = next(t for t in scheduler.tasks_to_schedule if t.name == "Morning walk")
    print(f"\n--- Completing '{walk.name}' (daily) ---")
    next_walk = walk.mark_complete()  # attaches the next occurrence to the pet
    print(f"Auto-created next occurrence due: {next_walk.due_date.isoformat()}")

    # The new occurrence lives on the pet, so rebuild the scheduler to pick it up.
    scheduler = Scheduler.from_owner(owner)
    scheduler.sort_tasks()
    print("Rex's tasks now (note the new pending walk for tomorrow):")
    for task in scheduler.filter_tasks(pet_name="Rex"):
        task.display_info()

    # 7. Flag any overlapping tasks (the owner can't be in two places at once).
    #    conflict_warnings() never raises -- it just returns printable strings.
    print("\n--- Conflict check ---")
    warnings = scheduler.conflict_warnings()
    if warnings:
        for message in warnings:
            print(message)
    else:
        print("No conflicts — the day flows cleanly.")

    # 8. Suggest the earliest free slot for a new task, working around the
    #    already-booked times for today.
    print("\n--- Next available slot ---")
    new_duration = 45
    slot = scheduler.find_next_available_slot(new_duration, on_date=today)
    if slot is not None:
        print(f"Earliest free {new_duration}-min slot today: {slot}")
    else:
        print(f"No free {new_duration}-min slot left in the day.")


if __name__ == "__main__":
    main()