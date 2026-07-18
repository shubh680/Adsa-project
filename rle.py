"""
rle.py — Run-Length Encoding (RLE) for preprocessing data before Huffman compression.

Implements RLE encoding/decoding to reduce repetitive byte sequences.
This is particularly effective as a preprocessing step before Huffman encoding
for data with runs of identical bytes (e.g., logs, text with spaces, images).

Algorithm:
- Encoding: Replace runs of identical bytes with (byte, count) pairs
- Uses escape sequence (0xFF, 0xFF) to mark RLE-encoded data
- Decoding: Expand (byte, count) pairs back to original runs
"""

from typing import List, Union


class RLE:
    """
    Run-Length Encoding preprocessor for file compression.
    
    Efficiently compresses repetitive byte sequences:
    - Single bytes: encoded as-is
    - Runs of 2+ identical bytes: encoded as (escape=255, byte, count)
    - Preserves non-repetitive data (no expansion for count=1)
    """

    # Escape byte to mark RLE sequences (255 is relatively rare in most files)
    ESCAPE: int = 255
    RLE_MARKER: int = 255  # When followed by ESCAPE, marks an RLE sequence

    @staticmethod
    def encode(data: Union[List[int], bytes]) -> List[int]:
        """
        Encode data using Run-Length Encoding.

        Format:
        - Single unique byte: byte (as-is)
        - Run of 2+ identical bytes: [255, byte, count]

        Args:
            data: List of integers (0-255) or bytes.

        Returns:
            List of encoded bytes.
        """
        if not data:
            return []

        encoded: List[int] = []
        i: int = 0
        data_len: int = len(data)

        while i < data_len:
            byte = data[i]
            run_length = 1

            # Count consecutive identical bytes
            while (
                i + run_length < data_len
                and data[i + run_length] == byte
                and run_length < 255
            ):
                run_length += 1

            if run_length >= 2:
                # Encode as RLE sequence: [ESCAPE, byte, count]
                encoded.append(RLE.ESCAPE)
                encoded.append(byte)
                encoded.append(run_length)
                i += run_length
            else:
                # Single byte - encode as-is, but escape if it's the marker
                if byte == RLE.ESCAPE:
                    encoded.append(RLE.ESCAPE)
                    encoded.append(RLE.ESCAPE)
                    encoded.append(1)
                else:
                    encoded.append(byte)
                i += 1

        return encoded

    @staticmethod
    def decode(data: List[int]) -> List[int]:
        """
        Decode RLE-encoded data back to original.

        Args:
            data: List of RLE-encoded bytes.

        Returns:
            List of original bytes.
        """
        if not data:
            return []

        decoded: List[int] = []
        i: int = 0
        data_len: int = len(data)

        while i < data_len:
            byte = data[i]

            if byte == RLE.ESCAPE:
                # Check if this is an RLE sequence
                if i + 2 < data_len:
                    next_byte = data[i + 1]
                    count = data[i + 2]

                    # Expand the run
                    decoded.extend([next_byte] * count)
                    i += 3
                else:
                    # Incomplete sequence at end - treat as regular byte
                    decoded.append(byte)
                    i += 1
            else:
                # Regular byte
                decoded.append(byte)
                i += 1

        return decoded
