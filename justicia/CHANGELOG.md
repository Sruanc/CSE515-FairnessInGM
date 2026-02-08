# Changelog

All notable changes to the Justicia project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive SETUP.md with detailed installation instructions
- CONTRIBUTING.md with guidelines for contributors
- PUBLICATION_CHECKLIST.md for pre-publication verification
- This CHANGELOG.md file

### Changed
- Consolidated multiple requirements files into single requirements.txt
- Updated README.md with better formatting, badges, and organization
- Improved .gitignore to properly exclude build artifacts and environments
- Streamlined dependencies to modern Python packages

### Removed
- Obsolete cleaning scripts (clean, clean.sh)
- Redundant activation script (activate_venv.sh)
- Old VENV_SETUP.md (replaced by SETUP.md)
- Multiple redundant requirements files
- Build artifacts and temporary output files
- Python cache directories

## [0.0.5] - 2021-2022

### Added
- Initial public release
- Support for group fairness verification
- Support for causal fairness verification via graphical models
- Integration with SSAT solver (ssatABC)
- Jupyter notebook tutorials (5 comprehensive notebooks)
- Example datasets: Adult, COMPAS, German Credit, Communities, Bank, Ricci, Titanic
- Influence function analysis
- Poison attack detection capabilities

### Research
- Published at AAAI 2021: "Justicia: A Stochastic SAT Approach to Formally Verify Fairness"
- Published at AAAI 2022: "Algorithmic Fairness Verification with Graphical Models"

## Version History

- **0.0.5** (2021-2022): Initial public release with AAAI paper implementations
- **Current**: Repository cleanup and documentation improvements

---

## Release Notes Format

For future releases, include:

### Added
- New features or capabilities

### Changed
- Changes to existing functionality

### Deprecated
- Features that will be removed in future versions

### Removed
- Features that have been removed

### Fixed
- Bug fixes

### Security
- Security vulnerability fixes

---

*For the complete commit history, see the [GitHub repository](https://github.com/meelgroup/justicia).*
