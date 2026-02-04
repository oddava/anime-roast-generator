import React, { useState, useRef } from 'react';
import { History, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import HistoryItem from './HistoryItem';

const MAX_HISTORY_ITEMS = 20;
const STORAGE_KEY = 'animeRoastHistory';

function RoastHistory({ history, onSelect, onDelete, onClearAll }) {
  const scrollRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  const checkScroll = () => {
    if (scrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
      setCanScrollLeft(scrollLeft > 0);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
    }
  };

  const scroll = (direction) => {
    if (scrollRef.current) {
      const scrollAmount = 320; // Card width + gap
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
      setTimeout(checkScroll, 300);
    }
  };

  if (history.length === 0) {
    return null;
  }

  return (
    <div className="mt-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <History className="w-5 h-5 text-[#3b82f6]" />
          <h3 className="text-white font-semibold">
            Your Roasted Anime Collection
          </h3>
          <span className="text-[#737373] text-sm">
            ({history.length}/{MAX_HISTORY_ITEMS})
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => onClearAll()}
            className="flex items-center gap-1.5 px-3 py-1.5 text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded-lg transition-colors text-sm"
          >
            <Trash2 className="w-4 h-4" />
            <span className="hidden sm:inline">Clear All</span>
          </button>

          <div className="flex items-center gap-1">
            <button
              onClick={() => scroll('left')}
              disabled={!canScrollLeft}
              className="p-2 bg-[#1f1f1f] hover:bg-[#262626] border border-[#262626] rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4 text-white" />
            </button>
            <button
              onClick={() => scroll('right')}
              disabled={!canScrollRight}
              className="p-2 bg-[#1f1f1f] hover:bg-[#262626] border border-[#262626] rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>
      </div>

      {/* Horizontal Scrolling Carousel */}
      <div className="relative">
        <div
          ref={scrollRef}
          onScroll={checkScroll}
          className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {history.map((item) => (
            <div 
              key={item.id} 
              className="flex-shrink-0 w-[280px] md:w-[300px]"
            >
              <HistoryItem
                item={item}
                viewMode="gallery"
                onSelect={onSelect}
                onDelete={onDelete}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default RoastHistory;
export { MAX_HISTORY_ITEMS, STORAGE_KEY };
