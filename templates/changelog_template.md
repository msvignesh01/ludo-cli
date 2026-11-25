# Changelog Template — Peer-Driven v2

Use this file only after genuine peer feedback produces accepted v2 changes.
Copy it to `v2_final/CHANGELOG.md` and replace every placeholder with real
evidence. Do not prefill pass results.

## Source Reports

- **Peer Team 1 report:** [Path and date]
- **Peer Team 2 report:** [Path and date]
- **Accepted findings:** [IDs]
- **Rejected/deferred findings and reasons:** [IDs and reasons]

## Changes

| ID | Source report | Severity/type | Observed issue | OOP change | Functional change | Regression test |
|---|---|---|---|---|---|---|
| CHG-01 | [Report/finding] | [Enter] | [Real reproduction] | [File/method] | [File/function] | [Test name] |

## Verification

Record only observed commands and results:

- **Command:** `python scripts/verify_gates.py --stage v2`
- **Exit code:** [Enter]
- **Unit/regression tests:** [Enter count and result]
- **Parity games and snapshots:** [Enter measured result]
- **Subprocess CLI result:** [Enter measured result]
- **AST/import audit:** [Enter measured result]
- **Failures and warnings:** [Enter measured result]

## Baseline Preservation

- **v1 handoff date:** [Enter]
- **Evidence v1 remained unchanged:** [Enter comparison method/result]
