# Architecture Review Checklist

Use this checklist before finalizing architecture documentation changes.

## Accuracy

- [ ] Every major claim is supported by code, tests, existing docs, or marked as inferred.
- [ ] The document describes current behavior separately from intended behavior.
- [ ] Known mismatches between code and docs are called out.
- [ ] No obsolete component descriptions remain.

## Structure

- [ ] Major directories are mapped.
- [ ] Major components have clear responsibilities.
- [ ] Ownership boundaries are explicit.
- [ ] Cross-component interactions are described.
- [ ] Dependency direction is documented.
- [ ] Forbidden dependencies are documented where relevant.

## Contracts

- [ ] Public APIs are documented.
- [ ] File formats are documented.
- [ ] Configuration surfaces are documented.
- [ ] Persistence schemas are documented.
- [ ] External integrations are documented.
- [ ] Error behavior is documented where it forms part of a contract.
- [ ] Backward compatibility expectations are documented.

## Object model

- [ ] Important domain objects are listed.
- [ ] DTOs, entities, commands, events, services, or adapters are listed where relevant.
- [ ] Ownership of object creation and mutation is clear.
- [ ] Serialization/deserialization behavior is documented where relevant.

## Maintainability

- [ ] Architectural debt is named plainly.
- [ ] Open questions are separated from settled design.
- [ ] User feedback is requested for unresolved design choices.
- [ ] The change log was updated.
- [ ] The document is concise enough to remain usable.