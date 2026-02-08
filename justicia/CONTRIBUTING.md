# Contributing to Justicia

Thank you for your interest in contributing to Justicia! This document provides guidelines for contributing to the project.

## Table of Contents
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Getting Started

Justicia is an academic research project focused on formal fairness verification for machine learning. We welcome contributions in the following areas:

- **Bug fixes**: Corrections to existing code
- **New features**: Additional fairness metrics, verification algorithms, or utilities
- **Documentation**: Improvements to docs, tutorials, or examples
- **Datasets**: New benchmark datasets for fairness evaluation
- **Performance**: Optimizations and efficiency improvements
- **Tests**: Additional test coverage

## Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/justicia.git
   cd justicia
   ```

3. **Set up development environment**:
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Install in editable mode
   pip install -e .
   
   # Build ssatABC solver
   cd ssatABC && make && cd ..
   ```

4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

## How to Contribute

### Adding New Features

1. **Discuss first**: For major changes, open an issue to discuss your idea before implementing
2. **Follow existing patterns**: Look at similar features in the codebase
3. **Document your code**: Add docstrings and comments
4. **Add examples**: Include usage examples in docstrings or notebooks
5. **Test thoroughly**: Ensure your feature works with existing datasets

### Improving Documentation

- Fix typos, clarify explanations, or add missing information
- Add examples demonstrating specific features
- Create or improve Jupyter notebooks in the `doc/` directory
- Update README.md or SETUP.md if installation/usage changes

### Adding Datasets

When adding new benchmark datasets to `data/`:

1. Place raw data in `data/raw/`
2. Create a data object class in `data/objects/` following existing patterns (e.g., `adult.py`)
3. Include data loading and preprocessing functions
4. Document the dataset source, features, and sensitive attributes
5. Ensure compliance with data usage licenses

### Bug Fixes

1. **Identify the issue**: Clearly understand the bug
2. **Create a test case**: If possible, add a test that reproduces the bug
3. **Fix the issue**: Make minimal changes to resolve the problem
4. **Verify the fix**: Ensure the bug is fixed and no new issues are introduced

## Code Style

### Python Style Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use meaningful variable and function names
- Maximum line length: 100 characters (flexible for readability)
- Use docstrings for all public functions and classes

#### Example Function Style:

```python
def verify_fairness(model, sensitive_attr, target, fairness_metric='demographic_parity'):
    """
    Verify fairness of a classifier with respect to a sensitive attribute.
    
    Parameters
    ----------
    model : Classifier
        The trained machine learning model to verify
    sensitive_attr : str
        Name of the sensitive attribute (e.g., 'race', 'gender')
    target : str
        Name of the target/decision variable
    fairness_metric : str, optional
        The fairness metric to use (default: 'demographic_parity')
        
    Returns
    -------
    dict
        Dictionary containing verification results with keys:
        - 'is_fair': bool indicating if model satisfies fairness
        - 'violation': float indicating degree of violation (if any)
        - 'details': additional verification information
        
    Examples
    --------
    >>> model = train_classifier(X_train, y_train)
    >>> result = verify_fairness(model, 'race', 'decision')
    >>> print(result['is_fair'])
    True
    """
    # Implementation here
    pass
```

### Naming Conventions

- **Functions**: `lowercase_with_underscores`
- **Classes**: `CapitalizedWords`
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`
- **Private methods**: `_leading_underscore`

### Imports

Organize imports in three groups:
1. Standard library imports
2. Third-party library imports
3. Local application imports

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import numpy as np
import pandas as pd
from pgmpy.models import BayesianNetwork

# Local
from justicia.utils import load_data
from justicia.metrics import fairness_score
```

## Testing

While Justicia doesn't currently have a comprehensive test suite, we encourage contributors to:

1. **Test manually**: Run your code with multiple datasets
2. **Verify notebooks**: Ensure Jupyter notebooks run without errors
3. **Check edge cases**: Test with unusual or extreme inputs
4. **Document testing**: Describe how you tested your changes in the PR

### Running Notebooks

Test that notebooks still work:
```bash
jupyter nbconvert --to notebook --execute doc/1.\ Introduction\ to\ Justicia*.ipynb
```

## Submitting Changes

### Commit Messages

Write clear, concise commit messages:

```
Short (50 chars or less) summary

More detailed explanatory text, if necessary. Wrap it to about 72
characters. The blank line separating the summary from the body is
critical.

- Bullet points are okay
- Use imperative mood: "Add feature" not "Added feature"

Fixes #123
```

### Pull Request Process

1. **Update documentation**: Ensure README, docstrings, and notebooks reflect your changes
2. **Clean your code**: Remove debug prints, commented code, and temporary files
3. **Rebase if needed**: Keep your branch up-to-date with master
4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** on GitHub with:
   - Clear title describing the change
   - Description of what changed and why
   - Reference to any related issues
   - Screenshots/examples if applicable

6. **Respond to reviews**: Be open to feedback and make requested changes

### Pull Request Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
Describe how you tested your changes.

## Related Issues
Fixes #(issue number)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] Notebooks run successfully (if applicable)
- [ ] No unnecessary files added
```

## Reporting Issues

### Bug Reports

Include:
- **Description**: Clear description of the bug
- **Steps to reproduce**: Minimal example to reproduce the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Environment**: Python version, OS, package versions
- **Error messages**: Full error traceback if applicable

### Feature Requests

Include:
- **Description**: What feature you'd like to see
- **Use case**: Why this feature would be useful
- **Examples**: How the feature would be used
- **References**: Links to papers or similar implementations (if applicable)

## Questions?

- Open an issue with the "question" label
- Email: bghosh@u.nus.edu
- Check existing documentation and notebooks first

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Credit others' work appropriately

## License

By contributing to Justicia, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Justicia! Your efforts help make fairness verification more accessible to the research community. 🎉
