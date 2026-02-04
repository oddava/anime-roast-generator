import React from 'react';

function SkeletonLoader({ loadingText }) {
  return (
    <div className="w-full max-w-4xl mx-auto animate-fade-in">
      <div className="bg-[#141414] border border-[#262626] rounded-xl overflow-hidden">
        {/* Header Skeleton */}
        <div className="p-4 border-b border-[#262626]">
          <div className="flex items-start gap-4">
            {/* Thumbnail Skeleton */}
            <div className="flex-shrink-0 w-20 h-28 md:w-24 md:h-32 rounded-lg bg-[#262626] animate-pulse" />

            {/* Title and Info Skeleton */}
            <div className="flex-1 min-w-0 space-y-3">
              <div className="h-6 bg-[#262626] rounded animate-pulse w-3/4" />
              <div className="flex gap-4">
                <div className="h-4 bg-[#262626] rounded animate-pulse w-16" />
                <div className="h-4 bg-[#262626] rounded animate-pulse w-20" />
                <div className="h-4 bg-[#262626] rounded animate-pulse w-14" />
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 space-y-4">
          {/* Review Badge Skeleton */}
          <div className="flex gap-2">
            <div className="h-8 bg-[#262626] rounded-full animate-pulse w-32" />
            <div className="h-8 bg-[#262626] rounded-full animate-pulse w-24" />
          </div>

          {/* Roast Text Skeleton */}
          <div className="space-y-2">
            <div className="h-4 bg-[#262626] rounded animate-pulse w-full" />
            <div className="h-4 bg-[#262626] rounded animate-pulse w-full" />
            <div className="h-4 bg-[#262626] rounded animate-pulse w-5/6" />
            <div className="h-4 bg-[#262626] rounded animate-pulse w-full" />
            <div className="h-4 bg-[#262626] rounded animate-pulse w-4/5" />
          </div>

          {/* Stats Chart Skeleton */}
          <div className="flex justify-center py-4">
            <div className="w-48 h-48 rounded-full border-4 border-[#262626] animate-pulse" />
          </div>

          {/* Buttons Skeleton */}
          <div className="flex gap-3">
            <div className="flex-1 h-10 bg-[#262626] rounded-lg animate-pulse" />
            <div className="flex-1 h-10 bg-[#262626] rounded-lg animate-pulse" />
          </div>
        </div>
      </div>

      {/* Loading Text */}
      <div className="text-center mt-6">
        <p className="text-[#737373] text-sm animate-pulse">{loadingText}</p>
      </div>
    </div>
  );
}

export default SkeletonLoader;
