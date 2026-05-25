---
name: write-a-spec
description: Create one or more governing project specificiation documents through user interview, codebase exploration, and module design, then submit as a GitHub issue. Use when user wants to write a spec or update an existing spec or other governing project document.
---

This skill will be invoked when the user wants to create or update a specification document. You may skip steps if you don't consider them necessary.

1. Ask the user for a long, detailed description of the problem they want to solve and any potential ideas for solutions.

2. Explore the repo to verify their assertions and understand the current state of the codebase.

3. Interview the user relentlessly about every aspect of this plan until you reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.

4. Sketch out the major modules you will need to build or modify to complete the implementation. Actively look for opportunities to extract deep modules that can be tested in isolation.

A deep module (as opposed to a shallow module) is one which encapsulates a lot of functionality in a simple, testable interface which rarely changes.

Check with the user that these modules match their expectations. Check with the user which modules they want tests written for.

5. Once you have a complete understanding of the problem and solution, use the template files below to write/update SPEC.md, SCHEMAS.md, and ARCHITECTURE.md.  SCHEMAS.md and SPEC.md should be marked as frozen, with changes only permitted with direct user approval. ARCHITECTURE.md should be marked as a living document, with changes permitted as long as they are documented in the changelog.
-`templates/ARCHITECTURE.template.md`
-`templates/SCHEMAS.template.md`
-`templates/SPEC.template.md`

6. The completed documents should be stored in the `docs/` directory of the repo or relevant project folder.