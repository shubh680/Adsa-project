"""
compressor_with_rle.py — Advanced file compression combining RLE + Adaptive Huffman.

Improves compression ratio by applying Run-Length Encoding (RLE) as a preprocessing
step before Adaptive Huffman encoding. This two-stage approach is particularly
effective for files with repetitive data patterns.

Pipeline:
1. Read input file
2. Apply RLE preprocessing (reduces runs of identical bytes)
3. Apply Adaptive Huffman encoding
4. Write compressed bits

Format: [version (8 bits)] [num_chunks (16 bits)] [chunk_1] [chunk_2] ...
where each chunk = [huffman-encoded RLE-preprocessed data]
"""

import time
import argparse
import os
from huffman import AdaptiveHuffman
from bit_io import BitWriter, BitReader
from rle import RLE


class CompressorWithRLE:
    """
    Advanced file compression using RLE preprocessing + Adaptive Huffman.
    
    Combines two-stage compression:
    - Stage 1: RLE preprocesses repetitive data
    - Stage 2: Adaptive Huffman encodes the result
    
    Particularly effective for files with runs of identical bytes.
    """
    
    CHUNK_SIZE = 4096  # 4KB chunks for memory efficiency
    VERSION = 2  # Version 2 includes RLE

    def __init__(self, verbose=False, use_rle=True):
        """
        Initialize compressor.
        
        Args:
            verbose: Print progress information.
            use_rle: Enable RLE preprocessing (recommended).
        """
        self.verbose = verbose
        self.use_rle = use_rle
        self.stats = {}

    def compress(self, input_file, output_file):
        """
        Compress a file using RLE + Adaptive Huffman encoding with chunking.
        
        For large files, data is split into chunks (<60K bytes).
        Each chunk is:
        1. Run-Length Encoded (if use_rle=True)
        2. Huffman encoded
        3. Written to output
        
        Format: [version (8 bits)] [num_chunks (16 bits)] [chunk_1] [chunk_2] ...
        
        Args:
            input_file: Path to input file.
            output_file: Path to output file (bit-compressed).
        
        Returns:
            dict with compression statistics.
        """
        stats = {
            'input_file': input_file,
            'output_file': output_file,
            'original_size': 0,
            'compressed_size': 0,
            'compression_ratio': 0.0,
            'time': 0.0,
            'chunks': 0,
            'rle_enabled': self.use_rle,
            'pre_rle_size': 0,
            'post_rle_size': 0,
        }

        start_time = time.time()

        try:
            # Read input file
            with open(input_file, 'rb') as f:
                data = f.read()
            
            original_size = len(data)
            stats['original_size'] = original_size

            if self.verbose:
                print(f"Compressing: {input_file} ({original_size} bytes)")
                if self.use_rle:
                    print("  Stage 1: Run-Length Encoding")

            # Split into chunks (max 60,000 bytes per chunk)
            MAX_CHUNK = 60000
            chunks = [data[i:i + MAX_CHUNK] for i in range(0, len(data), MAX_CHUNK)]
            num_chunks = len(chunks)
            stats['chunks'] = num_chunks

            if self.verbose:
                print(f"  Split into {num_chunks} chunks")

            # Apply RLE preprocessing to all data if enabled
            if self.use_rle:
                rle_encoded_chunks = []
                total_rle_size = 0
                for chunk in chunks:
                    rle_chunk = RLE.encode(list(chunk))
                    rle_encoded_chunks.append(rle_chunk)
                    total_rle_size += len(rle_chunk)
                stats['post_rle_size'] = total_rle_size
                stats['pre_rle_size'] = original_size
                if self.verbose:
                    print(f"  RLE preprocessing: {original_size} -> {total_rle_size} bytes")
            else:
                rle_encoded_chunks = [list(chunk) for chunk in chunks]

            if self.verbose:
                print("  Stage 2: Adaptive Huffman Encoding")

            # Write compressed file
            with open(output_file, 'wb') as f:
                writer = BitWriter(f)
                
                # Write version (8 bits)
                for i in range(8):
                    writer.write_bit((self.VERSION >> (7 - i)) & 1)
                
                # Write number of chunks as 16 bits
                for i in range(16):
                    writer.write_bit((num_chunks >> (15 - i)) & 1)
                
                # Compress and write each chunk
                for chunk_idx, rle_chunk in enumerate(rle_encoded_chunks):
                    if self.verbose and num_chunks > 1:
                        chunk_size = len(chunks[chunk_idx])
                        rle_size = len(rle_chunk)
                        print(f"  Compressing chunk {chunk_idx + 1}/{num_chunks} ({chunk_size} -> {rle_size} bytes)...")
                    
                    # Huffman encode this chunk
                    encoder = AdaptiveHuffman()
                    bits = encoder.encode(rle_chunk)
                    
                    # Write bits
                    for bit in bits:
                        writer.write_bit(bit)
                
                writer.flush()

            # Get output file size
            compressed_size = os.path.getsize(output_file)
            stats['compressed_size'] = compressed_size

            # Calculate compression ratio
            if original_size > 0:
                ratio = compressed_size / original_size
                stats['compression_ratio'] = ratio
            else:
                stats['compression_ratio'] = 0.0

            stats['time'] = time.time() - start_time

            if self.verbose:
                self._print_stats(stats)

            self.stats = stats
            return stats

        except Exception as e:
            print(f"ERROR during compression: {e}")
            raise

    def decompress(self, input_file, output_file):
        """
        Decompress a file that was compressed with compress().
        
        Reverses the two-stage pipeline:
        1. Huffman decode
        2. RLE decode (if file was RLE-encoded)
        
        Format: [version (8 bits)] [num_chunks (16 bits)] [chunk_1] [chunk_2] ...
        
        Args:
            input_file: Path to compressed file (bits).
            output_file: Path to output file (original bytes).
        
        Returns:
            dict with decompression statistics.
        """
        stats = {
            'input_file': input_file,
            'output_file': output_file,
            'compressed_size': 0,
            'decompressed_size': 0,
            'time': 0.0,
            'rle_used': False,
        }

        start_time = time.time()

        try:
            if self.verbose:
                print(f"Decompressing: {input_file}")

            # Read all bits from input file
            if self.verbose:
                print("  Reading bits...")
            with open(input_file, 'rb') as f:
                reader = BitReader(f)
                bits = []
                while True:
                    bit = reader.read_bit()
                    if bit is None:
                        break
                    bits.append(bit)

            compressed_size = os.path.getsize(input_file)
            stats['compressed_size'] = compressed_size

            if self.verbose:
                print(f"  Read {len(bits)} bits from {compressed_size} bytes")

            # Extract version (first 8 bits)
            if len(bits) < 8:
                print("ERROR: File too small (need at least 8 bits for version)")
                return stats

            version = 0
            for i in range(8):
                version = (version << 1) | bits[i]
            
            rle_used = (version == 2)
            stats['rle_used'] = rle_used
            if self.verbose:
                print(f"  File version: {version} (RLE: {'yes' if rle_used else 'no'})")

            # Extract number of chunks
            if len(bits) < 24:
                print("ERROR: File too small (need at least 24 bits)")
                return stats

            num_chunks = 0
            for i in range(16):
                num_chunks = (num_chunks << 1) | bits[8 + i]

            if self.verbose:
                print(f"  File contains {num_chunks} chunks")

            # Decompress each chunk
            all_symbols = []
            bit_idx = 24
            for chunk_idx in range(num_chunks):
                if self.verbose and num_chunks > 1:
                    print(f"  Decompressing chunk {chunk_idx + 1}/{num_chunks}...")

                # Decode this chunk
                decoder = AdaptiveHuffman()
                remaining_bits = bits[bit_idx:]
                
                try:
                    chunk_symbols = decoder.decode(remaining_bits)
                    
                    # Reverse RLE if it was used
                    if rle_used:
                        chunk_symbols = RLE.decode(chunk_symbols)
                    
                    all_symbols.extend(chunk_symbols)
                    
                    # Calculate bits consumed by this chunk
                    test_encoder = AdaptiveHuffman()
                    test_bits = test_encoder.encode(chunk_symbols if not rle_used else RLE.encode(chunk_symbols))
                    bit_idx += len(test_bits)
                    
                except Exception as e:
                    if self.verbose:
                        print(f"  Error decoding chunk {chunk_idx + 1}: {e}")
                    break

            if self.verbose:
                print(f"  Decoded {len(all_symbols)} total symbols")

            # Write symbols (bytes) to output file
            if self.verbose:
                print(f"  Writing to {output_file}...")
            with open(output_file, 'wb') as f:
                f.write(bytes(all_symbols))

            decompressed_size = len(all_symbols)
            stats['decompressed_size'] = decompressed_size
            stats['time'] = time.time() - start_time

            if self.verbose:
                self._print_stats(stats, mode='decompress')

            self.stats = stats
            return stats

        except Exception as e:
            print(f"ERROR during decompression: {e}")
            raise

    @staticmethod
    def _print_stats(stats, mode='compress'):
        """Print compression/decompression statistics."""
        print()
        print("=" * 60)
        if mode == 'compress':
            orig = stats['original_size']
            comp = stats['compressed_size']
            ratio = stats['compression_ratio']
            time_taken = stats['time']
            rle = stats['rle_enabled']

            print(f"Compression Statistics")
            print("=" * 60)
            print(f"Original:          {orig:,} bytes")
            if rle:
                print(f"After RLE:         {stats['post_rle_size']:,} bytes ({stats['post_rle_size']/orig*100:.1f}%)")
            print(f"Compressed:        {comp:,} bytes")
            print(f"Ratio:             {ratio:.2%} ({comp}/{orig})")
            if time_taken > 0:
                speed = orig / (1024 * 1024 * time_taken)
                print(f"Speed:             {speed:.1f} MB/s")
            print(f"Time:              {time_taken:.3f} seconds")
        else:
            comp = stats['compressed_size']
            decomp = stats['decompressed_size']
            time_taken = stats['time']
            rle = stats['rle_used']

            print(f"Decompression Statistics")
            print("=" * 60)
            print(f"Compressed:        {comp:,} bytes")
            print(f"Decompressed:      {decomp:,} bytes")
            print(f"RLE preprocessing: {'yes' if rle else 'no'}")
            if time_taken > 0:
                speed = decomp / (1024 * 1024 * time_taken)
                print(f"Speed:             {speed:.1f} MB/s")
            print(f"Time:              {time_taken:.3f} seconds")

        print("=" * 60)
        print()


def main():
    """Command-line interface for RLE+Huffman compression/decompression."""
    parser = argparse.ArgumentParser(
        description='Advanced File Compression (RLE + Adaptive Huffman)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Compress a file with RLE
  python3 compressor_with_rle.py compress input.txt output.bin -v

  # Decompress a file
  python3 compressor_with_rle.py decompress output.bin recovered.txt -v

  # Check compression
  python3 compressor_with_rle.py check input.txt output.bin -v

  # Compress without RLE (Huffman only)
  python3 compressor_with_rle.py compress input.txt output.bin --no-rle -v
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Compress command
    compress_parser = subparsers.add_parser('compress', help='Compress a file')
    compress_parser.add_argument('input', help='Input file to compress')
    compress_parser.add_argument('output', help='Output compressed file')
    compress_parser.add_argument(
        '-v', '--verbose', action='store_true', help='Verbose output'
    )
    compress_parser.add_argument(
        '--no-rle', action='store_true', help='Disable RLE preprocessing'
    )

    # Decompress command
    decompress_parser = subparsers.add_parser('decompress', help='Decompress a file')
    decompress_parser.add_argument('input', help='Compressed file to decompress')
    decompress_parser.add_argument('output', help='Output decompressed file')
    decompress_parser.add_argument(
        '-v', '--verbose', action='store_true', help='Verbose output'
    )

    # Check command (verify round-trip)
    check_parser = subparsers.add_parser(
        'check', help='Verify compression round-trip'
    )
    check_parser.add_argument('original', help='Original file')
    check_parser.add_argument('compressed', help='Compressed file')
    check_parser.add_argument(
        '-v', '--verbose', action='store_true', help='Verbose output'
    )
    check_parser.add_argument(
        '--no-rle', action='store_true', help='Disable RLE preprocessing'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    use_rle = not getattr(args, 'no_rle', False)
    compressor = CompressorWithRLE(verbose=args.verbose, use_rle=use_rle)

    try:
        if args.command == 'compress':
            stats = compressor.compress(args.input, args.output)
            if not args.verbose:
                print(f"[OK] Compressed: {args.input} -> {args.output}")
                print(f"  Ratio: {stats['compression_ratio']:.2%}")

        elif args.command == 'decompress':
            stats = compressor.decompress(args.input, args.output)
            if not args.verbose:
                print(f"[OK] Decompressed: {args.input} -> {args.output}")

        elif args.command == 'check':
            print(f"Verifying round-trip: {args.original}")
            print()

            # Compress
            print("Step 1: Compressing...")
            compressed_file = '__temp_check__.bin'
            stats1 = compressor.compress(args.original, compressed_file)

            # Decompress
            print("Step 2: Decompressing...")
            decompressed_file = '__temp_check_dec__.dat'
            stats2 = compressor.decompress(compressed_file, decompressed_file)

            # Verify
            print("Step 3: Verifying...")
            with open(args.original, 'rb') as f:
                original_data = f.read()
            with open(decompressed_file, 'rb') as f:
                decompressed_data = f.read()

            if original_data == decompressed_data:
                print("[PASS] Round-trip successful!")
                print(f"  Original size:      {len(original_data):,} bytes")
                print(f"  Compressed size:    {stats1['compressed_size']:,} bytes")
                print(f"  Decompressed size:  {len(decompressed_data):,} bytes")
                print(f"  Compression ratio:  {stats1['compression_ratio']:.2%}")
                print(f"  Total time:         {stats1['time'] + stats2['time']:.3f}s")
                if use_rle:
                    print(f"  RLE improvement:    {stats1['pre_rle_size']} -> {stats1['post_rle_size']} bytes ({(1 - stats1['post_rle_size']/stats1['pre_rle_size'])*100:.1f}% reduction)")
            else:
                print("[FAIL] Data mismatch!")
                print(f"  Original:     {len(original_data)} bytes")
                print(f"  Decompressed: {len(decompressed_data)} bytes")

            # Cleanup
            os.remove(compressed_file)
            os.remove(decompressed_file)

    except Exception as e:
        print(f"ERROR: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
