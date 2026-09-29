# Corrections, source discrepancies, and modeling choices

The supplied fourth-edition PDF was checked against the author's [official errata](https://www.stt.msu.edu/~mcubed/ErrataMathModel4ed.pdf), linked from his [book page](https://www.stt.msu.edu/~mcubed/modeling.html). Not every erratum corresponds to an implemented computation; this file records those material to the revised examples.

## Corrections used in computations

| Item | Treatment in this project |
|---|---|
| Pig-price units | Numerical prices such as 0.65 are dollars per pound, not cents per pound. |
| Example 3.6, 120-acre fields | Water coefficients are 360, 120, 180; labor coefficients are 96, 24, 36. The 25-acre coefficients are unchanged. |
| Example 3.7, loading times | Use 20 minutes for the small truck and 30 for the large truck. |
| Figure 5.6 | The resistor/capacitor labels in the source diagram are interchanged. Equations use the physical meanings of R and C. |
| Example 7.4 | The corrected textbook-style integer range ends at 199, not 198. |
| Example 9.6 | Released activity is 540 mCi = 0.54 Ci, not 540 Ci. |

For the corrected farm constraints, independent enumeration, a MILP solver and the educational branch-and-bound routine agree on an objective of **USD 162,250**. The divisible-acreage LP gives USD 162,500. The integer gap is therefore **USD 250**. Using the original incorrect field coefficients creates a different feasible set, not just a rounded answer.

## Additional source/model issues found by calculation

### Chair production: local does not mean global

Example 3.3 includes a term proportional to `x * y**(-0.2)`. For fixed positive x, that term diverges as y approaches zero from above. The textbook's positive-domain objective is unbounded even though the interior stationary point has a negative-definite Hessian. The notebook identifies a **local maximum**, demonstrates the boundary failure, and does not invent a global solution by silently imposing a lower bound.

### Truck-route distance disagreement

The transportation distance table gives source 4 to destination D as 2 miles, whereas the later route table uses 4 miles for route 5. The truck example first uses its own route table and then recomputes the assignment using the earlier distance. The resulting best savings with three large trucks are USD 1,000 and USD 760 respectively. Both assumptions are visible.

### Coexistence and stability

For the tree model parameterization `b_i = q a_i`, positive coexistence also exists above `q = 5/3`, not only below `q = 0.6`. The high-competition interior equilibrium is a saddle. Feasibility and stability are separate questions, and the singular/boundary cases are not classified by dividing through a zero denominator.

### Large-step whale example

The source's large-step Euler experiment starts with competition coefficient `1e-8`, whereas other whale examples use `1e-7`. The revised chapter distinguishes those parameter sets. Artificial oscillations from the discrete approximation are not attributed to the original continuous-time biological model.

### Wind after the town

The source wind is 3 km/hour outside the interval from 0 to 20 km, and `8 - 0.5*abs(x - 10)` inside it. It rises toward the town and falls beyond it. A clipped increasing ramp would instead remain at 8 km/hour after town. The revised function and its boundary cases are tested.

### Activity versus concentration

A total activity must be divided by a spatial observation width before it becomes a one-dimensional concentration. The fractional example uses 540 mCi and a 10-meter bin. For comparison of the numerical curve, it **explicitly interprets** the threshold as 2 mCi/m; that is a modeling choice, not a separately verified physical threshold. A literal threshold of 2 Ci/m would exceed the maximum possible 10-meter-bin average with only 0.54 Ci total activity. Radioactive decay and transverse dilution are not included. No real-world safety recommendation follows from this example.

### Stochastic and numerical conventions

The first-passage sum starts at X1; X0 only initializes the transition rate. Stochastic docking stores the previous acceleration and reports incomplete trials; rejection of negative Gaussian time draws is explicitly identified as a model modification. Multi-step AR(1) intervals propagate innovation variance, but still condition on fitted coefficients. Particle-count intervals are pointwise and do not include time-step error, parameter uncertainty, or the selection bias of a reported sample maximum.

Original images in the optional exercise bundle retain the original printing. They are not silently retouched to erase these distinctions.
