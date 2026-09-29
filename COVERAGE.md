# Coverage and verification scope

Coverage is recorded at different levels. A source item being listed is not evidence that it has been solved, executed, or independently verified.

## Reconciled numbered items

| Chapter | Instructional sections | Numbered examples reconstructed | End exercises inventoried |
|---|---:|---:|---:|
| 1 | 3 | 1 | 9 |
| 2 | 3 | 5 | 10 |
| 3 | 4 | 7 | 24 |
| 4 | 3 | 4 | 11 |
| 5 | 3 | 4 | 16 |
| 6 | 4 | 6 | 27 |
| 7 | 4 | 5 | 18 |
| 8 | 4 | 6 | 20 |
| 9 | 5 | 6 | 29 |
| **Total** | **33** | **44** | **164** |

The exercise counts exclude the numbered bibliographic entries under “Further Reading.” Chapter 8 ends with exercise 20, not 21.

## Meaning of the statuses

**Worked example:** an original English problem statement and a reconstruction of the central model, with assumptions, computations, checks, and interpretation. Execution status is in `reports/execution.json`. This does not certify every printed subsidiary calculation, figure, sensitivity scenario, or robustness analysis belonging to that example.

**Instructional section:** the topic is represented in its chapter notebook. This is a topic map, not a paragraph-by-paragraph reconstruction.

**Exercise statement only:** the problem is mapped to its source pages. Its complete original statement is in the separate source study bundle. **No exercise solution is claimed.** All lettered subparts still need to be solved and checked before an exercise can be marked complete. Selected supporting pages are included, but the study bundle does not reproduce all cross-referenced textbook exposition.

**Other source label:** automatic extraction detected a numbered equation, figure caption, or table caption. These labels are catalogued to expose the remaining scope. They have not all been individually reproduced, visually compared, or mathematically verified. Automatic label detection is not a proof that every printed label was found.

## What the audit found

The original project implemented selected representative models and omitted several numbered examples and the end-of-chapter exercise statements. The revised notebooks include the sphere/circle multiplier examples, the board-shortage case, transportation and truck assignment, the type-I counter, the continuous-time chain example, stochastic docking, and explicit boundary/stability cases.

The source audit also detected distinctions that a passing notebook cannot resolve: a global-optimum claim is invalid for the unconstrained chair-price model; two truck-route tables disagree about a distance; the tracer activity and threshold units cannot simply be equated; and a finite simulation does not establish a global safety statement. See `ERRATA.md` for the assumptions used.

## Remaining work, not hidden as “covered”

The 164 exercise solutions and their subparts remain unimplemented. Full one-to-one reproduction and verification of the book's equation sequence, figures, printed software reports, and all sensitivity/robustness studies are also incomplete. The automatic source inventory contains 227 equation labels, 180 figure labels, and 14 table labels; these are **detected labels**, not verified-result counts.

Some checks are deliberately limited. Facility location uses several numerical candidates, not a certified global lower bound. Chaotic long-time paths are not compared point by point. Fractional transport is a finite-step particle approximation rather than a complete convergence proof for the fractional PDE. Forecast intervals condition on fitted parameters. These limits are stated in the notebooks.

## Machine-readable records

`reports/source_inventory.json` contains the source PDF hash, page convention, example references, all exercise identifiers, section map, and detected other labels. `reports/coverage.csv` provides a flat table. Source references use **1-based PDF file pages**, which differ from printed page numbers in this PDF.

Use the inventory to extend the project: add the original problem formulation, implement every requested subpart, supply appropriate checks, execute in a fresh kernel, inspect the rendering, and only then update its status. A new assertion should validate a meaningful independent property, not merely repeat a number computed by the same algorithm.
