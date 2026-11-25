# Viva Defense Playbook Template

Use `docs/05_viva_prep.md` as the current detailed guide. Customize team roles
and timing without changing measured evidence.

## Team Ownership

Every member should understand both paradigms. Suggested roles:

| Role | Responsibility |
|---|---|
| Design and OOP | Geometry, coordinate model, classes, rule walkthrough |
| Functional and parity | State dictionary, function pipeline, canonical snapshots |
| Testing and demonstration | Unit/parity evidence, CLI/GUI demo, peer reports |

## Demonstration Rules

- Run the fast unit suite live; the complete 1,080-game verifier takes several
  minutes.
- Show recorded verifier output rather than claiming a live full-gate pass.
- Use identical seed and decisions when comparing implementations.
- Ignore only intentional `OOP:`/`Functional:` code-trace wording when comparing
  transcripts.
- Do not show v2 peer improvements until genuine reports and changes exist.
- Do not claim visual GUI testing unless a human actually performed it.

## High-Probability Questions

1. How does personal `steps` map to the shared track and private home lane?
2. How is the zero-class functional constraint enforced recursively?
3. Why are turn-cap and mutual-agreement draws both supported?
4. How do strict and safe-pair blockades differ?
5. Why does Kill-to-Enter loop instead of holding at the gate?
6. How does Podium Mode skip finished players?
7. Why is each game's `random.Random(seed)` isolated?
8. Why does `apply_move()` own post-move turn resolution?
9. Why are shared contracts acceptable but a shared rules engine rejected?
10. How do canonical snapshots prove parity after every action?

## Capstone Prompt

> If AI can generate both versions of a program, why is it important for a
> programmer to understand programming concepts and design?

Anchor the answer in real invariants, independent implementations, test
failures, root-cause fixes, and the ability to explain and safely extend code.
