import io
import logging
from typing import Generator, Tuple, Union, BinaryIO, Iterable
from config import Config

logger = logging.getLogger(__name__)

class ChunkService:
    DEFAULT_CHUNK_SIZE = Config.CHUNK_SIZE  # Default: 1 MiB (1048576 bytes)

    @classmethod
    def split_into_chunks(
        cls,
        data_source: Union[bytes, bytearray, BinaryIO],
        chunk_size: int = DEFAULT_CHUNK_SIZE
    ) -> Generator[Tuple[int, bytes], None, None]:
        """
        Split bytes or a binary stream into sequential chunks of chunk_size.
        
        Yields:
            Tuple of (chunk_index, chunk_bytes)
        """
        if chunk_size <= 0:
            raise ValueError(f"Chunk size must be positive, got {chunk_size}")

        index = 0
        if isinstance(data_source, (bytes, bytearray)):
            total_len = len(data_source)
            if total_len == 0:
                # Empty file produces one 0-byte chunk so it can be reconstructed as empty file
                yield 0, b""
                return

            offset = 0
            while offset < total_len:
                chunk = bytes(data_source[offset : offset + chunk_size])
                yield index, chunk
                index += 1
                offset += chunk_size
        else:
            # Assumed to be a binary stream / file-like object
            has_data = False
            while True:
                chunk = data_source.read(chunk_size)
                if not chunk:
                    if not has_data:
                        # Empty stream
                        yield 0, b""
                    break
                has_data = True
                yield index, bytes(chunk)
                index += 1

    @classmethod
    def combine_chunks(cls, chunks: Iterable[bytes]) -> Generator[bytes, None, None]:
        """
        Stream sequential chunks back together.
        Yields each chunk byte sequence in order.
        """
        for chunk in chunks:
            yield chunk

