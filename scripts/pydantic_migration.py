#!/usr/bin/env python
"""
Pydantic Migration Helper Script

This script helps identify and update Pydantic imports and usage patterns
to assist in migrating from Pydantic v1 to v2.

Usage:
    python scripts/pydantic_migration.py [--dry-run] [--path /path/to/code]

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


# Patterns to identify Pydantic imports
PYDANTIC_IMPORT_PATTERNS = [
    r"from\s+pydantic\s+import\s+(.*)",
    r"import\s+pydantic\s+as\s+(.*)",
    r"import\s+pydantic",
]

# Mapping of v1 imports to v2 imports
V1_TO_V2_IMPORT_MAP = {
    "BaseModel": "BaseModel",
    "Field": "Field",
    "validator": "field_validator",
    "root_validator": "model_validator",
    "ValidationError": "ValidationError",
    "parse_obj_as": "TypeAdapter",
    "create_model": "create_model",
    "validate_arguments": "validate_call",
    "Extra": "ConfigDict",
    "Schema": "Field",
    "PrivateAttr": "PrivateAttr",
    "Required": "Required",
    "Json": "Json",
    "SecretStr": "SecretStr",
    "SecretBytes": "SecretBytes",
    "DirectoryPath": "DirectoryPath",
    "FilePath": "FilePath",
    "EmailStr": "EmailStr",
    "NameEmail": "NameEmail",
    "PyObject": "PyObject",
    "Color": "Color",
    "constr": "StringConstraints",
    "conint": "IntConstraints",
    "confloat": "FloatConstraints",
    "condecimal": "DecimalConstraints",
    "conbytes": "BytesConstraints",
    "conlist": "List",
    "conset": "Set",
    "confrozenset": "FrozenSet",
    "condict": "Dict",
}

# Common patterns that need to be updated
PATTERNS_TO_UPDATE = [
    # Config class to model_config
    (r"class\s+Config\s*:", r"model_config = ConfigDict"),
    # validator decorator
    (r"@validator\((.*?)\)", r"@field_validator(\1)"),
    # root_validator decorator
    (r"@root_validator", r"@model_validator"),
    # parse_obj_as usage
    (r"parse_obj_as\((.*?),\s*(.*?)\)", r"TypeAdapter(\1).validate_python(\2)"),
    # validate_arguments
    (r"@validate_arguments", r"@validate_call"),
    # Schema to Field
    (r"Schema\((.*?)\)", r"Field(\1)"),
    # Extra enum
    (r"Extra\.forbid", r"ConfigDict(extra='forbid')"),
    (r"Extra\.ignore", r"ConfigDict(extra='ignore')"),
    (r"Extra\.allow", r"ConfigDict(extra='allow')"),
]


def find_python_files(path: str) -> List[Path]:
    """Find all Python files in the given path."""
    return list(Path(path).rglob("*.py"))


def analyze_file(file_path: Path) -> Tuple[List[str], Dict[str, Set[str]]]:
    """
    Analyze a Python file for Pydantic usage.
    
    Returns:
        Tuple of (lines, import_map) where:
            - lines: List of file lines
            - import_map: Dict mapping import aliases to imported names
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    import_map = {}
    for i, line in enumerate(lines):
        for pattern in PYDANTIC_IMPORT_PATTERNS:
            match = re.match(pattern, line.strip())
            if match:
                if "from pydantic import" in line:
                    imports = match.group(1).split(",")
                    imports = [imp.strip() for imp in imports]
                    import_map["direct"] = set(imports)
                elif "import pydantic as" in line:
                    alias = match.group(1).strip()
                    import_map[alias] = {"*"}
                elif "import pydantic" in line:
                    import_map["pydantic"] = {"*"}
    
    return lines, import_map


def update_imports(lines: List[str], import_map: Dict[str, Set[str]]) -> List[str]:
    """Update Pydantic imports to use v1 module."""
    updated_lines = lines.copy()
    
    for i, line in enumerate(lines):
        if "from pydantic import" in line:
            # Check if any imported names need to be updated
            imports = import_map.get("direct", set())
            v2_imports = []
            v1_imports = []
            
            for imp in imports:
                if imp in V1_TO_V2_IMPORT_MAP:
                    if V1_TO_V2_IMPORT_MAP[imp] != imp:
                        # This import has changed in v2
                        v2_imports.append(f"{imp} as {V1_TO_V2_IMPORT_MAP[imp]}")
                    else:
                        # Import name is the same in v2
                        v2_imports.append(imp)
                else:
                    # Not in our mapping, assume it needs to come from v1
                    v1_imports.append(imp)
            
            new_lines = []
            if v2_imports:
                new_lines.append(f"from pydantic import {', '.join(v2_imports)}\n")
            if v1_imports:
                new_lines.append(f"from pydantic.v1 import {', '.join(v1_imports)}\n")
            
            if new_lines:
                updated_lines[i] = "".join(new_lines)
    
    return updated_lines


def update_patterns(lines: List[str]) -> List[str]:
    """Update common Pydantic v1 patterns to v2 equivalents."""
    updated_lines = []
    
    for line in lines:
        updated_line = line
        for pattern, replacement in PATTERNS_TO_UPDATE:
            updated_line = re.sub(pattern, replacement, updated_line)
        updated_lines.append(updated_line)
    
    return updated_lines


def process_file(file_path: Path, dry_run: bool = False) -> bool:
    """
    Process a single Python file to update Pydantic imports and patterns.
    
    Args:
        file_path: Path to the Python file
        dry_run: If True, only show changes without applying them
        
    Returns:
        True if changes were made, False otherwise
    """
    print(f"Processing {file_path}...")
    
    lines, import_map = analyze_file(file_path)
    
    # Skip files with no Pydantic imports
    if not import_map:
        print(f"  No Pydantic imports found in {file_path}")
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


def main():
    parser = argparse.ArgumentParser(description="Pydantic v1 to v2 migration helper")
    parser.add_argument("--dry-run", action="store_true", help="Only show changes without applying them")
    parser.add_argument("--path", default=".", help="Path to the code directory")
    
    args = parser.parse_args()
    
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
        print("2. Manual review is still necessary, especially for complex Pydantic usage.")
        print("3. Test your code thoroughly after migration.")
        print("4. For more details, see: https://docs.pydantic.dev/latest/migration/")


if __name__ == "__main__":
    main() 