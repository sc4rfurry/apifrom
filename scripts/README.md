# Migration Scripts

This directory contains scripts to help with migrating between different versions of dependencies and addressing security vulnerabilities.

## Pydantic Migration Helper

The `pydantic_migration.py` script helps migrate code from Pydantic v1 to v2, which is a major breaking change in the updated dependencies.

### Usage

```bash
# Run in dry-run mode (show changes without applying them)
python scripts/pydantic_migration.py --dry-run

# Run on a specific directory
python scripts/pydantic_migration.py --path apifrom/models

# Apply changes to all Python files in the project
python scripts/pydantic_migration.py
```

### What it does

1. Identifies Pydantic imports in Python files
2. Updates import statements to use the appropriate modules in Pydantic v2
3. Updates common patterns like:
   - `class Config:` to `model_config = ConfigDict`
   - `@validator` to `@field_validator`
   - `@root_validator` to `@model_validator`
   - And more

### Limitations

- The script performs basic migrations but may not catch all cases
- Manual review is still necessary, especially for complex Pydantic usage
- Test your code thoroughly after migration

## Python-Jose to PyJWT Migration Helper

The `jose_to_pyjwt_migration.py` script helps migrate code from python-jose to PyJWT, which is recommended for better security.

### Usage

```bash
# Run in dry-run mode (show changes without applying them)
python scripts/jose_to_pyjwt_migration.py --dry-run

# Run on a specific directory
python scripts/jose_to_pyjwt_migration.py --path apifrom/security

# Apply changes to all Python files in the project
python scripts/jose_to_pyjwt_migration.py
```

### What it does

1. Updates `requirements.txt` to replace python-jose with PyJWT
2. Identifies python-jose imports in Python files
3. Updates import statements to use PyJWT
4. Updates common patterns for JWT encoding and decoding
5. Updates exception handling

### Limitations

- PyJWT has some differences from python-jose:
  - No direct JWE support (encryption)
  - Different exception hierarchy
  - Slightly different API for some functions
- Manual review is necessary, especially for complex JWT usage
- Test your code thoroughly after migration

## General Migration Process

When migrating to the updated dependencies, follow these steps:

1. Create a backup of your code
2. Update `requirements.txt` with the new versions
3. Run the migration scripts in dry-run mode to see what changes will be made
4. Run the migration scripts to apply the changes
5. Manually review and fix any issues that the scripts couldn't handle
6. Run tests to ensure everything works correctly
7. Deploy the updated code

## Additional Resources

- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [Security Advisory](../SECURITY_ADVISORY.md) for details on the security vulnerabilities addressed 