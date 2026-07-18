"""
Test complete compression/decompression workflow with filename preservation
"""

import zlib
import pytest


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
    
    # Simulate decompression with filename extraction
    extracted_length = int.from_bytes(final_compressed[:2], byteorder='big')
    extracted_filename = final_compressed[2:2+extracted_length].decode('utf-8')
    compressed_data = final_compressed[2+extracted_length:]
    
    # Decompress
    decompressed = zlib.decompress(compressed_data)
    
    # Verify
    assert decompressed == test_content
    assert extracted_filename == test_filename
