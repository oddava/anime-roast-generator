import React, { useState } from 'react';
import { Quote, ChevronDown, ChevronUp, Flame } from 'lucide-react';

function ReviewExcerpts({ spicyQuotes, topCriticisms }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if ((!spicyQuotes || spicyQuotes.length === 0) && (!topCriticisms || topCriticisms.length === 0)) {
    return null;
  }

  return (
    <div className="mt-6 bg-[#1f1f1f] border border-[#262626] rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-[#262626] transition-colors"
      >
        <div className="flex items-center gap-3">
          <Flame className="w-5 h-5 text-orange-500" />
          <span className="text-white font-medium">Community Hot Takes</span>
          <span className="text-[#737373] text-sm">
            ({(spicyQuotes?.length || 0) + (topCriticisms?.length || 0)} items)
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-[#737373]" />
        ) : (
          <ChevronDown className="w-5 h-5 text-[#737373]" />
        )}
      </button>

      {isExpanded && (
        <div className="p-4 border-t border-[#262626] space-y-4">
          {/* Spicy Quotes */}
          {spicyQuotes && spicyQuotes.length > 0 && (
            <div>
              <h4 className="text-[#a3a3a3] text-sm font-medium mb-3 flex items-center gap-2">
                <Quote className="w-4 h-4" />
                Spiciest Review Quotes
              </h4>
              <div className="space-y-3">
                {spicyQuotes.map((quote, index) => (
                  <div
                    key={index}
                    className="pl-4 border-l-2 border-orange-500/50"
                  >
                    <p className="text-[#d4d4d4] text-sm italic">"{quote}"</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top Criticisms */}
          {topCriticisms && topCriticisms.length > 0 && (
            <div className={spicyQuotes?.length > 0 ? 'pt-4 border-t border-[#262626]' : ''}>
              <h4 className="text-[#a3a3a3] text-sm font-medium mb-3 flex items-center gap-2">
                <Flame className="w-4 h-4" />
                Top Community Complaints
              </h4>
              <div className="flex flex-wrap gap-2">
                {topCriticisms.map((criticism, index) => (
                  <span
                    key={index}
                    className="px-3 py-1.5 bg-red-500/10 border border-red-500/20 rounded-full text-red-400 text-sm"
                  >
                    {criticism}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ReviewExcerpts;
