#!/usr/bin/env python3
"""
Version bump utility for NLP2CMD
Usage: python bump_version.py [patch|minor|major]
"""

import re
import sys
from pathlib import Path

def bump_version(version_type):
    """Bump version in pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        sys.exit(1)
    
    # Read current version
    content = pyproject_path.read_text()
    version_match = re.search(r'version = "(\d+\.\d+\.\d+)"', content)
    
    if not version_match:
        print("Error: Version not found in pyproject.toml")
        sys.exit(1)
    
    version = version_match.group(1)
    parts = version.split('.')
    
    # Bump according to type
    if version_type == "patch":
        parts[-1] = str(int(parts[-1]) + 1)
    elif version_type == "minor":
        parts[1] = str(int(parts[1]) + 1)
        parts[2] = "0"
    elif version_type == "major":
        parts[0] = str(int(parts[0]) + 1)
        parts[1] = "0"
        parts[2] = "0"
    else:
        print(f"Error: Invalid version type '{version_type}'. Use patch, minor, or major.")
        sys.exit(1)
    
    new_version = ".".join(parts)
    
    # Update content
    content = re.sub(
        r'version = "\d+\.\d+\.\d+"',
        f'version = "{new_version}"',
        content
    )
    
    # Write back
    pyproject_path.write_text(content)
    print(f"Version bumped to {new_version}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python bump_version.py [patch|minor|major]")
        sys.exit(1)
    
    bump_version(sys.argv[1])
