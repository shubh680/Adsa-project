"""
huffman.py — Adaptive Huffman Encoding (FGK Algorithm) for the Advanced File Compression System.

Implements the Faller, Gallager, Knuth (FGK) adaptive Huffman algorithm:
- Dynamically builds Huffman tree as symbols are encountered
- Maintains NYT (Not Yet Transmitted) node for unseen symbols
- Updates tree and frequencies incrementally
- Generates and decodes variable-length binary codes

No external dependencies.
"""


class Node:
    """
    Represents a node in the Huffman tree.

    Attributes:
        symbol: The character/byte this node represents (None for internal nodes).
        frequency: How many times this symbol has been encoded/decoded.
        left: Left child (0 bit).
        right: Right child (1 bit).
        parent: Parent node (for bottom-up traversal).
    """

    def __init__(self, symbol=None, frequency=0, left=None, right=None, parent=None):
        self.symbol = symbol
        self.frequency = frequency
        self.left = left
        self.right = right
        self.parent = parent

    def is_leaf(self):
        """Return True if this is a leaf node (has a symbol)."""
        return self.symbol is not None

    def is_nyt(self):
        """Return True if this is the NYT (Not Yet Transmitted) node."""
        return self.symbol is None and self.left is None and self.right is None

    def __repr__(self):
        if self.is_nyt():
            return f"NYT(freq={self.frequency})"
        elif self.is_leaf():
            return f"Leaf({self.symbol!r}, freq={self.frequency})"
        else:
            return f"Internal(freq={self.frequency})"


class AdaptiveHuffman:
    """
    Adaptive Huffman encoder/decoder using a simplified FGK algorithm.

    The tree is built dynamically:
    - Initially: tree contains only the NYT node
    - As new symbols are seen: NYT is split into [NYT, new_leaf]
    - After each symbol: frequencies are updated by walking up to root
    - No node swapping to avoid encoder/decoder sync issues
    """

    def __init__(self):
        """Initialize with empty tree (just NYT root)."""
        self.root = Node(symbol=None)  # Start with NYT root
        self.symbol_nodes = {}  # Map symbol -> its leaf node
        self.nyt_node = self.root  # Track the current NYT node

    def encode(self, symbols):
        """
        Encode a sequence of symbols to bits.

        Format: [length (16 bits)] [symbol data]

        Args:
            symbols: Iterable of symbols (integers 0-255).

        Returns:
            List of bits (0 and 1) representing the encoded data.
        """
        symbols = list(symbols)
        bits = []

        # Encode length as 16-bit value
        length = len(symbols)
        for i in range(16):
            bits.append((length >> (15 - i)) & 1)

        # Encode each symbol
        for symbol in symbols:
            bits.extend(self._encode_symbol(symbol))

        return bits

    def decode(self, bits):
        """
        Decode a bit sequence back to symbols.

        Format: [length (16 bits)] [symbol data]

        Args:
            bits: List of bits (0 and 1).

        Returns:
            List of decoded symbols.
        """
        if len(bits) < 16:
            return []

        # Decode length
        length = 0
        for i in range(16):
            length = (length << 1) | bits[i]

        # Decode symbols
        symbols = []
        i = 16
        while len(symbols) < length and i < len(bits):
            try:
                symbol, bits_consumed = self._decode_symbol(bits[i:])
                symbols.append(symbol)
                i += bits_consumed
            except ValueError:
                # Incomplete bit sequence
                break

        return symbols

    def _encode_symbol(self, symbol):
        """
        Encode a single symbol and update the tree.

        If symbol is unseen:
          - Emit code for NYT node
          - Emit the symbol's 8-bit value
          - Split NYT and introduce symbol
        If symbol is seen:
          - Emit code for its leaf node

        Then update frequencies up the tree.

        Args:
            symbol: The symbol to encode (0-255).

        Returns:
            List of bits representing the encoded symbol.
        """
        bits = []

        if symbol not in self.symbol_nodes:
            # Symbol not yet seen: emit NYT code + symbol value
            bits.extend(self._get_code(self.nyt_node))
            bits.extend(self._symbol_to_bits(symbol))
            self._introduce_symbol(symbol)
            # Update frequencies (starting from the new leaf)
            self._update_frequency(self.symbol_nodes[symbol])
        else:
            # Symbol already seen: emit its code
            node = self.symbol_nodes[symbol]
            bits.extend(self._get_code(node))
            # Update frequencies
            self._update_frequency(node)

        return bits

    def _decode_symbol(self, bits):
        """
        Decode a single symbol from bits and update the tree.

        Args:
            bits: List of remaining bits to read.

        Returns:
            Tuple (symbol, bits_consumed).
        """
        if not bits:
            raise ValueError("No bits to decode")

        node = self.root
        bits_consumed = 0

        # If root is NYT, this must be the first symbol
        if node.is_nyt():
            # Unseen symbol: read 8-bit representation
            if len(bits) < 8:
                raise ValueError("Incomplete symbol value")
            symbol = self._bits_to_symbol(bits[:8])
            self._introduce_symbol(symbol)
            self._update_frequency(self.symbol_nodes[symbol])
            return symbol, 8

        # Traverse tree following bits until we hit a leaf or NYT
        while bits_consumed < len(bits) and not node.is_leaf() and not node.is_nyt():
            bit = bits[bits_consumed]
            bits_consumed += 1
            node = node.right if bit == 1 else node.left

        # Handle leaf vs NYT
        if node.is_nyt():
            # Unseen symbol: read 8-bit representation
            if bits_consumed + 8 > len(bits):
                raise ValueError("Incomplete symbol value")
            symbol = self._bits_to_symbol(bits[bits_consumed:bits_consumed + 8])
            bits_consumed += 8
            self._introduce_symbol(symbol)
        elif node.is_leaf():
            # Known symbol
            symbol = node.symbol
        else:
            raise ValueError(f"Unexpected node state: {node}")

        # Update frequency
        self._update_frequency(self.symbol_nodes[symbol])

        return symbol, bits_consumed

    def _introduce_symbol(self, symbol):
        """
        Introduce a new symbol to the tree by splitting NYT.

        Splits the NYT node into an internal node with two children:
        - Left: new NYT node
        - Right: new leaf for the symbol

        Args:
            symbol: The symbol being introduced.
        """
        # Create new leaf for the symbol
        new_leaf = Node(symbol=symbol, frequency=0, parent=self.nyt_node)

        # Create new NYT node
        new_nyt = Node(symbol=None, frequency=0, parent=self.nyt_node)

        # Update current NYT to be internal
        self.nyt_node.left = new_nyt
        self.nyt_node.right = new_leaf
        self.nyt_node.symbol = None

        # Track nodes
        self.symbol_nodes[symbol] = new_leaf
        self.nyt_node = new_nyt

    def _update_frequency(self, node):
        """
        Update node frequency by walking up to root.

        Simple approach: just increment frequencies without swapping
        to ensure encoder and decoder stay in sync.

        Args:
            node: The node to start updating from.
        """
        while node is not None:
            node.frequency += 1
            node = node.parent

    def _get_code(self, node):
        """
        Generate the binary code for a node by traversing from root.

        Args:
            node: Target node.

        Returns:
            List of bits (0 = left, 1 = right).
        """
        path = []
        current = node

        # Collect path from node to root
        while current.parent is not None:
            parent = current.parent
            if parent.left == current:
                path.append(0)
            else:
                path.append(1)
            current = parent

        # Reverse to get root → node
        return path[::-1]

    @staticmethod
    def _symbol_to_bits(symbol):
        """Convert a symbol (0-255) to 8 bits."""
        symbol = symbol % 256  # Ensure in byte range
        return [(symbol >> (7 - i)) & 1 for i in range(8)]

    @staticmethod
    def _bits_to_symbol(bits):
        """Convert 8 bits to a symbol."""
        symbol = 0
        for i, bit in enumerate(bits[:8]):
            symbol = (symbol << 1) | bit
        return symbol


