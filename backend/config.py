import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "lan-cloud-storage-super-secret-key-2026")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    # Hadoop WebHDFS configuration
    MASTER_IP = os.getenv("MASTER_IP", "127.0.0.1")
    WEBHDFS_PORT = int(os.getenv("WEBHDFS_PORT", "9870"))
    WEBHDFS_URL = os.getenv("WEBHDFS_URL", f"http://{MASTER_IP}:{WEBHDFS_PORT}/webhdfs/v1")
    HDFS_USER = os.getenv("HDFS_USER", "sanmesh")

    # Cloud storage configuration
    STORAGE_ROOT = os.getenv("STORAGE_ROOT", "/cloud-storage/shared").rstrip("/")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", str(1024 * 1024)))  # 1 MiB chunks

    # AES-256-GCM encryption key (32 bytes = 256 bits, hex-encoded)
    # Default 32-byte key for local dev if not provided in environment
    AES_KEY_HEX = os.getenv(
        "AES_KEY",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    )
    
    @classmethod
    def get_aes_key_bytes(cls) -> bytes:
        return bytes.fromhex(cls.AES_KEY_HEX)

