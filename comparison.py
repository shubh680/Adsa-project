"""
comparison.py — Compare compression with and without RLE preprocessing.

Demonstrates the benefits of RLE as a preprocessing stage for Huffman encoding.
"""

import subprocess
import sys
import os


def test_file(filename):
    """Test a file with and without RLE."""
    print(f"\n{'='*70}")
    print(f"Testing: {filename}")
    print('='*70)
    
    if not os.path.exists(filename):
        print(f"[SKIP] File not found: {filename}")
        return
    
    with open(filename, 'rb') as f:
        original_data = f.read()
    original_size = len(original_data)
    
    # Test with RLE
    output_rle = f"__temp_{filename}.rle.bin"
    result = subprocess.run(
        [sys.executable, 'compressor_with_rle.py', 'compress', filename, output_rle],
        capture_output=True, text=True
    )
    
    if os.path.exists(output_rle):
        rle_size = os.path.getsize(output_rle)
    else:
        rle_size = None
    
    # Test without RLE
    output_no_rle = f"__temp_{filename}.no_rle.bin"
    result = subprocess.run(
        [sys.executable, 'compressor_with_rle.py', 'compress', filename, output_no_rle, '--no-rle'],
        capture_output=True, text=True
    )
    
    if os.path.exists(output_no_rle):
        no_rle_size = os.path.getsize(output_no_rle)
    else:
        no_rle_size = None
    
    # Print results
    print(f"\nOriginal size: {original_size:,} bytes")
    
    if rle_size:
        ratio_rle = rle_size / original_size * 100
        print(f"With RLE:      {rle_size:,} bytes ({ratio_rle:.2f}%)")
    
    if no_rle_size:
        ratio_no_rle = no_rle_size / original_size * 100
        print(f"Without RLE:   {no_rle_size:,} bytes ({ratio_no_rle:.2f}%)")
    
    if rle_size and no_rle_size:
        improvement = (1 - rle_size / no_rle_size) * 100
        if improvement > 0:
            print(f"\nRLE Improvement: {improvement:.1f}% smaller with RLE")
        else:
            print(f"\nRLE Impact: {abs(improvement):.1f}% larger with RLE (not beneficial)")
    
    # Cleanup
    for f in [output_rle, output_no_rle]:
        if os.path.exists(f):
            os.remove(f)


def main():
    """Run comparison tests."""
    print("\n" + "="*70)
    print("RLE Compression Comparison Test")
    print("="*70)
    
    test_files = [
        'repetitive.txt',
        'sample.txt',
        'test1_repetitive.txt',
        'test2_pattern.txt',
        'test3_limited.txt',
        'test4_logs.txt',
    ]
    
    for filename in test_files:
        test_file(filename)
    
    print("\n" + "="*70)
    print("Summary:")
    print("- RLE is most effective on repetitive data (logs, text with patterns)")
    print("- RLE may not help (or slightly expand) non-repetitive data")
    print("- Use 'compressor_with_rle.py' for best results on repetitive files")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
