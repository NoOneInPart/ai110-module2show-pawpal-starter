from dataclasses import dataclass, field
from datetime import date


@dataclass
class TimeSlot:
    start_hour: int
    start_minute: int
    duration_minutes: int

    def overlaps(self, other: "TimeSlot") -> bool:
        pass


@dataclass
class Task:
    task_type: str
    duration_minutes: int
    priority: int
    frequency: str
    pet: "Pet" = field(default=None, repr=False)


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    conditions: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass


@dataclass
class Owner:
    name: str
    availability: list[TimeSlot] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_schedule(self) -> "Schedule":
        pass


@dataclass
class Schedule:
    owner: Owner
    date: date = field(default_factory=date.today)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def explain(self) -> str:
        pass


@dataclass
class Scheduler:
    owner: Owner

    def generate(self, for_date: date = None) -> "Schedule":
        pass
