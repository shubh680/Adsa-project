"""
test_huffman.py — Test suite for the Adaptive Huffman encoder/decoder.

Tests verify:
- Round-trip encoding/decoding
- Symbol introduction (NYT splitting)
- Frequency updates
- Edge cases (empty, single symbol, repeated, mixed)
"""

from huffman import AdaptiveHuffman, Node


def test_round_trip(symbols, name):
    """
    Test round-trip: encode symbols → decode → verify match.

    Uses separate encoder and decoder instances to test independent streams.

    Args:
        symbols: List of symbols to encode.
        name: Test name for output.

    Returns:
        True if test passes, False otherwise.
    """
    encoder = AdaptiveHuffman()
    bits = encoder.encode(symbols)
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)

    if decoded != symbols:
        print(f"  MISMATCH: expected {symbols}, got {decoded}")
        return False

    print(f"  OK — {len(symbols)} symbols round-tripped successfully.")
    if len(symbols) > 0:
        print(f"       {len(bits)} bits generated (compression ratio: {len(bits) / (len(symbols) * 8) * 100:.1f}%)")
    return True


def test_empty():
    """Test encoding/decoding empty sequence."""
    encoder = AdaptiveHuffman()
    bits = encoder.encode([])
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)
    if decoded == []:
        print("  OK — empty sequence handled correctly.")
        return True
    print(f"  MISMATCH: expected [], got {decoded}")
    return False


def test_single_symbol():
    """Test single symbol."""
    encoder = AdaptiveHuffman()
    symbols = [42]
    bits = encoder.encode(symbols)
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)
    if decoded == symbols:
        print(f"  OK — single symbol round-tripped.")
        return True
    print(f"  MISMATCH: expected {symbols}, got {decoded}")
    return False


def test_repeated_symbol():
    """Test repeated symbol (should compress well)."""
    encoder = AdaptiveHuffman()
    symbols = [65] * 10  # 'A' repeated 10 times
    bits = encoder.encode(symbols)
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)
    if decoded == symbols:
        ratio = len(bits) / (len(symbols) * 8) * 100
        print(f"  OK — repeated symbol round-tripped.")
        print(f"       {len(bits)} bits for 10 × 'A' ({ratio:.1f}% of original)")
        return True
    print(f"  MISMATCH: expected {symbols}, got {decoded}")
    return False


def test_mixed_symbols():
    """Test mixed sequence of known and unknown symbols."""
    huffman = AdaptiveHuffman()
    symbols = [1, 2, 3, 1, 2, 4, 5, 1, 2, 3]
    bits = huffman.encode(symbols)
    decoded = huffman.decode(bits)
    if decoded == symbols:
        print(f"  OK — mixed symbol sequence round-tripped.")
        return True
    print(f"  MISMATCH: expected {symbols}, got {decoded}")
    return False


def test_all_byte_values():
    """Test all 256 byte values."""
    encoder = AdaptiveHuffman()
    symbols = list(range(256))
    bits = encoder.encode(symbols)
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)
    if decoded == symbols:
        print(f"  OK — all 256 byte values round-tripped.")
        return True
    print(f"  MISMATCH: values mismatch after encoding/decoding")
    return False


def test_long_sequence():
    """Test longer sequence to verify stability."""
    encoder = AdaptiveHuffman()
    # Simulate repeated pattern
    symbols = [65, 66, 67] * 30  # ABC repeated 30 times
    bits = encoder.encode(symbols)
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)
    if decoded == symbols:
        ratio = len(bits) / (len(symbols) * 8) * 100
        print(f"  OK — long sequence ({len(symbols)} symbols) round-tripped.")
        print(f"       Compression: {len(bits)} bits ({ratio:.1f}% of original)")
        return True
    print(f"  MISMATCH: expected {len(symbols)} symbols, got {len(decoded)}")
    return False


def test_nyt_node_creation():
    """Test that NYT node is properly created and split."""
    huffman = AdaptiveHuffman()
    # Check initial state
    if not huffman.root.is_nyt():
        print("  ERROR: root is not NYT initially")
        return False

    # Encode first symbol
    bits = huffman.encode([42])
    # Check that NYT was split
    if huffman.root.is_nyt():
        print("  ERROR: root is still NYT after encoding first symbol")
        return False
    if huffman.root.left is None or huffman.root.right is None:
        print("  ERROR: root children not created after NYT split")
        return False
    print("  OK — NYT node properly split on first symbol.")
    return True


def test_frequency_tracking():
    """Test that frequencies are updated correctly."""
    huffman = AdaptiveHuffman()
    huffman.encode([1, 1, 1])

    # Node for symbol 1 should have frequency > 0
    if 1 not in huffman.symbol_nodes:
        print("  ERROR: symbol 1 not tracked")
        return False

    node = huffman.symbol_nodes[1]
    if node.frequency != 3:
        print(f"  ERROR: expected frequency 3, got {node.frequency}")
        return False

    print("  OK — frequency tracking works correctly.")
    return True


def test_bytes_conversion():
    """Test symbol to bits and back conversion."""
    for sym in [0, 1, 127, 128, 255]:
        bits = AdaptiveHuffman._symbol_to_bits(sym)
        recovered = AdaptiveHuffman._bits_to_symbol(bits)
        if recovered != sym:
            print(f"  ERROR: symbol {sym} → bits → {recovered}")
            return False

    print("  OK — byte conversion is lossless.")
    return True


def test_string_encoding():
    """Test encoding a string."""
    encoder = AdaptiveHuffman()
    text = "hello world"
    symbols = [ord(c) for c in text]
    bits = encoder.encode(symbols)
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)
    recovered_text = ''.join(chr(s) for s in decoded)

    if recovered_text == text:
        ratio = len(bits) / (len(text) * 8) * 100
        print(f"  OK — string '{text}' encoded and decoded correctly.")
        print(f"       Compression: {len(bits)} bits ({ratio:.1f}% of original)")
        return True
    print(f"  MISMATCH: expected '{text}', got '{recovered_text}'")
    return False


def main():
    all_passed = True

    print("=" * 60)
    print(" Adaptive Huffman (FGK) — Encoding/Decoding Tests")
    print("=" * 60)

    # Test 1: Empty sequence
    print("\nTest 1: Empty sequence")
    all_passed &= test_empty()

    # Test 2: Single symbol
    print("\nTest 2: Single symbol")
    all_passed &= test_single_symbol()

    # Test 3: Repeated symbol
    print("\nTest 3: Repeated symbol (should compress)")
    all_passed &= test_repeated_symbol()

    # Test 4: Mixed symbols
    print("\nTest 4: Mixed known/unknown symbols")
    all_passed &= test_round_trip([1, 2, 3, 1, 2, 4, 5, 1, 2, 3], "mixed")

    # Test 5: All byte values
    print("\nTest 5: All 256 byte values")
    all_passed &= test_all_byte_values()

    # Test 6: Long sequence
    print("\nTest 6: Long sequence (ABC repeated 30 times)")
    all_passed &= test_long_sequence()

    # Test 7: NYT node creation
    print("\nTest 7: NYT node creation and splitting")
    all_passed &= test_nyt_node_creation()

    # Test 8: Frequency tracking
    print("\nTest 8: Frequency tracking")
    all_passed &= test_frequency_tracking()

    # Test 9: Byte conversion
    print("\nTest 9: Symbol ↔ bits conversion")
    all_passed &= test_bytes_conversion()

    # Test 10: String encoding
    print("\nTest 10: String encoding (\"hello world\")")
    all_passed &= test_string_encoding()

    print("\n" + "=" * 60)
    if all_passed:
        print(" All tests PASSED ✓")
    else:
        print(" Some tests FAILED ✗")
    print("=" * 60)


if __name__ == "__main__":
    main()
