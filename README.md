# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
Daily plan for Jordan — 2026-07-02
  [x] 08:00 — Morning walk for Mochi (30 min) [priority: 3]
  [x] 08:30 — Feeding for Mochi (10 min) [priority: 3]
  [ ] 08:40 — Feeding for Biscuit (10 min) [priority: 3]
  [ ] 08:50 — Medication for Biscuit (5 min) [priority: 2]
  [ ] 17:30 — Training for Mochi (45 min) [priority: 1]
Total scheduled: 100 min across 5 task(s); 2/5 done.
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.generate` | Sorts due tasks by priority (highest first), then shortest duration, so important — and quick — tasks claim time first. **App:** the "Current tasks" list is separately sortable by duration/priority/frequency/pet/title (asc/desc). |
| Filtering | `Scheduler.needs_doing`, `Scheduler.generate` | `needs_doing` drops tasks already satisfied for their period; `generate` sends any task that fits no window to `Schedule.unscheduled`. **App:** the "Current tasks" list filters by pet and by today's status (All/Pending/Done). |
| Conflict handling | `Scheduler.generate` | Per-window cursors advance as tasks are placed (best-fit), so no two tasks are ever assigned overlapping time. **App:** duplicate availability windows and same-title/frequency tasks are rejected on add. |
| Recurring tasks | `Scheduler.needs_doing`, `Task.done_in_week_of`, `Task.is_done_on` | `daily` always due; `weekly` hidden once `done_in_week_of` the ISO week; `once` hidden after any completion. **App:** completion is toggled via per-task checkboxes (`Task.mark_done_on`) and persists across reruns through `st.session_state`. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
