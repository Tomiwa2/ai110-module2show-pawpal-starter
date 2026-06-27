# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML design has four classes, split between data objects (Owner, Pet, and Task) that hold state and a service object (Scheduler) that does work:

- **Owner** — represents a pet owner. It holds the owner's `name` and a list of
  their `pets`, and is responsible for managing that collection through
  `add_pet()` and `get_pets()`.

- **Pet** — represents a single pet. It holds the pet's `name`, `species`, and a
  list of care `tasks`, and is responsible for managing its own tasks via
  `add_task()` and `get_tasks()`.

- **Task** — represents one unit of pet care. It holds the task's `name`,
  `duration` (in minutes), and `priority`, and is responsible for describing and
  updating itself through `display_info()` and `update_details()`.

- **Scheduler** — the one behavior-focused class. It takes a list of
  `tasks_to_schedule` and an `available_time` budget, and is responsible for the
  scheduling logic: ordering tasks with `sort_tasks()` and producing a workable
  plan that fits the time budget with `generate_plan()`.

The responsibilities follow a clear ownership chain — an Owner owns Pets, a Pet
owns Tasks — while the Scheduler stays separate so the scheduling logic is
decoupled from the data it operates on.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, my design changed in a few ways once I started implementing and reviewing
the skeleton:

- **`priority` went from a plain string to a `Priority` enum.** Originally Task
  stored `priority` as a string like `"high"`. The problem is that sorting
  strings is alphabetical, so `"high"`, `"low"`, `"medium"` would sort in the
  wrong order and a typo like `"hgh"` would silently break the scheduler. I
  introduced a `Priority(IntEnum)` (HIGH=0, MEDIUM=1, LOW=2) so the scheduler can
  sort by real importance and invalid values are impossible.

- **I added a link from the Scheduler back to the data.** My first design left
  `Scheduler.tasks_to_schedule` as a loose list with no way to populate it from
  an Owner. I added `Owner.get_all_tasks()` (which flattens every task across all
  of the owner's pets) and a `Scheduler.from_owner()` constructor so the
  scheduler can actually pull the data instead of relying on the caller to wire
  it up by hand.

- **I gave each Task a back-reference to its Pet.** Originally the relationship
  was one-directional (Pet → Task), but the generated plan only returned tasks,
  so it couldn't say *which* pet a task belonged to. Adding a `pet` field lets
  `display_info()` show "Walk (for Rex)" in the final plan.

The biggest driver behind these changes was making the scheduler actually
functional: without a real priority ordering and a way to collect tasks, the two
core methods (`sort_tasks` and `generate_plan`) had nothing meaningful to work
with.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
