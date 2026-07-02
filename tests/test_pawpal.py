from datetime import date

from pawpal_system import Pet, Task


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
