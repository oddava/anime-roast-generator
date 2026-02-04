import React, { useState, useCallback } from 'react';
import AnimeSearch from './AnimeSearch';

function RoastForm({ onSubmit, loading }) {
  const [selectedAnime, setSelectedAnime] = useState(null);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    if (selectedAnime && !loading) {
      const displayTitle = selectedAnime.title.english || 
                          selectedAnime.title.romaji || 
                          selectedAnime.title.native;
      onSubmit({
        anime_name: displayTitle,
        anime_id: selectedAnime.id
      });
    }
  }, [selectedAnime, loading, onSubmit]);

  const handleAnimeSelect = useCallback((anime) => {
    setSelectedAnime(anime);
  }, []);

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex flex-col gap-4">
        <AnimeSearch 
          onSelect={handleAnimeSelect}
          selectedAnime={selectedAnime}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !selectedAnime}
          className="w-full sm:w-auto px-8 py-4 bg-[#3b82f6] hover:bg-[#2563eb] text-white font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[#3b82f6] min-w-[140px] text-base"
        >
          {loading ? 'Roasting...' : 'Roast Me'}
        </button>
      </div>
    </form>
  );
}

export default RoastForm;
