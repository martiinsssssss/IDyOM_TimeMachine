from pathlib import Path
import kagglehub

# Project root (where this script sits)
project_root = Path(__file__).resolve().parent

# Create clean dataset folder
dataset_dir = project_root / "data" / "lakh"
dataset_dir.mkdir(parents=True, exist_ok=True)

# Download dataset there
path = kagglehub.dataset_download(
    "imsparsh/lakh-midi-clean",
    output_dir = dataset_dir,
    force_download=False  # change to True if you want overwrite
)

print("Path to dataset files:", path)