import os
import logging
from datetime import timedelta
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from routes.auth import auth_bp
from routes.folders import folders_bp
from routes.files import files_bp
from services.webhdfs_service import WebHDFSService

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
logger = logging.getLogger(__name__)

def create_app(test_config=None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    # Session settings
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False  # Allows LAN HTTP without SSL

    # Maximum payload size: 500 MiB (handles large lab files)
    app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

    # CORS configuration for frontend
    CORS(
        app,
        supports_credentials=True,
        resources={r"/api/*": {"origins": "*"}},
        expose_headers=["Content-Disposition", "Content-Length"]
    )

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(folders_bp, url_prefix="/api/folders")
    app.register_blueprint(files_bp, url_prefix="/api/files")

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint checking WebHDFS connectivity."""
        hdfs_online = False
        try:
            webhdfs = WebHDFSService()
            # Test pinging root of HDFS
            webhdfs.get_file_status("/")
            hdfs_online = True
        except Exception as e:
            logger.warning(f"Health check HDFS ping failed: {e}")

        return jsonify({
            "status": "healthy" if hdfs_online else "degraded",
            "service": "LAN Cloud Storage SaaS Controller",
            "webhdfs_connected": hdfs_online,
            "webhdfs_url": Config.WEBHDFS_URL,
            "storage_root": Config.STORAGE_ROOT,
            "chunk_size_bytes": Config.CHUNK_SIZE
        }), 200 if hdfs_online else 503

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Resource not found", "code": "NOT_FOUND"}), 404

    @app.errorhandler(413)
    def payload_too_large(error):
        return jsonify({"error": "File size exceeds the 500 MiB limit", "code": "PAYLOAD_TOO_LARGE"}), 413

    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal server error occurred", "code": "INTERNAL_ERROR"}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)

