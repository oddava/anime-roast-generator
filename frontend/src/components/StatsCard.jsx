import React from 'react';
import { BarChart3 } from 'lucide-react';
import AnimeStatsChart from './AnimeStatsChart';

function StatsCard({ stats }) {
  return (
    <div className="bg-[#141414] border border-[#262626] rounded-xl overflow-hidden h-full">
      {/* Header */}
      <div className="p-4 border-b border-[#262626]">
        <div className="flex items-center justify-center gap-2">
          <BarChart3 className="w-5 h-5 text-[#3b82f6]" />
          <h3 className="text-lg font-semibold text-white">
            Anime Analytics
          </h3>
        </div>
      </div>

      <div className="p-4">
        {/* Chart */}
        <AnimeStatsChart stats={stats} />

        {/* Stats Accuracy Joke */}
        <div className="text-center mt-2">
          <p className="text-[#737373] text-xs italic">
            Stats Accuracy: 11/10
          </p>
        </div>
      </div>
    </div>
  );
}

export default StatsCard;
