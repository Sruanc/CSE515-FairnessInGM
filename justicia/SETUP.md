# Justicia Setup Guide

This guide will walk you through setting up Justicia, a formal fairness verification tool for machine learning classifiers.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Option 1: Using Virtual Environment (Recommended)](#option-1-using-virtual-environment-recommended)
  - [Option 2: Direct Installation](#option-2-direct-installation)
- [SSAT Solver Setup](#ssat-solver-setup)
- [Verification](#verification)
- [Running Jupyter Notebooks](#running-jupyter-notebooks)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- **Python**: 3.10 or higher (tested on Python 3.10-3.12)
- **pip**: Latest version recommended
- **Git**: For cloning repositories
- **C/C++ Compiler**: Required for building ssatABC solver (gcc or clang)

## Installation

### Option 1: Using Virtual Environment (Recommended)

This approach isolates Justicia's dependencies from your system Python.

```bash
# Clone the repository
git clone https://github.com/meelgroup/justicia.git
cd justicia

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install Justicia in development mode
pip install -e .
```

### Option 2: Direct Installation

If you prefer to install directly into your system Python or an existing environment:

```bash
# Clone the repository
git clone https://github.com/meelgroup/justicia.git
cd justicia

# Install dependencies
pip install -r requirements.txt

# Install Justicia
pip install -e .
```

## SSAT Solver Setup

Justicia requires the ssatABC solver for formal verification. The solver is included in this repository and needs to be built:

```bash
# Navigate to the ssatABC directory
cd ssatABC

# Build the solver
make

# Verify the build
./bin/abc -h
```

**Note**: The ssatABC directory is already included at the specific commit version required for Justicia. No need to clone it separately.

If you encounter build issues:
- Ensure you have a C/C++ compiler installed (gcc, clang, or MSVC)
- On macOS: Install Xcode Command Line Tools with `xcode-select --install`
- On Ubuntu/Debian: Install build essentials with `sudo apt-get install build-essential`
- On Windows: Install Visual Studio Build Tools or MinGW

## Verification

Test your installation by running Python and importing Justicia:

```python
# Start Python
python

# Import Justicia
import justicia
from justicia.utils import *

# Check if basic imports work
import numpy as np
import pandas as pd
from pgmpy.models import BayesianNetwork
```

If all imports succeed without errors, your installation is complete!

## Running Jupyter Notebooks

Justicia includes tutorial notebooks in the `doc/` directory:

```bash
# Make sure your virtual environment is activated (if using one)
source venv/bin/activate

# Start Jupyter
jupyter notebook

# Or use JupyterLab for a modern interface
jupyter lab
```

Navigate to the `doc/` folder and explore:
1. **Introduction to Justicia**: Basic concepts and usage
2. **Verifying group fairness**: Group fairness metrics
3. **Verifying causal fairness**: Causal fairness verification
4. **Influence function**: Understanding model influences
5. **Advanced Justicia Features**: Advanced techniques

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'justicia'`

**Solution**:
```bash
# Make sure you're in the justicia directory
cd /path/to/justicia

# Install in editable mode
pip install -e .
```

### SSAT Solver Issues

**Problem**: Cannot find or execute ssatABC binary

**Solution**:
```bash
# Rebuild the solver
cd ssatABC
make clean
make

# Check permissions
chmod +x bin/abc
```

### Dependency Conflicts

**Problem**: Version conflicts between packages

**Solution**:
```bash
# Create a fresh virtual environment
python3 -m venv fresh_venv
source fresh_venv/bin/activate

# Install from scratch
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### CPLEX Installation (Optional)

Some advanced features may require IBM CPLEX optimizer:

1. Download CPLEX from [IBM Academic Initiative](https://www.ibm.com/academic/home) (free for academics)
2. Install CPLEX following IBM's instructions
3. Install Python API:
```bash
cd /path/to/cplex/python
pip install .
```

**Note**: CPLEX is optional and most features work without it.

### Python Version Issues

**Problem**: Features not working as expected on older Python versions

**Solution**:
- Justicia is tested on Python 3.10-3.12
- Use Python 3.10 or higher for best compatibility
- Check your Python version: `python --version`

## Environment Variables

For advanced usage, you may want to set:

```bash
# Add ssatABC to PATH (optional)
export PATH="$PATH:/path/to/justicia/ssatABC/bin"

# Set PYTHONPATH to include justicia (if not using pip install -e)
export PYTHONPATH="$PYTHONPATH:/path/to/justicia"
```

Add these to your `~/.bashrc`, `~/.zshrc`, or equivalent for persistence.

## Docker Alternative (Advanced)

For a completely isolated environment, we provide a Dockerfile:

```bash
# Build the Docker image
docker build -t justicia:latest .

# Run Jupyter in Docker
docker run -p 8888:8888 -v $(pwd):/workspace justicia:latest

# Or start an interactive session
docker run -it justicia:latest /bin/bash
```

*Note: Docker configuration is for advanced users. Check Docker documentation for more details.*

## Getting Help

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/meelgroup/justicia/issues) for similar problems
2. Review the tutorials in the `doc/` folder
3. Contact the maintainer: [Bishwamittra Ghosh](mailto:bghosh@u.nus.edu)

## Next Steps

Once setup is complete:
- Explore the Jupyter notebooks in `doc/`
- Read the original papers (see README.md for citations)
- Try verifying fairness on your own ML models
- Check out example datasets in `data/raw/`

Happy verifying! 🎉
