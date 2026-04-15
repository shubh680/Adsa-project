# Advanced File Compression System (ADSA)

A Python-based file compression project with:
- Adaptive Huffman coding
- Run-Length Encoding (RLE)
- Hybrid algorithm selection (RLE+Huffman vs DEFLATE)
- Flask API backend and a minimal web frontend

## Current Status

- Core compression/decompression modules: available
- Web API + frontend flow: available
- Repository cleaned for commit (removed temp/generated/extra files)

## Repository Structure

```text
ADSA-project/
├── app.py
├── index.html
├── compress.py
├── hybrid_compressor.py
├── compressor_with_rle.py
├── compressor.py
├── huffman.py
├── rle.py
├── bit_io.py
├── requirements.txt
├── run.bat
├── run.sh
├── Ship_Performance_Dataset.csv
├── test_bit_io.py
├── test_huffman.py
├── test_compressor.py
├── test_rle.py
└── test_complete_workflow.py
```

## Features Implemented

1. Compression and decompression through API:
   - `POST /api/compress`
   - `POST /api/decompress`
2. Auto-selection of compression strategy in hybrid mode.
3. Original filename metadata preserved during compression.
4. Decompression output extension auto-detection:
   - PDF (`%PDF-` signature)
   - CSV (delimiter/sample based check)
   - TXT fallback
5. Frontend improvements:
   - Drag-and-drop upload for compress/decompress
   - File visibility in both panels
   - Stats after compression and decompression
   - Ratios shown as percentages
   - Sizes shown in auto units (B/KB/MB)
   - Entropy hidden from UI stats display
   - Correct status transitions (no stale “Compressing/Decompressing...”)

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Then open:
- `http://localhost:5000/` (served by Flask)

## CLI Usage

```bash
# Compress (hybrid auto-selection)
python compress.py compress input.txt output.bin -v

# Decompress
python compress.py decompress output.bin recovered.txt -v

# Verify round-trip
python compress.py verify input.txt output.bin
```

## API Endpoints

- `GET /api/health`
- `GET /api/algorithms`
- `POST /api/compress`
- `POST /api/decompress`
- `POST /api/analyze`

## Notes

- Maximum upload size in API: 50 MB.
- Temporary API files are created under `temp_uploads/` at runtime.
- Keep `Ship_Performance_Dataset.csv` as sample test data.
