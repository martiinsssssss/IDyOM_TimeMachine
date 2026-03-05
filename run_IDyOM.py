#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
from pathlib import Path

# ------------------------------------------------------------
# Utility helpers
# ------------------------------------------------------------

def confirm(prompt: str) -> bool:
    """Prompt user for Y/N confirmation."""
    resp = input(prompt).strip()
    return resp.lower().startswith("y")


def run_process(cmd, *, input_text=None):
    """
    Launch a subprocess.
    Returns the Popen object.
    """
    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE if input_text is not None else None,
        text=True
    )


def ensure_dirs(*dirs):
    """Create directories, exit on failure."""
    try:
        for d in dirs:
            os.makedirs(d, exist_ok=True)
    except Exception as e:
        print(f"Error: Failed to create directories: {e}")
        sys.exit(1)


# ------------------------------------------------------------
# Intro message
# ------------------------------------------------------------

print("""
╔════════════════════════ IMPORTANT ════════════════════════╗
║                                                           ║
║  PLEASE ENSURE THE FOLLOWING BEFORE PROCEEDING:           ║
║                                                           ║
║  1. You have time to complete the process without         ║
║     interruption                                          ║
║  2. IDyOMpy is cloned under codeForPaper-IDyOMpy-/        ║
║  3. This script is in the IDyOMpy directory and           ║
║     running under the IDyOMpy environment                 ║
║  4. The results will be renamed and copied to             ║
║     'codeForPaper-IDyOMpy/benchmark_results/'             ║
║                                                           ║
║  NOTE: Interrupting the process may lead to errors in     ║
║        some operating systems. If errors occur when you   ║
║        run the code again (especially directory issues    ║
║        for 'models'), try rebooting your system or        ║
║        delete any partial results and restart the         ║
║        entire process.                                    ║
║                                                           ║
╚═══════════════════════ READ CAREFULLY ════════════════════╝
""")

if not confirm("Do you want to proceed? (Y/N): "):
    print("Execution cancelled.")
    sys.exit(0)

print("Checking the models directory...")

# ------------------------------------------------------------
# Model cleanup
# ------------------------------------------------------------

models_dir = Path("models")
model_files = [
    "bach_Pearce_quantization_24_maxOrder_20_viewpoints_pitch_length.model",
    "mixed2_quantization_24_maxOrder_20_viewpoints_pitch_length.model",
    "train_shanxi_quantization_24_maxOrder_20_viewpoints_pitch_length.model",
]

found_models = any((models_dir / f).is_file() for f in model_files)

if found_models:
    print("Found trained models in the 'models' directory.")
    if confirm("Do you want to delete these models? (Y/N): "):
        print("Deleting existing model files for benchmark...")
        for f in model_files:
            path = models_dir / f
            if path.is_file():
                path.unlink()
                print(f"Deleted: {f}")
        print("Deletion complete.")
    else:
        print("Models were not deleted. Exiting the script.")
        sys.exit(0)
else:
    print("No trained models found in the 'models' directory.")

# ------------------------------------------------------------
# Directory setup
# ------------------------------------------------------------

ensure_dirs(".TEMP", "out")
ensure_dirs("../benchmark_results/forBenchmark_IDyOMpy")

# ------------------------------------------------------------
# IDyOMpy runs – block 1 (parallel)
# ------------------------------------------------------------

processes = []

processes.append(run_process([
    "python3", "App.py",
    "-t", "../dataset/train_shanxi/",
    "-s", "../dataset/bach_Pearce/"
]))

processes.append(run_process([
    "python3", "App.py",
    "-t", "../dataset/bach_Pearce/",
    "-s", "../dataset/train_shanxi/"
]))

processes.append(run_process([
    "python3", "App.py",
    "-t", "../dataset/mixed2/",
    "-s", "../stimuli/GregoireMcGill/"
]))

# Wait for first batch
for p in processes:
    p.wait()

# ------------------------------------------------------------
# IDyOMpy runs – block 2 (parallel)
# ------------------------------------------------------------

processes = []

processes.append(run_process([
    "python3", "App.py",
    "-c", "../dataset/bach_Pearce/"
]))

processes.append(run_process(
    ["python3", "App.py", "-t", "../dataset/mixed2/", "-s", "../stimuli/giovanni/"],
    input_text="N\n"
))

processes.append(run_process(
    ["python3", "App.py", "-t", "../dataset/mixed2/", "-s", "../stimuli/Gold/"],
    input_text="N\n"
))

processes.append(run_process(
    ["python3", "App.py", "-t", "../dataset/bach_Pearce/", "-s", "../stimuli/GregoireMcGill/"],
    input_text="N\n"
))

processes.append(run_process(
    ["python3", "App.py", "-t", "../dataset/bach_Pearce/", "-s", "../stimuli/giovanni/"],
    input_text="N\n"
))

processes.append(run_process([
    "python3", "App.py",
    "-e", "../dataset/bach_Pearce/"
]))

processes.append(run_process([
    "python3", "App.py",
    "-c", "../dataset/train_shanxi/"
]))

processes.append(run_process([
    "python3", "App.py",
    "-c", "../dataset/mixed2/"
]))

# Send "N\n" where required and wait
for p in processes:
    if p.stdin:
        p.stdin.write("N\n")
        p.stdin.flush()

for p in processes:
    p.wait()

# ------------------------------------------------------------
# Copy benchmark results
# ------------------------------------------------------------

print("We copy the results to the benchmark_results folder...")

copies = [
    ("out/bach_Pearce/surprises/train_shanxi/data/train_shanxi_quantization_24_maxOrder_20_viewpoints_pitch_length.mat",
     "../benchmark_results/forBenchmark_IDyOMpy/Bach_Pearce_trained_on_Chinese_train.mat"),

    ("out/bach_Pearce/eval/data/likelihoods_cross-eval_k_fold_5_quantization_24_maxOrder_20_viewpoints_pitch_length.mat",
     "../benchmark_results/forBenchmark_IDyOMpy/Bach_Pearce_cross_eval.mat"),

    ("out/train_shanxi/eval/data/likelihoods_cross-eval_k_fold_5_quantization_24_maxOrder_20_viewpoints_pitch_length.mat",
     "../benchmark_results/forBenchmark_IDyOMpy/Chinese_train_cross_val.mat"),

    ("out/train_shanxi/surprises/bach_Pearce/data/bach_Pearce_quantization_24_maxOrder_20_viewpoints_pitch_length.mat",
     "../benchmark_results/forBenchmark_IDyOMpy/Chinese_train_trained_on_Bach_Pearce.mat"),

    ("out/GregoireMcGill/surprises/mixed2/data/mixed2_quantization_24_maxOrder_20_viewpoints_pitch_length.mat",
     "../benchmark_results/forBenchmark_IDyOMpy/Jneurosci_trained_on_mixed2.mat"),

    ("out/giovanni/surprises/mixed2/data/mixed2_quantization_24_maxOrder_20_viewpoints_pitch_length.mat",
     "../benchmark_results/forBenchmark_IDyOMpy/eLife_trained_on_mixed2.mat"),

    ("out/Gold/surprises/mixed2/data/mixed2_quantization_24_maxOrder_20_viewpoints_pitch_length.mat",
     "../benchmark_results/forBenchmark_IDyOMpy/Gold_trained_on_mixed2.mat"),

    ("out/mixed2/eval/data/likelihoods_cross-eval_k_fold_5_quantization_24_maxOrder_20_viewpoints_pitch_length.mat",
     "../benchmark_results/forBenchmark_IDyOMpy/Mixed2_cross_eval.mat"),

    ("out/GregoireMcGill/surprises/bach_Pearce/data/bach_Pearce_quantization_24_maxOrder_20_viewpoints_pitch_length.mat",
     "../benchmark_results/forBenchmark_IDyOMpy/Jneurosci_trained_on_bach_Pearce.mat"),

    ("out/giovanni/surprises/bach_Pearce/data/bach_Pearce_quantization_24_maxOrder_20_viewpoints_pitch_length.mat",
     "../benchmark_results/forBenchmark_IDyOMpy/eLife_trained_on_bach_Pearce.mat"),

    ("out/bach_Pearce/evolution/bach_Pearce.mat",
     "../benchmark_results/forBenchmark_IDyOMpy/evolution_Bach_Pearce.mat"),
]

for src, dst in copies:
    shutil.copy(src, dst)

print("Benchmark completed. Results are saved in folders benchmark_results/forBenchmark_IDyOMpy.")
