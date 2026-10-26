# How to Simplify a Line Chart: A Visual Feature-Based Taxonomy and Evaluation

Code, figures, and data for the paper *How to Simplify a Line Chart: A Visual Feature-Based
Taxonomy and Evaluation* — a framework that evaluates how 20+ smoothing, reduction, and
aggregation algorithms preserve visual features in line charts, across 80 real-world time
series and 21 feature-preservation metrics.

> **Note on hosting.** The figures and results were previously browsable through an
> interactive web app backed by a paid CDN. That deployment has been retired. Everything
> it served is now published permanently and free of charge as **[GitHub
> Release assets](https://github.com/RifatAraProma/Feature-Taxonomy/releases/latest)** —
> no account, no sign-up, and nothing that can lapse when a subscription ends.

## How to get the figures or data files

All figures and data files are attached to the
**[latest release](https://github.com/RifatAraProma/Feature-Taxonomy/releases/latest)**.
Download the bundle you need — in the browser, or from the command line:

```bash
# A single bundle (always resolves to the newest release)
curl -LO https://github.com/RifatAraProma/Feature-Taxonomy/releases/latest/download/paper-figures.zip

# Or everything at once, with the GitHub CLI
gh release download --repo RifatAraProma/Feature-Taxonomy --pattern '*.zip'
```

### What's in each bundle

| Bundle | Size | Contents |
| --- | --- | --- |
| `paper-figures.zip` | ~1 MB | Every figure in the paper as SVG (Fig 1–6), plus illustrations of the 12 visual features. |
| `grade-plots.zip` | ~1 MB | Grade heatmaps, the algorithm × metric histogram grid, the deviation table, and per-metric histograms. |
| `dataset-visualizations.zip` | ~1 MB | The original time series rendered as SVG, for all 80 evaluated datasets. |
| `source-datasets.zip` | ~0.5 MB | The input time series as JSON, plus the `datasets.json` index. |
| `csv-data.zip` | see release | Aggregated grade statistics and per-dataset metric scores as CSV — the numbers behind the tables. |
| `all-plots.zip` | see release | The complete per-dataset plot set: rankings, PAE analyses, and metric curves. |

Start with `paper-figures.zip` if you want the figures as published, and `csv-data.zip` if you
want the underlying numbers.

The figures from the paper are **also committed directly to this repository** under
[figures/](figures/), so they render in the browser and have stable permalinks without
downloading anything.

### Verifying a download

Each release includes `manifest.json` and `SHA256SUMS.txt` with a SHA-256 checksum for
every bundle:

```bash
curl -LO https://github.com/RifatAraProma/Feature-Taxonomy/releases/latest/download/SHA256SUMS.txt
sha256sum -c SHA256SUMS.txt
```

### What is not distributed

The intermediate `precomputed/` tree — every algorithm's output at all 100 smoothing levels
for all 80 datasets — is roughly **85 GB**, too large for any free archive and larger than
most readers need. It is fully reproducible from the code in this repository:

```bash
# One dataset
python precompute_all_unified.py stock_aapl_price

# A whole category, 4 algorithms at a time
python precompute_all_unified.py stock_price --dir --parallel 4
```

Every published figure and CSV in the release bundles is derived from that output, so the
results can be checked end to end without downloading it.

## Repository layout

| Path | Description |
| --- | --- |
| [figures/](figures/) | The paper's figures (SVG), committed for direct viewing. |
| `data/` | Input time series as JSON (`{"id": "...", "y": [...]}`) plus `datasets.json`. |
| `server/` | Flask API: loads series, runs algorithms, computes 45° banking, features, and metrics. |
| `web/` | React + Vega-Lite frontend for exploring original vs. simplified charts. |
| `scripts/` | Packaging and publishing tooling for the public figure/data archive. |
| `precompute_*.py` | Batch precomputation of algorithm outputs and preservation metrics. |
| `grade_algorithms.py`, `rank_algorithms_*.py` | Grading and ranking analyses. |
| `generate_*.py` | Figure generation for the paper and supplemental material. |

## Reproducing the analysis

```bash
python -m venv .venv && .venv\Scripts\activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python precompute_all_unified.py stock_price --dir --parallel 4   # 1. algorithm outputs + metrics
python grade_algorithms.py                                        # 2. per-metric letter grades
python aggregate_mode_grades.py                                   # 3. aggregate across datasets
python generate_algorithm_metric_histogram_grid_mode.py           # 4. paper figures
```

### Browsing interactively (optional, runs locally)

The web UI is no longer hosted, but it still runs on a local machine against locally
generated output:

```bash
# Backend
pip install -r requirements.txt
python -m flask --app server.app run        # API at http://127.0.0.1:5000

# Frontend
cd web && npm install && npm run dev        # UI at http://127.0.0.1:5173
```

With no `VITE_CDN_URL` set, the frontend reads plots and precomputed data from local paths
served by the Flask backend.

## Publishing a new version of the archive (maintainers)

```bash
python scripts/package_release.py                      # build bundles into release/
python scripts/package_release.py --list               # show available bundles
python scripts/publish_release.py --tag v1.0.0 --dry-run
python scripts/publish_release.py --tag v1.0.0         # upload to GitHub Releases
```

`package_release.py` writes the ZIP bundles plus `manifest.json` and `SHA256SUMS.txt`, and
warns if any bundle exceeds GitHub's 2 GB per-asset limit. `publish_release.py` creates or
updates the release, uploads every asset, and prints the public download URLs. Both are
free to run and require only an authenticated [GitHub CLI](https://cli.github.com).

## Citation

If you use this taxonomy, the evaluation framework, or the published figures and data,
please cite the paper. A `CITATION.cff` entry will be added once the final publication
details are available.
