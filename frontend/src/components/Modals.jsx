import React, { useState, useRef } from 'react';
import { X, AlertTriangle, UploadCloud, Shield, CheckCircle } from 'lucide-react';

export function NewFolderModal({ isOpen, onClose, onCreate }) {
  const [name, setName] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    onCreate(name.trim());
    setName('');
  };

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <div className="modal-header">
          <h2 className="modal-title">New folder</h2>
          <button className="card-action-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            className="modal-input"
            placeholder="Untitled folder"
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
          />
          <div className="modal-actions" style={{ marginTop: '20px' }}>
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={!name.trim()}>
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function RenameModal({ isOpen, onClose, item, onRename }) {
  const [newName, setNewName] = useState(item?.name || '');

  if (!isOpen || !item) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    onRename(item, newName.trim());
  };

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <div className="modal-header">
          <h2 className="modal-title">Rename</h2>
          <button className="card-action-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            className="modal-input"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            autoFocus
          />
          <div className="modal-actions" style={{ marginTop: '20px' }}>
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={!newName.trim()}>
              OK
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function DeleteConfirmModal({ isOpen, onClose, target, onConfirm }) {
  if (!isOpen || !target) return null;

  const isFolder = target.type === 'folder';

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertTriangle color="#d93025" size={24} />
            <h2 className="modal-title">Delete {isFolder ? 'folder' : 'file'}?</h2>
          </div>
          <button className="card-action-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div style={{ fontSize: '14px', color: '#3c4043', lineHeight: '1.5' }}>
          <p>
            Are you sure you want to permanently delete <strong>{target.name}</strong>?
          </p>
          <div
            style={{
              marginTop: '12px',
              padding: '10px 14px',
              background: '#fce8e6',
              borderRadius: '6px',
              border: '1px solid #f5c2c7',
              fontSize: '12px',
              color: '#c5221f',
            }}
          >
            <strong>Warning:</strong> This is a shared laboratory cloud drive. Deleting this {isFolder ? 'folder' : 'file'} will permanently remove it for <strong>all laboratory users</strong> on the LAN.
          </div>
        </div>

        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="btn-danger"
            onClick={() => onConfirm(target)}
          >
            Delete for Everyone
          </button>
        </div>
      </div>
    </div>
  );
}

export function UploadModal({ isOpen, onClose, onUpload, uploadState }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleStartUpload = () => {
    if (selectedFile) {
      onUpload(selectedFile);
    }
  };

  const isUploading = uploadState?.isUploading;

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <div className="modal-header">
          <h2 className="modal-title">Upload to Shared Drive</h2>
          {!isUploading && (
            <button className="card-action-btn" onClick={onClose}>
              <X size={18} />
            </button>
          )}
        </div>

        {!isUploading ? (
          <div>
            <div
              style={{
                border: '2px dashed #dadce0',
                borderRadius: '8px',
                padding: '30px 20px',
                textAlign: 'center',
                cursor: 'pointer',
                background: '#f8fafd',
              }}
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadCloud size={40} color="#1a73e8" style={{ margin: '0 auto 10px' }} />
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
              <p style={{ fontSize: '14px', fontWeight: 500, color: '#202124' }}>
                {selectedFile ? selectedFile.name : 'Choose a file to upload'}
              </p>
              <p style={{ fontSize: '12px', color: '#5f6368', marginTop: '4px' }}>
                {selectedFile
                  ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready`
                  : 'Click to browse from your computer'}
              </p>
            </div>

            <div
              style={{
                marginTop: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '12px',
                color: '#5f6368',
              }}
            >
              <Shield size={16} color="#188038" />
              <span>
                File will be segmented into 1 MiB chunks and encrypted with AES-256-GCM before HDFS storage.
              </span>
            </div>

            <div className="modal-actions" style={{ marginTop: '20px' }}>
              <button type="button" className="btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                disabled={!selectedFile}
                onClick={handleStartUpload}
              >
                Upload
              </button>
            </div>
          </div>
        ) : (
          <div>
            <p style={{ fontSize: '14px', fontWeight: 500 }}>
              Uploading <strong>{uploadState.filename}</strong>...
            </p>
            <div className="progress-bar-bg">
              <div
                className="progress-bar-fill"
                style={{ width: `${uploadState.percent}%` }}
              />
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '12px',
                color: '#5f6368',
                marginTop: '6px',
              }}
            >
              <span>{uploadState.statusText || 'Segmenting & Encrypting chunks...'}</span>
              <span>{uploadState.percent}%</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

