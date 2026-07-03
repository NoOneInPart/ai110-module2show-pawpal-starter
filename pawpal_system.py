from dataclasses import dataclass, field
from datetime import date


@dataclass
class TimeSlot:
    start_hour: int
    start_minute: int
    duration_minutes: int

    @property
    def start_minutes(self) -> int:
        """Minutes since midnight when this slot starts."""
        return self.start_hour * 60 + self.start_minute

    @property
    def end_minutes(self) -> int:
        """Minutes since midnight when this slot ends."""
        return self.start_minutes + self.duration_minutes

    def label(self) -> str:
        """Human-readable start time, e.g. ``08:05``."""
        return f"{self.start_hour:02d}:{self.start_minute:02d}"


@dataclass
class Task:
    task_type: str
    duration_minutes: int
    priority: int
    frequency: str
    pet: "Pet" = field(default=None, repr=False)
    # Dates on which this task was completed. Keyed by date so completion
    # persists across regenerated schedules and each day is independent
    # (a daily task done Tuesday is not "done" on Wednesday).
    completed_dates: set[date] = field(default_factory=set)

    def is_done_on(self, for_date: date) -> bool:
        """Whether this task was completed on ``for_date``."""
        return for_date in self.completed_dates

    def mark_done_on(self, for_date: date, done: bool = True) -> None:
        """Record (or clear) completion of this task on ``for_date``."""
        if done:
            self.completed_dates.add(for_date)
        else:
            self.completed_dates.discard(for_date)

    def done_in_week_of(self, for_date: date) -> bool:
        """Whether this task was completed during the ISO calendar week of ``for_date``."""
        target_week = for_date.isocalendar()[:2]  # (ISO year, ISO week number)
        return any(d.isocalendar()[:2] == target_week for d in self.completed_dates)


@dataclass
class Pet:
    name: str
    # Descriptive metadata about the pet. None of these currently affect any
    # logic — the scheduler only reads each task's duration/priority/frequency,
    # never the pet's traits. They're kept (with defaults, so a pet needs only a
    # name) as a hook for future features like species-specific care templates.
    species: str = "other"
    breed: str = ""
    age: int = 0
    conditions: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and back-link the pet onto the task."""
        task.pet = self
        self.tasks.append(task)


@dataclass
class Owner:
    name: str
    availability: list[TimeSlot] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's household."""
        self.pets.append(pet)

    def all_tasks(self) -> list[Task]:
        """Every task across every pet this owner has."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_schedule(self) -> "Schedule":
        """Build a schedule for today using this owner's scheduler."""
        return Scheduler(owner=self).generate()


@dataclass
class Schedule:
    owner: Owner
    date: date = field(default_factory=date.today)
    tasks: list[Task] = field(default_factory=list)
    # Assigned start times, parallel to ``tasks`` (filled in by the Scheduler).
    slots: list[TimeSlot] = field(default_factory=list)
    # Tasks that could not fit in the available time.
    unscheduled: list[Task] = field(default_factory=list)

    def add_task(self, task: Task, slot: "TimeSlot | None" = None) -> None:
        """Add a task to the plan, optionally with the time slot it occupies."""
        self.tasks.append(task)
        self.slots.append(slot)

    def mark_done(self, index: int, done: bool = True) -> None:
        """Mark the task at ``index`` complete (or incomplete) for this day.

        Completion is recorded on the task itself, keyed by this schedule's
        date, so it persists even after the schedule is regenerated.
        """
        self.tasks[index].mark_done_on(self.date, done)

    def is_done(self, index: int) -> bool:
        """Whether the task at ``index`` is completed for this schedule's date."""
        return self.tasks[index].is_done_on(self.date)

    def is_complete(self) -> bool:
        """True when every scheduled task has been completed for this date."""
        return bool(self.tasks) and all(t.is_done_on(self.date) for t in self.tasks)

    def progress(self) -> tuple[int, int]:
        """Return ``(done, total)`` completed vs. scheduled task counts."""
        done = sum(1 for t in self.tasks if t.is_done_on(self.date))
        return done, len(self.tasks)

    def total_minutes(self) -> int:
        """Total scheduled time across all placed tasks."""
        return sum(task.duration_minutes for task in self.tasks)

    def explain(self) -> str:
        """Return a readable, ordered explanation of the plan."""
        lines = [f"Daily plan for {self.owner.name} — {self.date.isoformat()}"]

        if not self.tasks:
            lines.append("  (no tasks scheduled)")
        for task, slot in zip(self.tasks, self.slots):
            pet_name = task.pet.name if task.pet else "?"
            check = "[x]" if task.is_done_on(self.date) else "[ ]"
            when = slot.label() if slot else "--:--"
            lines.append(
                f"  {check} {when} — {task.task_type} for {pet_name} "
                f"({task.duration_minutes} min) [priority: {task.priority}]"
            )

        done, total = self.progress()
        lines.append(
            f"Total scheduled: {self.total_minutes()} min across {total} task(s); "
            f"{done}/{total} done."
        )

        if self.unscheduled:
            lines.append("Skipped (no time available):")
            for task in self.unscheduled:
                pet_name = task.pet.name if task.pet else "?"
                lines.append(
                    f"  - {task.task_type} for {pet_name} "
                    f"({task.duration_minutes} min) [priority: {task.priority}]"
                )

        return "\n".join(lines)


@dataclass
class Scheduler:
    owner: Owner

    def needs_doing(self, task: Task, for_date: date) -> bool:
        """Whether ``task`` still needs to be scheduled on ``for_date``.

        This is where recurrence meets completion history:

        - ``daily``  -> always listed (a done one still shows, checked off)
        - ``weekly`` -> listed until it has been completed this ISO calendar
          week, then hidden until the following week
        - ``once``   -> listed until it has ever been completed
        """
        frequency = (task.frequency or "").strip().lower()
        if frequency == "weekly":
            return not task.done_in_week_of(for_date)
        if frequency == "once":
            return not task.completed_dates
        return True  # daily / unknown -> always a candidate

    def generate(self, for_date: date = None) -> "Schedule":
        """Greedily pack the tasks that still need doing into available time.

        Strategy:
        1. Collect every task that still needs doing on ``for_date`` (its
           recurrence is due and it isn't already satisfied for its period).
        2. Sort by priority (highest first), then longest duration, so the
           most important work claims time before anything else.
        3. Walk the owner's availability slots in chronological order,
           placing each task into the first slot with enough remaining room.
        4. Anything that never fits is recorded as ``unscheduled``.
        """
        if for_date is None:
            for_date = date.today()

        schedule = Schedule(owner=self.owner, date=for_date)

        due_tasks = [task for task in self.owner.all_tasks() if self.needs_doing(task, for_date)]
        # Highest priority first, then SHORTEST duration first. Ordering short
        # tasks ahead of long ones at equal priority fits more important work
        # into scarce time — a 5-min medication shouldn't be crowded out by a
        # 45-min session of the same priority.
        due_tasks.sort(key=lambda t: (-t.priority, t.duration_minutes))

        # Track a moving cursor (minutes-from-midnight) within each slot, in
        # chronological order so earlier availability is filled first.
        windows = sorted(self.owner.availability, key=lambda s: s.start_minutes)
        cursors = [window.start_minutes for window in windows]

        for task in due_tasks:
            # Best-fit: among windows that can still hold this task, pick the
            # one that leaves the least leftover room. This packs tasks tightly
            # instead of letting an early task carve into a big window it didn't
            # need, which would strand later tasks that could otherwise have fit.
            candidates = [
                i for i, window in enumerate(windows)
                if cursors[i] + task.duration_minutes <= window.end_minutes
            ]
            if not candidates:
                schedule.unscheduled.append(task)
                continue
            # Tightest fit = window with the least room left right now. The room
            # *after* placing is (end - cursor - duration), but duration is the
            # same for every candidate of this task, so it doesn't affect which
            # window wins — compare current room (end - cursor) directly.
            i = min(candidates, key=lambda i: windows[i].end_minutes - cursors[i])
            start = cursors[i]
            slot = TimeSlot(
                start_hour=start // 60,
                start_minute=start % 60,
                duration_minutes=task.duration_minutes,
            )
            schedule.add_task(task, slot)
            cursors[i] += task.duration_minutes

        return schedule
