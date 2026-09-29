# Source notes

Primary source: Mark M. Meerschaert, *Mathematical Modeling*, fourth edition, Academic Press, 2013, ISBN 978-0-12-386912-8. The work was based on the supplied 368-page PDF, not a different edition or a secondary summary.

The PDF is not redistributed in the main code archive. Its SHA-256 fingerprint and 1-based file-page references are recorded in `reports/source_inventory.json`. The PDF omits some blank pages, so a single offset does not consistently convert file pages into printed page labels.

The nine main notebooks contain original English restatements, model equations, code, explanations and newly computed plots. Their purpose is to make the **implemented central examples** understandable without separately opening the book. They are not an exhaustive replacement for the book's exposition or a complete exercise solutions manual.

The optional source exercise study bundle preserves the original English statements as embedded raster images. This avoids inventing corrupted LaTeX from PDF text extraction, but those images are not searchable mathematical transcriptions. The source excerpts remain textbook content and are outside the MIT license. Permission to publish them has not been established, which is why they are distributed separately from the code archive.

The full mortgage table is transcribed into `data/mortgage_indices.csv`; `data/cm1.csv` retains the existing CM1-only interface. All 37 CM1 values and dates agree between the two files. A source-table page render was generated for inspection. Additional historical values are data for textbook study, not current economic observations.

The author's official correction list and further model discrepancies are discussed in `ERRATA.md`. Additional modern diagnostics—solver status checks, fresh kernels, uncertainty intervals, horizon censoring, and multi-step forecast variance—are identified as verification or modeling choices rather than attributed to a nonexistent complete textbook implementation.

## Software references

Numerical optimization uses the official [SciPy `milp` interface](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html), together with independent enumeration where the example is small enough. Static HTML mathematics is generated with MathJax SVG output; only generated SVG paths are included, not font files or a bundled dependency installation.

## Citation

```bibtex
@book{meerschaert2013mathematical,
  title = {Mathematical Modeling},
  author = {Meerschaert, Mark M.},
  edition = {4},
  year = {2013},
  publisher = {Academic Press},
  isbn = {978-0-12-386912-8}
}
```
