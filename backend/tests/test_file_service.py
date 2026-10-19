import os
import sys
import hashlib
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.webhdfs_service import WebHDFSService
from services.encryption_service import EncryptionService, DecryptionError
from services.file_service import FileService, FileServiceError
from config import Config

@pytest.fixture
def file_service():
    webhdfs = WebHDFSService(base_url=Config.WEBHDFS_URL, user=Config.HDFS_USER)
    encryption = EncryptionService()
    return FileService(webhdfs=webhdfs, encryption=encryption, storage_root="/cloud-storage/test_shared")

def test_file_upload_download_roundtrip_multi_chunk(file_service):
    # 2.2 MiB binary payload to force multiple 1 MiB chunks
    original_size = int(2.2 * 1024 * 1024)
    original_data = os.urandom(original_size)
    original_sha256 = hashlib.sha256(original_data).hexdigest()
    
    filename = "college_lab_dataset.bin"
    relative_dir = "assignments/lab2"
    username = "student_alex"

    # 1. Clean up test root before starting
    file_service.webhdfs.delete("/cloud-storage/test_shared", recursive=True)

    # 2. Upload file
    manifest = file_service.upload_file(
        relative_dir=relative_dir,
        filename=filename,
        data_source=original_data,
        username=username
    )

    assert manifest["original_filename"] == filename
    assert manifest["file_size"] == original_size
    assert manifest["sha256"] == original_sha256
    assert manifest["chunk_count"] == 3  # 1MB + 1MB + 0.2MB
    assert manifest["uploaded_by"] == username

    file_hdfs_dir = manifest["hdfs_folder"]

    # 3. Verify encrypted chunks in HDFS cannot be read as plaintext
    chunk0_path = f"{file_hdfs_dir}/chunk_0000.enc"
    encrypted_bytes = file_service.webhdfs.read_file(chunk0_path)
    assert encrypted_bytes != original_data[:len(encrypted_bytes)], "Stored chunk must be encrypted, not plaintext!"

    # 4. Download file and verify byte-for-byte reconstruction
    retrieved_manifest, chunk_generator = file_service.download_file(file_hdfs_dir)
    assert retrieved_manifest["file_id"] == manifest["file_id"]

    downloaded_data = b"".join(chunk_generator)
    downloaded_sha256 = hashlib.sha256(downloaded_data).hexdigest()

    assert len(downloaded_data) == original_size
    assert downloaded_sha256 == original_sha256
    assert downloaded_data == original_data

    # 5. Test Directory Listing
    listing = file_service.list_directory(relative_dir)
    assert len(listing["files"]) == 1
    assert listing["files"][0]["name"] == filename
    assert listing["files"][0]["size"] == original_size

    # 6. Test File Rename
    new_name = "college_lab_dataset_FINAL.bin"
    updated_manifest = file_service.rename_file(file_hdfs_dir, new_name)
    assert updated_manifest["original_filename"] == new_name

    listing_after_rename = file_service.list_directory(relative_dir)
    assert listing_after_rename["files"][0]["name"] == new_name

    # 7. Test Search
    search_results = file_service.search_files("FINAL")
    assert len(search_results) == 1
    assert search_results[0]["name"] == new_name

    search_none = file_service.search_files("nonexistent_keyword")
    assert len(search_none) == 0

    # 8. Test Tamper Detection on Storage
    # Corrupt one byte of chunk 0 in HDFS
    tampered_bytes = bytearray(encrypted_bytes)
    tampered_bytes[42] ^= 0xFF
    file_service.webhdfs.write_file(chunk0_path, bytes(tampered_bytes), overwrite=True)

    # Downloading tampered file must fail with DecryptionError
    _, tampered_chunk_gen = file_service.download_file(file_hdfs_dir)
    with pytest.raises(DecryptionError, match="authentication tag mismatch or corrupted data"):
        # Consume generator to trigger decryption
        for _ in tampered_chunk_gen:
            pass

    # 9. Test Deletion
    deleted = file_service.delete_file(file_hdfs_dir)
    assert deleted is True

    # Verify listing is now empty
    listing_after_delete = file_service.list_directory(relative_dir)
    assert len(listing_after_delete["files"]) == 0

    # 10. Test Folder operations
    file_service.create_folder("assignments", "lab3")
    listing_parent = file_service.list_directory("assignments")
    folder_names = [f["name"] for f in listing_parent["folders"]]
    assert "lab3" in folder_names

    # Clean up test root
    file_service.webhdfs.delete("/cloud-storage/test_shared", recursive=True)

