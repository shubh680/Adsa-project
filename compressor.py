"""
compressor.py — End-to-end file compression/decompression system.

Combines BitWriter/BitReader with AdaptiveHuffman to provide:
- compress(input_file, output_file): Compress a file using adaptive Huffman
- decompress(input_file, output_file): Decompress a compressed file
- Performance metrics: compression ratio, time, speed

No external dependencies beyond bit_io and huffman modules.
"""

import time
import argparse
from huffman import AdaptiveHuffman
from bit_io import BitWriter, BitReader


class Compressor:
    """
    File compression using Adaptive Huffman and bit-level I/O.

    Reads input file in 4KB chunks, encodes with adaptive Huffman,
    and writes bits to output file.
    """

    CHUNK_SIZE = 4096  # 4KB chunks for memory efficiency

    def __init__(self, verbose=False):
        """
        Initialize compressor.

        Args:
            verbose: Print progress information.
        """
        self.verbose = verbose
        self.stats = {}

    def compress(self, input_file, output_file):
        """
        Compress a file using Adaptive Huffman encoding with chunking.

        For large files, data is split into chunks (<64K to fit in 16-bit length field).
        Each chunk is compressed independently, allowing the tree to adapt per chunk.

        Format: [num_chunks (16 bits)] [chunk_1] [chunk_2] ...
                where each chunk = [length (16 bits)] [huffman-encoded data]

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

            # Split into chunks (max 60,000 bytes per chunk to be safe)
            MAX_CHUNK = 60000
            chunks = [data[i:i + MAX_CHUNK] for i in range(0, len(data), MAX_CHUNK)]
            num_chunks = len(chunks)
            stats['chunks'] = num_chunks

            if self.verbose:
                print(f"  Split into {num_chunks} chunks")

            # Write compressed file
            with open(output_file, 'wb') as f:
                writer = BitWriter(f)
                
                # Write number of chunks as 16 bits
                for i in range(16):
                    writer.write_bit((num_chunks >> (15 - i)) & 1)
                
                # Compress and write each chunk
                for chunk_idx, chunk in enumerate(chunks):
                    if self.verbose and num_chunks > 1:
                        print(f"  Compressing chunk {chunk_idx + 1}/{num_chunks} ({len(chunk)} bytes)...")
                    
                    # Convert chunk bytes to symbols
                    symbols = list(chunk)
                    
                    # Encode this chunk
                    encoder = AdaptiveHuffman()
                    bits = encoder.encode(symbols)
                    
                    # Write bits
                    for bit in bits:
                        writer.write_bit(bit)
                
                writer.flush()

            # Get output file size
            import os
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

        Handles chunked format: [num_chunks (16 bits)] [chunk_1] [chunk_2] ...

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

            import os
            compressed_size = os.path.getsize(input_file)
            stats['compressed_size'] = compressed_size

            if self.verbose:
                print(f"  Read {len(bits)} bits from {compressed_size} bytes")

            # Extract number of chunks
            if len(bits) < 16:
                print("ERROR: File too small (need at least 16 bits for chunk count)")
                return stats

            num_chunks = 0
            for i in range(16):
                num_chunks = (num_chunks << 1) | bits[i]

            if self.verbose:
                print(f"  File contains {num_chunks} chunks")

            # Decompress each chunk
            all_symbols = []
            bit_idx = 16
            for chunk_idx in range(num_chunks):
                if self.verbose and num_chunks > 1:
                    print(f"  Decompressing chunk {chunk_idx + 1}/{num_chunks}...")

                # Decode this chunk
                decoder = AdaptiveHuffman()
                remaining_bits = bits[bit_idx:]
                
                try:
                    chunk_symbols = decoder.decode(remaining_bits)
                    all_symbols.extend(chunk_symbols)
                    
                    # Calculate bits consumed by this chunk
                    # We need to figure out where the decoder stopped
                    # Re-encode to find the bit count
                    test_encoder = AdaptiveHuffman()
                    test_bits = test_encoder.encode(chunk_symbols)
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
        """Print compression statistics."""
        print()
        print("=" * 60)
        if mode == 'compress':
            orig = stats['original_size']
            comp = stats['compressed_size']
            ratio = stats['compression_ratio']
            time_taken = stats['time']

            print(f"Compression Statistics")
            print("=" * 60)
            print(f"Original:     {orig:,} bytes")
            print(f"Compressed:   {comp:,} bytes")
            print(f"Ratio:        {ratio:.2%} ({comp}/{orig})")
            if time_taken > 0:
                speed = orig / (1024 * 1024 * time_taken)
                print(f"Speed:        {speed:.1f} MB/s")
            print(f"Time:         {time_taken:.3f} seconds")
        else:
            comp = stats['compressed_size']
            decomp = stats['decompressed_size']
            time_taken = stats['time']

            print(f"Decompression Statistics")
            print("=" * 60)
            print(f"Compressed:     {comp:,} bytes")
            print(f"Decompressed:   {decomp:,} bytes")
            if time_taken > 0:
                speed = decomp / (1024 * 1024 * time_taken)
                print(f"Speed:          {speed:.1f} MB/s")
            print(f"Time:           {time_taken:.3f} seconds")

        print("=" * 60)
        print()


def main():
    """Command-line interface for compression/decompression."""
    parser = argparse.ArgumentParser(
        description='Adaptive Huffman File Compression System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Compress a file
  python3 compressor.py compress input.txt output.bin -v

  # Decompress a file
  python3 compressor.py decompress output.bin recovered.txt -v

  # Check compression
  python3 compressor.py check input.txt output.bin
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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    compressor = Compressor(verbose=args.verbose)

    try:
        if args.command == 'compress':
            stats = compressor.compress(args.input, args.output)
            if not args.verbose:
                print(f"✓ Compressed: {args.input} → {args.output}")
                print(f"  Ratio: {stats['compression_ratio']:.2%}")

        elif args.command == 'decompress':
            stats = compressor.decompress(args.input, args.output)
            if not args.verbose:
                print(f"✓ Decompressed: {args.input} → {args.output}")

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
                print("✓ PASS: Round-trip successful!")
                print(f"  Original size:      {len(original_data):,} bytes")
                print(f"  Compressed size:    {stats1['compressed_size']:,} bytes")
                print(f"  Decompressed size:  {len(decompressed_data):,} bytes")
                print(f"  Compression ratio:  {stats1['compression_ratio']:.2%}")
                print(f"  Total time:         {stats1['time'] + stats2['time']:.3f}s")
            else:
                print("✗ FAIL: Data mismatch!")
                print(f"  Original:     {len(original_data)} bytes")
                print(f"  Decompressed: {len(decompressed_data)} bytes")

            # Cleanup
            import os
            os.remove(compressed_file)
            os.remove(decompressed_file)

    except Exception as e:
        print(f"ERROR: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
