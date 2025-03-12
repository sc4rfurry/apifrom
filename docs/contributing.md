# Contributing to APIFromAnything

Thank you for your interest in contributing to APIFromAnything! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please read and follow our [Code of Conduct](https://github.com/apifrom/apifrom/blob/main/CODE_OF_CONDUCT.md) to ensure a positive and inclusive environment for everyone.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Git
- A GitHub account

### Setting Up the Development Environment

1. **Fork the repository**:
   
   Go to the [APIFromAnything repository](https://github.com/apifrom/apifrom) and click the "Fork" button in the top-right corner.

2. **Clone your fork**:

   ```bash
   git clone https://github.com/YOUR_USERNAME/apifrom.git
   cd apifrom
   ```

3. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install development dependencies**:

   ```bash
   pip install -e ".[dev]"
   ```

5. **Set up pre-commit hooks**:

   ```bash
   pre-commit install
   ```

## Development Workflow

### Creating a Branch

Create a new branch for your changes:

```bash
git checkout -b feature/your-feature-name
```

Use a descriptive name for your branch that reflects the changes you're making.

### Making Changes

1. Make your changes to the codebase.
2. Write tests for your changes.
3. Run the tests to make sure they pass:

   ```bash
   pytest
   ```

4. Run the linters to ensure code quality:

   ```bash
   black .
   flake8
   mypy .
   ```

### Committing Changes

1. Stage your changes:

   ```bash
   git add .
   ```

2. Commit your changes with a descriptive message:

   ```bash
   git commit -m "Add feature: your feature description"
   ```

   Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for your commit messages:

   - `feat`: A new feature
   - `fix`: A bug fix
   - `docs`: Documentation changes
   - `style`: Changes that do not affect the meaning of the code (formatting, etc.)
   - `refactor`: Code changes that neither fix a bug nor add a feature
   - `perf`: Code changes that improve performance
   - `test`: Adding or modifying tests
   - `chore`: Changes to the build process or auxiliary tools

3. Push your changes to your fork:

   ```bash
   git push origin feature/your-feature-name
   ```

### Creating a Pull Request

1. Go to the [APIFromAnything repository](https://github.com/apifrom/apifrom) and click the "New pull request" button.
2. Click "compare across forks" and select your fork and branch.
3. Fill out the pull request template with a description of your changes.
4. Submit the pull request.

## Pull Request Guidelines

- Keep pull requests focused on a single feature or bug fix.
- Make sure all tests pass.
- Make sure the code passes all linters.
- Update documentation if necessary.
- Add tests for new features or bug fixes.
- Follow the code style of the project.
- Be responsive to feedback and questions.

## Code Style

APIFromAnything follows the [Black](https://black.readthedocs.io/) code style. We also use [Flake8](https://flake8.pycqa.org/) for linting and [MyPy](https://mypy.readthedocs.io/) for type checking.

### Imports

Organize imports in the following order:

1. Standard library imports
2. Related third-party imports
3. Local application/library specific imports

Within each group, imports should be sorted alphabetically.

```python
# Standard library imports
import asyncio
import json
import os
from typing import Dict, List, Optional

# Third-party imports
import jwt
import pydantic
import requests

# Local imports
from apifrom.core import app
from apifrom.middleware import Middleware
```

### Docstrings

Use Google-style docstrings:

```python
def function_with_types_in_docstring(param1, param2):
    """Example function with types documented in the docstring.

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    Raises:
        ValueError: If param1 is negative.
    """
    if param1 < 0:
        raise ValueError("param1 must be positive")
    return param1 > len(param2)
```

### Type Hints

Use type hints for function parameters and return values:

```python
def greeting(name: str) -> str:
    return f"Hello, {name}!"
```

## Testing

APIFromAnything uses [pytest](https://docs.pytest.org/) for testing. All new features and bug fixes should include tests.

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=apifrom

# Run a specific test file
pytest tests/test_file.py

# Run a specific test
pytest tests/test_file.py::test_function
```

### Writing Tests

- Test files should be named `test_*.py`.
- Test functions should be named `test_*`.
- Use descriptive names for test functions.
- Use fixtures for common setup and teardown.
- Use parameterized tests for testing multiple inputs.
- Use mocking for external dependencies.

Example:

```python
import pytest
from apifrom import API, api
from apifrom.testing import TestClient

@pytest.fixture
def app():
    app = API()
    
    @api(route="/hello/{name}", method="GET")
    def hello(name: str):
        return {"message": f"Hello, {name}!"}
    
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_hello(client):
    response = client.get("/hello/World")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}
```

## Documentation

APIFromAnything uses [Sphinx](https://www.sphinx-doc.org/) for documentation. All new features should include documentation.

### Building Documentation

```bash
cd docs
make html
```

The documentation will be built in the `docs/_build/html` directory.

### Writing Documentation

- Use Markdown for documentation files.
- Use code blocks for code examples.
- Use admonitions for notes, warnings, and tips.
- Use cross-references for linking to other parts of the documentation.
- Use tables for structured data.

## Reporting Bugs

If you find a bug, please report it by creating an issue on the [GitHub repository](https://github.com/apifrom/apifrom/issues).

When reporting a bug, please include:

- A clear and descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Screenshots or code snippets if applicable
- Environment information (OS, Python version, APIFromAnything version)

## Requesting Features

If you have an idea for a new feature, please create an issue on the [GitHub repository](https://github.com/apifrom/apifrom/issues).

When requesting a feature, please include:

- A clear and descriptive title
- A detailed description of the feature
- Why the feature would be useful
- Examples of how the feature would be used
- Any relevant references or resources

## Release Process

APIFromAnything follows [Semantic Versioning](https://semver.org/). The release process is as follows:

1. Update the version number in `pyproject.toml` and `__init__.py`.
2. Update the changelog with the new version and changes.
3. Create a new release on GitHub with the version number as the tag.
4. Publish the new version to PyPI.

## Community

Join our community to get help, share ideas, and contribute to the project:

- [Discord](https://discord.gg/apifrom)
- [Twitter](https://twitter.com/apifrom)
- [GitHub Discussions](https://github.com/apifrom/apifrom/discussions)

## License

By contributing to APIFromAnything, you agree that your contributions will be licensed under the [MIT License](https://github.com/apifrom/apifrom/blob/main/LICENSE). 