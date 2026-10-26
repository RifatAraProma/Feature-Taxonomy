# Hosting history and current setup

## Current setup: free, permanent

Figures and data files are published as **GitHub Release assets** on this repository:
<https://github.com/RifatAraProma/Feature-Taxonomy/releases/latest>

- No paid service, no account needed to download, nothing that expires.
- GitHub allows 2 GB per release asset; every bundle is far below that.
- The paper's figures are additionally committed to [figures/](figures/) for direct viewing.
- See the [README](README.md#how-to-get-the-figures-or-data-files) for download instructions.

Bundles are built and uploaded by:

```bash
python scripts/package_release.py
python scripts/publish_release.py --tag v1.0.0
```

## Previous setup: retired

During development the project ran a hosted interactive web app:

- **Frontend** — React + Vega-Lite, deployed as a static site.
- **Backend** — Flask API (`server/`) for on-demand smoothing, deployed to a PaaS.
- **Assets** — a DigitalOcean Spaces bucket + CDN holding `precomputed/` (~85 GB,
  153k files) and `plots/` (~2 GB), referenced through `VITE_CDN_URL`.

That stack cost money every month, so after publication it was shut down in favour of the
free release archive above. The code still works locally — see
[Browsing interactively](README.md#browsing-interactively-optional-runs-locally).

The upload helpers `upload_to_spaces.py`, `upload_plots_to_spaces.py`,
`upload_data_to_spaces.py`, and `upload_datasets_json.py` remain in the repository for
reference, but are no longer part of the publishing path. They expect
`DO_SPACE_NAME`, `DO_REGION`, `DO_ACCESS_KEY`, and `DO_SECRET_KEY` in a local `.env`
file, which is not committed.

### Why `precomputed/` is not in the archive

At ~85 GB (about 21 GB compressed) it exceeds every free archive's limits and is more than
most readers need. It is regenerable from this repository — see
[What is not distributed](README.md#what-is-not-distributed). All published figures and
CSVs derive from it, so the results remain verifiable end to end.
