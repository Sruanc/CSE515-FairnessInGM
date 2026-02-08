# Justicia: Formal Fairness Verification for Machine Learning

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **📌 Note**: This is a revised and enhanced version of the original [meelgroup/justicia](https://github.com/meelgroup/justicia) repository, optimized for standalone use with modern Python dependencies. See [REVISION_LOG.md](REVISION_LOG.md) for detailed changes.

Justicia is a **formal verification tool** for assessing fairness in machine learning classifiers. Based on AAAI [2021](https://arxiv.org/pdf/2009.06516.pdf) and [2022](https://arxiv.org/pdf/2109.09447.pdf) papers, Justicia uses stochastic SAT solving and graphical models to provide rigorous fairness guarantees.

![](images/fairness_illustration.png)

## 🌟 Features

- **Formal Verification**: Mathematically rigorous fairness verification using SAT solvers
- **Multiple Fairness Metrics**: Support for group fairness and causal fairness definitions
- **Graphical Models**: Integration with probabilistic graphical models for causal analysis
- **Real-world Datasets**: Pre-configured examples with Adult, COMPAS, German Credit, and more
- **Interactive Tutorials**: Step-by-step Jupyter notebooks for learning and experimentation
- **Standalone Package**: Bundled SSAT solver and modern Python 3.10-3.12 support
- **Easy Setup**: Single-command installation with comprehensive documentation

## 📋 What's Different in This Version

This repository enhances the original Justicia with:
- ✅ **Bundled ssatABC solver** - No separate clone needed
- ✅ **Modernized dependencies** - Python 3.10-3.12, NumPy 2.x, Pandas 3.x
- ✅ **Enhanced documentation** - SETUP.md, CONTRIBUTING.md, and detailed guides
- ✅ **Streamlined setup** - Virtual environment ready, ~20 core packages vs 275+
- ✅ **Additional tutorial** - New Advanced Features notebook

For a complete list of changes, see **[REVISION_LOG.md](REVISION_LOG.md)**.

## 📚 Documentation

- **[SETUP.md](SETUP.md)**: Complete installation and setup guide
- **[Jupyter Tutorials](doc/)**: Interactive notebooks covering all features:
  1. Introduction to Justicia
  2. Verifying Group Fairness
  3. Verifying Causal Fairness
  4. Influence Functions
  5. Advanced Features

## 🚀 Quick Start

### Installation

```bash
# Clone this repository
git clone <your-repo-url>
cd justicia

# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Justicia
pip install -e .

# Build the SSAT solver (included in this repo)
cd ssatABC && make && cd ..
```

> **Note**: The ssatABC solver is **included in this repository**. No need to clone it separately!

For detailed installation instructions and troubleshooting, see **[SETUP.md](SETUP.md)**.

### Basic Usage

```python
import justicia
from justicia.utils import *
from pgmpy.models import BayesianNetwork

# Load your classifier
model = load_classifier('your_model.pkl')

# Define fairness constraints
sensitive_attr = 'race'
target = 'decision'

# Verify fairness
result = verify_fairness(model, sensitive_attr, target)
print(f"Fairness verified: {result}")
```

## 📦 Dependencies

### Core Requirements
- Python 3.10 or higher
- NumPy, Pandas, SciPy, scikit-learn
- [PGMPY](https://github.com/pgmpy/pgmpy) - Probabilistic graphical models
- [PySAT](https://github.com/pysathq/pysat) - SAT solver library
- [ssatABC](https://github.com/NTU-ALComLab/ssatABC) - Stochastic SAT solver (included)

The ssatABC solver is **included in this repository** at the tested version. Simply run `make` in the `ssatABC/` directory.

See [requirements.txt](requirements.txt) for the complete list of dependencies.


## 📖 Research Papers

Justicia is based on research published at AAAI:

1. **[Algorithmic Fairness Verification with Graphical Models](https://arxiv.org/pdf/2109.09447.pdf)** (AAAI 2022)
2. **[Justicia: A Stochastic SAT Approach to Formally Verify Fairness](https://arxiv.org/pdf/2009.06516.pdf)** (AAAI 2021)

### Citation

If you use Justicia in your research, please cite:

```bibtex
@inproceedings{ghosh2022algorithmic,
  author    = {Ghosh, Bishwamittra and Basu, Debabrota and Meel, Kuldeep S.},
  title     = {Algorithmic Fairness Verification with Graphical Models},
  booktitle = {Proceedings of the AAAI Conference on Artificial Intelligence},
  month     = {February},
  year      = {2022}
}

@inproceedings{ghosh2021justicia,
  author    = {Ghosh, Bishwamittra and Basu, Debabrota and Meel, Kuldeep S.},
  title     = {Justicia: A Stochastic {SAT} Approach to Formally Verify Fairness},
  booktitle = {Proceedings of the AAAI Conference on Artificial Intelligence},
  month     = {February},
  year      = {2021}
}
```

## 🤝 Contributing

We welcome contributions! Please feel free to:
- Report bugs or issues on [GitHub Issues](https://github.com/meelgroup/justicia/issues)
- Submit pull requests with improvements
- Add new fairness metrics or datasets
- Improve documentation

## 📧 Contact

**Bishwamittra Ghosh**  
- Email: bghosh@u.nus.edu
- Website: [bishwamittra.github.io](https://bishwamittra.github.io/)

For questions, bug reports, or collaboration inquiries, please open an issue on GitHub or contact the maintainer directly.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- The ssatABC solver team at NTU ALComLab
- PGMPY and PySAT communities
- All contributors and users of Justicia

---

**Made with ❤️ by the Formal Verification and Machine Learning communities**

### Issues, questions, bugs, etc.
Please click on "issues" at the top and [create a new issue](https://github.com/meelgroup/justicia/issues). All issues are responded to promptly.
