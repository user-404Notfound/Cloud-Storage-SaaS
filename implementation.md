# Project: Shared LAN Cloud Storage Using Flask, React and Hadoop HDFS

## 1. Objective

Develop a simple web-based cloud storage application inspired by Google Drive that runs over a college laboratory LAN containing 4–5 Ubuntu PCs.

The system must use a custom Python Flask Cloud Controller, a React.js frontend, and Apache Hadoop HDFS for distributed file storage.

All authenticated users share the same cloud storage space. After logging in, every user can view, upload, download, rename, and delete files available in the shared storage.

This is a college mini-project focused on implementing a Cloud Controller integrated with real HDFS, including file segmentation, encrypted storage, and upload/download operations.

## 2. Technology Stack

- Frontend: React.js, Vite, JavaScript and CSS.
- Backend: Python Flask and REST APIs.
- Storage: Apache Hadoop HDFS.
- HDFS communication: WebHDFS HTTP API.
- Encryption: AES-256-GCM using Python's `cryptography` library.
- Authentication: Simple login system with password hashing and server-side sessions.
- Deployment: Ubuntu Linux PCs connected through the college LAN.

**Do not use MongoDB, SQLite, or any other database. Do not implement a custom VFS or per-user file ownership.**

## 3. Architecture

The React frontend communicates with the Flask Cloud Controller through REST APIs.

The Flask backend handles authentication, shared file operations, chunking, encryption, decryption, and WebHDFS communication.

HDFS stores all uploaded files in one shared directory, for example:

`/cloud-storage/shared/`

All authenticated users access the same files and folders. The controller enforces login requirements before allowing operations.

The master PC runs:
- Hadoop NameNode.
- Flask Cloud Controller.
- React frontend.
- WebHDFS endpoint.

Other Ubuntu PCs run Hadoop DataNodes. The master may also run a DataNode.

The master machine must be configurable through environment variables so the application can be deployed on any suitable LAN PC.

## 4. Authentication

Implement a simple login page.

- Provide a login form with username and password.
- Validate credentials on the Flask backend.
- Store password hashes in a local configuration file or a simple credentials file.
- Use secure session cookies or another appropriately implemented authentication mechanism.
- Protect every file API endpoint.
- Provide a logout option.

No user registration is required unless it is useful for demonstration. All logged-in users access the same shared cloud directory.

Authentication controls access to the application; it does not create separate user storage spaces.

## 5. Frontend Requirements

Create a clean, responsive, Google Drive-inspired interface with a light theme.

### Login Page
- Username and password fields.
- Login button.
- Validation and error messages.
- Simple professional layout.

### Shared Cloud Dashboard
- Sidebar navigation.
- Search bar.
- Upload File and New Folder actions.
- File and folder listing in grid or table view.
- Filename, size, type, and last-modified information where available.
- Folder navigation and breadcrumbs.
- Download, rename, and delete operations.
- Upload progress indicator.
- Loading states, error notifications, and empty states.
- Logout button.

The dashboard must show the same shared files to every authenticated user.

## 6. Flask Backend Modules

Organize the backend into clear modules:

- `routes/auth.py`: Login and logout.
- `routes/files.py`: File listing, upload, download, rename, and delete.
- `routes/folders.py`: Folder creation and navigation.
- `services/webhdfs_service.py`: HDFS communication.
- `services/encryption_service.py`: AES-256-GCM encryption and decryption.
- `services/chunk_service.py`: Application-level chunking and reconstruction.
- `services/file_service.py`: Coordinates file operations.
- `config.py`: Environment-based configuration.
- `app.py`: Flask application initialization.
- `run.py`: Development entry point.

Keep the code modular and easy to understand.

## 7. File Upload and Download

### Upload

1. Receive a file from the authenticated user.
2. Validate the filename and file size.
3. Split the file into configurable application-level chunks, initially 1 MiB each.
4. Encrypt each chunk using AES-256-GCM with a unique nonce.
5. Store encrypted chunks in HDFS under a unique file directory inside `/cloud-storage/shared/`.
6. Store a small manifest alongside each file describing its original filename, chunk order, chunk count, size, and encryption metadata.
7. Return the upload status to the frontend.

Do not use a database for manifests. Store them as files in HDFS, or use a deterministic directory and naming convention.

HDFS performs its own internal block splitting. Application-level chunking is an additional feature required by the assignment.

### Download

1. Authenticate the user.
2. Locate the requested file in shared HDFS storage.
3. Read its manifest and retrieve encrypted chunks.
4. Authenticate and decrypt every chunk.
5. Reconstruct the original file in the correct order.
6. Return the file to the browser using its original filename.

The downloaded file must match the original byte-for-byte.

### Other Operations

- List shared files and folders using WebHDFS directory operations.
- Create shared folders.
- Rename files and folders.
- Delete files and folders, including their chunks and manifests.
- Search filenames within the shared storage directory.

Handle partial uploads and clean up incomplete data when possible.

## 8. WebHDFS Integration

Use real WebHDFS operations for:

- Creating directories.
- Uploading encrypted chunks.
- Reading stored chunks.
- Listing files and folders.
- Renaming paths.
- Deleting files and directories.
- Checking file status.

Handle WebHDFS HTTP redirects correctly for file transfers to DataNodes.

The Flask backend must communicate with HDFS; the React frontend must never access WebHDFS directly.

Configure the NameNode address through an environment variable, for example:

`WEBHDFS_URL=http://MASTER_IP:9870/webhdfs/v1`

Replace `MASTER_IP` with the actual LAN address during deployment.

## 9. Encryption and Security

- Use AES-256-GCM for file chunk encryption.
- Generate a unique nonce for every encrypted chunk.
- Store the nonce and authentication tag with the chunk data or manifest.
- Keep the encryption key separate from the stored file data.
- Do not commit credentials or encryption keys to Git.
- Hash login passwords using a suitable password-hashing algorithm.
- Require authentication for every file operation.
- Validate filenames and prevent path traversal.
- Never trust client-supplied HDFS paths.
- Restrict access to WebHDFS and Hadoop administrative interfaces to trusted hosts.
- Handle encryption errors and corrupted chunks safely.

Because this is shared storage, every authenticated user has the same file permissions. Clearly communicate that deletion and renaming affect everyone.

## 10. LAN Deployment

Develop and test locally first.

Then deploy across the college laboratory LAN:

- One selected Ubuntu PC acts as the master.
- The master runs NameNode, Flask, React, and WebHDFS.
- The other Ubuntu PCs run DataNodes.
- Configure Hadoop with the actual IP addresses of the machines.
- Keep master addresses and ports in configuration rather than hardcoding them throughout the code.
- Test connectivity, HDFS uploads/downloads, DataNode registration, and replication.

The application must be portable to another master PC by updating the configuration and Hadoop cluster settings.

## 11. Development Plan

Implement incrementally:

1. Inspect the existing repository.
2. Verify Java, Hadoop, HDFS, and WebHDFS.
3. Build the Flask health-check endpoint.
4. Implement WebHDFS directory listing, upload, download, and deletion.
5. Implement shared login and session handling.
6. Add chunking, encryption, and file reconstruction.
7. Build the React login page and shared cloud dashboard.
8. Integrate the frontend and backend.
9. Test file integrity, corrupted chunks, concurrent uploads, and authentication.
10. Deploy the master and DataNodes across the LAN.

Do not mock HDFS in the final implementation.

## 12. Acceptance Criteria

- Users must log in before accessing the cloud.
- All authenticated users see the same shared files.
- Users can upload, download, rename, delete, and organize files.
- Files are encrypted before being stored in HDFS.
- File chunking and reconstruction work correctly.
- Downloaded files match their original contents.
- Real HDFS stores the file data across the configured cluster.
- The application works on a single machine for development and across multiple Ubuntu PCs for deployment.
- No MongoDB, SQLite, or custom VFS is used.
- Provide setup instructions, environment configuration, and LAN deployment documentation.

## Instructions to the Coding Agent

First inspect the existing repository and report what is already implemented. Preserve working code where practical.

Implement the project in small, testable phases. Start with real WebHDFS integration, then authentication, encryption, and finally the React UI.

Do not introduce a database, a custom VFS, or unnecessary abstractions. Prioritize a working LAN-based HDFS cloud storage application over extra features.