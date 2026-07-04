import streamlit as st
from datetime import date

from pawpal_system import Owner, Pet, Task, TimeSlot, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# --- Persistent state -------------------------------------------------------
# Streamlit reruns this entire script top-to-bottom on every interaction, so
# any plain local variable is rebuilt from scratch each rerun. We keep the
# Owner in st.session_state as the single source of truth: its pets, their
# tasks, and each task's completion history all hang off it and therefore
# survive across reruns. (This is what makes per-task completion tracking
# actually persist in the UI — the same Task objects stay alive.)
if "owner" not in st.session_state:
    owner = Owner(name="Jordan")
    # Start with no availability windows — the user adds their own below.
    st.session_state.owner = owner
owner = st.session_state.owner

# The UI offers text priorities; the model uses integers (higher = more important).
PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}
PRIORITY_LABEL = {1: "low", 2: "medium", 3: "high"}

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

st.divider()

# --- Owner & pet ------------------------------------------------------------
st.subheader("Owner & Pet")
owner.name = st.text_input("Owner name", value=owner.name)

pet_name = st.text_input("Pet name", value="Mochi")

# Species isn't collected in the UI: nothing in the current app (scheduling,
# filtering, display) depends on it, so asking for it would just be friction.
# The model still carries the field for future use — new pets get its default.


def get_or_create_pet(name: str) -> Pet:
    """Return the owner's pet with this name, creating and adding it if needed."""
    for pet in owner.pets:
        if pet.name == name:
            return pet
    pet = Pet(name=name, breed="", age=0)
    owner.add_pet(pet)
    return pet


def _mark_done_from_checkbox(task: Task, key: str, for_date: date) -> None:
    """Sync a schedule checkbox's new value onto its task's completion history.

    Used as an ``on_change`` handler so the mutation lands before Streamlit
    reruns the script, keeping the task list (rendered earlier) in sync on the
    same interaction rather than one event behind.
    """
    task.mark_done_on(for_date, st.session_state[key])


# --- Availability -----------------------------------------------------------
st.subheader("Availability")
st.caption("Time windows the owner is free. Tasks get packed into these.")

av1, av2, av3, av4 = st.columns([1, 1, 1, 1])
with av1:
    av_hour = st.number_input("Start hour", min_value=0, max_value=23, value=8)
with av2:
    av_minute = st.number_input("Start minute", min_value=0, max_value=59, value=0)
with av3:
    av_length = st.number_input("Length (min)", min_value=15, max_value=720, value=120, step=15)
with av4:
    st.write("")
    st.write("")
    if st.button("Add window"):
        new_slot = TimeSlot(
            start_hour=int(av_hour), start_minute=int(av_minute), duration_minutes=int(av_length)
        )
        # Skip an identical window so the list doesn't fill with duplicates.
        if any(
            (s.start_hour, s.start_minute, s.duration_minutes)
            == (new_slot.start_hour, new_slot.start_minute, new_slot.duration_minutes)
            for s in owner.availability
        ):
            st.warning("That availability window already exists.")
        else:
            owner.availability.append(new_slot)

if owner.availability:
    st.write(
        "Current windows: "
        + ", ".join(f"{s.label()} ({s.duration_minutes} min)" for s in owner.availability)
    )
else:
    st.info("No availability yet — add a window so tasks can be scheduled.")

st.divider()

# --- Tasks ------------------------------------------------------------------
st.subheader("Tasks")
st.caption("Add care tasks for the pet above. These feed into the scheduler.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])

if st.button("Add task"):
    pet = get_or_create_pet(pet_name)
    # Treat a task as a duplicate if this pet already has one with the same
    # title + frequency. (Give distinct titles, e.g. "Morning feeding" vs
    # "Evening feeding", for two of the same kind.)
    if any(t.task_type == task_title and t.frequency == frequency for t in pet.tasks):
        st.warning(f"{pet.name} already has a {frequency} '{task_title}' task.")
    else:
        pet.add_task(
            Task(
                task_type=task_title,
                duration_minutes=int(duration),
                priority=PRIORITY_MAP[priority],
                frequency=frequency,
            )
        )

# Show current tasks straight from the model, with a chosen sort order.
tasks = [task for pet in owner.pets for task in pet.tasks]
if tasks:
    st.write("Current tasks:")

    # Sort keys operate on the raw model values (so priority sorts high→low by
    # its integer, not alphabetically by its label). "Duration" is the closest
    # thing to a per-task time, since unscheduled tasks have no clock time yet.
    SORT_KEYS = {
        "Duration": lambda t: t.duration_minutes,
        "Priority": lambda t: -t.priority,
        "Frequency": lambda t: t.frequency,
        "Pet": lambda t: t.pet.name if t.pet else "",
        "Task": lambda t: t.task_type,
    }
    sc1, sc2 = st.columns([2, 1])
    with sc1:
        sort_by = st.selectbox("Sort tasks by", list(SORT_KEYS), key="task_sort_by")
    with sc2:
        descending = st.checkbox("Descending", value=False, key="task_sort_desc")

    # Filters. Status is completion for today (the same per-date completion the
    # schedule uses), so a task can read "done" here once it's checked off below.
    today = date.today()
    fc1, fc2 = st.columns([2, 1])
    with fc1:
        pet_names = [pet.name for pet in owner.pets]
        selected_pets = st.multiselect(
            "Filter by pet", pet_names, default=pet_names, key="task_filter_pets"
        )
    with fc2:
        status = st.selectbox("Status", ["All", "Pending", "Done"], key="task_filter_status")

    def keep(task) -> bool:
        pet_name = task.pet.name if task.pet else None
        if pet_name not in selected_pets:
            return False
        if status == "Done":
            return task.is_done_on(today)
        if status == "Pending":
            return not task.is_done_on(today)
        return True

    filtered = [task for task in tasks if keep(task)]
    ordered = sorted(filtered, key=SORT_KEYS[sort_by], reverse=descending)
    rows = [
        {
            "pet": task.pet.name if task.pet else "?",
            "task": task.task_type,
            "duration_minutes": task.duration_minutes,
            "priority": PRIORITY_LABEL.get(task.priority, task.priority),
            "frequency": task.frequency,
            "status": "done" if task.is_done_on(today) else "pending",
        }
        for task in ordered
    ]
    if rows:
        st.table(rows)
    else:
        st.caption("No tasks match the current filters.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule ---------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    st.session_state.show_schedule = True

if st.session_state.get("show_schedule"):
    # The Schedule is derived, so we rebuild it fresh from the owner each run.
    # Completion lives on the tasks, so nothing is lost by regenerating.
    today = date.today()
    schedule = Scheduler(owner=owner).generate(today)

    if not schedule.tasks:
        st.info("Nothing to schedule — add tasks (and availability) above.")
    else:
        st.write(f"**Plan for {owner.name} — {today.isoformat()}**")

        # Render the plan in scheduled (time) order, but drop a lightweight pet
        # subheader whenever the owner moves on to a different pet. Consecutive
        # tasks for the same pet visually cluster under one header without
        # reordering the time-based plan or changing per-task completion.
        current_pet = None
        for i, (task, slot) in enumerate(zip(schedule.tasks, schedule.slots)):
            if task.pet.name != current_pet:
                current_pet = task.pet.name
                st.markdown(f"**▸ {current_pet}**")
            # Checkbox is the source of the toggle; we mirror it onto the task's
            # completion history (keyed by today's date) so it persists. The
            # render index keeps the key unique even if two tasks share a title.
            #
            # The mutation runs in an on_change callback, not inline: Streamlit
            # fires callbacks *before* it reruns the script top-to-bottom, so
            # the task list rendered earlier in the page reflects this toggle on
            # the same interaction. Mutating inline (after render) would leave
            # that list one event stale.
            key = f"done|{i}|{task.pet.name}|{task.task_type}"
            label = (
                f"{slot.label()} — {task.task_type} "
                f"({task.duration_minutes} min, "
                f"{PRIORITY_LABEL.get(task.priority, task.priority)})"
            )
            st.checkbox(
                label,
                value=task.is_done_on(today),
                key=key,
                on_change=_mark_done_from_checkbox,
                args=(task, key, today),
            )

        done_count, total = schedule.progress()
        st.progress(done_count / total, text=f"{done_count}/{total} done")

    if schedule.has_conflicts():
        st.error("Time conflicts (overlapping availability double-booked): " + ", ".join(
            f"{schedule.slots[i].label()} {schedule.tasks[i].task_type} overlaps "
            f"{schedule.slots[j].label()} {schedule.tasks[j].task_type}"
            for i, j in schedule.conflicts()
        ))

    if schedule.unscheduled:
        st.warning("Skipped (no time available): " + ", ".join(
            f"{t.task_type} for {t.pet.name} ({t.duration_minutes} min)" for t in schedule.unscheduled
        ))

    with st.expander("Explain this plan"):
        st.text(schedule.explain())
