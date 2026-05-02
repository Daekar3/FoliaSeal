---
name: dev-loop
description: Work through a development loop to complete a slice of a task or project using various skills. Use when you want to implement a specific feature, fix a bug, or complete a portion of a larger task or project; also use when the user wants to engage in a development loop (dev loop, DevLoop) to iteratively work on a task or project.
---

# Dev Loop (DevLoop) Process

## Identify the Task or Project
Determine the next logical step or slice of the task or project to work on. This could be a specific feature, bug fix, or portion of a larger task or project.  Sometimes the user will specify what to work on, but if not, use your judgment to identify the most appropriate next step.

## Write an ExecPlan
Use the $write-execplan skill to create an execution plan for the identified task or project slice.

## Execute the Plan
Follow the steps outlined in the ExecPlan to work through the development loop. This may involve writing code, testing, debugging, and iterating as needed to complete the task or project slice.  Make sure you remember that the ExecPlan is a living document and may need to be updated as you progress. Use the $tdd skill where appropriate.

## Write a Git Commit
Once the ExecPlan has been executed and the task or project slice is complete, use the $write-git-commit skill to create a Git commit that documents the changes made during the implementation of the task or project slice.

## Review Compliance with Requirements
After committing your first pass, review `docs/ARCHITECTURE.md` and any other specifications or requirements in `docs/` to ensure that your implementation aligns with the overall architecture and requirements of the project. If there are any discrepancies or areas for improvement, use $write-execplan to create a new child ExecPlan to address these issues, implement the plan in accordance with `## Execute the Plan` above, write a git commit in accordance with `## Write a Git Commit` above, and repeat the development loop as needed until the implementation is compliant with the requirements.

## Update Documentation
If there are any relevant updates to documentation that need to be made as a result of the changes implemented during the development loop, update them. This review must include updating README files, architecture documentation using the $architecture-steward skill, and any other relevant documentation in the `docs/` directory.

## Report Outcomes
After completing the development loop, report the outcomes to the user. The report must have the sections below:

### Summary of Changes
Provide a summary of the changes made during the development loop, including a brief description of the feature implemented, bug fixed, or portion of the task or project completed. This should be a high-level overview that gives the user a clear understanding of what was accomplished during the development loop.

### Status of ExecPlan
Report on the status of the ExecPlan, including whether it was completed successfully, whether any steps were modified or added during the implementation, and whether any additional iterations of the development loop are needed to fully complete the task or project slice.

### Status of Architectural Compliance Review
First report on the compliance/noncompliance of the initial commit to `docs/ARCHITECTURE.md` and other requirements defined in `docs/`, and then report on the compliance/noncompliance of any subsequent commits made to address any issues identified in the initial review.

### Documentation Updates Made
Report on changes made to documentation, including README files, architecture documentation, and any other relevant documentation in the `docs/` directory.

### Next Steps and Recommendations
Make sure that your next steps or recommendations are clear and actionable, that they align with the overall goals and requirements of the project, and that they are suitable input for writing the next ExecPlan. If there are any outstanding issues or areas for improvement, make sure to highlight them in your report to the user, including recommendations on when to use $improve-codebase-architecture.
