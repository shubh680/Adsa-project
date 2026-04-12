"""
test_rle.py — Unit tests for Run-Length Encoding module.

Tests RLE encoding/decoding with various patterns:
- Single bytes
- Runs of identical bytes
- Mixed patterns
- Edge cases
"""

import sys
from rle import RLE


def test_single_bytes():
    """Test encoding of single unique bytes."""
    data = [1, 2, 3, 4, 5]
    encoded = RLE.encode(data)
    decoded = RLE.decode(encoded)
    assert decoded == data, f"Failed: {data} != {decoded}"
    print("[PASS] Single bytes test passed")


def test_simple_runs():
    """Test encoding of simple byte runs."""
    data = [1, 1, 1, 2, 2, 3]
    encoded = RLE.encode(data)
    decoded = RLE.decode(encoded)
    assert decoded == data, f"Failed: {data} != {decoded}"
    print("[PASS] Simple runs test passed")


def test_long_run():
    """Test encoding of long runs."""
    data = [5] * 200  # 200 identical bytes
    encoded = RLE.encode(data)
    decoded = RLE.decode(encoded)
    assert decoded == data, f"Failed: {len(data)} bytes != {len(decoded)} bytes"
    print("[PASS] Long run test passed")


def test_repetitive_pattern():
    """Test highly repetitive data (logs, text with spaces)."""
    # Simulate log data with repeated spaces and newlines
    data = [ord(' ')] * 50 + [ord('x')] * 5 + [ord('\n')] * 50 + [ord('y')] * 3
    encoded = RLE.encode(data)
    decoded = RLE.decode(encoded)
    assert decoded == data, f"Failed: {len(data)} != {len(decoded)}"
    print(f"[PASS] Repetitive pattern test passed (compression: {len(data)} -> {len(encoded)} bytes)")


def test_escape_byte():
    """Test handling of escape byte (255)."""
    data = [255, 255, 255, 100, 200]
    encoded = RLE.encode(data)
    decoded = RLE.decode(encoded)
    assert decoded == data, f"Failed: {data} != {decoded}"
    print("[PASS] Escape byte test passed")


def test_mixed_escape_and_runs():
    """Test mixed patterns with escape bytes and runs."""
    data = [255, 100, 100, 100, 200, 255, 255]
    encoded = RLE.encode(data)
    decoded = RLE.decode(encoded)
    assert decoded == data, f"Failed: {data} != {decoded}"
    print("[PASS] Mixed escape and runs test passed")


def test_empty_data():
    """Test empty data."""
    data = []
    encoded = RLE.encode(data)
    decoded = RLE.decode(encoded)
    assert decoded == data, f"Failed: {data} != {decoded}"
    print("[PASS] Empty data test passed")


def test_single_byte():
    """Test single byte."""
    data = [42]
    encoded = RLE.encode(data)
    decoded = RLE.decode(encoded)
    assert decoded == data, f"Failed: {data} != {decoded}"
    print("[PASS] Single byte test passed")


def test_all_byte_values():
    """Test all possible byte values."""
    data = list(range(256))  # All byte values 0-255
    encoded = RLE.encode(data)
    decoded = RLE.decode(encoded)
    assert decoded == data, f"Failed: {len(data)} != {len(decoded)}"
    print("[PASS] All byte values test passed")


def test_compression_benefit():
    """Test that RLE actually compresses repetitive data."""
    # Highly repetitive data
    data = [65] * 100  # 100 'A's
    encoded = RLE.encode(data)
    
    # For a run of 100 identical bytes, RLE should encode as [255, 65, 100] + padding
    # This is much better than 100 bytes
    assert len(encoded) < len(data) // 2, f"RLE didn't compress: {len(data)} -> {len(encoded)}"
    print(f"[PASS] Compression benefit test passed ({len(data)} -> {len(encoded)} bytes, {len(encoded)/len(data)*100:.1f}%)")


def run_all_tests():
    """Run all RLE tests."""
    print("Running RLE tests...\n")
    
    try:
        test_single_bytes()
        test_simple_runs()
        test_long_run()
        test_repetitive_pattern()
        test_escape_byte()
        test_mixed_escape_and_runs()
        test_empty_data()
        test_single_byte()
        test_all_byte_values()
        test_compression_benefit()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All RLE tests passed!")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print(f"\n[FAILED] Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
