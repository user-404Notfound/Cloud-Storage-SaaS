import logging
from flask import Blueprint, request, jsonify
from routes.auth import login_required
from services.file_service import FileService, FileServiceError

logger = logging.getLogger(__name__)

folders_bp = Blueprint("folders", __name__)
file_service = FileService()

@folders_bp.route("/list", methods=["GET"])
@login_required
def list_directory():
    """List folders and files in a directory."""
    path = request.args.get("path", "").strip()
    try:
        data = file_service.list_directory(path)
        return jsonify({"success": True, "data": data}), 200
    except FileNotFoundError:
        return jsonify({"error": f"Directory not found: '{path}'"}), 404
    except FileServiceError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing directory '{path}': {e}")
        return jsonify({"error": "Failed to list directory contents"}), 500

@folders_bp.route("/create", methods=["POST"])
@login_required
def create_folder():
    """Create a new folder in HDFS."""
    data = request.get_json(silent=True) or {}
    parent_path = data.get("parent_path", "").strip()
    folder_name = data.get("folder_name", "").strip()

    if not folder_name:
        return jsonify({"error": "Folder name is required"}), 400

    try:
        success = file_service.create_folder(parent_path, folder_name)
        if success:
            return jsonify({
                "success": True,
                "message": f"Folder '{folder_name}' created successfully"
            }), 201
        return jsonify({"error": "Failed to create folder"}), 500
    except FileServiceError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating folder '{folder_name}': {e}")
        return jsonify({"error": "Server error while creating folder"}), 500

@folders_bp.route("/delete", methods=["DELETE"])
@login_required
def delete_folder():
    """Delete a folder and all its contents recursively from HDFS."""
    data = request.get_json(silent=True) or {}
    path = data.get("path") or request.args.get("path", "")
    path = path.strip()

    if not path:
        return jsonify({"error": "Folder path is required"}), 400

    try:
        success = file_service.delete_folder(path)
        if success:
            return jsonify({
                "success": True,
                "message": f"Folder '{path}' deleted successfully"
            }), 200
        return jsonify({"error": "Folder not found or already deleted"}), 404
    except FileServiceError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error deleting folder '{path}': {e}")
        return jsonify({"error": "Failed to delete folder"}), 500

