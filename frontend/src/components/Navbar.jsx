import React, { useState } from 'react';
import { Cloud, Search, X, LogOut, Server, ShieldCheck } from 'lucide-react';

export default function Navbar({ user, onLogout, onSearch, searchQuery, health }) {
  const [query, setQuery] = useState(searchQuery || '');

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    onSearch(query);
  };

  const handleClear = () => {
    setQuery('');
    onSearch('');
  };

  return (
    <header className="navbar">
      <div className="nav-left">
        <div className="logo-badge">
          <div className="logo-icon">
            <Cloud size={24} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span className="logo-text">Drive</span>
              <span className="logo-subtext">LAN SaaS</span>
            </div>
          </div>
        </div>
      </div>

      <div className="search-container">
        <form onSubmit={handleSearchSubmit}>
          <div className="search-input-wrapper">
            <Search size={18} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search files in shared drive..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            {query && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={handleClear}
                title="Clear search"
              >
                <X size={16} />
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="nav-right">
        {health?.webhdfs_connected ? (
          <div className="cluster-pill" title={`WebHDFS connected: ${health?.webhdfs_url}`}>
            <Server size={14} />
            <span>HDFS Active</span>
          </div>
        ) : (
          <div
            className="cluster-pill"
            style={{ color: '#d93025', background: '#fce8e6' }}
            title="HDFS disconnected"
          >
            <Server size={14} />
            <span>HDFS Offline</span>
          </div>
        )}

        <div className="user-profile-badge" title="Authenticated User">
          <div className="user-avatar-circle">
            {user ? user.charAt(0) : 'U'}
          </div>
          <span>{user}</span>
        </div>

        <button className="logout-btn" onClick={onLogout} title="Sign Out">
          <LogOut size={14} />
          <span>Sign Out</span>
        </button>
      </div>
    </header>
  );
}

