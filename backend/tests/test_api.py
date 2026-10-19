import io
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from config import Config

@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-12345"
    })
    with app.test_client() as client:
        yield client

def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["webhdfs_connected"] is True

def test_unauthorized_access_protection(client):
    # me without login
    res = client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.get_json()["authenticated"] is False

    # protected endpoints must reject with 401
    res_list = client.get("/api/folders/list")
    assert res_list.status_code == 401
    assert res_list.get_json()["code"] == "UNAUTHORIZED"

    res_upload = client.post("/api/files/upload", data={"path": ""})
    assert res_upload.status_code == 401

def test_login_and_logout(client):
    # Invalid credentials
    res_fail = client.post("/api/auth/login", json={
        "username": "student1",
        "password": "wrongpassword"
    })
    assert res_fail.status_code == 401

    # Valid credentials
    res_login = client.post("/api/auth/login", json={
        "username": "student1",
        "password": "labpass1"
    })
    assert res_login.status_code == 200
    assert res_login.get_json()["success"] is True
    assert res_login.get_json()["user"] == "student1"

    # Check /me
    res_me = client.get("/api/auth/me")
    assert res_me.status_code == 200
    assert res_me.get_json()["authenticated"] is True
    assert res_me.get_json()["user"] == "student1"

    # Logout
    res_logout = client.post("/api/auth/logout")
    assert res_logout.status_code == 200
    assert res_logout.get_json()["success"] is True

    # Check /me is now unauthenticated
    res_me_after = client.get("/api/auth/me")
    assert res_me_after.get_json()["authenticated"] is False

def test_full_file_and_folder_lifecycle(client):
    # 1. Login as admin
    login_res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert login_res.status_code == 200

    folder_name = "chemistry_lab"
    # Clean up previous test runs if any
    client.delete("/api/folders/delete", json={"path": folder_name})

    # 2. Create a folder
    res_create_folder = client.post("/api/folders/create", json={
        "parent_path": "",
        "folder_name": folder_name
    })
    assert res_create_folder.status_code == 201

    # 3. List root to confirm folder exists
    res_list_root = client.get("/api/folders/list")
    assert res_list_root.status_code == 200
    folders = [f["name"] for f in res_list_root.get_json()["data"]["folders"]]
    assert folder_name in folders

    # 4. Upload file into the new folder
    test_file_content = b"Chemistry experiment results:\nSample A: 98.4%\nSample B: 99.1%\n"
    res_upload = client.post(
        "/api/files/upload",
        data={
            "path": folder_name,
            "file": (io.BytesIO(test_file_content), "experiment_results.txt")
        },
        content_type="multipart/form-data"
    )
    assert res_upload.status_code == 201
    upload_data = res_upload.get_json()
    assert upload_data["success"] is True
    file_manifest = upload_data["file"]
    hdfs_folder = file_manifest["hdfs_folder"]
    assert file_manifest["original_filename"] == "experiment_results.txt"
    assert file_manifest["file_size"] == len(test_file_content)

    # 5. List folder contents
    res_list_folder = client.get(f"/api/folders/list?path={folder_name}")
    assert res_list_folder.status_code == 200
    files_in_folder = res_list_folder.get_json()["data"]["files"]
    assert len(files_in_folder) == 1
    assert files_in_folder[0]["name"] == "experiment_results.txt"
    assert files_in_folder[0]["uploaded_by"] == "admin"

    # 6. Download file and verify byte equality
    res_download = client.get(f"/api/files/download?hdfs_folder={hdfs_folder}")
    assert res_download.status_code == 200
    assert res_download.data == test_file_content
    assert "attachment" in res_download.headers.get("Content-Disposition", "")

    # 7. Rename file
    res_rename = client.post("/api/files/rename", json={
        "hdfs_folder": hdfs_folder,
        "new_filename": "experiment_results_FINAL.txt"
    })
    assert res_rename.status_code == 200
    assert res_rename.get_json()["file"]["original_filename"] == "experiment_results_FINAL.txt"

    # 8. Search file
    res_search = client.get("/api/files/search?q=FINAL")
    assert res_search.status_code == 200
    search_results = res_search.get_json()["results"]
    assert len(search_results) >= 1
    assert any(r["name"] == "experiment_results_FINAL.txt" for r in search_results)

    # 9. Delete file
    res_delete_file = client.delete("/api/files/delete", json={
        "hdfs_folder": hdfs_folder
    })
    assert res_delete_file.status_code == 200

    # Verify file is deleted
    res_list_empty = client.get(f"/api/folders/list?path={folder_name}")
    assert len(res_list_empty.get_json()["data"]["files"]) == 0

    # 10. Delete folder
    res_delete_folder = client.delete("/api/folders/delete", json={
        "path": folder_name
    })
    assert res_delete_folder.status_code == 200

