#!/usr/bin/python3
"""
Setup script for linuxmuster-base7

All static configuration is in pyproject.toml. This file only supplies the
version, which comes from debian/changelog so that the Python metadata shipped
in the .deb matches the package version.
"""

import re
from pathlib import Path

from setuptools import setup


def changelog_version():
    """Return the version of the top debian/changelog entry in PEP 440 form."""
    changelog = Path(__file__).resolve().parent / "debian" / "changelog"
    with changelog.open(encoding="utf-8") as f:
        match = re.match(r"\S+ \(([^)]+)\)", f.readline())
    if not match:
        raise RuntimeError(f"No version in the first line of {changelog}")
    version = match.group(1).split(":", 1)[-1]  # drop the epoch
    version = version.rsplit("-", 1)[0]  # drop a Debian revision
    # PEP 440 has no '~'; a downstream suffix is a local version label there,
    # so 1:7.4.24~edu becomes 7.4.24+edu.
    public, _, local = version.partition("~")
    return f"{public}+{local}" if local else public


setup(version=changelog_version())
