#!/usr/bin/env python
"""
Python-Jose to PyJWT Migration Helper Script

This script helps identify and update python-jose imports and usage patterns
to assist in migrating to PyJWT, which has better security practices.

Usage:
    python scripts/jose_to_pyjwt_migration.py [--dry-run] [--path /path/to/code]

Options:
    --dry-run  Only show changes without applying them
    --path     Path to the code directory (default: current directory)
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Set


# Patterns to identify python-jose imports
JOSE_IMPORT_PATTERNS = [
    r"from\s+jose\s+import\s+(.*)",
    r"import\s+jose\s+as\s+(.*)",
    r"import\s+jose",
    r"from\s+jose\.(.*?)\s+import\s+(.*)",
]

# Mapping of jose imports to PyJWT imports
JOSE_TO_PYJWT_IMPORT_MAP = {
    "jwt": "jwt",
    "jws": "jwt",
    "jwe": None,  # PyJWT doesn't have direct JWE support
    "jwk": None,  # PyJWT doesn't have direct JWK support
    "exceptions": "exceptions",
}

# Common patterns that need to be updated
PATTERNS_TO_UPDATE = [
    # jwt.encode
    (r"jwt\.encode\((.*?),\s*(.*?),\s*algorithm=(.*?)\)", r"jwt.encode(\1, \2, algorithm=\3)"),
    # jwt.decode with audience
    (r"jwt\.decode\((.*?),\s*(.*?),\s*algorithms=(.*?),\s*audience=(.*?)\)", 
     r"jwt.decode(\1, \2, algorithms=\3, audience=\4)"),
    # jwt.decode without audience
    (r"jwt\.decode\((.*?),\s*(.*?),\s*algorithms=(.*?)\)", 
     r"jwt.decode(\1, \2, algorithms=\3)"),
    # JWTError to PyJWTError
    (r"except\s+jwt\.JWTError", r"except jwt.PyJWTError"),
    # ExpiredSignatureError
    (r"except\s+jwt\.ExpiredSignatureError", r"except jwt.ExpiredSignatureError"),
]


def find_python_files(path: str) -> List[Path]:
    """Find all Python files in the given path."""
    return list(Path(path).rglob("*.py"))


def analyze_file(file_path: Path) -> Tuple[List[str], Dict[str, Set[str]]]:
    """
    Analyze a Python file for python-jose usage.
    
    Returns:
        Tuple of (lines, import_map) where:
            - lines: List of file lines
            - import_map: Dict mapping import aliases to imported names
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    import_map = {}
    for i, line in enumerate(lines):
        for pattern in JOSE_IMPORT_PATTERNS:
            match = re.match(pattern, line.strip())
            if match:
                if "from jose import" in line:
                    imports = match.group(1).split(",")
                    imports = [imp.strip() for imp in imports]
                    import_map["direct"] = set(imports)
                elif "import jose as" in line:
                    alias = match.group(1).strip()
                    import_map[alias] = {"*"}
                elif "import jose" in line:
                    import_map["jose"] = {"*"}
                elif "from jose." in line:
                    module = match.group(1).strip()
                    imports = match.group(2).split(",")
                    imports = [imp.strip() for imp in imports]
                    import_map[f"jose.{module}"] = set(imports)
    
    return lines, import_map


def update_imports(lines: List[str], import_map: Dict[str, Set[str]]) -> List[str]:
    """Update python-jose imports to use PyJWT."""
    updated_lines = lines.copy()
    
    for i, line in enumerate(lines):
        if "from jose import" in line:
            # Check if any imported names need to be updated
            imports = import_map.get("direct", set())
            jwt_imports = []
            
            for imp in imports:
                if imp == "jwt":
                    jwt_imports.append(imp)
            
            if jwt_imports:
                updated_lines[i] = f"import jwt\n"
            else:
                # Keep the line as is if we're not importing jwt
                pass
        
        elif "from jose.jwt import" in line:
            # Replace with PyJWT imports
            imports = import_map.get("jose.jwt", set())
            updated_lines[i] = f"from jwt import {', '.join(imports)}\n"
        
        elif "import jose" in line:
            # Replace with PyJWT import
            updated_lines[i] = "import jwt\n"
    
    return updated_lines


def update_patterns(lines: List[str]) -> List[str]:
    """Update common python-jose patterns to PyJWT equivalents."""
    updated_lines = []
    
    for line in lines:
        updated_line = line
        for pattern, replacement in PATTERNS_TO_UPDATE:
            updated_line = re.sub(pattern, replacement, updated_line)
        updated_lines.append(updated_line)
    
    return updated_lines


def process_file(file_path: Path, dry_run: bool = False) -> bool:
    """
    Process a single Python file to update python-jose imports and patterns.
    
    Args:
        file_path: Path to the Python file
        dry_run: If True, only show changes without applying them
        
    Returns:
        True if changes were made, False otherwise
    """
    print(f"Processing {file_path}...")
    
    lines, import_map = analyze_file(file_path)
    
    # Skip files with no python-jose imports
    if not import_map:
        print(f"  No python-jose imports found in {file_path}")
        return False
    
    # Update imports
    updated_lines = update_imports(lines, import_map)
    
    # Update patterns
    updated_lines = update_patterns(updated_lines)
    
    # Check if any changes were made
    if updated_lines == lines:
        print(f"  No changes needed for {file_path}")
        return False
    
    # Show diff
    print(f"  Changes for {file_path}:")
    for i, (old, new) in enumerate(zip(lines, updated_lines)):
        if old != new:
            print(f"    Line {i+1}:")
            print(f"      - {old.strip()}")
            print(f"      + {new.strip()}")
    
    # Write changes if not dry run
    if not dry_run:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)
        print(f"  Updated {file_path}")
    
    return True


def add_pyjwt_to_requirements(path: str, dry_run: bool = False) -> None:
    """Add PyJWT to requirements.txt and update python-jose."""
    requirements_path = Path(path) / "requirements.txt"
    if not requirements_path.exists():
        print("requirements.txt not found, skipping update")
        return
    
    with open(requirements_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    updated_lines = []
    jose_found = False
    pyjwt_found = False
    
    for line in lines:
        if "python-jose" in line:
            jose_found = True
            # Comment out python-jose
            updated_lines.append(f"# {line.strip()} # Replaced with PyJWT\n")
        elif "pyjwt" in line.lower():
            pyjwt_found = True
            updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Add PyJWT if not already present
    if jose_found and not pyjwt_found:
        updated_lines.append("PyJWT[crypto]==2.8.0  # Added as replacement for python-jose\n")
    
    if updated_lines != lines:
        print("Updating requirements.txt to include PyJWT")
        if not dry_run:
            with open(requirements_path, "w", encoding="utf-8") as f:
                f.writelines(updated_lines)
            print("  Updated requirements.txt")
        else:
            print("  Would update requirements.txt (dry run)")


def main():
    parser = argparse.ArgumentParser(description="Python-Jose to PyJWT migration helper")
    parser.add_argument("--dry-run", action="store_true", help="Only show changes without applying them")
    parser.add_argument("--path", default=".", help="Path to the code directory")
    
    args = parser.parse_args()
    
    # Update requirements.txt
    add_pyjwt_to_requirements(args.path, args.dry_run)
    
    python_files = find_python_files(args.path)
    print(f"Found {len(python_files)} Python files to process")
    
    changed_files = 0
    for file_path in python_files:
        if process_file(file_path, args.dry_run):
            changed_files += 1
    
    print(f"\nSummary: {changed_files} files would be changed" if args.dry_run else f"\nSummary: {changed_files} files were updated")
    
    if changed_files > 0:
        print("\nNotes:")
        print("1. This script performs basic migrations but may not catch all cases.")
        print("2. Manual review is still necessary, especially for complex JWT usage.")
        print("3. PyJWT has some differences from python-jose:")
        print("   - No direct JWE support (encryption)")
        print("   - Different exception hierarchy")
        print("   - Slightly different API for some functions")
        print("4. Test your code thoroughly after migration.")
        print("5. For more details, see: https://pyjwt.readthedocs.io/")


if __name__ == "__main__":
    main() 