#!/usr/bin/env python3
"""Publish the packaged figure/data bundles to GitHub Releases (free hosting).

Reads release/manifest.json (written by package_release.py), creates or
updates a GitHub Release, uploads every bundle as a release asset, and prints
the permanent public download URLs to paste into the paper and README.

    python scripts/package_release.py
    python scripts/publish_release.py --tag v1.0.0
    python scripts/publish_release.py --tag v1.0.0 --dry-run

Requires the GitHub CLI (`gh auth login`) with `repo` scope.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = "RifatAraProma/Feature-Taxonomy"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, **kwargs)


def require_gh() -> None:
    if shutil.which("gh") is None:
        sys.exit("GitHub CLI not found. Install it from https://cli.github.com and run `gh auth login`.")
    if run(["gh", "auth", "status"]).returncode != 0:
        sys.exit("GitHub CLI is not authenticated. Run `gh auth login` first.")


def load_manifest(release_dir: Path) -> dict:
    manifest_path = release_dir / "manifest.json"
    if not manifest_path.exists():
        sys.exit(f"No manifest at {manifest_path}. Run `python scripts/package_release.py` first.")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def release_exists(repo: str, tag: str) -> bool:
    return run(["gh", "release", "view", tag, "-R", repo]).returncode == 0


def build_notes(manifest: dict, repo: str, tag: str) -> str:
    lines = [
        "Figures and data files for the paper **How to Simplify a Line Chart: "
        "A Visual Feature-Based Taxonomy and Evaluation**.",
        "",
        "These bundles replace the previously hosted interactive web app, so the "
        "material stays permanently available at no cost.",
        "",
        "| Bundle | Size | Contents |",
        "| --- | --- | --- |",
    ]
    for entry in manifest["bundles"]:
        lines.append(f"| `{entry['file']}` | {entry['size_human']} | {entry['summary']} |")

    base = f"https://github.com/{repo}/releases/download/{tag}"
    lines += [
        "",
        "### Verifying a download",
        "",
        "Every bundle's SHA-256 checksum is listed in `manifest.json` and `SHA256SUMS.txt`:",
        "",
        "```bash",
        f"curl -LO {base}/SHA256SUMS.txt",
        "sha256sum -c --ignore-missing SHA256SUMS.txt",
        "```",
        "",
        "`--ignore-missing` checks only the bundles you downloaded.",
        "",
        "### Not included",
        "",
        f"{manifest.get('note', '')}",
        "",
        f"See the [repository README](https://github.com/{repo}#readme) for full download "
        "and regeneration instructions.",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload figure/data bundles to a GitHub Release.")
    parser.add_argument("--tag", required=True, help="Release tag, e.g. v1.0.0")
    parser.add_argument("--repo", default=DEFAULT_REPO, help=f"owner/repo (default: {DEFAULT_REPO})")
    parser.add_argument(
        "--release-dir",
        type=Path,
        default=Path("release"),
        help="Directory holding the bundles and manifest.json (default: release/).",
    )
    parser.add_argument("--title", help="Release title (default: derived from the tag).")
    parser.add_argument(
        "--target",
        help="Branch or commit the new tag should point at (default: the repo's default branch).",
    )
    parser.add_argument(
        "--draft", action="store_true", help="Create the release as a draft for review before going public."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print what would be uploaded without touching GitHub."
    )
    args = parser.parse_args()

    release_dir = args.release_dir if args.release_dir.is_absolute() else ROOT / args.release_dir
    manifest = load_manifest(release_dir)

    assets: list[Path] = []
    for entry in manifest["bundles"]:
        path = release_dir / entry["file"]
        if not path.exists():
            sys.exit(f"Manifest lists {entry['file']} but it is missing from {release_dir}.")
        assets.append(path)
    for extra in ("manifest.json", "SHA256SUMS.txt"):
        path = release_dir / extra
        if path.exists():
            assets.append(path)

    title = args.title or f"Figures and data archive {args.tag}"
    notes = build_notes(manifest, args.repo, args.tag)
    base_url = f"https://github.com/{args.repo}/releases/download/{args.tag}"

    if args.dry_run:
        print(f"[dry-run] repo:  {args.repo}")
        print(f"[dry-run] tag:   {args.tag}")
        print(f"[dry-run] title: {title}")
        print("[dry-run] assets:")
        for path in assets:
            print(f"    {path.name}  ({path.stat().st_size / 1024**2:,.1f} MB)")
        print("\n[dry-run] release notes:\n")
        print(notes)
        return 0

    require_gh()

    notes_file = release_dir / "release_notes.md"
    notes_file.write_text(notes + "\n", encoding="utf-8")

    if release_exists(args.repo, args.tag):
        print(f"Release {args.tag} exists; updating notes and re-uploading assets.")
        edit = run(["gh", "release", "edit", args.tag, "-R", args.repo,
                    "--title", title, "--notes-file", str(notes_file)])
        if edit.returncode != 0:
            sys.exit(f"Failed to update release:\n{edit.stderr}")
    else:
        print(f"Creating release {args.tag} on {args.repo}...")
        cmd = ["gh", "release", "create", args.tag, "-R", args.repo,
               "--title", title, "--notes-file", str(notes_file)]
        if args.target:
            cmd += ["--target", args.target]
        if args.draft:
            cmd.append("--draft")
        created = run(cmd)
        if created.returncode != 0:
            sys.exit(f"Failed to create release:\n{created.stderr}")

    # Uploaded one at a time so a single large bundle failing doesn't hide the rest.
    for path in assets:
        size_mb = path.stat().st_size / 1024**2
        print(f"Uploading {path.name} ({size_mb:,.1f} MB)...")
        upload = run(["gh", "release", "upload", args.tag, str(path),
                      "-R", args.repo, "--clobber"])
        if upload.returncode != 0:
            print(f"  ! upload failed: {upload.stderr.strip()}", file=sys.stderr)
        else:
            print(f"  ok  {base_url}/{path.name}")

    print(f"\nRelease page: https://github.com/{args.repo}/releases/tag/{args.tag}")
    print("\nPublic download URLs (use these in the paper and README):")
    for path in assets:
        print(f"  {base_url}/{path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
