from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to **PawPal+**, a pet care planning assistant. Add an owner and their
pets, give each pet some care tasks, then generate a conflict-checked daily plan.
"""
)

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** helps a pet owner plan care tasks for their pet(s) based on
constraints like time, priority, and preferences. The scheduling logic lives in
`pawpal_system.py`; this Streamlit app is the UI on top of it.
"""
    )

# Map the friendly UI labels to our Priority enum.
PRIORITY_MAP = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}

st.divider()
st.subheader("Owner & Pets")

owner_name = st.text_input("Owner name", value="Jordan")

# Persist the Owner across re-runs. Streamlit re-runs this whole script on every
# interaction, so we only build the Owner if one isn't already in the session
# "vault" -- otherwise we'd wipe its pets/tasks on every click. On the very first
# run we try to load a previous session from data.json (Owner.load_from_json),
# falling back to a fresh Owner when no save file exists yet.
if "owner" not in st.session_state:
    st.session_state.owner = Owner.load_from_json() or Owner(owner_name)


def save_owner() -> None:
    """Write the current owner (pets + tasks) to data.json so it survives a restart."""
    st.session_state.owner.save_to_json()


# Keep the persisted owner's name in sync with the input box, then save so a
# renamed owner isn't lost on the next restart.
if st.session_state.owner.name != owner_name:
    st.session_state.owner.name = owner_name
    save_owner()

# --- Add a Pet -> Owner.add_pet() -------------------------------------------
st.markdown("### Add a Pet")
col_a, col_b = st.columns(2)
with col_a:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_b:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    if pet_name.strip():
        st.session_state.owner.add_pet(Pet(pet_name, species))
        save_owner()
        st.success(f"Added {pet_name} the {species}.")
    else:
        st.warning("Please enter a pet name.")

pets = st.session_state.owner.get_pets()
if pets:
    st.write("**Current pets:** " + ", ".join(f"{p.name} ({p.species})" for p in pets))
else:
    st.info("No pets yet. Add one above.")

# --- Add a Task -> Pet.add_task() -------------------------------------------
st.divider()
st.subheader("Add a Task")

if not pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col4, col5 = st.columns(2)
    with col4:
        which_pet = st.selectbox("For which pet?", [p.name for p in pets])
    with col5:
        start = st.time_input("Start time", value=time(8, 0))

    if st.button("Add task"):
        pet = next(p for p in pets if p.name == which_pet)
        pet.add_task(
            Task(
                name=task_title,
                duration=int(duration),
                priority=PRIORITY_MAP[priority],
                start_time=start.strftime("%H:%M"),
            )
        )
        save_owner()
        st.success(f"Added '{task_title}' for {which_pet}.")

    # Suggest the earliest free start time for a task of this duration, working
    # around everything already booked -> Scheduler.find_next_available_slot().
    if st.button("🔎 Find next free slot"):
        slot_scheduler = Scheduler.from_owner(st.session_state.owner)
        slot = slot_scheduler.find_next_available_slot(int(duration))
        if slot is not None:
            st.info(
                f"Earliest free {int(duration)}-min slot today is **{slot}** "
                "(within 08:00–20:00)."
            )
        else:
            st.warning(
                f"No free {int(duration)}-min slot left before 20:00 — "
                "the day is full."
            )

# Show the owner's tasks, sorted into the day's order and filterable.
all_tasks = st.session_state.owner.get_all_tasks()
if all_tasks:
    st.markdown("### Current Tasks")

    # Filter controls -> Scheduler.filter_tasks()
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        pet_filter = st.selectbox("Filter by pet", ["All pets"] + [p.name for p in pets])
    with fcol2:
        status_filter = st.selectbox("Filter by status", ["All", "Pending", "Done"])

    # Build a scheduler over the owner's tasks, sort them, then apply filters.
    display_scheduler = Scheduler.from_owner(st.session_state.owner)
    display_scheduler.sort_tasks()
    completed_arg = {"All": None, "Pending": False, "Done": True}[status_filter]
    pet_arg = None if pet_filter == "All pets" else pet_filter
    shown = display_scheduler.filter_tasks(completed=completed_arg, pet_name=pet_arg)

    if not shown:
        st.info("No tasks match these filters.")
    else:
        st.table(
            [
                {
                    "start": t.start_time or "--:--",
                    "task": t.name,
                    "pet": t.pet.name,
                    "duration (min)": t.duration,
                    "priority": t.priority.name.lower(),
                    "done": "✅" if t.completed else "—",
                }
                for t in shown
            ]
        )

        # Let the owner mark a pending task done. A daily/weekly task will
        # auto-spawn its next occurrence (Task.mark_complete -> next_occurrence).
        pending = [t for t in shown if not t.completed]
        if pending:
            done_choice = st.selectbox(
                "Mark a task complete",
                [f"{t.name} — {t.pet.name} ({t.start_time or 'unscheduled'})" for t in pending],
            )
            if st.button("✓ Mark complete"):
                task = pending[
                    [
                        f"{t.name} — {t.pet.name} ({t.start_time or 'unscheduled'})"
                        for t in pending
                    ].index(done_choice)
                ]
                upcoming = task.mark_complete()
                save_owner()
                if upcoming is not None:
                    st.success(
                        f"Marked '{task.name}' done. Next {task.frequency} occurrence "
                        f"scheduled for {upcoming.due_date.isoformat()}. 🔁"
                    )
                else:
                    st.success(f"Marked '{task.name}' done. ✅")
                st.rerun()

# --- Build Schedule -> Scheduler.generate_plan() / detect_conflicts() -------
st.divider()
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    scheduler = Scheduler.from_owner(st.session_state.owner)
    plan = scheduler.generate_plan()

    if not plan:
        st.info("Nothing to schedule yet. Add some tasks first.")
    else:
        st.markdown(f"### Today's Schedule for {st.session_state.owner.name}")
        st.table(
            [
                {
                    "start": t.start_time or "--:--",
                    "task": t.name,
                    "pet": t.pet.name,
                    "duration (min)": t.duration,
                    "priority": t.priority.name.lower(),
                }
                for t in plan
            ]
        )

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.error(
            f"⚠️ {len(conflicts)} scheduling "
            f"{'conflict' if len(conflicts) == 1 else 'conflicts'} found — "
            "you can't be in two places at once."
        )
        for a, b in conflicts:
            same_pet = a.pet is not None and a.pet is b.pet
            who = (
                f"both on **{a.pet.name}**'s schedule"
                if same_pet
                else f"between **{a.pet.name if a.pet else '?'}** and "
                f"**{b.pet.name if b.pet else '?'}**"
            )
            # Each conflict gets its own warning box: the two tasks, their times,
            # who's affected, and a concrete next step the owner can act on.
            st.warning(
                f"**{a.name}** ({a.start_time}, {a.duration} min) overlaps "
                f"**{b.name}** ({b.start_time}, {b.duration} min) — {who}.\n\n"
                f"💡 Consider moving one of these, shortening it, or asking for help "
                f"so they don't run at the same time."
            )
    elif plan:
        st.success("No conflicts — the day flows cleanly. ✅")