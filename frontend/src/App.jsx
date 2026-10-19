import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Breadcrumbs from './components/Breadcrumbs';
import FileList from './components/FileList';
import LoginPage from './components/LoginPage';
import {
  NewFolderModal,
  RenameModal,
  DeleteConfirmModal,
  UploadModal,
} from './components/Modals';
import { api } from './api';
import { LayoutGrid, List, RefreshCw } from 'lucide-react';

export default function App() {
  // Auth state
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [loginError, setLoginError] = useState('');

  // Storage and navigation state
  const [currentPath, setCurrentPath] = useState('');
  const [folders, setFolders] = useState([]);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'grid'
  const [searchQuery, setSearchQuery] = useState('');
  const [health, setHealth] = useState(null);

  // Modals state
  const [isNewFolderOpen, setIsNewFolderOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [renameTarget, setRenameTarget] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  // Upload progress state
  const [uploadState, setUploadState] = useState({
    isUploading: false,
    filename: '',
    percent: 0,
    statusText: '',
  });

  // Toasts
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  // Check auth session on startup
  useEffect(() => {
    api
      .checkAuth()
      .then((data) => {
        if (data.authenticated) {
          setUser(data.user);
        }
      })
      .catch(() => {})
      .finally(() => setAuthLoading(false));

    api
      .checkHealth()
      .then((data) => setHealth(data))
      .catch(() => {});
  }, []);

  // Fetch folder contents
  const fetchDirectory = useCallback(
    async (path = currentPath, query = searchQuery) => {
      setLoading(true);
      try {
        if (query) {
          const res = await api.search(query, path);
          setFolders([]);
          setFiles(res.results || []);
        } else {
          const res = await api.listFolder(path);
          setFolders(res.data.folders || []);
          setFiles(res.data.files || []);
        }
      } catch (err) {
        if (err.status === 401) {
          setUser(null);
        } else {
          addToast(err.message || 'Failed to load drive contents', 'error');
        }
      } finally {
        setLoading(false);
      }
    },
    [currentPath, searchQuery]
  );

  useEffect(() => {
    if (user) {
      fetchDirectory(currentPath, searchQuery);
    }
  }, [user, currentPath, searchQuery, fetchDirectory]);

  // Auth Handlers
  const handleLogin = async (username, password) => {
    setLoginError('');
    const res = await api.login(username, password);
    setUser(res.user);
    addToast(`Signed in as ${res.user}`);
  };

  const handleLogout = async () => {
    await api.logout();
    setUser(null);
    setCurrentPath('');
    setSearchQuery('');
    addToast('Signed out successfully');
  };

  // Navigation
  const handleNavigate = (path) => {
    setSearchQuery('');
    setCurrentPath(path);
  };

  const handleNavigateFolder = (folderName) => {
    setSearchQuery('');
    const nextPath = currentPath ? `${currentPath}/${folderName}` : folderName;
    setCurrentPath(nextPath);
  };

  const handleSearch = (q) => {
    setSearchQuery(q);
  };

  // File Operations
  const handleCreateFolder = async (folderName) => {
    try {
      await api.createFolder(currentPath, folderName);
      addToast(`Folder '${folderName}' created`);
      setIsNewFolderOpen(false);
      fetchDirectory();
    } catch (err) {
      addToast(err.message, 'error');
    }
  };

  const handleStartUpload = async (file) => {
    setUploadState({
      isUploading: true,
      filename: file.name,
      percent: 0,
      statusText: 'Streaming & encrypting chunks to HDFS...',
    });

    try {
      await api.uploadFile(file, currentPath, (percent) => {
        setUploadState((prev) => ({
          ...prev,
          percent,
          statusText: percent < 100 ? `Uploading & encrypting chunks (${percent}%)...` : 'Finalizing HDFS manifest...',
        }));
      });

      addToast(`'${file.name}' encrypted and uploaded to HDFS`);
      setIsUploadOpen(false);
      fetchDirectory();
    } catch (err) {
      addToast(err.message, 'error');
    } finally {
      setUploadState({
        isUploading: false,
        filename: '',
        percent: 0,
        statusText: '',
      });
    }
  };

  const handleDownloadFile = (file) => {
    const url = api.downloadUrl(file.hdfs_folder);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', file.name);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    addToast(`Downloading & decrypting '${file.name}'`);
  };

  const handleRename = async (item, newName) => {
    try {
      await api.renameFile(item.hdfs_folder, newName);
      addToast(`File renamed to '${newName}'`);
      setRenameTarget(null);
      fetchDirectory();
    } catch (err) {
      addToast(err.message, 'error');
    }
  };

  const handleConfirmDelete = async (target) => {
    try {
      if (target.type === 'folder') {
        const fullPath = currentPath ? `${currentPath}/${target.name}` : target.name;
        await api.deleteFolder(fullPath);
        addToast(`Folder '${target.name}' deleted for all users`);
      } else {
        await api.deleteFile(target.hdfs_folder);
        addToast(`File '${target.name}' deleted from HDFS`);
      }
      setDeleteTarget(null);
      fetchDirectory();
    } catch (err) {
      addToast(err.message, 'error');
    }
  };

  if (authLoading) {
    return (
      <div className="login-page">
        <div style={{ color: '#5f6368', fontSize: '15px' }}>
          Connecting to Cloud Drive...
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage onLogin={handleLogin} error={loginError} />;
  }

  return (
    <div className="app-container">
      <Navbar
        user={user}
        onLogout={handleLogout}
        onSearch={handleSearch}
        searchQuery={searchQuery}
        health={health}
      />

      <div className="main-layout">
        <Sidebar
          onOpenNewFolder={() => setIsNewFolderOpen(true)}
          onOpenUpload={() => setIsUploadOpen(true)}
          health={health}
          totalFilesCount={files.length}
        />

        <main className="content-area">
          <div className="toolbar">
            <Breadcrumbs currentPath={currentPath} onNavigate={handleNavigate} />

            <div className="view-controls">
              <button
                className="icon-btn"
                onClick={() => fetchDirectory()}
                title="Refresh contents"
              >
                <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
              </button>

              <button
                className={`icon-btn ${viewMode === 'table' ? 'active' : ''}`}
                onClick={() => setViewMode('table')}
                title="List view"
              >
                <List size={18} />
              </button>

              <button
                className={`icon-btn ${viewMode === 'grid' ? 'active' : ''}`}
                onClick={() => setViewMode('grid')}
                title="Grid view"
              >
                <LayoutGrid size={18} />
              </button>
            </div>
          </div>

          <div className="workspace">
            {searchQuery && (
              <div
                style={{
                  marginBottom: '16px',
                  fontSize: '14px',
                  color: '#5f6368',
                }}
              >
                Search results for: <strong>"{searchQuery}"</strong> ({files.length} found)
              </div>
            )}

            <FileList
              folders={folders}
              files={files}
              viewMode={viewMode}
              onNavigateFolder={handleNavigateFolder}
              onDownloadFile={handleDownloadFile}
              onRenameFile={(f) => setRenameTarget(f)}
              onDeleteFile={(f) => setDeleteTarget({ ...f, type: 'file' })}
              onDeleteFolder={(name) => setDeleteTarget({ name, type: 'folder' })}
            />
          </div>
        </main>
      </div>

      {/* Modals */}
      <NewFolderModal
        isOpen={isNewFolderOpen}
        onClose={() => setIsNewFolderOpen(false)}
        onCreate={handleCreateFolder}
      />

      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUpload={handleStartUpload}
        uploadState={uploadState}
      />

      <RenameModal
        isOpen={!!renameTarget}
        onClose={() => setRenameTarget(null)}
        item={renameTarget}
        onRename={handleRename}
      />

      <DeleteConfirmModal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        target={deleteTarget}
        onConfirm={handleConfirmDelete}
      />

      {/* Toasts */}
      <div className="toast-container">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`toast ${
              toast.type === 'error' ? 'toast-error' : 'toast-success'
            }`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  );
}

