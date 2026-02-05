import React from 'react';
import { Copy, Calendar, Film, Star, Tv } from 'lucide-react';
import ReviewBadge from './ReviewBadge';
import ReviewExcerpts from './ReviewExcerpts';
import ShareButton from './ShareButton';
import { trackRoastShared } from '../utils/analytics';

function RoastDisplay({ 
  animeName, 
  roast, 
  stats,
  coverImage, 
  animeDetails, 
  reviewAnalysis,
  reviewsUsed,
  isAnalyzing,
  onCopy 
}) {
  return (
    <div className="bg-[#141414] border border-[#262626] rounded-xl overflow-hidden">
      {/* Compact Header with Thumbnail */}
      <div className="p-4 border-b border-[#262626]">
        <div className="flex items-start gap-4">
          {/* Thumbnail */}
          {coverImage ? (
            <div className="flex-shrink-0 w-20 h-28 md:w-24 md:h-32 rounded-lg overflow-hidden bg-[#262626]">
              <img
                src={coverImage}
                alt={animeName}
                className="w-full h-full object-cover"
              />
            </div>
          ) : (
            <div className="flex-shrink-0 w-20 h-28 md:w-24 md:h-32 rounded-lg bg-[#262626] flex items-center justify-center">
              <span className="text-[#737373] text-xs">N/A</span>
            </div>
          )}

          {/* Title and Info */}
          <div className="flex-1 min-w-0">
            <h2 className="text-lg md:text-xl font-anime font-semibold text-white mb-2 truncate">
              {animeName}
            </h2>

            {/* Compact Anime Info */}
            {animeDetails && (
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[#a3a3a3]">
                {animeDetails.year && (
                  <div className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    <span>{animeDetails.year}</span>
                  </div>
                )}
                {animeDetails.episodes && (
                  <div className="flex items-center gap-1">
                    <Tv className="w-3 h-3" />
                    <span>{animeDetails.episodes} eps</span>
                  </div>
                )}
                {animeDetails.format && (
                  <div className="flex items-center gap-1">
                    <Film className="w-3 h-3" />
                    <span>{animeDetails.format}</span>
                  </div>
                )}
                {animeDetails.score && (
                  <div className="flex items-center gap-1 text-yellow-500">
                    <Star className="w-3 h-3 fill-current" />
                    <span>{animeDetails.score}%</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-4">
        {/* Review Badge */}
        <div className="mb-4">
          <ReviewBadge 
            reviewCount={reviewsUsed}
            averageRating={reviewAnalysis?.averageRating}
            isAnalyzing={isAnalyzing}
          />
        </div>

        {/* Roast Text */}
        <div className="mb-4">
          <p className="text-base md:text-lg leading-relaxed text-white">
            {roast}
          </p>
        </div>

        {/* Review Excerpts */}
        {reviewAnalysis && (
          <div className="mb-4">
            <ReviewExcerpts 
              spicyQuotes={reviewAnalysis.spicyQuotes}
              topCriticisms={reviewAnalysis.topCriticisms}
            />
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onCopy}
            className="flex-1 px-4 py-3 bg-[#1f1f1f] hover:bg-[#262626] border border-[#262626] text-white rounded-lg flex items-center justify-center gap-2 transition-colors text-sm"
          >
            <Copy className="w-4 h-4" />
            <span>Copy Roast</span>
          </button>
          
          {stats && (
            <ShareButton 
              animeName={animeName}
              roast={roast}
              stats={stats}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default RoastDisplay;
