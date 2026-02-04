import React, { useState, useEffect, useCallback } from 'react';
import { Copy, AlertCircle, Github, Twitter } from 'lucide-react';
import RoastForm from './components/RoastForm';
import RoastDisplay from './components/RoastDisplay';
import StatsCard from './components/StatsCard';
import SkeletonLoader from './components/SkeletonLoader';
import RoastHistory, { MAX_HISTORY_ITEMS, STORAGE_KEY } from './components/RoastHistory';

// API URL configuration for Vercel deployment
// On Vercel, API is served from same origin, so we use relative path
const API_URL = import.meta.env.VITE_API_URL || '';

function App() {
  const [animeName, setAnimeName] = useState('');
  const [roast, setRoast] = useState('');
  const [stats, setStats] = useState(null);
  const [coverImage, setCoverImage] = useState(null);
  const [animeDetails, setAnimeDetails] = useState(null);
  const [reviewAnalysis, setReviewAnalysis] = useState(null);
  const [reviewsUsed, setReviewsUsed] = useState(0);
  const [loading, setLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState('');
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');
  const [roastHistory, setRoastHistory] = useState([]);

  // Load history from localStorage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem(STORAGE_KEY);
    if (savedHistory) {
      try {
        const parsed = JSON.parse(savedHistory);
        setRoastHistory(parsed);
      } catch (e) {
        console.error('Failed to parse roast history:', e);
      }
    }
  }, []);

  // Save history to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(roastHistory));
  }, [roastHistory]);

  const addToHistory = useCallback((data) => {
    const newEntry = {
      id: Date.now(),
      animeName: data.anime_name,
      roast: data.roast,
      stats: data.stats,
      coverImage: data.cover_image,
      animeDetails: data.anime_details,
      reviewAnalysis: data.review_analysis,
      reviewsUsed: data.reviews_used,
      timestamp: Date.now()
    };

    setRoastHistory(prev => {
      // Remove any existing entry with the same anime name (case-insensitive)
      const filtered = prev.filter(
        item => item.animeName.toLowerCase() !== data.anime_name.toLowerCase()
      );
      // Add new entry at the beginning and limit to MAX_HISTORY_ITEMS
      const updated = [newEntry, ...filtered].slice(0, MAX_HISTORY_ITEMS);
      return updated;
    });
  }, []);

  const generateRoast = useCallback(async (animeData) => {
    if (!animeData || !animeData.anime_name) {
      setError('Please select an anime');
      return;
    }

    setLoading(true);
    setIsAnalyzing(true);
    setLoadingPhase('Fetching anime data...');
    setError('');
    setRoast('');
    setStats(null);
    setCoverImage(null);
    setAnimeDetails(null);
    setReviewAnalysis(null);
    setReviewsUsed(0);

    try {
      const response = await fetch(`${API_URL}/api/generate-roast`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          anime_name: animeData.anime_name,
          anime_id: animeData.anime_id
        }),
      });

      // Simulate loading phases for better UX
      setLoadingPhase('Analyzing community reviews...');
      await new Promise(resolve => setTimeout(resolve, 800));
      
      setLoadingPhase('Processing review data...');
      await new Promise(resolve => setTimeout(resolve, 600));
      
      setLoadingPhase('Crafting your roast...');
      await new Promise(resolve => setTimeout(resolve, 1000));

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please wait a minute before trying again.');
        }
        throw new Error(data.detail || 'Failed to generate roast');
      }

      setRoast(data.roast);
      setAnimeName(data.anime_name);
      setStats(data.stats);
      setCoverImage(data.cover_image);
      setAnimeDetails(data.anime_details);
      setReviewAnalysis(data.review_analysis);
      setReviewsUsed(data.reviews_used || 0);

      // Add to history
      addToHistory(data);
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
      setIsAnalyzing(false);
      setLoadingPhase('');
    }
  }, [addToHistory]);

  const copyToClipboard = useCallback(() => {
    if (roast) {
      navigator.clipboard.writeText(roast);
      setToast('Roast copied to clipboard');
      setTimeout(() => setToast(''), 3000);
    }
  }, [roast]);

  const handleHistorySelect = useCallback((item) => {
    setAnimeName(item.animeName);
    setRoast(item.roast);
    setStats(item.stats);
    setCoverImage(item.coverImage);
    setAnimeDetails(item.animeDetails);
    setReviewAnalysis(item.reviewAnalysis);
    setReviewsUsed(item.reviewsUsed || 0);
    setError('');
    // Scroll to top to show the selected roast
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handleHistoryDelete = useCallback((id) => {
    setRoastHistory(prev => prev.filter(item => item.id !== id));
  }, []);

  const handleClearAllHistory = useCallback(() => {
    if (window.confirm('Are you sure you want to clear all roast history?')) {
      setRoastHistory([]);
    }
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex flex-col">
      {/* Header */}
      <header className="py-8 md:py-12 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-anime font-bold text-white tracking-wider mb-3">
            ANIME ROAST
          </h1>
          <p className="text-[#a3a3a3] text-base md:text-lg">
            Search for your favorite anime and get roasted
          </p>
          <p className="text-[#737373] text-sm mt-1">
            Now powered by real AniList community reviews
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 px-4 pb-12">
        <div className="max-w-6xl mx-auto">
          {/* Input Form */}
          <div className="max-w-2xl mx-auto mb-8">
            <RoastForm onSubmit={generateRoast} loading={loading} />
          </div>

          {/* Error Message */}
          {error && (
            <div className="max-w-2xl mx-auto mb-6 p-4 bg-[#1f1f1f] border border-red-600/30 rounded-lg flex items-center gap-3 animate-fade-in">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Loading State with Skeleton */}
          {loading && (
            <SkeletonLoader loadingText={loadingPhase} />
          )}

          {/* Results Grid - Side by side on desktop */}
          {roast && !loading && (
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
              {/* Roast Card - Takes 3/5 width on desktop */}
              <div className="lg:col-span-3 animate-slide-up">
                <RoastDisplay 
                  animeName={animeName}
                  roast={roast}
                  stats={stats}
                  coverImage={coverImage}
                  animeDetails={animeDetails}
                  reviewAnalysis={reviewAnalysis}
                  reviewsUsed={reviewsUsed}
                  isAnalyzing={isAnalyzing}
                  onCopy={copyToClipboard}
                />
              </div>

              {/* Stats Chart - Takes 2/5 width on desktop */}
              {stats && (
                <div className="lg:col-span-2 animate-slide-up" style={{ animationDelay: '100ms' }}>
                  <StatsCard stats={stats} />
                </div>
              )}
            </div>
          )}

          {/* Roast History - Horizontal Carousel */}
          <RoastHistory
            history={roastHistory}
            onSelect={handleHistorySelect}
            onDelete={handleHistoryDelete}
            onClearAll={handleClearAllHistory}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 px-4 border-t border-[#262626]">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-center gap-4">
            <p className="text-[#737373] text-sm">
              Made for anime fans who can take a joke • Data from AniList
            </p>
            <div className="flex items-center gap-4">
              <a
                href="https://x.com/oddava"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-[#737373] hover:text-white transition-colors text-sm"
              >
                <Twitter className="w-4 h-4" />
                <span>@oddava</span>
              </a>
              <a
                href="https://github.com/oddava"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-[#737373] hover:text-white transition-colors text-sm"
              >
                <Github className="w-4 h-4" />
                <span>@oddava</span>
              </a>
            </div>
          </div>
        </div>
      </footer>

      {/* Toast Notification */}
      {toast && (
        <div className="toast flex items-center gap-3">
          <Copy className="w-4 h-4 text-[#3b82f6]" />
          <span className="text-white">{toast}</span>
        </div>
      )}
    </div>
  );
}

export default App;
