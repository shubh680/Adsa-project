#!/usr/bin/env python3
"""
compress.py — Main entry point for the Adaptive Huffman + RLE compression system.

A professional file compression utility combining:
- Run-Length Encoding (RLE) for preprocessing repetitive data
- Adaptive Huffman (FGK Algorithm) for optimal entropy encoding

Usage:
    python compress.py compress <input> <output> [--no-rle] [-v]
    python compress.py decompress <input> <output> [-v]
    python compress.py verify <input> <output> [-v]
    python compress.py compare <file> [<file2> ...] [-v]

Examples:
    # Compress with RLE + Huffman (recommended)
    python compress.py compress data.txt data.bin
    
    # Decompress
    python compress.py decompress data.bin data.txt
    
    # Verify round-trip
    python compress.py verify data.txt data.bin
    
    # Compare compression on multiple files
    python compress.py compare file1.txt file2.txt file3.txt
"""

import sys
import argparse
import time
import os
import subprocess
from hybrid_compressor import HybridCompressor


def format_bytes(num_bytes):
    """Format bytes as human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} TB"


def format_ratio(ratio):
    """Format compression ratio as percentage."""
    return f"{ratio * 100:.2f}%"


def print_stats(stats):
    """Print compression statistics in a formatted table."""
    print("\n" + "=" * 70)
    print("COMPRESSION STATISTICS")
    print("=" * 70)
    original_size = stats['original_size']
    compressed_size = stats['compressed_size']
    elapsed_time = stats.get('time', 0)
    
    print(f"Original size:          {format_bytes(original_size)} ({original_size:,} bytes)")
    
    if 'post_rle_size' in stats:
        rle_size = stats['post_rle_size']
        print(f"After RLE preprocessing: {format_bytes(rle_size)} ({rle_size:,} bytes)")
        print(f"RLE reduction:          {format_ratio(1 - rle_size / original_size)}")
    
    print(f"Compressed size:        {format_bytes(compressed_size)} ({compressed_size:,} bytes)")
    compression_ratio = stats['compression_ratio']
    print(f"Compression ratio:      {format_ratio(compression_ratio)}")
    
    if elapsed_time > 0:
        speed_mbps = (original_size / 1024 / 1024) / elapsed_time if elapsed_time > 0 else 0
        print(f"Speed:                  {speed_mbps:.2f} MB/s")
    
    print(f"Time:                   {elapsed_time:.3f} seconds")
    print("=" * 70 + "\n")


def cmd_compress(args):
    """Handle compress command."""
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        return False
    
    input_size = os.path.getsize(args.input)
    if input_size == 0:
        print("Warning: Input file is empty", file=sys.stderr)
    
    if args.verbose:
        print(f"\nCompressing: {args.input} ({format_bytes(input_size)})")
    
    compressor = HybridCompressor(verbose=args.verbose)
    
    try:
        stats = compressor.compress(args.input, args.output)
        
        if args.verbose:
            print_stats(stats)
        else:
            print(f"{args.input} → {args.output}")
            print(f"  Algorithm: {stats['algorithm']}")
            print(f"  Ratio: {stats['compression_ratio']*100:.2f}%")
        
        return True
    except Exception as e:
        print(f"Error during compression: {e}", file=sys.stderr)
        return False


def cmd_decompress(args):
    """Handle decompress command."""
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        return False
    
    if args.verbose:
        print(f"\nDecompressing: {args.input}")
    
    compressor = HybridCompressor(verbose=args.verbose)
    
    try:
        compressor.decompress(args.input, args.output)
        
        output_size = os.path.getsize(args.output)
        if args.verbose:
            print(f"Successfully decompressed to: {args.output} ({format_bytes(output_size)})")
        else:
            print(f"{args.input} → {args.output}")
        
        return True
    except Exception as e:
        print(f"Error during decompression: {e}", file=sys.stderr)
        return False


def cmd_verify(args):
    """Handle verify command (compress -> decompress -> compare)."""
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        return False
    
    if args.verbose:
        print(f"\nVerifying round-trip: {args.input}")
    
    compressor = CompressorWithRLE(verbose=args.verbose)
    temp_file = "__temp_decompress__.tmp"
    
    try:
        # Step 1: Compress
        if args.verbose:
            print("\nStep 1: Compressing...")
        stats = compressor.compress(args.input, args.output)
        
        # Step 2: Decompress
        if args.verbose:
            print("Step 2: Decompressing...")
        compressor.decompress(args.output, temp_file)
        
        # Step 3: Verify
        if args.verbose:
            print("Step 3: Verifying...")
        
        with open(args.input, 'rb') as f1:
            original = f1.read()
        with open(temp_file, 'rb') as f2:
            decompressed = f2.read()
        
        if original == decompressed:
            if args.verbose:
                print_stats(stats)
                print("✓ PASS: Round-trip successful!")
                print(f"  Original size:      {format_bytes(len(original))}")
                print(f"  Compressed size:    {format_bytes(os.path.getsize(args.output))}")
                print(f"  Decompressed size:  {format_bytes(len(decompressed))}")
                print(f"  Compression ratio:  {format_ratio(stats['compression_ratio'])}")
                if 'rle_size' in stats:
                    print(f"  RLE improvement:    {stats['original_size']} → {stats['rle_size']} bytes")
            else:
                print("✓ PASS: Round-trip successful!")
            return True
        else:
            print(f"✗ FAIL: Data mismatch! {len(original)} → {len(decompressed)} bytes", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error during verification: {e}", file=sys.stderr)
        return False
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def cmd_compare(args):
    """Handle compare command."""
    if not args.files:
        print("Error: No files specified", file=sys.stderr)
        return False
    
    for file_path in args.files:
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found", file=sys.stderr)
            return False
    
    if args.verbose:
        print(f"\nComparing compression on {len(args.files)} file(s)...")
    
    try:
        compressor = CompressorWithRLE(verbose=args.verbose)
        print(f"\n{'='*70}")
        print("COMPRESSION COMPARISON")
        print('='*70)
        
        for file_path in args.files:
            # Compress with RLE
            temp_rle = f"__temp_{os.path.basename(file_path)}.rle.bin"
            stats_rle = compressor.compress(file_path, temp_rle)
            
            # Compress without RLE
            temp_no_rle = f"__temp_{os.path.basename(file_path)}.no_rle.bin"
            compressor_no_rle = CompressorWithRLE(verbose=False, use_rle=False)
            stats_no_rle = compressor_no_rle.compress(file_path, temp_no_rle)
            
            original_size = stats_rle['original_size']
            rle_size = os.path.getsize(temp_rle)
            no_rle_size = os.path.getsize(temp_no_rle)
            
            print(f"\n{file_path}")
            print(f"  Original:   {format_bytes(original_size)} ({original_size:,} bytes)")
            print(f"  With RLE:   {format_bytes(rle_size)} ({rle_size:,} bytes, {format_ratio(rle_size/original_size)})")
            print(f"  Without RLE: {format_bytes(no_rle_size)} ({no_rle_size:,} bytes, {format_ratio(no_rle_size/original_size)})")
            
            improvement = (1 - rle_size / no_rle_size) * 100
            if improvement > 0.1:
                print(f"  RLE benefit: {improvement:.1f}% smaller with RLE ✓")
            elif improvement < -0.1:
                print(f"  RLE impact: {abs(improvement):.1f}% larger with RLE (skipped)")
            else:
                print(f"  RLE impact: No significant difference")
            
            # Cleanup
            for f in [temp_rle, temp_no_rle]:
                if os.path.exists(f):
                    os.remove(f)
        
        print(f"\n{'='*70}\n")
        return True
    except Exception as e:
        print(f"Error during comparison: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Professional file compression using Adaptive Huffman + RLE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s compress input.txt output.bin          Compress with RLE + Huffman
  %(prog)s compress input.txt output.bin --no-rle Compress with Huffman only
  %(prog)s decompress output.bin recovered.txt    Decompress file
  %(prog)s verify input.txt output.bin -v         Verify round-trip compression
  %(prog)s compare file1.txt file2.txt -v         Compare compression ratios
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Compress command
    compress_parser = subparsers.add_parser('compress', help='Compress a file')
    compress_parser.add_argument('input', help='Input file to compress')
    compress_parser.add_argument('output', help='Output compressed file')
    compress_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    compress_parser.set_defaults(func=cmd_compress)
    
    # Decompress command
    decompress_parser = subparsers.add_parser('decompress', help='Decompress a file')
    decompress_parser.add_argument('input', help='Compressed file to decompress')
    decompress_parser.add_argument('output', help='Output decompressed file')
    decompress_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    decompress_parser.set_defaults(func=cmd_decompress)
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify round-trip compression')
    verify_parser.add_argument('input', help='Original input file')
    verify_parser.add_argument('output', help='Compressed file path')
    verify_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    verify_parser.set_defaults(func=cmd_verify)
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare compression on multiple files')
    compare_parser.add_argument('files', nargs='+', help='Files to compare')
    compare_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    compare_parser.set_defaults(func=cmd_compare)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        success = args.func(args)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\nAborted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
