#!/usr/bin/env python3
"""
Organizes MIDI files into sliding 5-year window folders.

File naming convention: YYYY_<song#>[letter]_<segment#>.mid
  e.g. 1950_02_1.mid, 1958_02a_1.mid, 1963_05_misc.mid

Output folders: YYYY-(YYYY+4), e.g. 1950-1955, 1951-1956, ...
Each folder contains copies of all MIDI files whose year falls within [start, start+4].
"""

import os
import re
import shutil
from collections import defaultdict
from optparse import OptionParser

# ── Configuration ────────────────────────────────────────────────────────────
SOURCE_DIR = "clean_monophonic_midis"   # folder containing the original MIDIs
OUTPUT_DIR = "midis_by_5yr_window"      # parent folder for the range sub-folders
WINDOW_SIZE = 4                         # inclusive span: start … start + WINDOW_SIZE
STEP = 1                                # how many years each window shifts
# ─────────────────────────────────────────────────────────────────────────────

FILENAME_RE = re.compile(
    r"^(\d{4})_[A-Za-z0-9]+[a-zA-Z]?_(?:[1-5]|misc)\.mid$",
    re.IGNORECASE,
)


def extract_year(filename: str) -> int | None:
    """Return the 4-digit year embedded at the start of a MIDI filename, or None."""
    m = re.match(r"^(\d{4})_", filename)
    return int(m.group(1)) if m else None


def main(SOURCE_DIR, OUTPUT_DIR, WINDOW_SIZE, STEP):
    if not os.path.isdir(SOURCE_DIR):
        raise FileNotFoundError(
            f"Source directory '{SOURCE_DIR}' not found. "
            "Run this script from the parent folder that contains it."
        )

    # Collect all valid MIDI files and group them by year
    midi_files = [
        f for f in os.listdir(SOURCE_DIR)
        if f.lower().endswith(".mid")
    ]

    by_year: dict[int, list[str]] = defaultdict(list)
    skipped = []
    for fname in midi_files:
        year = extract_year(fname)
        if year is not None:
            by_year[year].append(fname)
        else:
            skipped.append(fname)

    if skipped:
        print(f"⚠  Skipped {len(skipped)} file(s) with unrecognised names:")
        for s in skipped:
            print(f"   {s}")

    if not by_year:
        print("No valid MIDI files found. Nothing to do.")
        return

    all_years = sorted(by_year)
    min_year, max_year = all_years[0], all_years[-1]
    print(f"Found {sum(len(v) for v in by_year.values())} MIDI file(s) "
          f"spanning {min_year}–{max_year}.")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate every window that overlaps with the data's year range
    window_start = min_year
    window_end_limit = max_year  # last possible window start
    folders_created = 0
    files_copied = 0

    start = min_year
    while start <= window_end_limit:
        end = start + WINDOW_SIZE
        # Collect files whose year falls within [start, end]
        files_in_window = [
            fname
            for year in range(start, end + 1)
            for fname in by_year.get(year, [])
        ]

        if files_in_window:
            folder_name = f"{start}-{end}"
            folder_path = os.path.join(OUTPUT_DIR, folder_name)
            os.makedirs(folder_path, exist_ok=True)

            for fname in files_in_window:
                src = os.path.join(SOURCE_DIR, fname)
                dst = os.path.join(folder_path, fname)
                shutil.copy2(src, dst)
                files_copied += 1

            print(f"  📁 {folder_name}  →  {len(files_in_window)} file(s)")
            folders_created += 1

        start += STEP

    print(f"\n✅ Done. Created {folders_created} folder(s), copied {files_copied} file(s).")
    print(f"   Output directory: '{OUTPUT_DIR}/'")


if __name__ == "__main__":
    
    usage = "usage %prog [options]"
    parser = OptionParser(usage)
 
    parser.add_option("-i", "--input_folder", type="string",
					  help="provide input folder of midis labeled by YYYY-0#-#.mid",
					  dest="SOURCE_DIR", default="clean_monophonic_midis")
    
    parser.add_option("-o", "--output_folder", type="string",
					  help="provide directory where the organized midis will be saved",
					  dest="OUTPUT_DIR", default="midis_by_5yr_window")
    
    parser.add_option("-w", "--window_size", type="int",
				  help="Specify the window size you want to use for each subfolder",
				  dest="WINDOW_SIZE", default=4)
    
    parser.add_option("-s", "--step", type="int",
				  help="Specify the step size you want to use for each of the subfolders",
				  dest="STEP", default=1)
    
    options, _ = parser.parse_args()  
    main(options.SOURCE_DIR, options.OUTPUT_DIR, options.WINDOW_SIZE, options.STEP)  