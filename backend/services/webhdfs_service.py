import logging
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import quote
from config import Config

logger = logging.getLogger(__name__)

class WebHDFSError(Exception):
    """Custom exception for WebHDFS operations."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_json: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_json = response_json

class WebHDFSService:
    def __init__(self, base_url: Optional[str] = None, user: Optional[str] = None):
        self.base_url = (base_url or Config.WEBHDFS_URL).rstrip("/")
        self.user = user or Config.HDFS_USER

    def _build_url(self, hdfs_path: str, op: str, **params) -> str:
        """Construct WebHDFS URL with normalized path and query parameters."""
        clean_path = "/" + hdfs_path.strip("/") if hdfs_path.strip("/") else ""
        quoted_path = quote(clean_path, safe="/")
        query_params = [f"op={op}"]
        if self.user:
            query_params.append(f"user.name={self.user}")
        for k, v in params.items():
            if v is not None:
                query_params.append(f"{k}={str(v).lower() if isinstance(v, bool) else quote(str(v))}")
        query_string = "&".join(query_params)
        return f"{self.base_url}{quoted_path}?{query_string}"

    def mkdirs(self, hdfs_path: str) -> bool:
        """Create a directory in HDFS (creates parents automatically)."""
        url = self._build_url(hdfs_path, "MKDIRS")
        try:
            resp = requests.put(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("boolean", False)
            self._handle_error_response("mkdirs", hdfs_path, resp)
        except requests.RequestException as e:
            logger.error(f"Network error during mkdirs({hdfs_path}): {e}")
            raise WebHDFSError(f"Network error during mkdirs: {e}")

    def list_status(self, hdfs_path: str) -> List[Dict[str, Any]]:
        """List contents of a directory in HDFS."""
        url = self._build_url(hdfs_path, "LISTSTATUS")
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("FileStatuses", {}).get("FileStatus", [])
            if resp.status_code == 404:
                raise FileNotFoundError(f"Path not found in HDFS: {hdfs_path}")
            self._handle_error_response("list_status", hdfs_path, resp)
        except requests.RequestException as e:
            logger.error(f"Network error during list_status({hdfs_path}): {e}")
            raise WebHDFSError(f"Network error during list_status: {e}")

    def get_file_status(self, hdfs_path: str) -> Dict[str, Any]:
        """Get metadata status for a specific file or directory in HDFS."""
        url = self._build_url(hdfs_path, "GETFILESTATUS")
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("FileStatus", {})
            if resp.status_code == 404:
                raise FileNotFoundError(f"Path not found in HDFS: {hdfs_path}")
            self._handle_error_response("get_file_status", hdfs_path, resp)
        except requests.RequestException as e:
            logger.error(f"Network error during get_file_status({hdfs_path}): {e}")
            raise WebHDFSError(f"Network error during get_file_status: {e}")

    def delete(self, hdfs_path: str, recursive: bool = True) -> bool:
        """Delete a file or directory in HDFS."""
        url = self._build_url(hdfs_path, "DELETE", recursive=recursive)
        try:
            resp = requests.delete(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("boolean", False)
            if resp.status_code == 404:
                return False
            self._handle_error_response("delete", hdfs_path, resp)
        except requests.RequestException as e:
            logger.error(f"Network error during delete({hdfs_path}): {e}")
            raise WebHDFSError(f"Network error during delete: {e}")

    def rename(self, src_path: str, dst_path: str) -> bool:
        """Rename or move a file or folder in HDFS."""
        clean_dst = "/" + dst_path.strip("/")
        url = self._build_url(src_path, "RENAME", destination=clean_dst)
        try:
            resp = requests.put(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("boolean", False)
            self._handle_error_response("rename", src_path, resp)
        except requests.RequestException as e:
            logger.error(f"Network error during rename({src_path} -> {dst_path}): {e}")
            raise WebHDFSError(f"Network error during rename: {e}")

    def write_file(self, hdfs_path: str, data: bytes, overwrite: bool = True) -> bool:
        """
        Upload file data to HDFS using the WebHDFS two-step write protocol:
        1. Send PUT request to NameNode with op=CREATE without following redirect automatically.
        2. NameNode responds with HTTP 307 Temporary Redirect containing DataNode Location header.
        3. Send PUT request to DataNode with raw data payload.
        """
        step1_url = self._build_url(hdfs_path, "CREATE", overwrite=overwrite)
        try:
            resp1 = requests.put(step1_url, allow_redirects=False, timeout=10)
            if resp1.status_code != 307:
                self._handle_error_response("write_file_step1", hdfs_path, resp1)

            datanode_url = resp1.headers.get("Location")
            if not datanode_url:
                raise WebHDFSError(f"Missing DataNode redirect Location header for {hdfs_path}")

            resp2 = requests.put(
                datanode_url,
                data=data,
                headers={"Content-Type": "application/octet-stream"},
                timeout=60
            )
            if resp2.status_code in (200, 201):
                return True

            self._handle_error_response("write_file_step2", hdfs_path, resp2)
        except requests.RequestException as e:
            logger.error(f"Network error during write_file({hdfs_path}): {e}")
            raise WebHDFSError(f"Network error during write_file: {e}")

    def read_file(self, hdfs_path: str) -> bytes:
        """
        Read file contents from HDFS:
        Sends GET request with op=OPEN and automatically follows HTTP 307 redirect to DataNode.
        """
        url = self._build_url(hdfs_path, "OPEN")
        try:
            resp = requests.get(url, allow_redirects=True, timeout=60)
            if resp.status_code == 200:
                return resp.content
            if resp.status_code == 404:
                raise FileNotFoundError(f"File not found in HDFS: {hdfs_path}")
            self._handle_error_response("read_file", hdfs_path, resp)
        except requests.RequestException as e:
            logger.error(f"Network error during read_file({hdfs_path}): {e}")
            raise WebHDFSError(f"Network error during read_file: {e}")

    def _handle_error_response(self, action: str, path: str, response: requests.Response):
        """Extract and raise structured error from WebHDFS RemoteException response."""
        err_msg = f"WebHDFS {action} failed for path '{path}' with HTTP {response.status_code}"
        json_data = None
        try:
            json_data = response.json()
            if "RemoteException" in json_data:
                remote_err = json_data["RemoteException"]
                err_msg += f": [{remote_err.get('exception')}] {remote_err.get('message')}"
        except Exception:
            err_msg += f": {response.text[:200]}"
        logger.error(err_msg)
        raise WebHDFSError(err_msg, status_code=response.status_code, response_json=json_data)

