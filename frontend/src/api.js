/**
 * API client for the LAN Cloud Storage Flask Controller.
 * Uses native fetch with credentials: 'include' for session cookie support.
 */

const API_BASE = '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = options.headers || {};

  // If body is JSON, add content-type header
  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    credentials: 'include',
    ...options,
    headers,
  });

  // Handle file downloads (blob streams)
  if (options.responseType === 'blob') {
    if (!response.ok) {
      const err = await response.json().catch(() => ({ error: 'Download failed' }));
      throw new Error(err.error || `Download failed with HTTP ${response.status}`);
    }
    return response;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorMsg = data?.error || `HTTP ${response.status}: Request failed`;
    const err = new Error(errorMsg);
    err.status = response.status;
    err.code = data?.code;
    throw err;
  }

  return data;
}

export const api = {
  // Auth
  checkAuth: () => request('/auth/me'),
  login: (username, password) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  logout: () =>
    request('/auth/logout', {
      method: 'POST',
    }),

  // Health
  checkHealth: () => request('/health'),

  // Folders
  listFolder: (path = '') =>
    request(`/folders/list?path=${encodeURIComponent(path)}`),
  createFolder: (parentPath, folderName) =>
    request('/folders/create', {
      method: 'POST',
      body: JSON.stringify({ parent_path: parentPath, folder_name: folderName }),
    }),
  deleteFolder: (path) =>
    request('/folders/delete', {
      method: 'DELETE',
      body: JSON.stringify({ path }),
    }),

  // Files
  uploadFile: (file, path = '', onProgress) => {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('path', path);

      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API_BASE}/files/upload`);
      xhr.withCredentials = true;

      if (onProgress && xhr.upload) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            onProgress(percent, e.loaded, e.total);
          }
        };
      }

      xhr.onload = () => {
        try {
          const data = JSON.parse(xhr.responseText);
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(data);
          } else {
            reject(new Error(data.error || `Upload failed with status ${xhr.status}`));
          }
        } catch {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      };

      xhr.onerror = () => reject(new Error('Network error during upload'));
      xhr.send(formData);
    });
  },

  downloadUrl: (hdfsFolder) =>
    `${API_BASE}/files/download?hdfs_folder=${encodeURIComponent(hdfsFolder)}`,

  renameFile: (hdfsFolder, newFilename) =>
    request('/files/rename', {
      method: 'POST',
      body: JSON.stringify({ hdfs_folder: hdfsFolder, new_filename: newFilename }),
    }),

  deleteFile: (hdfsFolder) =>
    request('/files/delete', {
      method: 'DELETE',
      body: JSON.stringify({ hdfs_folder: hdfsFolder }),
    }),

  search: (query, path = '') =>
    request(`/files/search?q=${encodeURIComponent(query)}&path=${encodeURIComponent(path)}`),
};

