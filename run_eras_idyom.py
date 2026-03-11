#!/usr/bin/env python3
"""
run_eras_idyom.py

For every consecutive pair of 5-year windows produced by organize_midis.py,
trains IDyOM on the first window and evaluates surprisal on the second.
Results from each pair are saved as a pickle file.

Usage:
    python3 run_eras_idyom.py [OPTIONS]

Examples:
    python3 run_eras_idyom.py
    python3 run_eras_idyom.py -d midis_by_5yr_window -r my_results
    python3 run_eras_idyom.py --base_dir midis_by_5yr_window --step 2
"""

import argparse
import csv
import os
import pickle
import re
import subprocess
import sys
import time
from pathlib import Path


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run IDyOM over sliding 5-year MIDI windows.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_option = parser.add_argument  # alias for familiarity
    parser.add_argument("-d", "--base_dir",   default="midis_by_5yr_window",
                        help="Folder containing the YYYY-YYYY subfolders")
    parser.add_argument("-m", "--models_dir", default="models",
                        help="Directory where IDyOM stores trained models")
    parser.add_argument("-o", "--out_dir",    default="out",
                        help="Directory where IDyOM writes output files")
    parser.add_argument("-r", "--results_dir",default="results",
                        help="Destination directory for pickle result files")
    parser.add_argument("-s", "--step",       default=1, type=int,
                        help="Step size used when building windows (informational)")
    return parser.parse_args()


# ── Model cleanup ─────────────────────────────────────────────────────────────

def handle_existing_models(models_dir: Path) -> None:
    """Prompt user to delete any .model files found in models_dir."""
    if not models_dir.is_dir():
        print(f"No models directory found at '{models_dir}' — nothing to clean.")
        return

    model_files = list(models_dir.glob("*.model"))
    if not model_files:
        print(f"No existing models found in '{models_dir}'.")
        return

    print(f"\nFound {len(model_files)} model file(s) in '{models_dir}':")
    for mf in model_files:
        print(f"  {mf.name}")

    answer = input("\nDelete these models before running? (Y/N): ").strip()
    if answer.lower() == "y":
        for mf in model_files:
            mf.unlink()
            print(f"  Deleted: {mf.name}")
        print("Deletion complete.")
    else:
        print("Keeping existing models. Note: stale models may affect results.")


# ── Window discovery ──────────────────────────────────────────────────────────

WINDOW_RE = re.compile(r"^\d{4}-\d{4}$")

def get_sorted_windows(base_dir: Path) -> list[Path]:
    """Return all YYYY-YYYY subdirectories, sorted chronologically."""
    windows = [
        p for p in base_dir.iterdir()
        if p.is_dir() and WINDOW_RE.match(p.name)
    ]
    return sorted(windows, key=lambda p: p.name)


# ── Newest-file helper ────────────────────────────────────────────────────────

def newest_file_since(directory: Path, since: float) -> Path | None:
    """Return the most recently modified file in directory created after `since`."""
    candidates = [
        f for f in directory.iterdir()
        if f.is_file() and f.stat().st_mtime > since
    ]
    return max(candidates, key=lambda f: f.stat().st_mtime) if candidates else None


# ── Pickle helper ─────────────────────────────────────────────────────────────

def save_pickle(src: Path, dest: Path, train_label: str, eval_label: str) -> None:
    """Load IDyOM output (pickle → CSV → raw bytes) and re-save as a labelled pickle."""
    # Try loading as pickle first
    try:
        with open(src, "rb") as f:
            data = pickle.load(f)
    except Exception:
        # Fall back to CSV
        try:
            with open(src, newline="") as f:
                data = list(csv.DictReader(f))
        except Exception:
            # Last resort: store raw bytes
            data = src.read_bytes()

    payload = {
        "train_window": train_label,
        "eval_window":  eval_label,
        "source_file":  str(src),
        "data":         data,
    }

    with open(dest, "wb") as f:
        pickle.dump(payload, f)

    print(f"   Saved pickle → {dest}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    base_dir    = Path(args.base_dir)
    models_dir  = Path(args.models_dir)
    out_dir     = Path(args.out_dir)
    results_dir = Path(args.results_dir)

    # Validate base directory
    if not base_dir.is_dir():
        print(f"Error: Base directory '{base_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    # Discover windows
    windows = get_sorted_windows(base_dir)
    if len(windows) < 2:
        print(
            f"Error: Need at least 2 window folders in '{base_dir}' "
            "to form a train/eval pair.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Found {len(windows)} window folders in '{base_dir}'.")

    # Handle existing models
    handle_existing_models(models_dir)

    # Create required directories
    print("\nCreating working directories...")
    for d in [Path(".TEMP"), out_dir, results_dir, models_dir]:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Error: Could not create directory '{d}': {e}", file=sys.stderr)
            sys.exit(1)

    # Sliding-window evaluation loop
    print("\nStarting IDyOM sliding-window evaluation...")
    print("=" * 52)

    pair_count = 0
    failed_pairs: list[str] = []

    for i in range(len(windows) - 1):
        train_dir  = windows[i]
        eval_dir   = windows[i + 1]
        train_label = train_dir.name
        eval_label  = eval_dir.name

        print(f"\nPair {i + 1}: train={train_label}  |  eval={eval_label}")
        print("-" * 52)

        # Remove stale model for this training window
        for stale in models_dir.glob(f"{train_label}*.model"):
            stale.unlink()
            print(f"   Removed stale model: {stale.name}")

        # Timestamp before running so we can detect new output files
        before = time.time()

        result = subprocess.run(
            ["python3", "IDyOM/App.py", "-t", str(train_dir), "-s", str(eval_dir)],
            text=True,
        )

        if result.returncode == 0:
            print(f"✅  Completed: {train_label} → {eval_label}")

            # Find newest output file written during this run
            new_file = newest_file_since(out_dir, before)
            if new_file:
                pickle_path = results_dir / f"surprisal_{train_label}_eval_{eval_label}.pkl"
                try:
                    save_pickle(new_file, pickle_path, train_label, eval_label)
                except Exception as e:
                    print(f"   ⚠  Could not save pickle: {e}")
            else:
                print(f"   ⚠  No new output file detected in '{out_dir}'; skipping pickle.")

            pair_count += 1

        else:
            msg = f"{train_label} → {eval_label}"
            print(f"❌  IDyOM failed for pair: {msg}", file=sys.stderr)
            failed_pairs.append(msg)

    # Summary
    print("\n" + "=" * 52)
    print(f"Done. Processed {pair_count} pair(s) successfully.")

    if failed_pairs:
        print(f"\nFailed pairs ({len(failed_pairs)}):")
        for p in failed_pairs:
            print(f"  ✗ {p}")
        sys.exit(1)

    print(f"Pickle results saved to: '{results_dir}/'")


if __name__ == "__main__":
    main()