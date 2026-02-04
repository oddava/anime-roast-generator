import React from 'react';
import { MessageSquare, Users, Star, AlertTriangle } from 'lucide-react';

function ReviewBadge({ reviewCount, averageRating, isAnalyzing }) {
  if (isAnalyzing) {
    return (
      <div className="inline-flex items-center gap-2 px-4 py-2 bg-[#1f1f1f] border border-[#3b82f6]/30 rounded-full text-[#3b82f6] animate-pulse">
        <div className="w-4 h-4 border-2 border-[#3b82f6] border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-medium">Analyzing community opinions...</span>
      </div>
    );
  }

  if (!reviewCount || reviewCount === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="inline-flex items-center gap-2 px-4 py-2 bg-[#1f1f1f] border border-[#262626] rounded-full">
        <MessageSquare className="w-4 h-4 text-[#3b82f6]" />
        <span className="text-white text-sm font-medium">
          Powered by real AniList reviews
        </span>
      </div>

      <div className="inline-flex items-center gap-2 px-3 py-2 bg-[#1f1f1f] border border-[#262626] rounded-full">
        <Users className="w-4 h-4 text-[#a3a3a3]" />
        <span className="text-[#a3a3a3] text-sm">
          Analyzed {reviewCount} community reviews
        </span>
      </div>

      {averageRating && (
        <div className="inline-flex items-center gap-1.5 px-3 py-2 bg-[#1f1f1f] border border-[#262626] rounded-full">
          <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
          <span className="text-yellow-500 text-sm font-medium">
            {averageRating.toFixed(1)}/10
          </span>
          <span className="text-[#737373] text-xs">avg rating</span>
        </div>
      )}

      <div className="inline-flex items-center gap-1.5 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-full">
        <AlertTriangle className="w-4 h-4 text-red-400" />
        <span className="text-red-400 text-sm font-medium">
          Based on {reviewCount} toxic fans
        </span>
      </div>
    </div>
  );
}

export default ReviewBadge;
