import React from 'react';
import {
  Folder,
  FileText,
  FileCode,
  FileArchive,
  Image,
  Film,
  Music,
  File,
  Download,
  Edit2,
  Trash2,
  FolderOpen,
  Calendar,
  User,
  ShieldCheck,
} from 'lucide-react';

function getFileIcon(filename, size = 18) {
  const ext = filename ? filename.split('.').pop().toLowerCase() : '';
  switch (ext) {
    case 'pdf':
      return <FileText size={size} color="#ea4335" />;
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'svg':
    case 'webp':
      return <Image size={size} color="#34a853" />;
    case 'mp4':
    case 'mkv':
    case 'avi':
    case 'mov':
      return <Film size={size} color="#a142f4" />;
    case 'mp3':
    case 'wav':
    case 'ogg':
      return <Music size={size} color="#fbbc04" />;
    case 'zip':
    case 'tar':
    case 'gz':
    case 'rar':
    case '7z':
      return <FileArchive size={size} color="#fa7b17" />;
    case 'py':
    case 'js':
    case 'jsx':
    case 'html':
    case 'css':
    case 'json':
    case 'c':
    case 'cpp':
    case 'java':
    case 'sh':
      return <FileCode size={size} color="#1a73e8" />;
    default:
      return <File size={size} color="#5f6368" />;
  }
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  if (!bytes) return '-';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function formatDate(isoString) {
  if (!isoString) return '-';
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
}

export default function FileList({
  folders,
  files,
  viewMode,
  onNavigateFolder,
  onDownloadFile,
  onRenameFile,
  onDeleteFile,
  onDeleteFolder,
}) {
  const hasContent = folders.length > 0 || files.length > 0;

  if (!hasContent) {
    return (
      <div className="empty-state">
        <FolderOpen className="empty-icon" />
        <p style={{ fontSize: '16px', fontWeight: 500, color: '#3c4043' }}>
          This folder is empty
        </p>
        <p style={{ fontSize: '13px' }}>
          Use the <strong>+ New</strong> button to upload files or create folders in this shared directory.
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Folders Section */}
      {folders.length > 0 && (
        <div style={{ marginBottom: '28px' }}>
          <h3 className="section-title">FOLDERS</h3>
          <div className="folder-grid">
            {folders.map((folder) => (
              <div
                key={folder.name}
                className="folder-card"
                onClick={() => onNavigateFolder(folder.name)}
                title={`Open folder '${folder.name}'`}
              >
                <div className="folder-card-main">
                  <Folder className="folder-icon" size={20} />
                  <span className="folder-name">{folder.name}</span>
                </div>
                <button
                  className="card-action-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteFolder(folder.name);
                  }}
                  title="Delete Folder"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Files Section */}
      {files.length > 0 && (
        <div>
          <h3 className="section-title">FILES</h3>

          {viewMode === 'table' ? (
            <table className="file-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Owner</th>
                  <th>Encrypted Chunks</th>
                  <th>File size</th>
                  <th>Modified</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {files.map((file) => (
                  <tr key={file.file_id || file.hdfs_folder}>
                    <td>
                      <div className="file-name-cell" title={file.name}>
                        {getFileIcon(file.name)}
                        <span className="file-name-text">{file.name}</span>
                      </div>
                    </td>
                    <td>
                      <span className="file-owner-cell">
                        {file.uploaded_by || 'shared'}
                      </span>
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: '11px',
                          background: '#f1f3f4',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                        title={`Split into ${file.chunk_count} AES-256-GCM encrypted chunks in HDFS`}
                      >
                        <ShieldCheck size={12} color="#188038" />
                        {file.chunk_count} chunk{file.chunk_count > 1 ? 's' : ''}
                      </span>
                    </td>
                    <td className="file-size-cell">{formatFileSize(file.size)}</td>
                    <td className="file-owner-cell">{formatDate(file.uploaded_at)}</td>
                    <td>
                      <div className="file-actions-cell">
                        <button
                          className="table-action-btn"
                          onClick={() => onDownloadFile(file)}
                          title="Download & Decrypt"
                        >
                          <Download size={16} color="#1a73e8" />
                        </button>
                        <button
                          className="table-action-btn"
                          onClick={() => onRenameFile(file)}
                          title="Rename file"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          className="table-action-btn delete-hover"
                          onClick={() => onDeleteFile(file)}
                          title="Delete file"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            /* Grid View */
            <div className="file-grid">
              {files.map((file) => (
                <div key={file.file_id || file.hdfs_folder} className="file-grid-card">
                  <div className="file-grid-icon-box">
                    {getFileIcon(file.name, 40)}
                  </div>
                  <div>
                    <div className="file-grid-name" title={file.name}>
                      {file.name}
                    </div>
                    <div className="file-grid-meta" style={{ marginTop: '4px' }}>
                      <span>{formatFileSize(file.size)}</span>
                      <span>{file.uploaded_by}</span>
                    </div>
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-end',
                      gap: '4px',
                      borderTop: '1px solid #f1f3f4',
                      paddingTop: '8px',
                    }}
                  >
                    <button
                      className="table-action-btn"
                      onClick={() => onDownloadFile(file)}
                      title="Download"
                    >
                      <Download size={15} color="#1a73e8" />
                    </button>
                    <button
                      className="table-action-btn"
                      onClick={() => onRenameFile(file)}
                      title="Rename"
                    >
                      <Edit2 size={15} />
                    </button>
                    <button
                      className="table-action-btn delete-hover"
                      onClick={() => onDeleteFile(file)}
                      title="Delete"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

