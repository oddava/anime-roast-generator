import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Search, X, Loader2 } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || '';

function AnimeSearch({ onSelect, selectedAnime, disabled }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [error, setError] = useState('');
  const debounceTimer = useRef(null);
  const inputRef = useRef(null);

  // Debounced search function
  const searchAnime = useCallback(async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(
        `${API_URL}/api/search-anime?q=${encodeURIComponent(searchQuery)}`
      );

      if (!response.ok) {
        throw new Error('Failed to search anime');
      }

      const data = await response.json();
      const results = data.results || [];
      setSuggestions(results);
      // Auto-show suggestions when results come in and input is focused
      if (results.length > 0 && inputRef.current === document.activeElement) {
        setShowSuggestions(true);
      }
    } catch (err) {
      console.error('Search error:', err);
      // Provide more helpful error messages
      let errorMessage = 'Failed to search anime';
      if (err.message?.includes('Failed to fetch') || err.message?.includes('NetworkError')) {
        errorMessage = 'Cannot connect to server. Please make sure the backend is running on port 8000.';
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle input changes with debounce
  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);

    // Clear previous timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Show suggestions immediately if we have results and query is valid
    if (value.length >= 2 && suggestions.length > 0) {
      setShowSuggestions(true);
    }

    // Set new timer for debounced search
    debounceTimer.current = setTimeout(() => {
      searchAnime(value);
    }, 300);
  };

  // Handle anime selection
  const handleSelect = (anime) => {
    const displayTitle = anime.title.english || anime.title.romaji || anime.title.native;
    setQuery(displayTitle);
    setShowSuggestions(false);
    onSelect(anime);
  };

  // Handle clearing selection
  const handleClear = () => {
    setQuery('');
    setSuggestions([]);
    setShowSuggestions(false);
    onSelect(null);
    inputRef.current?.focus();
  };

  // Handle clicking outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.anime-search-container')) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Cleanup debounce timer
  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, []);

  // Get display title helper
  const getDisplayTitle = (anime) => {
    return anime.title.english || anime.title.romaji || anime.title.native || 'Unknown';
  };

  // Get subtitle (alternative title)
  const getSubtitle = (anime) => {
    const title = anime.title;
    if (title.english && title.romaji && title.english !== title.romaji) {
      return title.romaji;
    }
    if (title.native && title.native !== title.romaji) {
      return title.native;
    }
    return null;
  };

  return (
    <div className="anime-search-container relative w-full">
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => {
            if (query.length >= 2 && suggestions.length > 0) {
              setShowSuggestions(true);
            }
          }}
          placeholder="Search for an anime..."
          disabled={disabled}
          maxLength={100}
          className="w-full px-6 py-4 bg-[#141414] border border-[#262626] rounded-lg text-white placeholder-[#737373] focus:border-[#3b82f6] transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-base pr-12"
        />
        
        {/* Search icon or loading spinner */}
        <div className="absolute right-4 top-1/2 -translate-y-1/2">
          {loading ? (
            <Loader2 className="w-5 h-5 text-[#737373] animate-spin" />
          ) : query ? (
            <button
              onClick={handleClear}
              className="text-[#737373] hover:text-white transition-colors"
              type="button"
            >
              <X className="w-5 h-5" />
            </button>
          ) : (
            <Search className="w-5 h-5 text-[#737373]" />
          )}
        </div>
      </div>

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-[#1f1f1f] border border-[#262626] rounded-lg shadow-xl max-h-96 overflow-y-auto">
          {suggestions.map((anime) => (
            <button
              key={anime.id}
              onClick={() => handleSelect(anime)}
              className="w-full px-4 py-3 flex items-center gap-4 hover:bg-[#262626] transition-colors text-left border-b border-[#262626] last:border-b-0"
              type="button"
            >
              {/* Cover Image */}
              {anime.coverImage?.medium && (
                <img
                  src={anime.coverImage.medium}
                  alt={getDisplayTitle(anime)}
                  className="w-12 h-16 object-cover rounded flex-shrink-0"
                  loading="lazy"
                />
              )}
              
              {/* Anime Info */}
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium truncate">
                  {getDisplayTitle(anime)}
                </p>
                {getSubtitle(anime) && (
                  <p className="text-[#737373] text-sm truncate">
                    {getSubtitle(anime)}
                  </p>
                )}
                <div className="flex items-center gap-3 mt-1 text-xs text-[#737373]">
                  {anime.year && <span>{anime.year}</span>}
                  {anime.episodes && <span>{anime.episodes} eps</span>}
                  {anime.format && <span>{anime.format}</span>}
                  {anime.score && (
                    <span className="text-yellow-500">★ {anime.score}%</span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No results message */}
      {showSuggestions && query.length >= 2 && !loading && suggestions.length === 0 && (
        <div className="absolute z-50 w-full mt-2 bg-[#1f1f1f] border border-[#262626] rounded-lg shadow-xl p-4 text-center">
          <p className="text-[#737373]">No anime found</p>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="absolute z-50 w-full mt-2 bg-[#1f1f1f] border border-red-600/30 rounded-lg shadow-xl p-4">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}

export default AnimeSearch;
