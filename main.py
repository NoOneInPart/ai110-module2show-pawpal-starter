"""Small CLI demo for PawPal+.

Builds an owner with two pets, gives each pet a few care tasks with
different durations/priorities, generates a daily schedule, and prints
the explained plan.

Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Task, TimeSlot


def main() -> None:
    # An owner who is free in the morning and again after work.
    owner = Owner(
        name="Jordan",
        availability=[
            TimeSlot(start_hour=8, start_minute=0, duration_minutes=90),   # 08:00–09:30
            TimeSlot(start_hour=17, start_minute=30, duration_minutes=60),  # 17:30–18:30
        ],
    )

    # Two pets with different needs.
    mochi = Pet(name="Mochi", species="dog", breed="Corgi", age=3)
    biscuit = Pet(name="Biscuit", species="cat", breed="Tabby", age=7, conditions=["senior"])

    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    # Mochi's tasks (higher priority = more important).
    mochi.add_task(Task(task_type="Morning walk", duration_minutes=30, priority=3, frequency="daily"))
    mochi.add_task(Task(task_type="Feeding", duration_minutes=10, priority=3, frequency="daily"))
    mochi.add_task(Task(task_type="Training", duration_minutes=45, priority=1, frequency="daily"))

    # Biscuit's tasks.
    biscuit.add_task(Task(task_type="Feeding", duration_minutes=10, priority=3, frequency="daily"))
    biscuit.add_task(Task(task_type="Medication", duration_minutes=5, priority=2, frequency="daily"))
    biscuit.add_task(Task(task_type="Grooming", duration_minutes=20, priority=1, frequency="weekly"))

    # Generate today's plan and print the explanation.
    schedule = owner.get_schedule()
    print(schedule.explain())

    # Simulate completing the first couple of tasks, then reprint.
    print("\n--- after finishing the morning walk and first feeding ---\n")
    schedule.mark_done(0)
    schedule.mark_done(1)
    print(schedule.explain())

    # Completion is stored on the tasks (keyed by date), so regenerating the
    # plan for the same day preserves what was already done.
    print("\n--- regenerated plan for the same day (completions persist) ---\n")
    fresh = owner.get_schedule()
    print(fresh.explain())

    # Weekly tasks stay listed until done, then disappear until next week.
    # Find Biscuit's weekly grooming in today's plan and complete it.
    print("\n--- complete the weekly grooming, then regenerate ---\n")
    for i, task in enumerate(fresh.tasks):
        if task.task_type == "Grooming":
            fresh.mark_done(i)
            break
    after = owner.get_schedule()
    print(after.explain())
    print("\n(Grooming is gone above — already done this calendar week.)")


if __name__ == "__main__":
    main()
