# GitHub and ReadTheDocs Deployment

This guide provides detailed instructions for setting up continuous integration, deployment, and documentation publishing for your APIFromAnything project using GitHub Actions and ReadTheDocs.

## Overview

The deployment setup consists of several components:

1. **GitHub Actions Workflows** for:
   - Testing and publishing Python packages to PyPI
   - Building and deploying documentation to GitHub Pages
   - Triggering documentation builds on ReadTheDocs
   - Building and publishing Docker images

2. **ReadTheDocs Configuration** for hosting comprehensive documentation

## GitHub Actions Setup

### Prerequisites

Before setting up the GitHub Actions workflows, you need to:

1. Create a GitHub repository for your project
2. Push your code to the repository
3. Set up the necessary secrets in your repository settings

### Required Secrets

Set up the following secrets in your GitHub repository:

1. **PYPI_API_TOKEN**: API token for publishing to PyPI
2. **DOCKERHUB_USERNAME**: Your Docker Hub username
3. **DOCKERHUB_TOKEN**: Your Docker Hub access token
4. **RTDS_WEBHOOK_URL**: ReadTheDocs webhook URL
5. **RTDS_WEBHOOK_TOKEN**: ReadTheDocs webhook token

To add these secrets:

1. Go to your GitHub repository
2. Click on "Settings" > "Secrets and variables" > "Actions"
3. Click on "New repository secret"
4. Add each secret with its corresponding value

### Workflow Files

The following workflow files should be placed in the `.github/workflows/` directory:

#### 1. Python Package Workflow (`python-package.yml`)

This workflow tests your Python package and publishes it to PyPI when a new tag is pushed.

```yaml
name: Python Package

on:
  push:
    branches: [ main, master ]
    tags:
      - 'v*'
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
        cache: 'pip'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install pytest pytest-asyncio pytest-cov flake8 mypy
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        pip install -e .
    - name: Lint with flake8
      run: |
        # stop the build if there are Python syntax errors or undefined names
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        # exit-zero treats all errors as warnings
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    - name: Type check with mypy
      run: |
        mypy --ignore-missing-imports apifrom/
    - name: Test with pytest
      run: |
        pytest --cov=apifrom tests/

  build-and-publish:
    needs: test
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: |
        python -m build
    - name: Publish package to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        user: __token__
        password: ${{ secrets.PYPI_API_TOKEN }}
        skip_existing: true
```

#### 2. Documentation Workflow (`docs.yml`)

This workflow builds and deploys your documentation to GitHub Pages.

```yaml
name: Documentation

on:
  push:
    branches: [ main, master ]
    paths:
      - 'docs/**'
      - 'mkdocs.yml'
      - '.github/workflows/docs.yml'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'docs/**'
      - 'mkdocs.yml'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install mkdocs mkdocs-material mkdocstrings
          pip install -r requirements.txt
      
      - name: Build documentation
        run: mkdocs build
      
      - name: Upload documentation artifact
        uses: actions/upload-artifact@v3
        with:
          name: site
          path: site/
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master')
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Download documentation artifact
        uses: actions/download-artifact@v3
        with:
          name: site
          path: site
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
          force_orphan: true
          user_name: 'github-actions[bot]'
          user_email: 'github-actions[bot]@users.noreply.github.com'
          commit_message: 'Deploy documentation updates'
```

#### 3. ReadTheDocs Workflow (`readthedocs.yml`)

This workflow triggers a build on ReadTheDocs when documentation files are updated.

```yaml
name: ReadTheDocs

on:
  push:
    branches: [ main, master ]
    paths:
      - 'docs/**'
      - '.readthedocs.yml'
      - 'docs/requirements.txt'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'docs/**'
      - '.readthedocs.yml'
      - 'docs/requirements.txt'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Trigger ReadTheDocs build
        uses: dfm/rtds-action@v1
        with:
          webhook_url: ${{ secrets.RTDS_WEBHOOK_URL }}
          webhook_token: ${{ secrets.RTDS_WEBHOOK_TOKEN }}
          commit_ref: ${{ github.ref }}
```

#### 4. Docker Workflow (`docker.yml`)

This workflow builds and publishes Docker images to Docker Hub and GitHub Container Registry.

```yaml
name: Docker

on:
  push:
    branches: [ main, master ]
    tags: [ 'v*' ]
    paths:
      - 'Dockerfile'
      - 'docker-compose.yml'
      - 'docker/**'
      - 'apifrom/**'
      - 'requirements.txt'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'Dockerfile'
      - 'docker-compose.yml'
      - 'docker/**'
      - 'apifrom/**'
      - 'requirements.txt'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to DockerHub
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Login to GitHub Container Registry
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.repository_owner }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata for Docker
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: |
            apifrom/apifrom
            ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## ReadTheDocs Setup

### Prerequisites

Before setting up ReadTheDocs, you need to:

1. Create an account on [ReadTheDocs](https://readthedocs.org/)
2. Connect your GitHub account to ReadTheDocs
3. Import your repository into ReadTheDocs

### Configuration File

Create a `.readthedocs.yml` file in the root of your repository:

```yaml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.10"

python:
  install:
    - requirements: docs/requirements.txt
    - method: pip
      path: .
      extra_requirements:
        - docs

mkdocs:
  configuration: mkdocs.yml
```

### Documentation Requirements

Create a `docs/requirements.txt` file with the necessary dependencies:

```
mkdocs==1.4.2
mkdocs-material==9.1.5
mkdocstrings==0.21.2
mkdocstrings-python==1.1.2
pymdown-extensions==10.0.1
pygments==2.15.1
markdown==3.3.7
jinja2==3.1.2
```

### MkDocs Configuration

Create a `mkdocs.yml` file in the root of your repository:

```yaml
site_name: APIFromAnything
site_description: Transform Python functions into API endpoints with minimal code changes
site_author: APIFromAnything Team
site_url: https://apifrom.readthedocs.io/

repo_name: apifrom/apifrom
repo_url: https://github.com/apifrom/apifrom
edit_uri: edit/main/docs/

theme:
  name: material
  palette:
    primary: indigo
    accent: indigo
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - search.highlight
    - search.share
    - content.code.copy
  icon:
    repo: fontawesome/brands/github

markdown_extensions:
  - admonition
  - attr_list
  - codehilite
  - footnotes
  - meta
  - pymdownx.arithmatex
  - pymdownx.betterem
  - pymdownx.caret
  - pymdownx.critic
  - pymdownx.details
  - pymdownx.emoji:
      emoji_index: !!python/name:materialx.emoji.twemoji
      emoji_generator: !!python/name:materialx.emoji.to_svg
  - pymdownx.highlight
  - pymdownx.inlinehilite
  - pymdownx.keys
  - pymdownx.mark
  - pymdownx.smartsymbols
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.tasklist:
      custom_checkbox: true
  - pymdownx.tilde
  - toc:
      permalink: true

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          setup_commands:
            - import sys
            - sys.path.append(".")
          selection:
            docstring_style: google
          rendering:
            show_source: true
            show_root_heading: true
            show_root_full_path: false
            show_category_heading: true
            show_if_no_docstring: false

nav:
  - Home: index.md
  - Getting Started: getting_started.md
  - Core Concepts: core_concepts.md
  - API Reference: api_reference.md
  - Middleware: middleware.md
  - Security: security.md
  - Performance: performance.md
  - Testing: testing.md
  - Deployment: 
    - Overview: deployment.md
    - GitHub & ReadTheDocs: github_deployment.md
  - Serverless: serverless.md
  - Advanced Caching: advanced_caching.md
  - Plugins: plugins.md
  - Troubleshooting: troubleshooting.md
  - Migration Guide: migration_guide.md
  - Monitoring: monitoring.md
  - Environment & Monitoring: environment_and_monitoring.md
  - Production Readiness: production_readiness.md
  - Contributing: contributing.md

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/apifrom/apifrom
    - icon: fontawesome/brands/python
      link: https://pypi.org/project/apifrom/
  version:
    provider: mike

copyright: Copyright &copy; 2025 APIFromAnything Team
```

## Setting Up ReadTheDocs Webhooks

To set up the ReadTheDocs webhook for automatic builds:

1. Go to your project on ReadTheDocs
2. Click on "Admin" > "Integrations"
3. Click on "Add integration" > "GitHub incoming webhook"
4. Copy the webhook URL and token
5. Add them as secrets in your GitHub repository:
   - `RTDS_WEBHOOK_URL`: The webhook URL
   - `RTDS_WEBHOOK_TOKEN`: The webhook token

## GitHub Pages Setup

To set up GitHub Pages for your documentation:

1. Go to your GitHub repository
2. Click on "Settings" > "Pages"
3. Under "Source", select "GitHub Actions"
4. The `docs.yml` workflow will automatically deploy your documentation to GitHub Pages

## Versioning Documentation

To version your documentation:

1. Install the `mike` tool:
   ```bash
   pip install mike
   ```

2. Build a specific version:
   ```bash
   mike deploy 1.0.0
   ```

3. Set the default version:
   ```bash
   mike set-default 1.0.0
   ```

4. Push the changes:
   ```bash
   git push origin gh-pages
   ```

## Releasing a New Version

To release a new version of your package:

1. Update the version number in your package (e.g., in `setup.py` or `pyproject.toml`)
2. Update the `CHANGELOG.md` file with the changes
3. Commit the changes:
   ```bash
   git add .
   git commit -m "Release v1.0.0"
   ```
4. Create a new tag:
   ```bash
   git tag v1.0.0
   ```
5. Push the changes and tag:
   ```bash
   git push origin main
   git push origin v1.0.0
   ```

The GitHub Actions workflows will automatically:
- Run tests on the code
- Build and publish the package to PyPI
- Build and deploy the documentation to GitHub Pages
- Trigger a build on ReadTheDocs
- Build and publish Docker images

## Troubleshooting

### GitHub Actions Issues

If you encounter issues with GitHub Actions:

1. Check the workflow run logs for error messages
2. Verify that all required secrets are set correctly
3. Ensure that your repository has the necessary permissions

### ReadTheDocs Issues

If you encounter issues with ReadTheDocs:

1. Check the build logs on ReadTheDocs
2. Verify that your `.readthedocs.yml` file is correct
3. Ensure that all required dependencies are listed in `docs/requirements.txt`

### Docker Build Issues

If you encounter issues with Docker builds:

1. Check the workflow run logs for error messages
2. Verify that your `Dockerfile` is correct
3. Ensure that all required secrets are set correctly

## Best Practices

### Documentation

- Keep your documentation up-to-date with code changes
- Use clear and concise language
- Include code examples and screenshots
- Organize documentation logically
- Test documentation links regularly

### Continuous Integration

- Run tests on all pull requests
- Maintain high test coverage
- Use linting and type checking
- Automate as much of the release process as possible

### Versioning

- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Document all changes in the `CHANGELOG.md` file
- Tag releases in Git
- Version documentation to match code releases

## Conclusion

By following this guide, you have set up a comprehensive CI/CD pipeline for your APIFromAnything project, including:

- Automated testing and package publishing
- Documentation building and deployment
- Docker image building and publishing

This setup ensures that your code is thoroughly tested, your documentation is always up-to-date, and your package is easily accessible to users.
