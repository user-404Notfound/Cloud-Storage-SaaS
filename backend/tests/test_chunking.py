import io
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.chunk_service import ChunkService

def test_split_and_combine_exact_bytes():
    # 2.5 MiB data buffer
    chunk_size = 1024 * 1024  # 1 MiB
    total_size = int(2.5 * 1024 * 1024)
    data = os.urandom(total_size)
    
    chunks = list(ChunkService.split_into_chunks(data, chunk_size=chunk_size))
    
    # 2.5 MiB with 1 MiB chunks -> 3 chunks (1MB, 1MB, 0.5MB)
    assert len(chunks) == 3
    assert chunks[0][0] == 0
    assert len(chunks[0][1]) == chunk_size
    assert chunks[1][0] == 1
    assert len(chunks[1][1]) == chunk_size
    assert chunks[2][0] == 2
    assert len(chunks[2][1]) == int(0.5 * 1024 * 1024)
    
    # Combine chunks and verify exact byte equality
    reconstructed = b"".join(ChunkService.combine_chunks([c[1] for c in chunks]))
    assert reconstructed == data

def test_split_stream_io():
    stream_content = b"Stream chunk testing data line 1\nStream chunk testing data line 2\n"
    stream = io.BytesIO(stream_content)
    
    # Tiny chunk size to force multiple chunks
    chunks = list(ChunkService.split_into_chunks(stream, chunk_size=10))
    assert len(chunks) > 1
    
    reconstructed = b"".join(ChunkService.combine_chunks([c[1] for c in chunks]))
    assert reconstructed == stream_content

def test_empty_file_chunking():
    empty_data = b""
    chunks = list(ChunkService.split_into_chunks(empty_data))
    assert len(chunks) == 1
    assert chunks[0] == (0, b"")
    
    reconstructed = b"".join(ChunkService.combine_chunks([c[1] for c in chunks]))
    assert reconstructed == empty_data

