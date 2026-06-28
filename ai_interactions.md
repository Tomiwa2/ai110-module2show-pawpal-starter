# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I asked the agent (Claude) to add a third algorithmic capability to PawPal+ that
goes beyond the basic requirements — something like "next available slot" or
weighted prioritization — and to wire it through the whole project, then document
the work here.

**What did you complete / what did the agent do?**

The agent chose to implement a **"next available slot"** finder: a gap-finding
algorithm that sweeps the day's booked time intervals and returns the earliest
free `HH:MM` start time that fits a task of a given duration (or `None` when the
day is full). It is date-aware and ignores completed/unscheduled tasks, matching
the rules already used by conflict detection.

Files modified:

- **`pawpal_system.py`** — added the `_to_hhmm()` helper and the
  `Scheduler.find_next_available_slot(duration, day_start, day_end, on_date)`
  method (a sorted sweep-line over booked intervals, clipped to a working window).
- **`tests/test_pawpal.py`** — added 6 tests covering an empty day, a fittable
  gap, a too-small gap, a full day (returns `None`), ignoring completed/
  unscheduled tasks, and date-awareness. Suite went from 10 → 16 passing tests.
- **`main.py`** — added a "Next available slot" step to the CLI demo that suggests
  the earliest free 45-minute slot for today.
- **`app.py`** — added a "🔎 Find next free slot" button to the Streamlit Add-a-Task
  form that reports the earliest open start time for the chosen duration.
- **`README.md`** — documented the feature in the Features list, the Smarter
  Scheduling table + a detail subsection, the test-coverage notes, the confidence
  paragraph, the updated sample test output (16 passing), and the CLI demo output.
- **`diagrams/uml_final.mmd`** — added the new method to the `Scheduler` class box.

The agent ran `pytest` (16 passed), executed `python main.py` to confirm the slot
output (`08:25`), and byte-compiled `app.py`/`main.py`/`pawpal_system.py`.

**What did you have to verify or fix manually?**

A few things still need a human eye:

- **The UML PNG is stale.** The agent updated the diagram source
  (`diagrams/uml_final.mmd`) to include the new method, but it did **not**
  regenerate `diagrams/uml_final.png` — that needs the Mermaid CLI (Node.js),
  which isn't installed here. I need to run the export command from the README
  (`npx @mermaid-js/mermaid-cli -i diagrams/uml_final.mmd -o diagrams/uml_final.png -b white`)
  to refresh the rendered image.
- **The Streamlit button wasn't tested live.** The new "🔎 Find next free slot"
  button was only confirmed via `py_compile` (syntax check), not by actually
  running `streamlit run app.py` and clicking it. I did  a quick manual
  click-through to confirm it behaves as expected in the UI.
- **The CLI sample output is hard-coded to today's date.** `main.py` anchors
  tasks to `date.today()`, so the dates shown in the README demo output
  (`2026-06-28`) will differ when run on another day. The slot result (`08:25`)
  and the logic are stable; only the printed dates change.

What the agent got right and I verified: the full test suite passes (16/16),
`python main.py` produced the expected `08:25` slot, and all three modules
byte-compile cleanly.


---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
