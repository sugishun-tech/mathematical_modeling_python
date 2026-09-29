# Changelog

## 2.0.0 — textbook-driven reconstruction

Rebuilt the nine chapter notebooks around 44 numbered examples, with original English problem statements, assumptions, units, explanatory method notes, calculations, checks, and limitations. Split long calculations into executable blocks without interrupting a partially constructed figure. Removed the original dismissive asides.

Centralized repeated iteration, optimization, dynamic systems, stationary distributions, Monte Carlo, particle tracking and forecast calculations in `modeling/`. Added explicit failure and censoring behavior instead of global runtime-warning suppression. Each chapter now runs in a fresh kernel and records source/model/data hashes; failed runs do not overwrite successful notebooks.

Corrected integer-farm field coefficients and the resulting objective/gap; distinguished local and global chair-model claims; exposed the inconsistent truck-route distance; corrected the large-step whale parameter, positive-coexistence range, variable wind field, first-passage indexing, forecast uncertainty and tracer activity units. Added independent enumeration, analytic checks, invariant checks and boundary tests.

Added a complete numbered-example and exercise inventory. The main archive has no end-exercise solution claims. A separate source study bundle provides 164 original exercise statements and selected supporting pages as embedded images, with an explicit third-party-content notice.

Added offline HTML with static SVG mathematics, browser rendering checks, source/provenance reports and plot review evidence. Separated convergent and divergent curves that previously made the stable behavior unreadable, separated crowded large-step whale traces, and adjusted the 3-D view to keep axis labels visible.

Added the full historical mortgage-index table, automated project audits, documented dependencies, local commands, and an actual GitHub Actions workflow. Remote CI was not run during delivery. All change history is kept in this single file; there are no per-change UPDATE files.
