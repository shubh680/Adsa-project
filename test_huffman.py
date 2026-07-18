"""
test_huffman.py — Test suite for the Adaptive Huffman encoder/decoder.

Tests verify:
- Round-trip encoding/decoding
- Symbol introduction (NYT splitting)
- Frequency updates
- Edge cases (empty, single symbol, repeated, mixed)
"""

import pytest
from huffman import AdaptiveHuffman


def test_round_trip():
    """
    Test round-trip: encode symbols → decode → verify match.

    Uses separate encoder and decoder instances to test independent streams.
    """
    symbols = [1, 2, 3, 1, 2, 4, 5, 1, 2, 3]
    encoder = AdaptiveHuffman()
    bits = encoder.encode(symbols)
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)

    assert decoded == symbols


def test_empty():
    """Test encoding/decoding empty sequence."""
    encoder = AdaptiveHuffman()
    bits = encoder.encode([])
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)
    assert decoded == []


def test_single_symbol():
    """Test single symbol."""
    encoder = AdaptiveHuffman()
    symbols = [42]
    bits = encoder.encode(symbols)
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)
    assert decoded == symbols


def test_repeated_symbol():
    """Test repeated symbol (should compress well)."""
    encoder = AdaptiveHuffman()
    symbols = [65] * 10  # 'A' repeated 10 times
    bits = encoder.encode(symbols)
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)
    assert decoded == symbols


def test_mixed_symbols():
    """Test mixed sequence of known and unknown symbols."""
    huffman = AdaptiveHuffman()
    symbols = [1, 2, 3, 1, 2, 4, 5, 1, 2, 3]
    bits = huffman.encode(symbols)
    decoded = huffman.decode(bits)
    assert decoded == symbols


def test_all_byte_values():
    """Test all 256 byte values."""
    encoder = AdaptiveHuffman()
    symbols = list(range(256))
    bits = encoder.encode(symbols)
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)
    assert decoded == symbols


def test_long_sequence():
    """Test longer sequence to verify stability."""
    encoder = AdaptiveHuffman()
    # Simulate repeated pattern
    symbols = [65, 66, 67] * 30  # ABC repeated 30 times
    bits = encoder.encode(symbols)
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)
    assert decoded == symbols


def test_nyt_node_creation():
    """Test that NYT node is properly created and split."""
    huffman = AdaptiveHuffman()
    # Check initial state
    assert huffman.root.is_nyt()

    # Encode first symbol
    huffman.encode([42])
    # Check that NYT was split
    assert not huffman.root.is_nyt()
    assert huffman.root.left is not None
    assert huffman.root.right is not None


def test_frequency_tracking():
    """Test that frequencies are updated correctly."""
    huffman = AdaptiveHuffman()
    huffman.encode([1, 1, 1])

    # Node for symbol 1 should have frequency > 0
    assert 1 in huffman.symbol_nodes

    node = huffman.symbol_nodes[1]
    assert node.frequency == 3


def test_bytes_conversion():
    """Test symbol to bits and back conversion."""
    for sym in [0, 1, 127, 128, 255]:
        bits = AdaptiveHuffman._symbol_to_bits(sym)
        recovered = AdaptiveHuffman._bits_to_symbol(bits)
        assert recovered == sym


def test_string_encoding():
    """Test encoding a string."""
    encoder = AdaptiveHuffman()
    text = "hello world"
    symbols = [ord(c) for c in text]
    bits = encoder.encode(symbols)
    
    decoder = AdaptiveHuffman()
    decoded = decoder.decode(bits)
    recovered_text = ''.join(chr(s) for s in decoded)

    assert recovered_text == text
