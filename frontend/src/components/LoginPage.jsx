import React, { useState } from 'react';
import { Cloud, Lock, User, KeyRound, AlertCircle } from 'lucide-react';

export default function LoginPage({ onLogin, error }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setLocalError('Please enter both username and password');
      return;
    }
    setLocalError('');
    setLoading(true);
    try {
      await onLogin(username.trim(), password);
    } catch (err) {
      setLocalError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (u, p) => {
    setUsername(u);
    setPassword(p);
    setLocalError('');
    setLoading(true);
    onLogin(u, p).catch((err) => {
      setLocalError(err.message || 'Login failed');
      setLoading(false);
    });
  };

  const activeError = localError || error;

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <div className="login-icon">
            <Cloud size={30} />
          </div>
          <h1 className="login-title">Sign in</h1>
          <p className="login-subtitle">to College LAN Cloud Drive</p>
        </div>

        {activeError && (
          <div
            style={{
              padding: '10px 14px',
              background: '#fce8e6',
              borderRadius: '8px',
              border: '1px solid #f5c2c7',
              color: '#c5221f',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <AlertCircle size={16} />
            <span>{activeError}</span>
          </div>
        )}

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. admin or student1"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="login-submit-btn"
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="demo-users-box">
          <div className="demo-title">Lab Demo Accounts (One-Click)</div>
          <div className="demo-buttons-row">
            <button
              type="button"
              className="demo-user-btn"
              onClick={() => handleQuickLogin('admin', 'admin123')}
            >
              <User size={13} color="#1a73e8" />
              <span>admin</span>
            </button>
            <button
              type="button"
              className="demo-user-btn"
              onClick={() => handleQuickLogin('student1', 'labpass1')}
            >
              <User size={13} color="#188038" />
              <span>student1</span>
            </button>
            <button
              type="button"
              className="demo-user-btn"
              onClick={() => handleQuickLogin('student2', 'labpass2')}
            >
              <User size={13} color="#e37400" />
              <span>student2</span>
            </button>
          </div>
        </div>

        <div
          style={{
            fontSize: '11px',
            color: '#80868b',
            textAlign: 'center',
            lineHeight: '1.4',
          }}
        >
          Shared Storage SaaS • Apache Hadoop HDFS • AES-256-GCM Encryption
        </div>
      </div>
    </div>
  );
}

