import React from 'react';
import { ChevronRight, HardDrive } from 'lucide-react';

export default function Breadcrumbs({ currentPath, onNavigate }) {
  const parts = currentPath ? currentPath.split('/').filter(Boolean) : [];

  return (
    <div className="breadcrumbs">
      <button
        className={`crumb-btn ${parts.length === 0 ? 'active' : ''}`}
        onClick={() => onNavigate('')}
        title="Shared Drive Root"
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
          <HardDrive size={16} />
          Shared Drive
        </span>
      </button>

      {parts.map((part, index) => {
        const fullPath = parts.slice(0, index + 1).join('/');
        const isLast = index === parts.length - 1;

        return (
          <React.Fragment key={fullPath}>
            <span className="crumb-separator">
              <ChevronRight size={16} />
            </span>
            <button
              className={`crumb-btn ${isLast ? 'active' : ''}`}
              onClick={() => onNavigate(fullPath)}
            >
              {part}
            </button>
          </React.Fragment>
        );
      })}
    </div>
  );
}

