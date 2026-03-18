---
status: <<< What is the status of this ADR? ex: proposed | rejected | accepted | deprecated | superseded by ADR-0123 [[default: proposed]] >>>
date: <<< What is the current date? [[default: {YYYY-MM-DD}]] >>>
decision-makers: <<< Who is involved in making the decision? [[default: {env.$USER}]] >>>
consulted: <<< [[OPTIONAL]] Whose opinions matter? Who was/will be consulted? >>>
informed: <<< [[OPTIONAL]] Who should be kept in the loop? >>>
---

# <<< TITLE | Give a short title, representative of solved problem and found solution >>>

## Context and Problem Statement

<<< CONTEXT | Describe the context and problem statement, e.g., in free form using two to three sentences or in the form of an illustrative story. You may want to articulate the problem in form of a question and add links to collaboration boards or issue management systems. >>>

## Decision Drivers

- <<< DRIVERS [[REPEATED]] | Name a decision driver, e.g., a force, facing concern, >>>

## Considered Options

- <<< OPTIONS [[REPEATED]] | Name a potential solution // option and give a brief description. Do not mention (or worry about) pros and cons yet. >>>

## Decision Outcome

- Chosen option: <<< CHOICE | What is the TITLE of the option you chose? >>>, because <<< Give a brief justification >>> option did you choose? Why? >>> (see below)

### Consequences

- <<< CONSEQUENCES | Give a brief summary of the EXPECTED pros and cons of this option - this is a prediction, not a retrospective to be filled in later >>>

### Confirmation

- <<< CONFIRMATION | Describe how the implementation of/compliance with the ADR can/will be confirmed. This is NOT how we will confirm that the decision worked as intended - it's how we will validate that it was IMPLEMENTED as intended. >>>

## Pros and Cons of the Options
<<< FOREACH $OPTIONS$ as "$OPTION" >>>
### <<< $OPTION >>>

- <<< [[REPEATED]] | Name a pro or con for {$OPTION} >>>
