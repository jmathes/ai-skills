Expected input:

"""
accepted\n
Feb 19, 1999\n
Milton\n
The Bobs\n
Lumburgh, Michael Bolton\n
I believe you have my stapler\n
I like my red swing line stapler. Bill Lumburgh took my stapler. What do I do about it?\n
I like my stapler.\n
I'll burn the building down.\n
\n
Ask for my stapler.\n
Burn down the building.\n
Really, I'll burn down the building.\n
\n
Burn it down\n
I warned him and he didn't listen.\n
They'll take me seriously or at least I'll feel better\n
Burning building\n
It's polite\n
He'll ignore me\n
\n
I tried to be polite\n
He ignored me\n
I'll burn the building down\n
\n
I warned him\n
\n
"""

Expected result:
"""

---
status: accepted
date: Feb 19, 1999
decision-makers: Milton
consulted: The Bobs
informed: Lumburgh, Michael Bolton
---

# I believe you have my stapler

## Context and Problem Statement

I like my red swing line stapler. Bill Lumburgh took my stapler. What do I do about it?

## Decision Drivers

- I like my stapler.
- I'll burn the building down.

## Considered Options

- Ask for my stapler.
- Burn down the building.
- Really, I'll burn down the building.

## Decision Outcome

- Chosen option: Burn it down, because I warned him and he didn't listen. (see below)

### Consequences

- They'll take me seriously or at least I'll feel better

### Confirmation

- Burning building

## Pros and Cons of the Options

### Ask for my stapler.

- It's polite
- He'll ignore me

### Burn down the building.

- I tried to be polite
- He ignored me
- I'll burn the building down

### Really, I'll burn down the building.

- I warned him
