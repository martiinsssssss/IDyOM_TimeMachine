# IDyOM TimeMachine

## Project Overview

IDyOM TimeMachine is a computational musicology research project that studies how musical styles and predictability evolve over time. The project uses **IDyOM** (Information Dynamics of Music), a machine learning model that predicts note surprisal in music based on learned statistical models of musical style.

## Project Structure

### Core Scripts

- **`organize_midis_by_5yr.py`**: Organizes MIDI files into sliding 5-year windows
  - Parses MIDI filenames to extract year information
  - Creates overlapping time windows for longitudinal analysis
  - Supports configurable window size and step size
  
- **`run_eras_idyom.py`**: Main analysis orchestrator
  - Trains IDyOM models on consecutive 5-year and 10-year windows (when specifying the window size)
  - Evaluates surprisal on songs from new years only
  - Manages model cleanup and result persistence
  - Command-line interface with configurable parameters

### Analysis Notebooks

- **`IDyOM_TimeMachine.ipynb`**: Primary analysis notebook
  - Comprehensive visualizations of temporal trends
  - Statistical analysis and significance testing
  - Genre distribution and heatmap analyses
  - Multiple trend charts (5-year, 10-year, cross-validation)
  - *Note: Additional plots and detailed analyses are available in this notebook*

- **`run_IDyOM.ipynb`**: Rough draft IDyOM model execution and results
  - Model training and evaluation workflows
  - Result visualization and interpretation
  - *Additional plots and detailed diagnostics in this notebook*

- **`testing_requirements.ipynb`**: Environment validation
  - Verifies correct package installation
  - Tests library compatibility

### Output Artifacts

- **`slide_charts/`**: Generated visualizations
  - 5-year and 10-year trend charts
  - Genre distribution and heatmaps
  - Statistical significance charts
  - Cross-validation trend plots

- **`outlier analysis .xlsx`**: Detailed outlier analysis results

- **`sound_examples/`**: Outlier songs exported as .mp3 files


## Getting Started

All steps are detailed in `IDyOM_TimeMachine.ipynb`, but key environment setup instructions are detailed below:

### 1. Create a conda environment

    conda create -n idyompyenv

### 2. Activate the environment

    conda activate idyompyenv

*(Note: You will need to activate this environment each time you work with the project)*

### 3. Install dependencies

    pip install -r requirements.txt

**Important**: Check that the requirements file is up-to-date with your system configuration (Python version compatibility may require adjustments)

## Usage Workflow

### Step 1: Git Clone dataset and IDyOMpy model
```bash
git clone https://github.com/madelinehamilton/BiMMuDa.git data/
git clone https://github.com/GuiMarion/IDyOMpy.git
```
### Step 2: Install IDyOM dependencies
```bash
cd IDyOM
pip install -r requirements.txt
```
### Step 3: Analyze Results
Open and run the analysis notebooks:
- `IDyOM_TimeMachine.ipynb` for main findings
- `run_IDyOM.ipynb` for model diagnostics

## Dependencies

Key Python packages (see `requirements.txt` for full list):
- **pandas** (2.3.3): Data manipulation and analysis
- **scipy** (1.12.0): Scientific computing
- **scikit-learn** (1.7.2): Machine learning tools
- **statsmodels** (0.14.6): Statistical modeling
- **matplotlib** / **seaborn**: Visualization
- **pretty_midi** (0.2.10): MIDI file processing
- **ruptures** (1.1.10): Change point detection

## Additional Notes

- More detailed plots, analyses, and results are available directly in the Jupyter notebook `IDyOM_TimeMachine.ipynb`
- The IDyOM model requires substantial computational resources for large datasets
- Model files can be large; ensure adequate disk space for the `models/` directory
- Results are stored as pickle files for efficient reloading and further analysis

## References
- Information Dynamics of Music: G. Marion, F. Gao, B. P. Gold, G. M. D. Liberto, and S. Shamma, “IDyOMpy: A new Python-based model for the statistical analysis of musical expectations,” Journal of Neuroscience Methods, vol. 415, p. 110347, March 2025. https://github.com/GuiMarion/IDyOMpy

- BiMMuDa Dataset https://github.com/madelinehamilton/BiMMuDa

