"""
Flask API server for ADSA Compression System
Provides RESTful endpoints for file compression/decompression
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import base64
import uuid
import csv
import io
import traceback
from hybrid_compressor import HybridCompressor
from compressor_with_rle import CompressorWithRLE
import zlib

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def _detect_decompressed_extension(data):
    """Detect whether decompressed data best matches PDF, CSV, or plain text."""
    # PDF signature: %PDF-
    if data.startswith(b'%PDF-'):
        return 'pdf'

    try:
        decoded = data.decode('utf-8')
    except UnicodeDecodeError:
        return 'bin'

    lines = [line for line in decoded.splitlines() if line.strip()]
    if len(lines) < 2:
        return 'txt'

    sample = '\n'.join(lines[:50])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
        rows = [row for row in csv.reader(io.StringIO(sample), dialect) if row]
        if len(rows) >= 2:
            widths = [len(row) for row in rows]
            if min(widths) > 1 and len(set(widths)) <= 2:
                return 'csv'
    except csv.Error:
        pass

    return 'txt'


def _apply_detected_extension(filename, detected_ext):
    base_name, _ = os.path.splitext(filename or 'decompressed')
    return f"{base_name}.{detected_ext}"


@app.route('/', methods=['GET'])
def index():
    """Serve the frontend"""
    return send_file('index.html', mimetype='text/html')


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'ADSA Compression',
        'version': '2.0'
    }), 200


@app.route('/api/algorithms', methods=['GET'])
def list_algorithms():
    """Get list of available compression algorithms"""
    return jsonify({
        'algorithms': [
            {
                'id': 'auto',
                'name': 'Intelligent Auto-Select',
                'description': 'Analyzes data and automatically selects the best compression algorithm',
                'bestFor': ['Mixed data', 'Unknown file types'],
                'compression': 'High (varies by data)'
            },
            {
                'id': 'rle_huffman',
                'name': 'RLE + Adaptive Huffman',
                'description': 'Run-Length Encoding followed by Adaptive Huffman coding',
                'bestFor': ['Highly repetitive data', 'Log files', 'Text with patterns'],
                'compression': 'Excellent (99%+)'
            },
            {
                'id': 'huffman',
                'name': 'Adaptive Huffman Only',
                'description': 'Adaptive Huffman coding without RLE preprocessing',
                'bestFor': ['Natural text', 'General files'],
                'compression': 'Good (40-60%)'
            },
            {
                'id': 'deflate',
                'name': 'DEFLATE (zlib)',
                'description': 'DEFLATE compression with LZ77 and Huffman encoding',
                'bestFor': ['Structured data', 'CSV, JSON files', 'Generic files'],
                'compression': 'Very Good (50-70%)'
            }
        ]
    }), 200


@app.route('/api/compress', methods=['POST'])
def compress_file():
    """
    Compress a file using specified or auto-detected algorithm
    """
    temp_id = str(uuid.uuid4())[:8]
    input_path = os.path.join(UPLOAD_FOLDER, f'{temp_id}_input.bin')
    output_path = os.path.join(UPLOAD_FOLDER, f'{temp_id}_output.bin')
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        algorithm = request.form.get('algorithm', 'auto')
        input_data = file.read()
        original_filename = file.filename
        
        if len(input_data) == 0:
            return jsonify({'error': 'File is empty'}), 400
        
        if len(input_data) > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large'}), 413
        
        # Store original filename with compressed data
        filename_bytes = original_filename.encode('utf-8')
        filename_length = len(filename_bytes).to_bytes(2, byteorder='big')
        
        # Save input file
        with open(input_path, 'wb') as f:
            f.write(input_data)
        
        try:
            # Perform compression
            if algorithm == 'auto':
                compressor = HybridCompressor(verbose=False)
            elif algorithm == 'rle_huffman':
                compressor = CompressorWithRLE(verbose=False, use_rle=True)
            elif algorithm == 'huffman':
                compressor = CompressorWithRLE(verbose=False, use_rle=False)
            elif algorithm == 'deflate':
                compressed_data = zlib.compress(input_data, 9)
                # Add filename metadata
                final_compressed = filename_length + filename_bytes + compressed_data
                result = {
                    'original_size': len(input_data),
                    'compressed_size': len(final_compressed),
                    'compression_ratio': len(final_compressed) / len(input_data),
                    'algorithm': 'DEFLATE'
                }
                os.remove(input_path)
                return jsonify({
                    'success': True,
                    'compressed_data': base64.b64encode(final_compressed).decode('utf-8'),
                    'stats': result
                }), 200
            else:
                return jsonify({'error': f'Unknown algorithm'}), 400
            
            stats = compressor.compress(input_path, output_path)
            
            # Read compressed data
            with open(output_path, 'rb') as f:
                compressed_data = f.read()
            
            # Add filename metadata
            final_compressed = filename_length + filename_bytes + compressed_data
            
            return jsonify({
                'success': True,
                'compressed_data': base64.b64encode(final_compressed).decode('utf-8'),
                'stats': stats
            }), 200
        
        finally:
            # Cleanup
            for path in [input_path, output_path]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass
    
    except Exception as e:
        return jsonify({'error': f'Compression failed: {str(e)}'}), 500


@app.route('/api/decompress', methods=['POST'])
def decompress_file():
    """
    Decompress a file (auto-detects algorithm from file header)
    """
    temp_id = str(uuid.uuid4())[:8]
    input_path = os.path.join(UPLOAD_FOLDER, f'{temp_id}_compressed.bin')
    output_path = os.path.join(UPLOAD_FOLDER, f'{temp_id}_decompressed.bin')
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        input_data = file.read()
        
        if len(input_data) == 0:
            return jsonify({'error': 'File is empty'}), 400
        
        # Try to extract original filename from metadata
        original_filename = 'decompressed'
        try:
            filename_length = int.from_bytes(input_data[:2], byteorder='big')
            if filename_length > 0 and filename_length < 256:
                original_filename = input_data[2:2+filename_length].decode('utf-8')
                # Remove metadata from input data
                input_data = input_data[2+filename_length:]
        except:
            pass
        
        with open(input_path, 'wb') as f:
            f.write(input_data)
        
        decompressed_data = None
        stats = None
        
        # Try HybridCompressor first
        try:
            compressor = HybridCompressor(verbose=False)
            stats = compressor.decompress(input_path, output_path)
            with open(output_path, 'rb') as f:
                decompressed_data = f.read()
        except:
            pass
        
        # Try CompressorWithRLE if HybridCompressor failed
        if decompressed_data is None:
            try:
                compressor = CompressorWithRLE(verbose=False)
                stats = compressor.decompress(input_path, output_path)
                with open(output_path, 'rb') as f:
                    decompressed_data = f.read()
            except:
                pass
        
        # Try zlib as last resort
        if decompressed_data is None:
            try:
                decompressed_data = zlib.decompress(input_data)
                stats = {
                    'compressed_size': len(input_data),
                    'decompressed_size': len(decompressed_data),
                    'algorithm': 'DEFLATE'
                }
            except:
                pass
        
        if decompressed_data is None:
            return jsonify({'error': 'Could not decompress file - unsupported format'}), 400

        detected_ext = _detect_decompressed_extension(decompressed_data)
        original_filename = _apply_detected_extension(original_filename, detected_ext)

        if not isinstance(stats, dict):
            stats = {}

        compressed_size = stats.get('compressed_size', len(input_data))
        decompressed_size = stats.get('decompressed_size', len(decompressed_data))

        stats['compressed_size'] = compressed_size
        stats['decompressed_size'] = decompressed_size
        stats['original_size'] = decompressed_size
        stats['decompression_ratio'] = (
            (decompressed_size / compressed_size) if compressed_size > 0 else 0
        )
        stats['detected_format'] = detected_ext.upper()

        # Mirror compression-side analysis for decompressed output.
        analyzer = HybridCompressor(verbose=False)
        _, _, has_runs, has_delimiters, compression_type = analyzer._analyze_data(
            decompressed_data[:min(len(decompressed_data), 1000000)]
        )
        stats['compression_type'] = compression_type
        stats['has_long_runs'] = has_runs
        stats['has_delimiters'] = has_delimiters
        stats.setdefault('algorithm', 'Auto-detected')
        
        return jsonify({
            'success': True,
            'decompressed_data': base64.b64encode(decompressed_data).decode('utf-8'),
            'original_filename': original_filename,
            'stats': stats or {}
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Decompression failed: {str(e)}'}), 500
    
    finally:
        for path in [input_path, output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass


@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """
    Analyze file data and predict best compression algorithm
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        input_data = file.read()
        
        if len(input_data) == 0:
            return jsonify({'error': 'File is empty'}), 400
        
        compressor = HybridCompressor()
        algorithm, entropy, has_runs, has_delimiters, compression_type = compressor._analyze_data(
            input_data[:min(len(input_data), 1000000)]
        )
        
        algorithm_map = {
            0: 'RLE + Huffman',
            1: 'DEFLATE',
            2: 'Hybrid'
        }
        
        return jsonify({
            'success': True,
            'analysis': {
                'file_size': len(input_data),
                'entropy': round(entropy, 4),
                'has_long_runs': has_runs,
                'has_delimiters': has_delimiters,
                'compression_type': compression_type,
                'recommended_algorithm': algorithm_map.get(algorithm, 'auto')
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large'}), 413


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
