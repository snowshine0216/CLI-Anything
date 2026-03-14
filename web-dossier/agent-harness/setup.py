#!/usr/bin/env python3
"""setup.py for cli-anything-web-dossier."""

from pathlib import Path
from setuptools import setup, find_namespace_packages

readme_path = Path("cli_anything/web_dossier/README.md")
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else "CLI harness for web-dossier workflows"

setup(
    name="cli-anything-web-dossier",
    version="1.0.0",
    author="cli-anything contributors",
    description="CLI harness for web-dossier build/test/repo workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/HKUDS/CLI-Anything",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "cli-anything-web-dossier=cli_anything.web_dossier.web_dossier_cli:main",
        ]
    },
    include_package_data=True,
    zip_safe=False,
)
