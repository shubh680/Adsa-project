"""
test_bit_io.py — Test script for the BitWriter and BitReader classes.

Writes a known sequence of bits to a temporary binary file, reads them
back, and verifies that the round-trip is lossless.
"""

import os
import tempfile
from bit_io import BitWriter, BitReader


def test_round_trip(bits: list[int]) -> bool:
    """
    Write `bits` to a temp file and read them back.

    Returns True if the first len(bits) bits read back match exactly,
    False otherwise.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        tmp_path = tmp.name

    try:
        # ── Write ──────────────────────────────────────────────────────────
        with open(tmp_path, "wb") as f:
            writer = BitWriter(f)
            for bit in bits:
                writer.write_bit(bit)
            writer.flush()  # zero-pad and write any leftover bits

        # ── Read ───────────────────────────────────────────────────────────
        recovered = []
        with open(tmp_path, "rb") as f:
            reader = BitReader(f)
            for _ in range(len(bits)):
                bit = reader.read_bit()
                if bit is None:
                    print("  ERROR: unexpected end of file during read.")
                    return False
                recovered.append(bit)

            # Verify EOF behaviour after consuming all meaningful bits.
            extra = reader.read_bit()

        # ── Verify ─────────────────────────────────────────────────────────
        if recovered != bits:
            print(f"  MISMATCH\n    expected : {bits}\n    got      : {recovered}")
            return False

        # Padding bits may still exist in the last byte; that is expected.
        print(f"  OK  — {len(bits)} bits round-tripped successfully.")
        return True

    finally:
        os.unlink(tmp_path)


def test_eof_returns_none() -> bool:
    """Verify that BitReader.read_bit() returns None on an empty file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        tmp_path = tmp.name

    try:
        # Write and immediately flush an empty writer (no bits written).
        with open(tmp_path, "wb") as f:
            BitWriter(f).flush()

        with open(tmp_path, "rb") as f:
            result = BitReader(f).read_bit()
        if result is None:
            print("  OK  — read_bit() correctly returns None on empty file.")
            return True
        else:
            print(f"  ERROR: expected None, got {result!r}")
            return False
    finally:
        os.unlink(tmp_path)


def test_invalid_bit() -> bool:
    """Verify that write_bit() raises ValueError for invalid input."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        tmp_path = tmp.name

    try:
        with open(tmp_path, "wb") as f:
            writer = BitWriter(f)
            try:
                writer.write_bit(5)
                print("  ERROR: ValueError was not raised for bit=5")
                return False
            except ValueError:
                print("  OK  — ValueError raised for invalid bit value.")
                return True
    finally:
        os.unlink(tmp_path)


def main():
    all_passed = True

    print("=" * 55)
    print(" BitWriter / BitReader — Round-Trip Tests")
    print("=" * 55)

    # Test 1: Exact multiple of 8 bits (no padding needed).
    print("\nTest 1: 8-bit sequence (no padding)")
    bits1 = [1, 0, 1, 1, 0, 0, 1, 0]
    all_passed &= test_round_trip(bits1)

    # Test 2: 5 bits — requires 3 padding bits at flush.
    print("\nTest 2: 5-bit sequence (3 padding bits)")
    bits2 = [1, 1, 0, 0, 1]
    all_passed &= test_round_trip(bits2)

    # Test 3: 16 bits spanning two full bytes.
    print("\nTest 3: 16-bit sequence (two full bytes)")
    bits3 = [1, 0, 1, 0, 1, 0, 1, 0,
             0, 1, 0, 1, 0, 1, 0, 1]
    all_passed &= test_round_trip(bits3)

    # Test 4: All-zeros sequence.
    print("\nTest 4: All-zero bits (16 bits)")
    bits4 = [0] * 16
    all_passed &= test_round_trip(bits4)

    # Test 5: All-ones sequence.
    print("\nTest 5: All-one bits (16 bits)")
    bits5 = [1] * 16
    all_passed &= test_round_trip(bits5)

    # Test 6: Single bit.
    print("\nTest 6: Single bit (1)")
    all_passed &= test_round_trip([1])

    # Test 7: EOF returns None.
    print("\nTest 7: EOF returns None on empty file")
    all_passed &= test_eof_returns_none()

    # Test 8: Invalid bit raises ValueError.
    print("\nTest 8: Invalid bit raises ValueError")
    all_passed &= test_invalid_bit()
    print("\n" + "=" * 55)
    if all_passed:
        print(" All tests PASSED ✓")
    else:
        print(" Some tests FAILED ✗")
    print("=" * 55)
if __name__ == "__main__":
    main()
