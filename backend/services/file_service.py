import io
import json
import uuid
import re
import hashlib
import mimetypes
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Generator, Union, BinaryIO

from config import Config
from services.webhdfs_service import WebHDFSService, WebHDFSError
from services.encryption_service import EncryptionService, EncryptionError, DecryptionError
from services.chunk_service import ChunkService

logger = logging.getLogger(__name__)

class FileServiceError(Exception):
    """Base exception for FileService operations."""
    pass

class FileService:
    def __init__(
        self,
        webhdfs: Optional[WebHDFSService] = None,
        encryption: Optional[EncryptionService] = None,
        storage_root: Optional[str] = None
    ):
        self.webhdfs = webhdfs or WebHDFSService()
        self.encryption = encryption or EncryptionService()
        self.storage_root = (storage_root or Config.STORAGE_ROOT).rstrip("/")

    def _resolve_hdfs_path(self, relative_path: str) -> str:
        """
        Safely resolve a relative user path to an absolute HDFS path.
        Prevents path traversal attacks (e.g. '../').
        """
        clean_rel = relative_path.strip().replace("\\", "/").strip("/")
        parts = [p for p in clean_rel.split("/") if p and p != "."]
        for part in parts:
            if part == "..":
                raise FileServiceError("Path traversal (..) is strictly prohibited")
        return f"{self.storage_root}/{'/'.join(parts)}" if parts else self.storage_root

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent special character issues in HDFS directory names."""
        clean_name = os_basename = filename.strip().replace("\\", "/").split("/")[-1]
        # Keep alphanumeric, dots, underscores, dashes
        safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', clean_name)
        return safe_name[:60] if safe_name else "file"

    def upload_file(
        self,
        relative_dir: str,
        filename: str,
        data_source: Union[bytes, bytearray, BinaryIO],
        username: str
    ) -> Dict[str, Any]:
        """
        Uploads a file to shared HDFS storage:
        1. Splits file into 1 MiB chunks.
        2. Encrypts each chunk using AES-256-GCM with a unique nonce.
        3. Stores encrypted chunks in HDFS under .file_<filename>_<file_id>/
        4. Writes manifest.json in the file's HDFS folder.
        5. Cleans up on any failure.
        """
        if not filename or not filename.strip():
            raise FileServiceError("Filename cannot be empty")

        clean_filename = filename.strip().replace("\\", "/").split("/")[-1]
        parent_hdfs_dir = self._resolve_hdfs_path(relative_dir)
        file_id = str(uuid.uuid4())
        safe_name = self._sanitize_filename(clean_filename)
        file_folder_name = f".file_{safe_name}_{file_id}"
        file_hdfs_dir = f"{parent_hdfs_dir}/{file_folder_name}"

        # Ensure parent directory exists in HDFS
        self.webhdfs.mkdirs(parent_hdfs_dir)
        # Create file container directory
        self.webhdfs.mkdirs(file_hdfs_dir)

        sha256_hasher = hashlib.sha256()
        total_size = 0
        chunks_meta = []

        try:
            for index, chunk_plaintext in ChunkService.split_into_chunks(data_source, Config.CHUNK_SIZE):
                sha256_hasher.update(chunk_plaintext)
                chunk_len = len(chunk_plaintext)
                total_size += chunk_len

                # Encrypt chunk
                ciphertext, nonce_hex, tag_hex = self.encryption.encrypt_chunk(chunk_plaintext)

                # Store encrypted chunk in HDFS
                chunk_filename = f"chunk_{index:04d}.enc"
                chunk_hdfs_path = f"{file_hdfs_dir}/{chunk_filename}"
                self.webhdfs.write_file(chunk_hdfs_path, ciphertext, overwrite=True)

                chunks_meta.append({
                    "index": index,
                    "chunk_filename": chunk_filename,
                    "size": chunk_len,
                    "encrypted_size": len(ciphertext),
                    "nonce": nonce_hex,
                    "tag": tag_hex
                })

            mime_type, _ = mimetypes.guess_type(clean_filename)
            manifest = {
                "file_id": file_id,
                "original_filename": clean_filename,
                "relative_dir": relative_dir.strip().strip("/"),
                "file_size": total_size,
                "sha256": sha256_hasher.hexdigest(),
                "mime_type": mime_type or "application/octet-stream",
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "uploaded_by": username,
                "chunk_size": Config.CHUNK_SIZE,
                "chunk_count": len(chunks_meta),
                "chunks": chunks_meta,
                "hdfs_folder": file_hdfs_dir
            }

            # Save manifest.json in HDFS
            manifest_json_bytes = json.dumps(manifest, indent=2).encode("utf-8")
            self.webhdfs.write_file(f"{file_hdfs_dir}/manifest.json", manifest_json_bytes, overwrite=True)

            logger.info(f"File '{clean_filename}' ({total_size} bytes, {len(chunks_meta)} chunks) uploaded to {file_hdfs_dir}")
            return manifest

        except Exception as e:
            logger.error(f"Upload failed for '{clean_filename}', rolling back {file_hdfs_dir}: {e}")
            self.webhdfs.delete(file_hdfs_dir, recursive=True)
            raise FileServiceError(f"Upload failed: {e}")

    def get_manifest(self, file_hdfs_dir: str) -> Dict[str, Any]:
        """Read and parse manifest.json for a file from HDFS."""
        manifest_path = f"{file_hdfs_dir.rstrip('/')}/manifest.json"
        manifest_bytes = self.webhdfs.read_file(manifest_path)
        return json.loads(manifest_bytes.decode("utf-8"))

    def download_file(self, file_hdfs_dir: str) -> Tuple[Dict[str, Any], Generator[bytes, None, None]]:
        """
        Download and decrypt a file:
        1. Reads manifest.json from HDFS.
        2. Returns manifest and a generator yielding decrypted chunks sequentially.
        """
        manifest = self.get_manifest(file_hdfs_dir)
        chunks = manifest.get("chunks", [])

        def chunk_stream_generator() -> Generator[bytes, None, None]:
            for chunk_meta in sorted(chunks, key=lambda c: c["index"]):
                chunk_filename = chunk_meta["chunk_filename"]
                chunk_hdfs_path = f"{file_hdfs_dir.rstrip('/')}/{chunk_filename}"
                ciphertext = self.webhdfs.read_file(chunk_hdfs_path)

                # Decrypt chunk with authentication tag check
                plaintext = self.encryption.decrypt_chunk(
                    ciphertext=ciphertext,
                    nonce_hex=chunk_meta["nonce"],
                    tag_hex=chunk_meta["tag"]
                )
                yield plaintext

        return manifest, chunk_stream_generator()

    def delete_file(self, file_hdfs_dir: str) -> bool:
        """Delete an encrypted file directory from HDFS."""
        return self.webhdfs.delete(file_hdfs_dir, recursive=True)

    def rename_file(self, file_hdfs_dir: str, new_filename: str) -> Dict[str, Any]:
        """
        Rename an existing file by updating its manifest.
        Does not require re-encrypting or moving chunk blocks.
        """
        if not new_filename or not new_filename.strip():
            raise FileServiceError("New filename cannot be empty")

        clean_new_name = new_filename.strip().replace("\\", "/").split("/")[-1]
        manifest = self.get_manifest(file_hdfs_dir)
        manifest["original_filename"] = clean_new_name
        mime_type, _ = mimetypes.guess_type(clean_new_name)
        manifest["mime_type"] = mime_type or "application/octet-stream"

        manifest_json_bytes = json.dumps(manifest, indent=2).encode("utf-8")
        self.webhdfs.write_file(f"{file_hdfs_dir.rstrip('/')}/manifest.json", manifest_json_bytes, overwrite=True)
        return manifest

    def create_folder(self, relative_dir: str, folder_name: str) -> bool:
        """Create a new folder in HDFS."""
        if not folder_name or not folder_name.strip():
            raise FileServiceError("Folder name cannot be empty")

        clean_name = folder_name.strip().replace("\\", "/").split("/")[-1]
        if clean_name.startswith("."):
            raise FileServiceError("Folder names cannot start with a dot")

        parent_hdfs_dir = self._resolve_hdfs_path(relative_dir)
        target_hdfs_dir = f"{parent_hdfs_dir}/{clean_name}"
        return self.webhdfs.mkdirs(target_hdfs_dir)

    def delete_folder(self, relative_dir: str) -> bool:
        """Delete a folder and all its contents from HDFS."""
        hdfs_dir = self._resolve_hdfs_path(relative_dir)
        if hdfs_dir == self.storage_root:
            raise FileServiceError("Cannot delete root shared storage directory")
        return self.webhdfs.delete(hdfs_dir, recursive=True)

    def list_directory(self, relative_dir: str = "") -> Dict[str, Any]:
        """
        List shared files and folders at the specified relative path.
        Distinguishes normal user folders from encrypted file directories (.file_*).
        """
        hdfs_dir = self._resolve_hdfs_path(relative_dir)
        try:
            entries = self.webhdfs.list_status(hdfs_dir)
        except FileNotFoundError:
            # If root doesn't exist, create it
            if hdfs_dir == self.storage_root:
                self.webhdfs.mkdirs(self.storage_root)
                entries = []
            else:
                raise

        folders = []
        files = []

        for entry in entries:
            name = entry.get("pathSuffix", "")
            entry_type = entry.get("type", "")

            if entry_type == "DIRECTORY":
                if name.startswith(".file_"):
                    # This is an encrypted file container! Read its manifest
                    file_hdfs_path = f"{hdfs_dir}/{name}"
                    try:
                        manifest = self.get_manifest(file_hdfs_path)
                        files.append({
                            "file_id": manifest.get("file_id"),
                            "name": manifest.get("original_filename"),
                            "size": manifest.get("file_size"),
                            "mime_type": manifest.get("mime_type"),
                            "uploaded_at": manifest.get("uploaded_at"),
                            "uploaded_by": manifest.get("uploaded_by"),
                            "chunk_count": manifest.get("chunk_count"),
                            "hdfs_folder": file_hdfs_path,
                            "relative_dir": relative_dir.strip().strip("/")
                        })
                    except Exception as e:
                        logger.warning(f"Could not read manifest for {file_hdfs_path}: {e}")
                else:
                    # Regular user folder
                    folders.append({
                        "name": name,
                        "modification_time": entry.get("modificationTime"),
                        "permission": entry.get("permission"),
                        "relative_dir": relative_dir.strip().strip("/")
                    })

        return {
            "current_path": relative_dir.strip().strip("/"),
            "folders": sorted(folders, key=lambda f: f["name"].lower()),
            "files": sorted(files, key=lambda f: f["name"].lower())
        }

    def search_files(self, query: str, relative_dir: str = "") -> List[Dict[str, Any]]:
        """
        Recursively search for files matching query (case-insensitive)
        across the shared HDFS storage tree.
        """
        q = query.strip().lower()
        if not q:
            return []

        results = []
        base_hdfs_dir = self._resolve_hdfs_path(relative_dir)

        def walk(current_hdfs_dir: str, current_rel_dir: str):
            try:
                entries = self.webhdfs.list_status(current_hdfs_dir)
            except Exception:
                return

            for entry in entries:
                name = entry.get("pathSuffix", "")
                if entry.get("type") == "DIRECTORY":
                    if name.startswith(".file_"):
                        # Check manifest
                        file_hdfs_path = f"{current_hdfs_dir}/{name}"
                        try:
                            manifest = self.get_manifest(file_hdfs_path)
                            orig_name = manifest.get("original_filename", "")
                            if q in orig_name.lower():
                                results.append({
                                    "file_id": manifest.get("file_id"),
                                    "name": orig_name,
                                    "size": manifest.get("file_size"),
                                    "mime_type": manifest.get("mime_type"),
                                    "uploaded_at": manifest.get("uploaded_at"),
                                    "uploaded_by": manifest.get("uploaded_by"),
                                    "chunk_count": manifest.get("chunk_count"),
                                    "hdfs_folder": file_hdfs_path,
                                    "relative_dir": current_rel_dir
                                })
                        except Exception:
                            continue
                    else:
                        # Recurse into child folder
                        sub_rel = f"{current_rel_dir}/{name}".strip("/") if current_rel_dir else name
                        walk(f"{current_hdfs_dir}/{name}", sub_rel)

        walk(base_hdfs_dir, relative_dir.strip().strip("/"))
        return results

