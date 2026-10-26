#!/usr/bin/env python3
"""Package the project's figures and data files into free-hosting release bundles.

The paper's figures and result files used to be served from a paid
DigitalOcean Spaces CDN behind a hosted web app. This script rebuilds the
same reader-facing material as a handful of ZIP bundles that fit inside
GitHub Releases' free limits (2 GB per asset), together with a manifest of
SHA-256 checksums so readers can verify what they downloaded.

    python scripts/package_release.py                  # all default bundles
    python scripts/package_release.py --only paper-figures csv-data
    python scripts/package_release.py --list

Deliberately NOT packaged: precomputed/ (~85 GB of per-level algorithm
output). It is regenerable with precompute_all_unified.py -- see README.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# GitHub refuses release assets larger than 2 GiB.
GITHUB_ASSET_LIMIT = 2 * 1024**3


@dataclass
class Bundle:
    """One downloadable ZIP in the release."""

    name: str
    summary: str
    # (source path relative to repo root, prefix inside the zip)
    sources: list[tuple[str, str]]
    extras: list[tuple[str, str]] = field(default_factory=list)

    @property
    def filename(self) -> str:
        return f"{self.name}.zip"


BUNDLES: list[Bundle] = [
    Bundle(
        name="paper-figures",
        summary="Every figure in the paper (SVG), plus the 12 visual-feature illustrations.",
        sources=[("supplemental_material/paper_figures", "paper_figures")],
    ),
    Bundle(
        name="grade-plots",
        summary="Grade heatmaps, histogram grids, deviation table, and per-metric histograms.",
        sources=[("supplemental_material/grade_plots", "grade_plots")],
    ),
    Bundle(
        name="dataset-visualizations",
        summary="Original time series rendered as SVG, for all 80 evaluated datasets.",
        sources=[("supplemental_material/dataset visualization", "dataset_visualizations")],
    ),
    Bundle(
        name="csv-data",
        summary="Aggregated grade statistics and per-dataset metric scores as CSV.",
        sources=[("supplemental_material/csv_data", "csv_data")],
    ),
    Bundle(
        name="source-datasets",
        summary="The input time series in JSON form, plus the datasets.json index.",
        sources=[("data", "data")],
        extras=[("datasets.json", "datasets.json")],
    ),
    Bundle(
        name="all-plots",
        summary="Full per-dataset plot set: rankings, PAE analyses, and metric curves for all datasets.",
        sources=[("plots", "plots")],
    ),
]

BUNDLES_BY_NAME = {bundle.name: bundle for bundle in BUNDLES}


def human(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:,.1f} {unit}"
        size /= 1024
    return f"{size:,.1f} GB"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_source_files(source: Path):
    """Yield files under `source`, skipping OS and editor cruft."""
    skip_names = {".DS_Store", "Thumbs.db"}
    for item in sorted(source.rglob("*")):
        if item.is_dir():
            continue
        if item.name in skip_names or item.name.endswith("~"):
            continue
        yield item


def build_bundle(bundle: Bundle, output_dir: Path) -> Path | None:
    """Zip one bundle. Returns the archive path, or None if nothing was found."""
    present = [(ROOT / rel, prefix) for rel, prefix in bundle.sources if (ROOT / rel).exists()]
    extras = [(ROOT / rel, arc) for rel, arc in bundle.extras if (ROOT / rel).exists()]

    missing = [rel for rel, _ in bundle.sources if not (ROOT / rel).exists()]
    for rel in missing:
        print(f"  ! missing source, skipped: {rel}")

    if not present and not extras:
        return None

    archive_path = output_dir / bundle.filename
    raw_bytes = 0
    file_count = 0

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for source, prefix in present:
            for item in iter_source_files(source):
                arcname = f"{prefix}/{item.relative_to(source).as_posix()}"
                archive.write(item, arcname=arcname)
                raw_bytes += item.stat().st_size
                file_count += 1
        for source, arcname in extras:
            archive.write(source, arcname=arcname)
            raw_bytes += source.stat().st_size
            file_count += 1

    zipped = archive_path.stat().st_size
    ratio = f"{raw_bytes / zipped:.1f}x" if zipped else "n/a"
    print(f"  {archive_path.name}: {file_count:,} files, {human(raw_bytes)} -> {human(zipped)} ({ratio})")

    if zipped > GITHUB_ASSET_LIMIT:
        print(
            f"  ! {archive_path.name} is {human(zipped)}, over GitHub's {human(GITHUB_ASSET_LIMIT)} "
            "per-asset limit. Split it or host this bundle on OSF instead."
        )

    return archive_path


def write_manifest(output_dir: Path, built: list[tuple[Bundle, Path]]) -> Path:
    entries = []
    for bundle, path in built:
        entries.append(
            {
                "file": path.name,
                "bundle": bundle.name,
                "summary": bundle.summary,
                "size_bytes": path.stat().st_size,
                "size_human": human(path.stat().st_size),
                "sha256": sha256_file(path),
            }
        )

    manifest = {
        "project": "How to Simplify a Line Chart: A Visual Feature-Based Taxonomy and Evaluation",
        "repository": "https://github.com/RifatAraProma/Feature-Taxonomy",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": (
            "precomputed/ (~85 GB of per-level algorithm output) is not distributed; "
            "regenerate it with precompute_all_unified.py as described in the README."
        ),
        "bundles": entries,
    }

    # Both files are published artifacts that readers consume on Linux/macOS, so they
    # are written with LF endings explicitly -- CRLF would make `sha256sum -c` reject
    # every line when this script runs on Windows.
    manifest_path = output_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2) + "\n")

    # A plain checksum file so readers can run `sha256sum -c SHA256SUMS.txt`.
    sums_path = output_dir / "SHA256SUMS.txt"
    with sums_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.writelines(f"{entry['sha256']}  {entry['file']}\n" for entry in entries)

    print(f"  manifest.json and SHA256SUMS.txt written to {output_dir.name}/")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Package figures and data files for free hosting on GitHub Releases."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("release"),
        help="Where the bundles are written (default: release/).",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="BUNDLE",
        help="Build only these bundles (see --list for names).",
    )
    parser.add_argument(
        "--skip",
        nargs="+",
        metavar="BUNDLE",
        default=[],
        help="Build everything except these bundles.",
    )
    parser.add_argument("--list", action="store_true", help="List bundle names and exit.")
    args = parser.parse_args()

    if args.list:
        print("Available bundles:\n")
        for bundle in BUNDLES:
            print(f"  {bundle.name:<24} {bundle.summary}")
        return 0

    unknown = {name for name in (args.only or []) + args.skip} - set(BUNDLES_BY_NAME)
    if unknown:
        print(f"Unknown bundle(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        print(f"Known: {', '.join(BUNDLES_BY_NAME)}", file=sys.stderr)
        return 2

    selected = [BUNDLES_BY_NAME[name] for name in args.only] if args.only else list(BUNDLES)
    selected = [bundle for bundle in selected if bundle.name not in args.skip]

    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Packaging {len(selected)} bundle(s) into {output_dir}\n")

    built: list[tuple[Bundle, Path]] = []
    for bundle in selected:
        print(f"{bundle.name}:")
        archive_path = build_bundle(bundle, output_dir)
        if archive_path is None:
            print("  nothing to package, skipped")
            continue
        built.append((bundle, archive_path))

    if not built:
        print("\nNo bundles were built. Generate the outputs first, then re-run.", file=sys.stderr)
        return 1

    print("\nChecksums:")
    write_manifest(output_dir, built)

    total = sum(path.stat().st_size for _, path in built)
    print(f"\nDone: {len(built)} bundle(s), {human(total)} total.")
    print("Next: python scripts/publish_release.py --tag v1.0.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
