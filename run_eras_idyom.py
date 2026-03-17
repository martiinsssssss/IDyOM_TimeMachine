#!/usr/bin/env python3
"""
run_eras_idyom.py

For every consecutive pair of 5-year windows produced by organize_midis.py,
trains IDyOM on the first window and evaluates surprisal only on songs from
the new year — i.e. the final year of the eval window that is not present in
the training window.

Example: train=1950-1954, eval_dir=1951-1955 → only songs from 1955 are
evaluated, since 1951-1954 were already in the training window.

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
import shutil
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
    parser.add_argument("-d", "--base_dir",    default="midis_by_5yr_window",
                        help="Folder containing the YYYY-YYYY subfolders")
    parser.add_argument("-m", "--models_dir",  default="models",
                        help="Directory where IDyOM stores trained models")
    parser.add_argument("-o", "--out_dir",     default="out",
                        help="Directory where IDyOM writes output files")
    parser.add_argument("-r", "--results_dir", default="results",
                        help="Destination directory for pickle result files")
    parser.add_argument("-s", "--step",        default=1, type=int,
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


def parse_window_years(window: Path) -> tuple[int, int]:
    """Extract (start_year, end_year) from a YYYY-YYYY folder name."""
    start, end = window.name.split("-")
    return int(start), int(end)


# ── New-year MIDI filtering ───────────────────────────────────────────────────

def build_new_year_eval_dir(eval_dir: Path, new_year: int, temp_root: Path) -> Path:
    """
    Copy only MIDIs whose filename starts with `new_year` from eval_dir into
    a fresh temp subfolder. MIDI filenames are expected to start with the year,
    e.g. '1955_04_1.mid'.

    Returns the path to the temp eval folder.
    """
    temp_eval = temp_root / f"eval_{new_year}"
    if temp_eval.exists():
        shutil.rmtree(temp_eval)
    temp_eval.mkdir(parents=True)

    year_prefix = str(new_year)
    copied = 0
    for midi in eval_dir.rglob("*.mid"):
        if midi.name.startswith(year_prefix):
            shutil.copy2(midi, temp_eval / midi.name)
            copied += 1

    # Also check .midi extension
    for midi in eval_dir.rglob("*.midi"):
        if midi.name.startswith(year_prefix):
            shutil.copy2(midi, temp_eval / midi.name)
            copied += 1

    print(f"   Copied {copied} MIDI file(s) for year {new_year} → {temp_eval}")

    if copied == 0:
        print(f"   ⚠  No MIDIs found for year {new_year} in '{eval_dir}'. Skipping pair.")
        return None

    return temp_eval


# ── Newest-file helper ────────────────────────────────────────────────────────

def newest_file_since(directory: Path, since: float) -> Path | None:
    """Return the most recently modified file in directory created after `since`."""
    candidates = [
        f for f in directory.iterdir()
        if f.is_file() and f.stat().st_mtime > since
    ]
    return max(candidates, key=lambda f: f.stat().st_mtime) if candidates else None


# ── Pickle helper ─────────────────────────────────────────────────────────────

def save_pickle(src: Path, dest: Path, train_label: str, eval_label: str, new_year: int) -> None:
    """Load IDyOM output (pickle → CSV → raw bytes) and re-save as a labelled pickle."""
    try:
        with open(src, "rb") as f:
            data = pickle.load(f)
    except Exception:
        try:
            with open(src, newline="") as f:
                data = list(csv.DictReader(f))
        except Exception:
            data = src.read_bytes()

    payload = {
        "train_window": train_label,
        "eval_window":  eval_label,
        "eval_year":    new_year,
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
    temp_root   = Path(".TEMP")

    if not base_dir.is_dir():
        print(f"Error: Base directory '{base_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    windows = get_sorted_windows(base_dir)
    if len(windows) < 2:
        print(
            f"Error: Need at least 2 window folders in '{base_dir}' "
            "to form a train/eval pair.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Found {len(windows)} window folders in '{base_dir}'.")

    handle_existing_models(models_dir)

    print("\nCreating working directories...")
    for d in [temp_root, out_dir, results_dir, models_dir]:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Error: Could not create directory '{d}': {e}", file=sys.stderr)
            sys.exit(1)

    print("\nStarting IDyOM sliding-window evaluation...")
    print("=" * 52)

    pair_count = 0
    failed_pairs: list[str] = []

    for i in range(len(windows) - 1):
        train_dir  = windows[i]
        eval_dir   = windows[i + 1]
        train_label = train_dir.name
        eval_label  = eval_dir.name

        train_start, train_end = parse_window_years(train_dir)
        _, eval_end            = parse_window_years(eval_dir)

        # The new year is the final year of the eval window — the one year
        # not covered by the training window.
        new_year = eval_end

        print(f"\nPair {i + 1}: train={train_label}  |  eval={eval_label}  |  new songs year={new_year}")
        print("-" * 52)

        # Remove stale model for this training window
        for stale in models_dir.glob(f"{train_label}*.model"):
            stale.unlink()
            print(f"   Removed stale model: {stale.name}")

        # Build a temp eval folder containing only new_year MIDIs
        temp_eval_dir = build_new_year_eval_dir(eval_dir, new_year, temp_root)
        if temp_eval_dir is None:
            failed_pairs.append(f"{train_label} → {eval_label} (no MIDIs for {new_year})")
            continue

        before = time.time()

        result = subprocess.run(
            ["python3", "IDyOM/App.py", "-t", str(train_dir), "-s", str(temp_eval_dir)],
            text=True,
        )

        if result.returncode == 0:
            print(f"✅  Completed: {train_label} → {eval_label} (year {new_year} only)")

            new_file = newest_file_since(out_dir, before)
            if new_file:
                pickle_path = results_dir / f"surprisal_{train_label}_eval_{new_year}.pkl"
                try:
                    save_pickle(new_file, pickle_path, train_label, eval_label, new_year)
                except Exception as e:
                    print(f"   ⚠  Could not save pickle: {e}")
            else:
                print(f"   ⚠  No new output file detected in '{out_dir}'; skipping pickle.")

            pair_count += 1

        else:
            msg = f"{train_label} → {eval_label} (year {new_year})"
            print(f"❌  IDyOM failed for pair: {msg}", file=sys.stderr)
            failed_pairs.append(msg)

        # Clean up temp eval dir for this pair
        shutil.rmtree(temp_eval_dir, ignore_errors=True)

    # Final cleanup of temp root
    shutil.rmtree(temp_root, ignore_errors=True)

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