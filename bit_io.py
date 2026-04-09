"""
bit_io.py — Bit-Level I/O module for the Advanced File Compression System.

Provides BitWriter and BitReader classes for writing and reading individual
bits to/from binary files. Designed for integration with Adaptive Huffman
encoding and other bit-level compression algorithms.
"""


class BitWriter:
    """
    Writes individual bits to a binary file.

    Bits are packed into bytes (MSB first) and flushed to the file
    once a full byte is assembled. Any remaining bits at the end are
    zero-padded and written via flush().

    Usage:
        with open("output.bin", "wb") as f:
            writer = BitWriter(f)
            writer.write_bit(1)
            writer.write_bit(0)
            ...
            writer.flush()
    """

    def __init__(self, file):
        """
        Args:
            file: A binary file object opened in write mode ("wb").
        """
        self._file = file
        self._buffer = 0      # current byte being assembled
        self._bit_count = 0   # number of bits written into the buffer so far

    def write_bit(self, bit: int) -> None:
        """
        Write a single bit (0 or 1) to the output stream.

        Bits are packed MSB-first into an 8-bit buffer. When the buffer
        is full, the byte is written to the file and the buffer resets.

        Args:
            bit: Integer 0 or 1.

        Raises:
            ValueError: If bit is not 0 or 1.
        """
        if bit not in (0, 1):
            raise ValueError(f"bit must be 0 or 1, got {bit!r}")

        # Shift the existing bits left to make room, then OR in the new bit.
        self._buffer = (self._buffer << 1) | bit
        self._bit_count += 1

        if self._bit_count == 8:
            self._flush_buffer()

    def flush(self) -> None:
        """
        Write any remaining bits in the buffer to the file.

        If the buffer holds fewer than 8 bits, it is zero-padded on the
        right (LSB side) to form a complete byte before writing.
        Should always be called when writing is complete.
        """
        if self._bit_count > 0:
            # Shift remaining bits to the MSB positions; LSBs become 0.
            self._buffer <<= (8 - self._bit_count)
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Write the current byte buffer to the file and reset state."""
        self._file.write(bytes([self._buffer]))
        self._buffer = 0
        self._bit_count = 0


class BitReader:
    """
    Reads individual bits from a binary file.

    Reads one byte at a time from the file and serves bits one at a time
    from MSB to LSB. Returns None when the file is exhausted.

    Usage:
        with open("output.bin", "rb") as f:
            reader = BitReader(f)
            bit = reader.read_bit()   # returns 0, 1, or None
    """

    def __init__(self, file):
        """
        Args:
            file: A binary file object opened in read mode ("rb").
        """
        self._file = file
        self._buffer = 0      # current byte being consumed
        self._bits_left = 0  # number of unread bits remaining in the buffer

    def read_bit(self):
        """
        Read and return the next bit from the input stream.

        Returns:
            int: 0 or 1 — the next bit.
            None: if the end of file has been reached.
        """
        if self._bits_left == 0:
            byte = self._file.read(1)
            if not byte:
                return None  # EOF
            self._buffer = byte[0]
            self._bits_left = 8

        # Extract the MSB: shift it to position 0, then mask with 1.
        self._bits_left -= 1
        return (self._buffer >> self._bits_left) & 1
