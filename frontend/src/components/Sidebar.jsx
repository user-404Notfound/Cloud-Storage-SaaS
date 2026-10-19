import React, { useState, useRef, useEffect } from 'react';
import { Plus, FolderPlus, Upload, HardDrive, Shield, Network, DatabaseZap } from 'lucide-react';

export default function Sidebar({ onOpenNewFolder, onOpenUpload, health, totalFilesCount }) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <aside className="sidebar">
      <div>
        <div className="new-btn-wrapper" ref={dropdownRef}>
          <button
            className="new-btn"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            title="Create new folder or upload file"
          >
            <Plus size={20} color="#1a73e8" />
            <span>New</span>
          </button>

          {dropdownOpen && (
            <div className="new-dropdown">
              <button
                className="dropdown-item"
                onClick={() => {
                  setDropdownOpen(false);
                  onOpenNewFolder();
                }}
              >
                <FolderPlus size={18} color="#5f6368" />
                <span>New folder</span>
              </button>
              <button
                className="dropdown-item"
                onClick={() => {
                  setDropdownOpen(false);
                  onOpenUpload();
                }}
              >
                <Upload size={18} color="#5f6368" />
                <span>File upload</span>
              </button>
            </div>
          )}
        </div>

        <nav className="sidebar-nav">
          <button className="sidebar-nav-item active">
            <HardDrive size={18} />
            <span>Shared Drive</span>
          </button>
        </nav>
      </div>

      <div className="sidebar-footer">
        <div className="storage-title">
          <Network size={16} color="#1a73e8" />
          <span>College LAN Storage</span>
        </div>
        <div className="storage-badge-group">
          <div className="storage-item">
            <span>Cluster:</span>
            <strong>Hadoop HDFS</strong>
          </div>
          <div className="storage-item">
            <span>Security:</span>
            <strong>AES-256-GCM</strong>
          </div>
          <div className="storage-item">
            <span>Chunking:</span>
            <strong>1 MiB Segments</strong>
          </div>
          <div className="storage-item">
            <span>Storage Root:</span>
            <span style={{ fontSize: '11px', color: '#1a73e8' }}>
              {health?.storage_root || '/cloud-storage/shared'}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}

