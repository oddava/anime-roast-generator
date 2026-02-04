import React from 'react';
import { LayoutGrid, List } from 'lucide-react';

function ViewToggle({ viewMode, onChange }) {
  return (
    <div className="flex items-center gap-1 bg-[#1f1f1f] border border-[#262626] rounded-lg p-1">
      <button
        onClick={() => onChange('gallery')}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors text-sm font-medium ${
          viewMode === 'gallery'
            ? 'bg-[#3b82f6] text-white'
            : 'text-[#a3a3a3] hover:text-white'
        }`}
      >
        <LayoutGrid className="w-4 h-4" />
        Gallery
      </button>
      <button
        onClick={() => onChange('list')}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors text-sm font-medium ${
          viewMode === 'list'
            ? 'bg-[#3b82f6] text-white'
            : 'text-[#a3a3a3] hover:text-white'
        }`}
      >
        <List className="w-4 h-4" />
        List
      </button>
    </div>
  );
}

export default ViewToggle;
