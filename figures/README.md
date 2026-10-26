# Paper figures

Every figure from *How to Simplify a Line Chart: A Visual Feature-Based Taxonomy and
Evaluation*, as SVG. Click any file to view it rendered in the browser.

These same files are also packaged as `paper-figures.zip` in the
[latest release](https://github.com/RifatAraProma/Feature-Taxonomy/releases/latest), along
with the grade plots, dataset visualizations, and CSV data. See the
[repository README](../README.md#how-to-get-the-figures-or-data-files) for all download
options.

| Figure | File(s) | Shows |
| --- | --- | --- |
| Fig 1 | [Fig 1.svg](Fig%201.svg) | The visual feature taxonomy. |
| Fig 2 | `Fig 2 input.svg`, `Fig 2 gaussian.svg`, `Fig 2 chebyshev.svg`, `Fig 2 douglas-peucker.svg`, `Fig 2 paa.svg`, `Fig 2 uniform-subsample.svg`, `Fig 2 asap.svg` | The same series simplified by one algorithm from each family. |
| Fig 3 a–c | `Fig 3 a.svg` … `Fig 3 c.svg` | Algorithm consistency: histogram, deviation table, cross-dataset comparison. |
| Fig 4 a–i | `Fig 4 a.svg` … `Fig 4 i.svg` | Feature preservation examples across nine cases. |
| Fig 5 a–c | `Fig 5 a.svg` … `Fig 5 c.svg` | Cross-dataset performance analysis. |
| Fig 6 a–c | `Fig 6 a.svg` … `Fig 6 c.svg` | Algorithm recommendations by use case. |

## Feature illustrations

[`feature illustrations/`](feature%20illustrations/) illustrates each of the 12 visual
features the taxonomy defines, one SVG per feature: `level`, `extrema`,
`regime_change_points`, `spikes_dips`, `slope`, `curvature`, `roughness`, `trend`, `noise`,
`periodicity`, `mean`, and `regression_fit`.

## Regenerating

The figures are produced from precomputed algorithm output by the `generate_*.py` scripts in
the repository root — for example `generate_algorithm_metric_histogram_grid_mode.py` for the
consistency histogram grid and `generate_mode_grade_heatmaps.py` for the grade heatmaps. See
[Reproducing the analysis](../README.md#reproducing-the-analysis).
