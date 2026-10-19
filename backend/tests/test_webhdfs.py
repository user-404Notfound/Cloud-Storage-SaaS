import os
import sys
import pytest

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.webhdfs_service import WebHDFSService, WebHDFSError
from config import Config

@pytest.fixture
def hdfs_client():
    return WebHDFSService(base_url=Config.WEBHDFS_URL, user=Config.HDFS_USER)

def test_webhdfs_live_cluster_operations(hdfs_client):
    test_dir = "/cloud-storage/test_phase1"
    test_file = f"{test_dir}/sample.txt"
    test_content = b"Phase 1 WebHDFS Integration Test Byte Stream!"
    renamed_file = f"{test_dir}/sample_renamed.txt"

    # 1. Clean up any previous test remnants
    hdfs_client.delete(test_dir, recursive=True)

    # 2. MKDIRS
    created = hdfs_client.mkdirs(test_dir)
    assert created is True, "Failed to create directory in HDFS"

    # 3. WRITE_FILE (2-step upload)
    uploaded = hdfs_client.write_file(test_file, test_content, overwrite=True)
    assert uploaded is True, "Failed to write file to HDFS"

    # 4. GET_FILE_STATUS
    status = hdfs_client.get_file_status(test_file)
    assert status.get("type") == "FILE", "Expected FILE type"
    assert status.get("length") == len(test_content), "File length mismatch"

    # 5. LIST_STATUS
    entries = hdfs_client.list_status(test_dir)
    assert len(entries) == 1, f"Expected 1 entry, got {len(entries)}"
    assert entries[0]["pathSuffix"] == "sample.txt"

    # 6. READ_FILE (Download & byte comparison)
    downloaded_data = hdfs_client.read_file(test_file)
    assert downloaded_data == test_content, "Downloaded content did not match uploaded bytes"

    # 7. RENAME
    renamed = hdfs_client.rename(test_file, renamed_file)
    assert renamed is True, "Failed to rename file in HDFS"

    # Verify old file is gone and new file exists
    with pytest.raises(FileNotFoundError):
        hdfs_client.get_file_status(test_file)

    renamed_data = hdfs_client.read_file(renamed_file)
    assert renamed_data == test_content

    # 8. DELETE
    deleted = hdfs_client.delete(test_dir, recursive=True)
    assert deleted is True, "Failed to delete test directory"

    # Verify directory is gone
    with pytest.raises(FileNotFoundError):
        hdfs_client.list_status(test_dir)

