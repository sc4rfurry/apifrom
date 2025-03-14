import os
import re
from setuptools import setup, find_packages

# Read version from __init__.py
with open(os.path.join("apifrom", "__init__.py"), "r") as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        version = "1.0.0"  # Default to 1.0.0 if not found

# Read requirements from requirements.txt
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f.readlines() if not line.startswith("#") and line.strip()]

# Read README.md for long description
try:
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except UnicodeDecodeError:
    # Fallback if there are encoding issues
    long_description = "APIFromAnything - Transform any Python function into a REST API endpoint."

setup(
    name="apifrom",
    version=version,  # Use the extracted version
    description="Transform any Python function into a REST API endpoint.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="sc4rfurry",
    author_email="info@apifrom.example.com",
    url="https://github.com/sc4rfurry/apifrom",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # Core dependencies
        "starlette>=0.20.0",
        "pydantic>=1.8.0",
        "uvicorn>=0.17.0",
        "typing-extensions>=4.0.0",
        "python-multipart>=0.0.5",
        "jinja2>=3.0.0",
        "httpx>=0.22.0",
        # Security
        "pyjwt>=2.4.0",
        "cryptography>=37.0.0",
        "passlib>=1.7.4",
    ],
    extras_require={
        "database": [
            "sqlalchemy>=1.4.0",
            "asyncpg>=0.25.0",  # For PostgreSQL
            "aiomysql>=0.1.0",  # For MySQL
            "aiosqlite>=0.17.0",  # For SQLite
        ],
        "cache": [
            "redis>=4.3.0",
            "aioredis>=2.0.0",
        ],
        "monitoring": [
            "prometheus-client>=0.14.0",
        ],
        "dev": [
            "pytest>=7.1.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=3.0.0",
            "black>=22.3.0",
            "isort>=5.10.0",
            "mypy>=0.950",
            "flake8>=4.0.0",
        ],
        "docs": [
            "sphinx>=4.5.0",
            "sphinx-rtd-theme>=1.0.0",
            "recommonmark>=0.7.1",
            "sphinx-markdown-tables>=0.0.15",
            "sphinx-autodoc-typehints>=1.18.3",
            "sphinx-copybutton>=0.5.0",
            "sphinx-tabs>=3.4.0",
            "sphinx-togglebutton>=0.3.2",
            "myst-parser>=0.18.1",
            "sphinx-design>=0.3.0",
            "sphinx-notfound-page>=0.8.3",
            "sphinx-prompt>=1.5.0",
            "sphinx-inline-tabs>=2022.1.2b11",
            "sphinx-autoapi>=2.0.0",
        ],
        "all": [
            "sqlalchemy>=1.4.0",
            "asyncpg>=0.25.0",
            "aiomysql>=0.1.0",
            "aiosqlite>=0.17.0",
            "redis>=4.3.0",
            "aioredis>=2.0.0",
            "prometheus-client>=0.14.0",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.7",
    keywords="api, rest, web, async, framework",
    project_urls={
        "Homepage": "https://github.com/sc4rfurry/apifrom",
        "Bug Tracker": "https://github.com/sc4rfurry/apifrom/issues",
        "Documentation": "https://github.com/sc4rfurry/apifrom/blob/main/README.md",
        "Source Code": "https://github.com/sc4rfurry/apifrom",
    },
) 