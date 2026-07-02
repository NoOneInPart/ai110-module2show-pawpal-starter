# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
    > Three core actions a user should be able to perform are add/edit a pet and attributes, schedule tasks for a pet, and print a schedule (to the screen). The main objects needed for this project would be Owner, Pet, Task, and Schedule. 
- What classes did you include, and what responsibilities did you assign to each?
    > There ended up being a few more. TimeSlot represents abstract blocks of time, e.g. the start and end times when an owner is free. Task is meant to represent a task and holds metadata about a task, like which pet it concerns, how long it takes, the priority, the dates that the task has been completed, and the frequency. Pet represents a pet and holds metadata such as the pet's name, species, breed, age, the tasks required by the pet, and even medical condition (that particular one was at the behest of Claude). Owner represents an owner and the associated info, like their name, availability, and the owner's pets, with the ability to add pets, view tasks required by the owner, and get the owner's schedule. Schedule represents the schedule for an owner, like the tasks and timeslots, whereas Scheduler generates a Schedule for an Owner.

**b. Design changes**

- Did your design change during implementation?
    Yes
- If yes, describe at least one change and why you made it.
    Claude came up with the idea of backlinking a Pet onto a Task so that when dealing with Task objects one can determine which Pet it the Task belongs to.

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
