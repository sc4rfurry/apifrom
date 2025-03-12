# Example Tests

This directory contains tests for the example applications in the `examples/` directory.

## Files

- `test_example.py`: Tests for the basic example API that demonstrates core functionality including:
  - Basic endpoint testing
  - Request body handling
  - JWT authentication
  - API key authentication

## Running the Tests

To run these tests, use the following command from the project root:

```bash
python -m pytest tests/examples
```

Or to run a specific test file:

```bash
python -m pytest tests/examples/test_example.py
``` 