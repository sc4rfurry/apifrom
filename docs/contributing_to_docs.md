# Contributing to Documentation

This guide explains how to contribute to the APIFromAnything documentation.

## Documentation Structure

The documentation is built using [Sphinx](https://www.sphinx-doc.org/) with the [Read the Docs](https://sphinx-rtd-theme.readthedocs.io/) theme. The source files are written in Markdown and are located in the `docs/` directory.

## Setting Up the Documentation Environment

To build the documentation locally, follow these steps:

1. Install the documentation dependencies:
   ```bash
   pip install -e .[docs]
   ```

2. Navigate to the docs directory:
   ```bash
   cd docs
   ```

3. Build the documentation:
   ```bash
   sphinx-build -b html . _build/html
   ```

4. Open the generated documentation in your browser:
   ```bash
   # On Linux/macOS
   open _build/html/index.html
   
   # On Windows
   start _build/html/index.html
   ```

## Writing Documentation

### File Format

Documentation files are written in Markdown (`.md`) format. Sphinx uses the MyST parser to convert Markdown to reStructuredText.

### Adding a New Page

To add a new documentation page:

1. Create a new Markdown file in the `docs/` directory.
2. Add the file to the table of contents in `docs/index.md`.

### Code Examples

Code examples should be formatted with syntax highlighting:

```python
from apifrom import API

app = API(title="Example API")

@app.add_route("/hello/{name}")
def hello(request):
    name = request.path_params.get("name", "world")
    return {"message": f"Hello, {name}!"}

if __name__ == "__main__":
    app.run()
```

### Cross-References

You can link to other documentation pages using Markdown links:

```markdown
See the [Getting Started](getting_started.md) guide for more information.
```

## Documentation Deployment

The documentation is automatically built and deployed to [Read the Docs](https://apifrom.readthedocs.io/) when changes are pushed to the main branch.

The deployment process is handled by:

1. GitHub Actions workflow (`.github/workflows/readthedocs.yml`) - Builds the documentation and triggers a Read the Docs build
2. Read the Docs configuration (`.readthedocs.yml`) - Configures how Read the Docs builds the documentation

## Documentation Style Guide

- Use clear, concise language
- Include code examples for complex concepts
- Break up long sections with headings
- Use lists and tables to organize information
- Include diagrams where appropriate
- Explain the "why" as well as the "how"

## Getting Help

If you need help with the documentation, please open an issue on GitHub or reach out to the maintainers. 