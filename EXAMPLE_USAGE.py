"""
EXAMPLE_USAGE.md - Complete RLE Compression Examples

This file demonstrates how to use the new RLE compression system
with practical examples and code snippets.
"""

# ============================================================================
# EXAMPLE 1: Basic Compression with RLE (Recommended for Repetitive Data)
# ============================================================================

from compressor_with_rle import CompressorWithRLE

# Create compressor with RLE enabled (default)
compressor = CompressorWithRLE(verbose=True, use_rle=True)

# Compress a file
stats = compressor.compress('input.txt', 'output.bin')

print(f"Original size: {stats['original_size']} bytes")
print(f"Compressed size: {stats['compressed_size']} bytes")
print(f"Compression ratio: {stats['compression_ratio']:.2%}")
print(f"RLE preprocessing: {stats['pre_rle_size']} -> {stats['post_rle_size']} bytes")

# Output example:
# Original size: 10000 bytes
# Compressed size: 28 bytes
# Compression ratio: 0.28%
# RLE preprocessing: 10000 -> 120 bytes


# ============================================================================
# EXAMPLE 2: Compression Without RLE (For Non-Repetitive Data)
# ============================================================================

# Create compressor with RLE disabled
compressor = CompressorWithRLE(verbose=True, use_rle=False)

# Compress without preprocessing
stats = compressor.compress('varied_data.txt', 'output.bin')

# This skips Stage 1 (RLE) and goes directly to Huffman encoding
# Better for files that don't have repetitive patterns


# ============================================================================
# EXAMPLE 3: Decompression (Auto-Detects Format)
# ============================================================================

compressor = CompressorWithRLE(verbose=True)

# Decompress any file - automatically detects if RLE was used
stats = compressor.decompress('output.bin', 'recovered.txt')

print(f"RLE was used: {stats['rle_used']}")
# The system automatically detects version and applies correct decompression


# ============================================================================
# EXAMPLE 4: Batch Processing Multiple Files
# ============================================================================

import os

files_to_compress = [
    'log1.txt',
    'log2.txt',
    'document.txt',
    'data.csv',
]

compressor = CompressorWithRLE(verbose=True, use_rle=True)

results = {}
for filename in files_to_compress:
    if os.path.exists(filename):
        output = filename + '.compressed'
        stats = compressor.compress(filename, output)
        results[filename] = {
            'original': stats['original_size'],
            'compressed': stats['compressed_size'],
            'ratio': stats['compression_ratio']
        }

# Print summary
print("\nCompression Summary:")
print("-" * 60)
for filename, data in results.items():
    ratio_pct = data['ratio'] * 100
    print(f"{filename:20} {data['original']:>10} -> {data['compressed']:>10} ({ratio_pct:>6.2f}%)")


# ============================================================================
# EXAMPLE 5: Comparison - With and Without RLE
# ============================================================================

# Test same file with and without RLE
test_file = 'repetitive.txt'

# With RLE
compressor_rle = CompressorWithRLE(use_rle=True)
stats_rle = compressor_rle.compress(test_file, 'output_rle.bin')

# Without RLE
compressor_no_rle = CompressorWithRLE(use_rle=False)
stats_no_rle = compressor_no_rle.compress(test_file, 'output_no_rle.bin')

# Compare
print(f"\nCompression Comparison for {test_file}:")
print(f"  Original size:     {stats_rle['original_size']:,} bytes")
print(f"  With RLE:          {stats_rle['compressed_size']:,} bytes ({stats_rle['compression_ratio']:.2%})")
print(f"  Without RLE:       {stats_no_rle['compressed_size']:,} bytes ({stats_no_rle['compression_ratio']:.2%})")

improvement = (1 - stats_rle['compressed_size'] / stats_no_rle['compressed_size']) * 100
print(f"  RLE Improvement:   {improvement:.1f}% better")


# ============================================================================
# EXAMPLE 6: Direct RLE Usage (Advanced)
# ============================================================================

from rle import RLE

# Manually compress with RLE
data = [ord('A')] * 100 + [ord('B')] * 50 + [1, 2, 3, 4, 5]
encoded = RLE.encode(data)
decoded = RLE.decode(encoded)

print(f"\nDirect RLE Usage:")
print(f"  Original: {len(data)} bytes")
print(f"  Encoded:  {len(encoded)} bytes")
print(f"  Ratio:    {len(encoded)/len(data)*100:.1f}%")
print(f"  Verified: {data == decoded}")


# ============================================================================
# EXAMPLE 7: Error Handling
# ============================================================================

try:
    compressor = CompressorWithRLE(verbose=False)
    stats = compressor.compress('nonexistent.txt', 'output.bin')
except FileNotFoundError as e:
    print(f"Error: File not found - {e}")

# The system provides error messages for various failure cases
# - File not found
# - Permission denied
# - Disk full
# - Corrupted compressed data


# ============================================================================
# EXAMPLE 8: Performance Measurement
# ============================================================================

import time

compressor = CompressorWithRLE(use_rle=True)

start = time.time()
stats = compressor.compress('large_file.txt', 'output.bin')
elapsed = time.time() - start

speed = stats['original_size'] / (1024 * 1024 * elapsed)  # MB/s
print(f"\nPerformance:")
print(f"  Compression time: {elapsed:.3f} seconds")
print(f"  Compression speed: {speed:.1f} MB/s")
print(f"  Ratio achieved: {stats['compression_ratio']:.2%}")


# ============================================================================
# EXAMPLE 9: Recommended Usage Patterns
# ============================================================================

# PATTERN 1: Compress logs (highly repetitive)
# -> Use RLE + Huffman
compressor = CompressorWithRLE(use_rle=True)
compressor.compress('app.log', 'app.log.compressed')
# Expected: 90%+ reduction

# PATTERN 2: Compress source code (moderately repetitive)
# -> Use RLE + Huffman
compressor = CompressorWithRLE(use_rle=True)
compressor.compress('main.py', 'main.py.compressed')
# Expected: 40-60% reduction

# PATTERN 3: Compress already compressed files (no benefit)
# -> Skip RLE to avoid overhead
compressor = CompressorWithRLE(use_rle=False)
compressor.compress('archive.zip', 'archive.zip.compressed')

# PATTERN 4: Compress mixed data
# -> Try both and compare
files_to_test = ['data1.txt', 'data2.txt', 'data3.txt']
for f in files_to_test:
    comp_rle = CompressorWithRLE(use_rle=True).compress(f, f'{f}.rle')
    comp_no_rle = CompressorWithRLE(use_rle=False).compress(f, f'{f}.no_rle')
    # Choose the format that gives better compression


# ============================================================================
# EXAMPLE 10: Integration with Existing Code
# ============================================================================

# If you have existing code using the original compressor:

# OLD WAY (Huffman only):
# from compressor import Compressor
# comp = Compressor()
# comp.compress('input.txt', 'output.bin')

# NEW WAY (RLE + Huffman):
from compressor_with_rle import CompressorWithRLE
comp = CompressorWithRLE(use_rle=True)
comp.compress('input.txt', 'output.bin')

# The new format is backward compatible!
# Files compressed with version 2 (RLE+Huffman) are clearly marked
# The decompressor automatically detects and handles both versions


# ============================================================================
# COMMAND LINE EXAMPLES
# ============================================================================

"""
# Compress a file with RLE (recommended)
$ python compressor_with_rle.py compress input.txt output.bin -v
Compressing: input.txt (10000 bytes)
  Stage 1: Run-Length Encoding
  Split into 1 chunks
  RLE preprocessing: 10000 -> 120 bytes
  Stage 2: Adaptive Huffman Encoding
============================================================
Compression Statistics
============================================================
Original:          10,000 bytes
After RLE:         120 bytes (1.2%)
Compressed:        28 bytes
Ratio:             0.28% (28/10000)
Speed:             4.8 MB/s
Time:              0.002 seconds
============================================================

# Decompress
$ python compressor_with_rle.py decompress output.bin recovered.txt -v

# Verify round-trip
$ python compressor_with_rle.py check input.txt output.bin -v

# Compress without RLE
$ python compressor_with_rle.py compress input.txt output.bin --no-rle -v

# Run tests
$ python test_rle.py
[PASS] Single bytes test passed
[PASS] Simple runs test passed
...
[SUCCESS] All RLE tests passed!

# Compare performance
$ python comparison.py
"""

# ============================================================================
# Summary Table: When to Use RLE
# ============================================================================

"""
Data Type                    RLE Benefit    Use Case                  Recommendation
-----------                  -----------    --------                  ---------------
Highly repetitive text       90%+           Logs, repeated spaces     USE RLE
Moderately repetitive        20-50%         Code, natural text        USE RLE
Non-repetitive               No benefit     Random data               SKIP RLE
Already compressed           Expansion      ZIP, JPEG, MP3            SKIP RLE
Binary data with patterns    50%+           Images, structured data   USE RLE
Random binary data           No benefit     Cryptography, hashes      SKIP RLE

DEFAULT: Use RLE for all files except those already compressed
RESULT: Better compression on most files, no harm on others
"""
