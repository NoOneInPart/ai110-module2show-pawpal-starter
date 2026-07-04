from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task, TimeSlot


def test_task_completion_changes_status():
    """Marking a task done for a date flips its completion status for that date."""
    task = Task(task_type="Feeding", duration_minutes=10, priority=3, frequency="daily")
    today = date(2026, 7, 2)

    assert task.is_done_on(today) is False

    task.mark_done_on(today)
    assert task.is_done_on(today) is True

    # And it can be cleared again.
    task.mark_done_on(today, done=False)
    assert task.is_done_on(today) is False


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet increases that pet's task count by one."""
    pet = Pet(name="Mochi", species="dog", breed="Corgi", age=3)
    assert len(pet.tasks) == 0

    pet.add_task(Task(task_type="Morning walk", duration_minutes=30, priority=3, frequency="daily"))
    assert len(pet.tasks) == 1

    pet.add_task(Task(task_type="Feeding", duration_minutes=10, priority=3, frequency="daily"))
    assert len(pet.tasks) == 2


# --- Sorting: the schedule is returned in chronological (start-time) order ---


def test_schedule_is_returned_in_chronological_order():
    """generate() returns tasks ordered by start time, not placement/priority.

    With two availability windows and best-fit placement, the highest-priority
    task is *placed* first but can land in the later window, while a
    lower-priority task lands in the earlier one. The returned schedule must
    still read top-to-bottom in time order.
    """
    owner = Owner(name="Jordan")
    # 08:00-09:00 (roomy) and 10:00-10:20 (tight).
    owner.availability = [TimeSlot(8, 0, 60), TimeSlot(10, 0, 20)]
    pet = Pet(name="Mochi")
    owner.add_pet(pet)
    # High priority + short: best-fit sends it to the tight 10:00 window first.
    pet.add_task(Task(task_type="Meds", duration_minutes=20, priority=5, frequency="daily"))
    # Lower priority: placed second, lands in the earlier 08:00 window.
    pet.add_task(Task(task_type="Walk", duration_minutes=30, priority=3, frequency="daily"))

    schedule = Scheduler(owner=owner).generate(date(2026, 7, 4))

    starts = [slot.start_minutes for slot in schedule.slots]
    assert starts == sorted(starts)
    # Concretely: Walk (08:00) comes before Meds (10:00), despite Meds' priority.
    assert [task.task_type for task in schedule.tasks] == ["Walk", "Meds"]


def test_within_single_window_tasks_are_back_to_back_in_order():
    """Tasks packed into one window come back in ascending start-time order."""
    owner = Owner(name="Jordan")
    owner.availability = [TimeSlot(8, 0, 120)]
    pet = Pet(name="Mochi")
    owner.add_pet(pet)
    pet.add_task(Task(task_type="A", duration_minutes=30, priority=3, frequency="daily"))
    pet.add_task(Task(task_type="B", duration_minutes=20, priority=3, frequency="daily"))
    pet.add_task(Task(task_type="C", duration_minutes=10, priority=3, frequency="daily"))

    schedule = Scheduler(owner=owner).generate(date(2026, 7, 4))

    starts = [slot.start_minutes for slot in schedule.slots]
    assert starts == sorted(starts)
    # No overlaps and no gaps within the single window: each starts where the
    # previous ended.
    for earlier, later in zip(schedule.slots, schedule.slots[1:]):
        assert later.start_minutes == earlier.end_minutes


# --- Recurrence: a completed daily task reappears the next day --------------


def test_daily_task_reappears_next_day_after_completion():
    """Marking a daily task done for one day still schedules it the next day."""
    owner = Owner(name="Jordan")
    owner.availability = [TimeSlot(8, 0, 120)]
    pet = Pet(name="Mochi")
    owner.add_pet(pet)
    task = Task(task_type="Feeding", duration_minutes=10, priority=3, frequency="daily")
    pet.add_task(task)

    today = date(2026, 7, 4)
    tomorrow = today + timedelta(days=1)

    # Complete it today...
    today_schedule = Scheduler(owner=owner).generate(today)
    assert task in today_schedule.tasks
    task.mark_done_on(today)
    assert today_schedule.is_done(today_schedule.tasks.index(task)) is True

    # ...and it is still scheduled (and not pre-marked done) tomorrow.
    tomorrow_schedule = Scheduler(owner=owner).generate(tomorrow)
    assert task in tomorrow_schedule.tasks
    assert task.is_done_on(tomorrow) is False


def _weekly_owner():
    """An owner with a single weekly task and roomy availability."""
    owner = Owner(name="Jordan")
    owner.availability = [TimeSlot(8, 0, 120)]
    pet = Pet(name="Mochi")
    owner.add_pet(pet)
    task = Task(task_type="Bath", duration_minutes=30, priority=3, frequency="weekly")
    pet.add_task(task)
    return owner, task


def test_weekly_task_hidden_for_rest_of_week_after_completion():
    """A weekly task, once done, drops out of the schedule for the same ISO week."""
    owner, task = _weekly_owner()
    # 2026-07-06 (Mon) .. 2026-07-08 (Wed) are all in the same ISO week.
    monday = date(2026, 7, 6)
    wednesday = date(2026, 7, 8)
    assert monday.isocalendar()[:2] == wednesday.isocalendar()[:2]

    assert task in Scheduler(owner=owner).generate(monday).tasks
    task.mark_done_on(monday)

    # Later the same week: no longer due.
    assert task not in Scheduler(owner=owner).generate(wednesday).tasks


def test_weekly_task_returns_the_following_week():
    """A weekly task done one week is due again the next ISO week."""
    owner, task = _weekly_owner()
    this_week = date(2026, 7, 8)      # Wed, ISO week N
    next_week = date(2026, 7, 15)     # Wed, ISO week N+1
    assert this_week.isocalendar()[:2] != next_week.isocalendar()[:2]

    task.mark_done_on(this_week)
    assert task not in Scheduler(owner=owner).generate(this_week).tasks
    assert task in Scheduler(owner=owner).generate(next_week).tasks


def test_weekly_task_completed_sunday_reappears_monday():
    """ISO weeks start Monday: a Sunday completion doesn't cover the next Monday."""
    owner, task = _weekly_owner()
    sunday = date(2026, 7, 12)        # Sun, end of one ISO week
    monday = date(2026, 7, 13)        # Mon, start of the next ISO week
    assert sunday.isocalendar()[:2] != monday.isocalendar()[:2]

    task.mark_done_on(sunday)
    assert task in Scheduler(owner=owner).generate(monday).tasks


def test_weekly_task_matches_by_iso_week_across_year_boundary():
    """ISO week/year, not calendar year, decides recurrence at a year boundary.

    2026-12-31 (Thu) and 2027-01-01 (Fri) fall in the same ISO week (2026-W53),
    so a Thursday completion should suppress the Friday occurrence even though
    the calendar year changed.
    """
    owner, task = _weekly_owner()
    dec31 = date(2026, 12, 31)
    jan01 = date(2027, 1, 1)
    assert dec31.isocalendar()[:2] == jan01.isocalendar()[:2]

    task.mark_done_on(dec31)
    assert task not in Scheduler(owner=owner).generate(jan01).tasks


def test_once_task_hidden_after_completion_then_reappears_if_uncompleted():
    """A 'once' task drops out once ever completed, and returns if that's undone."""
    owner = Owner(name="Jordan")
    owner.availability = [TimeSlot(8, 0, 120)]
    pet = Pet(name="Mochi")
    owner.add_pet(pet)
    task = Task(task_type="Vet visit", duration_minutes=45, priority=3, frequency="once")
    pet.add_task(task)

    day1 = date(2026, 7, 4)
    day2 = date(2026, 7, 20)

    assert task in Scheduler(owner=owner).generate(day1).tasks
    task.mark_done_on(day1)

    # Never due again on any later date once completed...
    assert task not in Scheduler(owner=owner).generate(day2).tasks

    # ...but clearing the (only) completion makes it due once more.
    task.mark_done_on(day1, done=False)
    assert task in Scheduler(owner=owner).generate(day2).tasks


def test_unknown_frequency_is_treated_as_daily():
    """An unrecognized frequency falls through to always-due (daily-like)."""
    owner = Owner(name="Jordan")
    owner.availability = [TimeSlot(8, 0, 120)]
    pet = Pet(name="Mochi")
    owner.add_pet(pet)
    task = Task(task_type="Mystery", duration_minutes=15, priority=3, frequency="monthly")
    pet.add_task(task)

    day1 = date(2026, 7, 4)
    task.mark_done_on(day1)
    # Still due the same day despite being marked done — treated as daily.
    assert task in Scheduler(owner=owner).generate(day1).tasks


# --- Conflict detection: overlapping availability double-books --------------


def test_scheduler_flags_conflicting_times():
    """Overlapping availability windows that double-book a time are flagged."""
    owner = Owner(name="Jordan")
    # Windows overlap between 08:30 and 09:00.
    owner.availability = [TimeSlot(8, 0, 60), TimeSlot(8, 30, 60)]
    pet = Pet(name="Mochi")
    owner.add_pet(pet)
    pet.add_task(Task(task_type="A", duration_minutes=40, priority=5, frequency="daily"))
    pet.add_task(Task(task_type="B", duration_minutes=40, priority=4, frequency="daily"))

    schedule = Scheduler(owner=owner).generate(date(2026, 7, 4))

    assert schedule.has_conflicts() is True
    # Exactly one overlapping pair, reported as (i, j) with i < j.
    assert schedule.conflicts() == [(0, 1)]


def test_no_conflict_when_windows_do_not_overlap():
    """Non-overlapping availability produces a conflict-free schedule."""
    owner = Owner(name="Jordan")
    owner.availability = [TimeSlot(8, 0, 60), TimeSlot(10, 0, 60)]
    pet = Pet(name="Mochi")
    owner.add_pet(pet)
    pet.add_task(Task(task_type="A", duration_minutes=40, priority=5, frequency="daily"))
    pet.add_task(Task(task_type="B", duration_minutes=40, priority=4, frequency="daily"))

    schedule = Scheduler(owner=owner).generate(date(2026, 7, 4))

    assert schedule.has_conflicts() is False
    assert schedule.conflicts() == []


def test_touching_slots_do_not_conflict():
    """Slots that meet end-to-start (one ends as the next begins) don't overlap."""
    owner = Owner(name="Jordan")
    owner.availability = [TimeSlot(8, 0, 60)]
    pet = Pet(name="Mochi")
    owner.add_pet(pet)
    # Two 30-min tasks fill the window back-to-back: 08:00-08:30, 08:30-09:00.
    pet.add_task(Task(task_type="A", duration_minutes=30, priority=5, frequency="daily"))
    pet.add_task(Task(task_type="B", duration_minutes=30, priority=4, frequency="daily"))

    schedule = Scheduler(owner=owner).generate(date(2026, 7, 4))

    assert schedule.has_conflicts() is False
