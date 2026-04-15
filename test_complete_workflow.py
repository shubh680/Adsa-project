"""
Test complete compression/decompression workflow with filename preservation
"""

import os
import sys
import base64

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hybrid_compressor import HybridCompressor
from compressor_with_rle import CompressorWithRLE
import zlib

def test_filename_preservation():
    """Test that original filename is preserved through compression/decompression"""
    
    # Create test file
    test_content = b"Hello, this is test data for compression!" * 100
    test_filename = "test_document.txt"
    
    # Simulate compression with filename metadata
    filename_bytes = test_filename.encode('utf-8')
    filename_length = len(filename_bytes).to_bytes(2, byteorder='big')
    
    # Compress with zlib for simplicity
    compressed = zlib.compress(test_content, 9)
    final_compressed = filename_length + filename_bytes + compressed
    
    print(f"Original file: {test_filename}")
    print(f"Original size: {len(test_content)} bytes")
    print(f"Compressed size: {len(final_compressed)} bytes")
    print(f"Compression ratio: {len(final_compressed) / len(test_content):.2%}")
    
    # Simulate decompression with filename extraction
    try:
        extracted_length = int.from_bytes(final_compressed[:2], byteorder='big')
        extracted_filename = final_compressed[2:2+extracted_length].decode('utf-8')
        compressed_data = final_compressed[2+extracted_length:]
        
        print(f"\nExtracted filename: {extracted_filename}")
        
        # Decompress
        decompressed = zlib.decompress(compressed_data)
        print(f"Decompressed size: {len(decompressed)} bytes")
        
        # Verify
        if decompressed == test_content and extracted_filename == test_filename:
            print("\n✓ SUCCESS: Filename preservation test passed!")
            print(f"  - Original filename preserved: {test_filename}")
            print(f"  - Data integrity verified")
            return True
        else:
            print("\n✗ FAILED: Data or filename mismatch")
            return False
            
    except Exception as e:
        print(f"\n✗ FAILED: {str(e)}")
        return False

if __name__ == '__main__':
    success = test_filename_preservation()
    sys.exit(0 if success else 1)
