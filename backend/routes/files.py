import logging
from urllib.parse import quote
from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from routes.auth import login_required
from services.file_service import FileService, FileServiceError
from services.encryption_service import DecryptionError

logger = logging.getLogger(__name__)

files_bp = Blueprint("files", __name__)
file_service = FileService()

@files_bp.route("/upload", methods=["POST"])
@login_required
def upload_file():
    """
    Accepts multipart/form-data upload:
    - file: The uploaded file stream
    - path: Target relative directory path (optional, defaults to root)
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    uploaded_file = request.files["file"]
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"error": "No file selected for upload"}), 400

    destination_path = request.form.get("path", "").strip()
    username = session.get("user", "unknown")

    try:
        manifest = file_service.upload_file(
            relative_dir=destination_path,
            filename=uploaded_file.filename,
            data_source=uploaded_file.stream,
            username=username
        )
        return jsonify({
            "success": True,
            "message": f"File '{uploaded_file.filename}' uploaded successfully",
            "file": manifest
        }), 201
    except FileServiceError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected upload failure: {e}")
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@files_bp.route("/download", methods=["GET"])
@login_required
def download_file():
    """
    Download and decrypt a file from HDFS:
    - hdfs_folder: The file's unique container path in HDFS
    Streams decrypted chunks to the client.
    """
    hdfs_folder = request.args.get("hdfs_folder", "").strip()
    if not hdfs_folder:
        return jsonify({"error": "Parameter 'hdfs_folder' is required"}), 400

    try:
        manifest, chunk_generator = file_service.download_file(hdfs_folder)
        filename = manifest.get("original_filename", "downloaded_file")
        mime_type = manifest.get("mime_type") or "application/octet-stream"
        file_size = manifest.get("file_size", 0)

        # RFC 5987 encoded filename for Content-Disposition
        encoded_filename = quote(filename)

        response = Response(
            stream_with_context(chunk_generator),
            mimetype=mime_type,
            direct_passthrough=True
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'
        response.headers["Content-Length"] = str(file_size)
        return response

    except FileNotFoundError:
        return jsonify({"error": "File container not found in HDFS"}), 404
    except DecryptionError as e:
        logger.error(f"Decryption integrity failure for {hdfs_folder}: {e}")
        return jsonify({"error": "File integrity verification failed: data is corrupted or tampered"}), 500
    except Exception as e:
        logger.error(f"Error downloading file {hdfs_folder}: {e}")
        return jsonify({"error": f"Failed to download file: {str(e)}"}), 500

@files_bp.route("/rename", methods=["POST"])
@login_required
def rename_file():
    """
    Rename an existing file:
    - hdfs_folder: Path of the file container in HDFS
    - new_filename: New name for the file
    """
    data = request.get_json(silent=True) or {}
    hdfs_folder = data.get("hdfs_folder", "").strip()
    new_filename = data.get("new_filename", "").strip()

    if not hdfs_folder or not new_filename:
        return jsonify({"error": "Both 'hdfs_folder' and 'new_filename' are required"}), 400

    try:
        updated_manifest = file_service.rename_file(hdfs_folder, new_filename)
        return jsonify({
            "success": True,
            "message": f"File renamed to '{new_filename}'",
            "file": updated_manifest
        }), 200
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except FileServiceError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error renaming {hdfs_folder}: {e}")
        return jsonify({"error": "Failed to rename file"}), 500

@files_bp.route("/delete", methods=["DELETE"])
@login_required
def delete_file():
    """
    Permanently delete an encrypted file container from HDFS:
    - hdfs_folder: Path of the file container in HDFS
    """
    data = request.get_json(silent=True) or {}
    hdfs_folder = data.get("hdfs_folder") or request.args.get("hdfs_folder", "")
    hdfs_folder = hdfs_folder.strip()

    if not hdfs_folder:
        return jsonify({"error": "Parameter 'hdfs_folder' is required"}), 400

    try:
        success = file_service.delete_file(hdfs_folder)
        if success:
            return jsonify({
                "success": True,
                "message": "File deleted successfully"
            }), 200
        return jsonify({"error": "File not found or already deleted"}), 404
    except Exception as e:
        logger.error(f"Error deleting file {hdfs_folder}: {e}")
        return jsonify({"error": "Failed to delete file"}), 500

@files_bp.route("/search", methods=["GET"])
@login_required
def search_files():
    """
    Search files by keyword:
    - q: Query string
    - path: Optional search root subdirectory
    """
    query = request.args.get("q", "").strip()
    path = request.args.get("path", "").strip()

    if not query:
        return jsonify({"success": True, "results": []}), 200

    try:
        results = file_service.search_files(query, path)
        return jsonify({
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        }), 200
    except Exception as e:
        logger.error(f"Error searching files with query '{query}': {e}")
        return jsonify({"error": "Search failed"}), 500

