"""
hybrid_compressor.py — Intelligent multi-algorithm compression system.

Automatically detects data type and applies the best compression algorithm:
- RLE + Huffman: For highly repetitive data (99%+ compression)
- DEFLATE (zlib): For structured data (CSV, JSON), natural text
- Hybrid: For mixed data patterns

File Format:
[8 bits]   Algorithm ID (0=RLE+Huffman, 1=DEFLATE, 2=Hybrid)
[variable] Algorithm-specific data
"""

import zlib
import time
import os
from compressor_with_rle import CompressorWithRLE
from bit_io import BitWriter, BitReader


class HybridCompressor:
    """
    Intelligent compression that selects the best algorithm for any data type.
    
    Supports:
    - Highly repetitive data (RLE + Huffman)
    - Structured data (CSV, JSON)
    - Natural language text
    - Mixed/random data
    - Already compressed files
    """
    
    # Algorithm IDs
    ALG_RLE_HUFFMAN = 0
    ALG_DEFLATE = 1
    ALG_HYBRID = 2
    
    def __init__(self, verbose=False):
        """Initialize hybrid compressor."""
        self.verbose = verbose
        self.stats = {}
    
    def _analyze_data(self, data):
        """
        Analyze data to determine best compression algorithm.
        
        Returns: (algorithm_id, entropy, has_runs, has_delimiters, compression_type)
        """
        if len(data) == 0:
            return self.ALG_DEFLATE, 0, False, False, "empty"
        
        # Calculate byte frequency
        freq = {}
        for byte in data:
            freq[byte] = freq.get(byte, 0) + 1
        
        unique_bytes = len(freq)
        entropy = sum((count / len(data)) ** 2 for count in freq.values())
        entropy = 1.0 - entropy  # Normalize (0=low entropy, 1=high entropy)
        
        # Check for long runs (RLE-friendly)
        has_runs = self._has_long_runs(data)
        
        # Check for delimiters (CSV, structured)
        has_delimiters = self._has_delimiters(data)
        
        # Decide algorithm
        if has_runs and not has_delimiters and unique_bytes <= 20:
            # Highly repetitive data without delimiters
            algorithm = self.ALG_RLE_HUFFMAN
            compression_type = "highly_repetitive"
        elif has_delimiters or (unique_bytes > 100 and entropy > 0.5):
            # Structured data or high entropy
            algorithm = self.ALG_DEFLATE
            compression_type = "structured_or_natural"
        else:
            # Mixed patterns
            algorithm = self.ALG_DEFLATE
            compression_type = "mixed"
        
        return algorithm, entropy, has_runs, has_delimiters, compression_type
    
    def _has_long_runs(self, data, min_run_length=100):
        """Check if data has long runs of identical bytes."""
        if len(data) < min_run_length:
            return False
        
        current_byte = data[0]
        run_length = 1
        
        for byte in data[1:]:
            if byte == current_byte:
                run_length += 1
                if run_length >= min_run_length:
                    return True
            else:
                current_byte = byte
                run_length = 1
        
        return False
    
    def _has_delimiters(self, data):
        """Check if data contains delimiters (CSV, structured)."""
        delimiters = [b',', b'\n', b'\r', b'{', b'}', b'[', b']', b':', b';']
        delimiter_count = 0
        
        for delimiter in delimiters:
            delimiter_count += data.count(delimiter)
        
        # If delimiters represent >1% of data, it's structured
        return delimiter_count > len(data) * 0.01
    
    def compress(self, input_file, output_file):
        """
        Compress file using the best algorithm.
        
        Args:
            input_file: Path to input file
            output_file: Path to output compressed file
            
        Returns:
            Dictionary with compression statistics
        """
        start_time = time.time()
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Read input file
        with open(input_file, 'rb') as f:
            data = f.read()
        
        original_size = len(data)
        
        if self.verbose:
            print(f"Analyzing data...")
        
        # Analyze data to choose algorithm
        algorithm, entropy, has_runs, has_delimiters, compression_type = self._analyze_data(data)
        
        if self.verbose:
            print(f"  Entropy: {entropy:.2f}")
            print(f"  Has long runs: {has_runs}")
            print(f"  Has delimiters: {has_delimiters}")
            print(f"  Data type: {compression_type}")
            print(f"  Selected algorithm: {self._get_algorithm_name(algorithm)}")
        
        # Compress using selected algorithm
        if algorithm == self.ALG_RLE_HUFFMAN:
            compressed_data = self._compress_rle_huffman(data)
            alg_id = self.ALG_RLE_HUFFMAN
        else:  # DEFLATE for everything else
            compressed_data = self._compress_deflate(data)
            alg_id = self.ALG_DEFLATE
        
        # Write file with header
        with open(output_file, 'wb') as f:
            # Write algorithm ID (8 bits)
            f.write(bytes([alg_id]))
            # Write compressed data
            f.write(compressed_data)
        
        compressed_size = os.path.getsize(output_file)
        elapsed_time = time.time() - start_time
        
        # Calculate statistics
        self.stats = {
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': compressed_size / original_size if original_size > 0 else 0,
            'algorithm': self._get_algorithm_name(alg_id),
            'entropy': entropy,
            'time': elapsed_time,
            'compression_type': compression_type
        }
        
        if self.verbose:
            self._print_stats(self.stats)
        
        return self.stats
    
    def _compress_rle_huffman(self, data):
        """Compress using RLE + Huffman."""
        compressor = CompressorWithRLE(verbose=False, use_rle=True)
        
        # Write to temporary file
        temp_file = '__temp_rle_huffman__.bin'
        with open(temp_file, 'wb') as f:
            f.write(data)
        
        # Compress with RLE+Huffman
        temp_output = '__temp_rle_huffman_out__.bin'
        compressor.compress(temp_file, temp_output)
        
        # Read compressed data
        with open(temp_output, 'rb') as f:
            compressed = f.read()
        
        # Cleanup
        os.remove(temp_file)
        os.remove(temp_output)
        
        return compressed
    
    def _compress_deflate(self, data):
        """Compress using DEFLATE (zlib)."""
        # Use zlib with best compression
        return zlib.compress(data, level=9)
    
    def decompress(self, input_file, output_file):
        """
        Decompress file (auto-detects algorithm).
        
        Args:
            input_file: Path to compressed file
            output_file: Path to output file
        """
        start_time = time.time()
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Compressed file not found: {input_file}")
        
        # Read compressed file
        with open(input_file, 'rb') as f:
            alg_id = f.read(1)[0]
            compressed_data = f.read()
        
        if self.verbose:
            print(f"Detected algorithm: {self._get_algorithm_name(alg_id)}")
        
        # Decompress using detected algorithm
        if alg_id == self.ALG_RLE_HUFFMAN:
            decompressed = self._decompress_rle_huffman(compressed_data)
        elif alg_id == self.ALG_DEFLATE:
            decompressed = self._decompress_deflate(compressed_data)
        else:
            raise ValueError(f"Unknown algorithm ID: {alg_id}")
        
        # Write output file
        with open(output_file, 'wb') as f:
            f.write(decompressed)
        
        elapsed_time = time.time() - start_time
        
        if self.verbose:
            print(f"Decompressed: {len(decompressed):,} bytes")
            print(f"Time: {elapsed_time:.3f} seconds")
        
        return len(decompressed)
    
    def _decompress_rle_huffman(self, compressed_data):
        """Decompress RLE + Huffman data."""
        # Write to temporary file
        temp_file = '__temp_rle_huffman_compressed__.bin'
        with open(temp_file, 'wb') as f:
            f.write(compressed_data)
        
        # Decompress
        temp_output = '__temp_rle_huffman_decompressed__.bin'
        compressor = CompressorWithRLE(verbose=False)
        compressor.decompress(temp_file, temp_output)
        
        # Read decompressed data
        with open(temp_output, 'rb') as f:
            decompressed = f.read()
        
        # Cleanup
        os.remove(temp_file)
        os.remove(temp_output)
        
        return decompressed
    
    def _decompress_deflate(self, compressed_data):
        """Decompress DEFLATE data."""
        return zlib.decompress(compressed_data)
    
    def _get_algorithm_name(self, alg_id):
        """Get human-readable algorithm name."""
        names = {
            self.ALG_RLE_HUFFMAN: "RLE + Huffman",
            self.ALG_DEFLATE: "DEFLATE (zlib)",
            self.ALG_HYBRID: "Hybrid"
        }
        return names.get(alg_id, "Unknown")
    
    def _print_stats(self, stats):
        """Print compression statistics."""
        print("\n" + "=" * 70)
        print("COMPRESSION STATISTICS")
        print("=" * 70)
        print(f"Data type:              {stats['compression_type']}")
        print(f"Algorithm:              {stats['algorithm']}")
        print(f"Entropy:                {stats['entropy']:.2f}")
        print(f"Original size:          {stats['original_size']:,} bytes")
        print(f"Compressed size:        {stats['compressed_size']:,} bytes")
        print(f"Compression ratio:      {stats['compression_ratio']*100:.2f}%")
        print(f"Time:                   {stats['time']:.3f} seconds")
        print("=" * 70 + "\n")
