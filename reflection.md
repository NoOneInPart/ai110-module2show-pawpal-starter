# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
    > Three core actions a user should be able to perform are add/edit a pet and attributes, schedule tasks for a pet, and print a schedule (to the screen). The main objects needed for this project would be Owner, Pet, Task, and Schedule. 
- What classes did you include, and what responsibilities did you assign to each?
    > There ended up being a few more. TimeSlot represents abstract blocks of time, e.g. the start and end times when an owner is free. Task is meant to represent a task and holds metadata about a task, like which pet it concerns, how long it takes, the priority, the dates that the task has been completed, and the frequency. Pet represents a pet and holds metadata such as the pet's name, species, breed, age, the tasks required by the pet, and even medical condition (that particular one was at the behest of Claude). Owner represents an owner and the associated info, like their name, availability, and the owner's pets, with the ability to add pets, view tasks required by the owner, and get the owner's schedule. Schedule represents the schedule for an owner, like the tasks and timeslots, whereas Scheduler generates a Schedule for an Owner.

**b. Design changes**

- Did your design change during implementation?
    > Yes
- If yes, describe at least one change and why you made it.
    > Claude came up with the idea of backlinking a Pet onto a Task so that when dealing with Task objects one can determine which Pet it the Task belongs to.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
    > The scheduler only considers time slots for availability and task priority/duration/recurrence. It tries to fit tasks into available timeslots in order of priority, then duration (shortest first to maximize how many tasks get completed). Tasks track the date that they are completed, so daily tasks that are complete are showed again the next day, wheras weekly tasks that are completed will not appear until the next Monday.
- How did you decide which constraints mattered most?
    > Availability is the major constraint because we can't assume an owner can let a task go past the amount of free time they've indicated, everything must fit neatly within the timeslots. Priority is next in importance because high priority items are...well, high priority, and then duration comes after that. Shorter tasks are preferred because more of them can be completed, so one might be able to complete all the high priority tasks and then maybe one or two of the shorter medium priority tasks in a day, for example.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
    > It doesn't group identical tasks between pets that can be accomplished concurrently, like feeding and walking
- Why is that tradeoff reasonable for this scenario?
    > Logistically it is difficult to determine exactly which pets and which particular tasks should be grouped together and which pets shouldn't, and it is possible that the end-user doesn't want this happening automatically. Implementing the ability to allow the user to configure this themselves for specific tasks adds complexity (and is a little beyond the scope of this project).

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
    > I ask Claude about how it would implement something, maybe make some comments if I think something should be done a particular way, then I let it draft an implementation. I look through the code to see if there is anything obviously wrong with it, then I run the code (or ask Claude to write tests if applicable), and ask it to make some more changes if something doesn't work right or doesn't work as I expected.
- What kinds of prompts or questions were most helpful?
    > Asking it to go back and look through the code for optimizations ended up being pretty helpful because it suggested prioritizing fitting shorter tasks to get more things complete, which it didn't do the first time around, and it came up with a neat best-fit algorithm that crams tasks into whichever availability window yields the smallest leftover room for more efficient time use, rather than into the earliest availability window with sufficient space.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
    > When working with Claude to implement weekly recursion, it initially anchored the task to only appear on Mondays, so I convinced it to keep track of dates of when tasks are completed, and then implement logic in the Scheduler to resurface weekly tasks on Monday if the latest completion date was last week.
- How did you evaluate or verify what the AI suggested?
    > I asked Claude to also write tests for the algorithms, while I had to test the Streamlit frontend myself.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
    > I tested event creation, different pets, different tasks, and schedule generation.
- Why were these tests important?
    > The point of the project is that it works so I had to make sure the program works.

**b. Confidence**

- How confident are you that your scheduler works correctly?
    > Probably about 80%, I did ask Claude to look over the code again and find edge cases to fix and I did try the program myself, but I am not entirely certain someone else could find an unexpected edge case.
- What edge cases would you test next if you had more time?
    > Juggling multiple owners, I didn't really focus on it this time.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
    > The program works and this is the first project I have completely vibecoded. Even if it was extensively supervised, I didn't have to agonize over how to design every minutia of it myself in my head, which was pretty satisfying. 

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
    > I would work some more on the UI, it's pretty barebones. Maybe have some way to pick between existing owners and existing pets instead of just entering them in and making sure you type them in the exact same way every time.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
    > AI will make mistakes that it won't tell you about (or doesn't realize), so make sure to go back at some point and ask it to scan over the code again for discrepancies and ask it about edge cases too.