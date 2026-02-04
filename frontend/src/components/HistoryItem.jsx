import React from 'react';
import { LayoutGrid, List, Trash2, X } from 'lucide-react';
import MiniStatsChart from './MiniStatsChart';

function HistoryItem({ item, viewMode, onSelect, onDelete }) {
  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getRoastSnippet = (roast) => {
    return roast.length > 60 ? roast.substring(0, 60) + '...' : roast;
  };

  if (viewMode === 'gallery') {
    return (
      <div
        onClick={() => onSelect(item)}
        className="bg-[#1f1f1f] border border-[#262626] rounded-lg overflow-hidden cursor-pointer hover:border-[#3b82f6] transition-all hover:shadow-lg hover:shadow-[#3b82f6]/10 group"
      >
        {/* Cover Image */}
        <div className="relative h-32 overflow-hidden">
          {item.coverImage ? (
            <img
              src={item.coverImage}
              alt={item.animeName}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full bg-[#262626] flex items-center justify-center">
              <span className="text-[#737373] text-sm">No Image</span>
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-[#1f1f1f] to-transparent" />
          
          {/* Delete Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(item.id);
            }}
            className="absolute top-2 right-2 p-1.5 bg-[#1f1f1f]/80 hover:bg-red-600/80 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <Trash2 className="w-3.5 h-3.5 text-white" />
          </button>
        </div>

        {/* Content */}
        <div className="p-3">
          <h4 className="text-white font-semibold text-sm truncate mb-1">
            {item.animeName}
          </h4>          
          <p className="text-[#a3a3a3] text-xs mb-2 line-clamp-2">
            {getRoastSnippet(item.roast)}
          </p>

          {/* Mini Chart */}
          {item.stats && <MiniStatsChart stats={item.stats} />}

          <div className="flex justify-between items-center mt-2">
            <span className="text-[#737373] text-xs">
              {formatDate(item.timestamp)}
            </span>
          </div>
        </div>
      </div>
    );
  }

  // List view
  return (
    <div
      onClick={() => onSelect(item)}
      className="flex items-center gap-4 p-3 bg-[#1f1f1f] border border-[#262626] rounded-lg cursor-pointer hover:border-[#3b82f6] transition-colors group"
    >
      {/* Thumbnail */}
      <div className="w-12 h-16 flex-shrink-0 rounded overflow-hidden bg-[#262626]">
        {item.coverImage ? (
          <img
            src={item.coverImage}
            alt={item.animeName}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-[#737373] text-xs">N/A</span>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <h4 className="text-white font-medium text-sm truncate">
          {item.animeName}
        </h4>
        <p className="text-[#a3a3a3] text-xs truncate mt-0.5">
          {getRoastSnippet(item.roast)}
        </p>
        <span className="text-[#737373] text-xs mt-1 block">
          {formatDate(item.timestamp)}
        </span>
      </div>

      {/* Delete Button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete(item.id);
        }}
        className="p-2 hover:bg-red-600/20 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <Trash2 className="w-4 h-4 text-red-400" />
      </button>
    </div>
  );
}

export default HistoryItem;
