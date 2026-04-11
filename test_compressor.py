"""
test_compressor.py — Test suite for end-to-end compression system.

Tests compression/decompression round-trip for various file types and sizes.
"""

import os
import tempfile
from compressor import Compressor


def test_round_trip(name, data):
    """
    Test compress → decompress → verify match.

    Args:
        name: Test name for output.
        data: Bytes to compress.

    Returns:
        True if test passes, False otherwise.
    """
    compressor = Compressor(verbose=False)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write test data
        input_file = os.path.join(tmpdir, 'input.bin')
        with open(input_file, 'wb') as f:
            f.write(data)

        # Compress
        compressed_file = os.path.join(tmpdir, 'compressed.bin')
        try:
            stats1 = compressor.compress(input_file, compressed_file)
        except Exception as e:
            print(f"  ERROR during compression: {e}")
            return False

        # Decompress
        output_file = os.path.join(tmpdir, 'output.bin')
        try:
            stats2 = compressor.decompress(compressed_file, output_file)
        except Exception as e:
            print(f"  ERROR during decompression: {e}")
            return False

        # Verify
        with open(output_file, 'rb') as f:
            decompressed_data = f.read()

        if decompressed_data != data:
            print(f"  MISMATCH: {len(data)} bytes → {len(decompressed_data)} bytes")
            return False

        ratio = stats1['compression_ratio']
        orig_size = stats1['original_size']
        comp_size = stats1['compressed_size']

        print(f"  OK — {name}")
        print(f"       {orig_size:,} → {comp_size:,} bytes ({ratio:.1%})")

        return True


def test_empty_file():
    """Test empty file."""
    print("Test 1: Empty file")
    return test_round_trip("Empty", b'')


def test_single_byte():
    """Test single byte."""
    print("Test 2: Single byte")
    return test_round_trip("Single byte", b'\x42')


def test_repeated_byte():
    """Test repeated byte (should compress well)."""
    print("Test 3: Repeated byte")
    return test_round_trip("1000 × 'A'", b'A' * 1000)


def test_all_bytes():
    """Test all 256 byte values."""
    print("Test 4: All 256 byte values")
    data = bytes(range(256))
    return test_round_trip("All bytes", data)


def test_random_data():
    """Test random-like data (should not compress)."""
    print("Test 5: Random data")
    import random
    random.seed(42)
    data = bytes(random.randint(0, 255) for _ in range(1000))
    return test_round_trip("1000 random bytes", data)


def test_text_data():
    """Test realistic text data."""
    print("Test 6: Text data")
    text = "The quick brown fox jumps over the lazy dog. " * 100
    data = text.encode('utf-8')
    return test_round_trip(f"Repeated text ({len(data)} bytes)", data)


def test_structured_data():
    """Test structured data (alternating pattern)."""
    print("Test 7: Structured data")
    data = b'ABCABC' * 100
    return test_round_trip("Repeating pattern (600 bytes)", data)


def test_large_file():
    """Test larger file (100 KB)."""
    print("Test 8: Large file")
    # Create 100KB of somewhat compressible data
    chunk = b'ABCDEFGHIJ' * 100  # 1000 bytes
    data = chunk * 100  # 100KB
    return test_round_trip("100 KB of patterned data", data)


def test_binary_file():
    """Test binary file with various byte values."""
    print("Test 9: Binary file")
    data = b''
    for i in range(256):
        data += bytes([i]) * (i % 10 + 1)
    return test_round_trip("Binary sequence", data)


def test_highly_repetitive():
    """Test highly repetitive data (should compress extremely well)."""
    print("Test 10: Highly repetitive")
    data = b'\x00' * 10000 + b'\xFF' * 10000
    return test_round_trip("20KB repetitive (10K zeros + 10K 0xFF)", data)


def test_cli_compress():
    """Test CLI compress command."""
    print("Test 11: CLI compress command")
    import subprocess

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, 'test.txt')
        output_file = os.path.join(tmpdir, 'test.bin')

        # Create test file
        with open(input_file, 'wb') as f:
            f.write(b'Hello World! ' * 100)

        # Run CLI
        try:
            result = subprocess.run(
                ['python3', 'compressor.py', 'compress', input_file, output_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                print(f"  ERROR: CLI failed")
                print(result.stderr)
                return False

            if os.path.exists(output_file):
                print(f"  OK — CLI compress succeeded")
                return True
            else:
                print(f"  ERROR: Output file not created")
                return False

        except Exception as e:
            print(f"  ERROR: {e}")
            return False


def test_cli_decompress():
    """Test CLI decompress command."""
    print("Test 12: CLI decompress command")
    import subprocess

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, 'test.txt')
        compressed_file = os.path.join(tmpdir, 'test.bin')
        output_file = os.path.join(tmpdir, 'recovered.txt')

        # Create and compress
        original_data = b'Hello World! ' * 100
        with open(input_file, 'wb') as f:
            f.write(original_data)

        compressor = Compressor()
        compressor.compress(input_file, compressed_file)

        # Run CLI decompress
        try:
            result = subprocess.run(
                ['python3', 'compressor.py', 'decompress', compressed_file, output_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                print(f"  ERROR: CLI failed")
                return False

            # Verify
            with open(output_file, 'rb') as f:
                recovered_data = f.read()

            if recovered_data == original_data:
                print(f"  OK — CLI decompress succeeded")
                return True
            else:
                print(f"  ERROR: Data mismatch")
                return False

        except Exception as e:
            print(f"  ERROR: {e}")
            return False


def main():
    """Run all tests."""
    all_passed = True

    print("=" * 70)
    print(" Compressor — End-to-End Compression Tests")
    print("=" * 70)
    print()

    all_passed &= test_empty_file()
    print()

    all_passed &= test_single_byte()
    print()

    all_passed &= test_repeated_byte()
    print()

    all_passed &= test_all_bytes()
    print()

    all_passed &= test_random_data()
    print()

    all_passed &= test_text_data()
    print()

    all_passed &= test_structured_data()
    print()

    all_passed &= test_large_file()
    print()

    all_passed &= test_binary_file()
    print()

    all_passed &= test_highly_repetitive()
    print()

    all_passed &= test_cli_compress()
    print()

    all_passed &= test_cli_decompress()
    print()

    print("=" * 70)
    if all_passed:
        print(" All tests PASSED ✓")
    else:
        print(" Some tests FAILED ✗")
    print("=" * 70)


if __name__ == '__main__':
    main()
