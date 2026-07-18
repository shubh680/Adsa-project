# Debt Report

## huffman.py
- Debt: 40/100
- Observations: Missing type hints, some methods (like `_decode_symbol`) are slightly complex.
- Suggested Refactors:
    - Add type hints to all method signatures and class attributes.
    - Break down `_decode_symbol` into smaller, more focused private methods.
    - Improve error handling in `decode` to provide more context.

## rle.py
- Debt: 30/100
- Observations: Straightforward implementation.
- Suggested Refactors:
    - Add type hints to `encode` and `decode` methods.
    - Consider defining a custom exception for encoding errors.
    - The `decode` method could benefit from slightly more descriptive variable names for the internal buffer.

## Other files
Documentation and tests added to all core files.
