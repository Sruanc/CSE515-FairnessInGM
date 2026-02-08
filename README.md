# cse515-FairnessInGM

This repo contains our CSE 515 project, based on Algorithmic Fairness Verification with Graphical Models (Justicia) and an extension to crash-reporting selection bias.

## Fairness Verification Library

This project uses a revised version of [Justicia](https://github.com/meelgroup/justicia) 
for formal fairness verification. The revised version includes:

- **Bundled ssatABC solver** - No separate installation needed
- **Modern Python support** - Compatible with Python 3.10-3.12
- **Streamlined dependencies** - Simplified installation
- **Enhanced documentation** - Comprehensive guides and tutorials

See [`justicia/REVISION_LOG.md`](justicia/REVISION_LOG.md) for complete details on modifications.

### Setup

```bash
# Install Justicia dependencies
pip install -r justicia/requirements.txt

# Install Justicia package
pip install -e justicia/

# Build the ssatABC solver
cd justicia/ssatABC && make && cd ../..

# Verify installation
python -c "import justicia; print('Justicia installed successfully!')"
```

### Usage in Project

See tutorials in [`justicia/doc/`](justicia/doc/) for examples.