# Project Implementation Plan: LAN Cloud Storage SaaS (HDFS + Flask + React)

## 1. Overview & Architectural Goals

The goal of this project is to build a distributed Cloud Storage SaaS running over a college laboratory Local Area Network (LAN) across 4–5 Ubuntu PCs. The solution features:
- **Cloud Controller**: Python Flask backend exposing modular REST APIs for authentication, chunking, encryption, and storage orchestration.
- **Distributed Storage**: Apache Hadoop HDFS accessed directly through the native **WebHDFS REST API** (handling HTTP 307 DataNode redirects).
- **Security & Segmentation**: Application-level file splitting (1 MiB chunks) and **AES-256-GCM** encryption per chunk with unique 96-bit nonces and 128-bit authentication tags.
- **Frontend**: Clean, responsive, Google Drive-inspired light-themed React.js (Vite) user interface.
- **Zero Database Architecture**: Strictly no SQLite, MongoDB, or other databases. File metadata, chunk manifests, and directory trees are maintained natively within HDFS.
- **Shared Access Model**: Single shared cloud storage directory (`/cloud-storage/shared/`) accessible by all authenticated lab users.

---

## 2. Directory Structure & Layout

```text
Cloud-Storage-SaaS/
├── backend/
│   ├── app.py                      # Application factory & blueprint registration
│   ├── run.py                      # Development entry point
│   ├── config.py                   # Environment configuration (WebHDFS URL, Secret Key, etc.)
│   ├── credentials.json            # Hashed user credentials (No DB constraint)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                 # Login, session validation, logout
│   │   ├── files.py                # Upload, download, rename, delete, search
│   │   └── folders.py              # Folder creation and directory listing
│   ├── services/
│   │   ├── __init__.py
│   │   ├── webhdfs_service.py      # Low-level WebHDFS HTTP communication & redirects
│   │   ├── encryption_service.py   # AES-256-GCM encrypt/decrypt with nonce/tag
│   │   ├── chunk_service.py        # 1 MiB chunk splitting & sequential reconstruction
│   │   └── file_service.py         # High-level coordinator (upload/download pipelines)
│   ├── tests/
│   │   ├── test_encryption.py      # Unit tests for AES-256-GCM and integrity tampering
│   │   ├── test_chunking.py        # Unit tests for chunk splitting & reconstruction
│   │   └── test_webhdfs.py         # Integration tests for HDFS operations
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── assets/                 # Icons, logos
│   │   ├── components/
│   │   │   ├── Navbar.jsx          # Search bar, user profile, logout
│   │   │   ├── Sidebar.jsx         # Navigation, storage indicator
│   │   │   ├── Breadcrumbs.jsx     # Dynamic path navigation
│   │   │   ├── FileList.jsx        # Table & Grid views with actions
│   │   │   ├── UploadModal.jsx     # Chunked upload progress modal
│   │   │   └── NewFolderModal.jsx  # Create directory modal
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx       # Authentication page
│   │   │   └── DashboardPage.jsx   # Shared Google Drive interface
│   │   ├── services/
│   │   │   └── api.js              # Axios / Fetch client for Flask backend
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── start_master.sh             # Starts Hadoop master, WebHDFS, Flask, & React
│   └── start_datanode.sh           # Starts Hadoop worker DataNode on LAN machines
├── implementation.md
├── plan.md
└── LAN_DEPLOYMENT.md
```

---

## 3. Storage & Manifest Specification

All files and folders reside within the HDFS root: `/cloud-storage/shared/`.

### Directory & Chunk Structure
For each uploaded file `example.pdf` inside folder `/reports/`:
```text
/cloud-storage/shared/reports/
  └── .file_<sanitized_filename>_<file_id>/
      ├── manifest.json             # File metadata and chunk map
      ├── chunk_0000.enc            # AES-256-GCM encrypted chunk
      ├── chunk_0001.enc
      └── chunk_0002.enc
```

### Manifest Schema (`manifest.json`)
```json
{
  "file_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "original_filename": "project_report.pdf",
  "relative_path": "/reports/project_report.pdf",
  "file_size": 2621440,
  "mime_type": "application/pdf",
  "uploaded_at": "2026-10-19T05:50:00Z",
  "uploaded_by": "lab_user1",
  "chunk_size": 1048576,
  "chunk_count": 3,
  "chunks": [
    {
      "index": 0,
      "chunk_filename": "chunk_0000.enc",
      "size": 1048576,
      "nonce": "a1b2c3d4e5f60718293a4b5c",
      "tag": "d8e9f0123456789abcdef0123456789a"
    },
    {
      "index": 1,
      "chunk_filename": "chunk_0001.enc",
      "size": 1048576,
      "nonce": "b2c3d4e5f60718293a4b5c6d",
      "tag": "e9f0123456789abcdef0123456789ab1"
    },
    {
      "index": 2,
      "chunk_filename": "chunk_0002.enc",
      "size": 524288,
      "nonce": "c3d4e5f60718293a4b5c6d7e",
      "tag": "f0123456789abcdef0123456789ab1c2"
    }
  ]
}
```

---

## 4. Phase-by-Phase Roadmap

### Phase 1: Environment & WebHDFS Integration Foundation
**Objective**: Establish a verified, running Hadoop HDFS cluster locally, configure WebHDFS, and build the core Python WebHDFS service layer.

- [x] **1.1 Hadoop / HDFS Daemon Initialization**:
  - Configure `/usr/local/hadoop/etc/hadoop/hdfs-site.xml` to ensure `dfs.webhdfs.enabled` is `true`.
  - Format NameNode if not already initialized.
  - Start NameNode and DataNode daemons (`start-dfs.sh` or daemon commands).
  - Verify WebHDFS API accessibility on port 9870 via curl:
    `curl http://localhost:9870/webhdfs/v1/?op=LISTSTATUS`
  - Initialize the root shared HDFS directory: `/cloud-storage/shared`.
- [x] **1.2 Backend Environment & Configuration**:
  - Create Python virtual environment (`.venv`) and install dependencies: `Flask`, `Flask-CORS`, `cryptography`, `requests`, `python-dotenv`, `pytest`.
  - Implement `backend/config.py` supporting environment overrides (`WEBHDFS_URL`, `SECRET_KEY`, `AES_KEY`, `CHUNK_SIZE`, `STORAGE_ROOT`).
  - Create `.env.example` and `.env` with development defaults.
- [x] **1.3 WebHDFS Service Implementation (`services/webhdfs_service.py`)**:
  - `mkdir(hdfs_path)`: Create directory in HDFS (`MKDIRS`).
  - `list_status(hdfs_path)`: Retrieve directory entries (`LISTSTATUS`).
  - `get_file_status(hdfs_path)`: Retrieve metadata for a path (`GETFILESTATUS`).
  - `delete(hdfs_path, recursive=True)`: Remove file or directory (`DELETE`).
  - `rename(src_path, dst_path)`: Move or rename paths (`RENAME`).
  - `upload_file(hdfs_path, data_bytes, overwrite=True)`:
    - Step 1: `PUT .../webhdfs/v1/<path>?op=CREATE&overwrite=true` without following redirects immediately.
    - Step 2: Extract `Location` header (DataNode HTTP address with authorization token).
    - Step 3: `PUT` data bytes directly to the DataNode URL.
  - `download_file(hdfs_path)`:
    - `GET .../webhdfs/v1/<path>?op=OPEN` (streaming response through DataNode redirect).
- [x] **1.4 Unit / Integration Verification**:
  - Write `tests/test_webhdfs.py` to create a directory, upload a test byte stream, read it back, verify equality, and delete it.

---

### Phase 2: Chunking, AES-256-GCM Encryption & Manifest Engine
**Objective**: Build the core Cloud Controller data pipeline ensuring file segmentation, authenticated symmetric encryption, and byte-for-byte fidelity upon retrieval.

- [x] **2.1 AES-256-GCM Encryption Engine (`services/encryption_service.py`)**:
  - Initialize 256-bit AES master key from configuration (derived or hex-decoded).
  - `encrypt_chunk(chunk_bytes)`:
    - Generate unique 12-byte (96-bit) cryptographically secure random nonce (`os.urandom(12)`).
    - Encrypt plaintext using AES-256-GCM.
    - Return `(ciphertext_bytes, nonce_hex, tag_hex)`.
  - `decrypt_chunk(ciphertext_bytes, nonce_hex, tag_hex)`:
    - Verify authentication tag against ciphertext using the nonce.
    - Decrypt and return original chunk bytes.
    - Raise `DecryptionError` if data has been tampered with or corrupted.
- [x] **2.2 Chunking Service (`services/chunk_service.py`)**:
  - `split_into_chunks(stream_or_bytes, chunk_size=1048576)`:
    - Generator yielding `(chunk_index, chunk_bytes)`.
  - `combine_chunks(chunks_generator_or_list)`:
    - Sequentially assemble chunks back into a contiguous byte stream.
- [x] **2.3 Manifest & File Coordinator (`services/file_service.py`)**:
  - `upload_file(folder_path, filename, stream, content_length, username)`:
    - Create dedicated folder in HDFS: `/cloud-storage/shared/<folder_path>/.file_<filename>_<uuid>/`.
    - Split incoming stream into 1 MiB chunks.
    - Encrypt each chunk using `encryption_service`.
    - Stream each encrypted chunk directly to WebHDFS as `chunk_0000.enc`, `chunk_0001.enc`, etc.
    - Build `manifest.json` containing chunk indices, nonces, and authentication tags.
    - Save `manifest.json` into the file's HDFS folder.
    - On failure: Clean up partial HDFS folder and raise exception.
  - `download_file(file_folder_path)`:
    - Fetch and parse `manifest.json` from HDFS.
    - Read each encrypted chunk from HDFS in sequence.
    - Decrypt and verify each chunk with `encryption_service`.
    - Yield decrypted chunks as a generator for memory-efficient streaming to client.
- [x] **2.4 Testing & Roundtrip Integrity**:
  - Write `tests/test_encryption.py` and `tests/test_chunking.py`.
  - Test binary files (images, PDFs) and verify SHA-256 hash matches original before and after download.
  - Test chunk corruption detection (simulate tampered byte in chunk, assert decryption failure).

---

### Phase 3: Flask REST APIs & Shared Authentication
**Objective**: Expose robust REST API endpoints with server-side session authentication guarding the shared storage pool.

- [x] **3.1 Authentication Controller (`routes/auth.py`)**:
  - Store predefined lab credentials in `credentials.json` with hashed passwords (`werkzeug.security.generate_password_hash`).
  - `POST /api/auth/login`: Validate credentials and set secure HTTP session cookie.
  - `POST /api/auth/logout`: Invalidate session.
  - `GET /api/auth/me`: Check current session status and return username.
  - Create `@login_required` decorator to protect all file/folder endpoints.
- [x] **3.2 Directory & Navigation Endpoints (`routes/folders.py`)**:
  - `GET /api/folders/list?path=<dir>`:
    - Traverse HDFS directory.
    - For subdirectories representing files (`.file_*`), read manifest to return file details (name, size, upload date, owner).
    - Return list of folders and files formatted for the frontend.
  - `POST /api/folders/create`:
    - Create a new directory in HDFS under current path.
- [x] **3.3 File Operation Endpoints (`routes/files.py`)**:
  - `POST /api/files/upload`: Accept `multipart/form-data` with destination path and stream file through `file_service.upload_file`.
  - `GET /api/files/download`: Accept file path, stream decrypted chunks via `flask.Response(stream_with_context(...))` with `Content-Disposition`.
  - `DELETE /api/files/delete`: Delete file or folder and all underlying chunks/manifests from HDFS.
  - `POST /api/files/rename`: Rename folder or update file manifest in HDFS.
  - `GET /api/files/search?q=<query>`: Recursively list HDFS shared storage and match filenames against query.
- [x] **3.4 API Integration Testing**:
  - Create integration test suite verifying end-to-end HTTP calls: Login -> Create Folder -> Upload File -> List Directory -> Download File -> Verify SHA-256 -> Delete File.

---

### Phase 4: Google Drive-Style React Frontend & LAN Deployment Guide
**Objective**: Build a clean, light-themed Google Drive-like web interface and prepare deployment scripts for the college laboratory LAN.

- [ ] **4.1 React Scaffolding & Theme**:
  - Initialize React with Vite in `frontend/`.
  - Style with modern CSS / Tailwind CSS for a Google Drive-inspired light layout (clean cards, light gray borders, blue primary accents).
- [ ] **4.2 User Interface Components**:
  - **Login Page**: Clean card layout, lab credentials indicator, error handling.
  - **Dashboard Layout**:
    - Top header: Search bar, active username badge, logout button.
    - Left sidebar: "Storage (Shared LAN)", "New" button (+ Upload File, + New Folder), drive capacity/status.
    - Breadcrumb navigation: Clickable path components (`Shared / Documents / Lab3`).
  - **File Explorer**:
    - Toggle between Table View (Name, Size, Modified Date, Actions) and Grid View (Card icons).
    - Double-click folder navigation.
    - Contextual action buttons: Download, Rename, Delete.
    - Delete confirmation dialog explicitly warning: *"This is a shared cloud storage. Deleting this file removes it for all laboratory users."*
  - **Upload Progress Modal**:
    - Visual progress bar showing chunk upload status.
- [ ] **4.3 API Client Integration**:
  - Configure `axios` or `fetch` instance with `credentials: 'include'` for session cookie support.
  - Error toast notifications for network or decryption errors.
- [ ] **4.4 Multi-PC LAN Deployment Setup**:
  - Create `scripts/start_master.sh` to launch Hadoop Master (NameNode + DataNode), Flask backend, and serve frontend build.
  - Create `scripts/start_datanode.sh` for worker Ubuntu PCs.
  - Write `LAN_DEPLOYMENT.md` providing step-by-step instructions:
    1. Static IP configuration for master PC (`MASTER_IP`).
    2. Editing `core-site.xml` and `hdfs-site.xml` on worker nodes.
    3. Firewall rules (`ufw allow 9870`, `ufw allow 9000`, `ufw allow 9864`, `ufw allow 5000`).
    4. Verification of DataNodes registering with NameNode.

---

## 5. Verification & Acceptance Checklist

| Requirement | Verification Method | Status |
| :--- | :--- | :--- |
| **No Database** | Inspect code to verify zero SQL/NoSQL dependencies; only HDFS & `credentials.json` | Pending |
| **Shared Storage** | Verify all logged-in accounts see and share `/cloud-storage/shared/` | Pending |
| **Real WebHDFS** | Verify HTTP communication with NameNode (9870) and DataNodes (9864) | Pending |
| **1 MiB Chunking** | Verify files > 1 MiB are split into sequential chunk files in HDFS | Pending |
| **AES-256-GCM** | Verify encrypted chunks cannot be read directly from HDFS; verify unique nonces & tag checks | Pending |
| **Data Integrity** | Compare SHA-256 hash of downloaded file against original upload | Pending |
| **Google Drive UI** | Test responsive React interface with breadcrumbs, upload progress, and grid/table views | Pending |
| **LAN Portability** | Master IP configurable via `.env` without hardcoded localhost references | Pending |

