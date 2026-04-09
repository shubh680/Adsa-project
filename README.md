# Advanced File Compression System

A modular, production-level file compression system built in Python.
The project is developed incrementally in phases, with each phase building on the last.

---

## Project Structure

```
ADSA project/
├── bit_io.py          # Phase 1 — Bit-Level I/O module
├── test_bit_io.py     # Phase 1 — Test suite for BitWriter / BitReader
└── README.md
```

---

## Phase 1 — Bit-Level I/O (`bit_io.py`)

### Overview

The foundation of any compression system is the ability to read and write data at the **bit level**, not just the byte level. This module provides two classes — `BitWriter` and `BitReader` — that wrap a standard Python binary file object and expose a clean, single-bit interface.

No external libraries are used. Everything is built on Python's built-in file I/O and integer bit operations.

---

### How It Works

#### `BitWriter`

Writes individual bits to a binary file.

| Internal State | Purpose |
|----------------|---------|
| `_buffer` | 8-bit integer being assembled |
| `_bit_count` | How many bits have been packed into the buffer |

**Bit packing (MSB-first):**

Each call to `write_bit(bit)` shifts the buffer left by 1 and ORs in the new bit:

```
buffer = (buffer << 1) | bit
```

Once 8 bits are collected, the byte is written to the file and the buffer resets.

**Flushing:**

When writing is complete, `flush()` must be called. If the buffer holds fewer than 8 bits, the remaining positions are zero-padded on the right (LSB side) before writing.

```
Example: bits [1, 1, 0, 0, 1] → stored as byte 11001000
                                                       ^^^
                                                  zero padding
```

#### `BitReader`

Reads individual bits from a binary file.

| Internal State | Purpose |
|----------------|---------|
| `_buffer` | Current byte loaded from file |
| `_bits_left` | How many bits remain unread in the buffer |

Reads one byte at a time from the file and serves bits one at a time from MSB to LSB:

```
bit = (buffer >> bits_left) & 1
```

Returns `None` when the file is exhausted (EOF).

---

### API Reference

#### `BitWriter(file)`

```python
with open("output.bin", "wb") as f:
    writer = BitWriter(f)
    writer.write_bit(1)
    writer.write_bit(0)
    writer.write_bit(1)
    writer.flush()   # always call flush() when done
```

| Method | Description |
|--------|-------------|
| `write_bit(bit: int)` | Write a single bit (0 or 1). Raises `ValueError` for invalid input. |
| `flush()` | Flush remaining bits with zero-padding. Call once at the end. |

#### `BitReader(file)`

```python
with open("output.bin", "rb") as f:
    reader = BitReader(f)
    bit = reader.read_bit()   # returns 0, 1, or None at EOF
```

| Method | Returns | Description |
|--------|---------|-------------|
| `read_bit()` | `int` (0 or 1) or `None` | Read the next bit. Returns `None` at end of file. |

---

### Running the Tests

No installation required. Run directly with Python 3:

```bash
cd "ADSA project"
python3 test_bit_io.py
```

#### Test Cases

| # | Scenario | What it checks |
|---|----------|----------------|
| 1 | 8-bit sequence | Exact byte, no padding needed |
| 2 | 5-bit sequence | Correct zero-padding on `flush()` |
| 3 | 16-bit sequence | Two full bytes, correct ordering |
| 4 | All-zero bits | Boundary case — all 0s |
| 5 | All-one bits | Boundary case — all 1s |
| 6 | Single bit | Minimum possible write |
| 7 | Empty file | `read_bit()` returns `None` at EOF |
| 8 | Invalid bit value | `ValueError` raised for input outside {0, 1} |

#### Expected Output

```
=======================================================
 BitWriter / BitReader — Round-Trip Tests
=======================================================

Test 1: 8-bit sequence (no padding)
  OK  — 8 bits round-tripped successfully.

Test 2: 5-bit sequence (3 padding bits)
  OK  — 5 bits round-tripped successfully.

Test 3: 16-bit sequence (two full bytes)
  OK  — 16 bits round-tripped successfully.

Test 4: All-zero bits (16 bits)
  OK  — 16 bits round-tripped successfully.

Test 5: All-one bits (16 bits)
  OK  — 16 bits round-tripped successfully.

Test 6: Single bit (1)
  OK  — 1 bits round-tripped successfully.

Test 7: EOF returns None on empty file
  OK  — read_bit() correctly returns None on empty file.

Test 8: Invalid bit raises ValueError
  OK  — ValueError raised for invalid bit value.

=======================================================
 All tests PASSED ✓
=======================================================
```

---

### Design Decisions

- **MSB-first bit ordering** — consistent with standard binary encoding and required for correct Huffman code reconstruction.
- **Zero-padding on flush** — the decoder must know the original bit count to avoid reading padding. This is typically handled by encoding the length in the file header (to be implemented in a later phase).
- **No external dependencies** — only Python built-ins are used, keeping the module portable and lightweight.
- **Clean interface** — `BitWriter` and `BitReader` accept any file-like object, making them easy to test with `io.BytesIO` as well.

---

## Requirements

- Python 3.10 or higher
- No external packages

---

## Upcoming Phases

| Phase | Module | Description |
|-------|--------|-------------|
| 1 ✅ | `bit_io.py` | Bit-level file I/O |
| 2 | `huffman.py` | Adaptive Huffman encoding / decoding |
| 3 | `compressor.py` | End-to-end compress / decompress pipeline |
