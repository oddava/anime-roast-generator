/**
 * Google Analytics tracking utility
 * Simple wrapper around gtag for type-safe event tracking
 */

// Check if analytics is enabled (user consented)
const isAnalyticsEnabled = () => {
  const consent = localStorage.getItem('ga-consent');
  return consent === 'granted' || consent === null; // Default to enabled if not set
};

// Set consent status
export const setAnalyticsConsent = (granted) => {
  localStorage.setItem('ga-consent', granted ? 'granted' : 'denied');
  if (granted && window.gtag) {
    gtag('consent', 'update', {
      analytics_storage: 'granted'
    });
  } else if (window.gtag) {
    gtag('consent', 'update', {
      analytics_storage: 'denied'
    });
  }
};

// Get consent status
export const getAnalyticsConsent = () => {
  return localStorage.getItem('ga-consent');
};

// Track a custom event
export const trackEvent = (eventName, params = {}) => {
  if (!isAnalyticsEnabled()) return;
  
  if (window.gtag) {
    gtag('event', eventName, params);
  }
};

// Predefined events for the app
export const AnalyticsEvents = {
  // Roast events
  ROAST_GENERATED: 'roast_generated',
  ROAST_COPIED: 'roast_copied',
  ROAST_SHARED: 'roast_shared',
  ROAST_SHARED_TWITTER: 'roast_shared_twitter',
  
  // Search events
  ANIME_SEARCH: 'anime_search',
  ANIME_SELECTED: 'anime_selected',
  
  // Comment events
  COMMENT_POSTED: 'comment_posted',
  COMMENT_VOTED: 'comment_voted',
  COMMENT_DELETED: 'comment_deleted',
  
  // UI events
  HISTORY_ITEM_SELECTED: 'history_item_selected',
  STATS_TOGGLED: 'stats_toggled',
  
  // Error events
  ROAST_GENERATION_FAILED: 'roast_generation_failed',
  SEARCH_FAILED: 'search_failed',
};

// Helper functions for common events
export const trackRoastGenerated = (animeName, hasStats, reviewsUsed) => {
  trackEvent(AnalyticsEvents.ROAST_GENERATED, {
    anime_name: animeName,
    has_stats: hasStats,
    reviews_used: reviewsUsed,
  });
};

export const trackRoastCopied = (animeName) => {
  trackEvent(AnalyticsEvents.ROAST_COPIED, {
    anime_name: animeName,
  });
};

export const trackRoastShared = (animeName, platform) => {
  trackEvent(AnalyticsEvents.ROAST_SHARED, {
    anime_name: animeName,
    platform: platform,
  });
  
  if (platform === 'twitter') {
    trackEvent(AnalyticsEvents.ROAST_SHARED_TWITTER, {
      anime_name: animeName,
    });
  }
};

export const trackAnimeSearch = (query, resultsCount) => {
  trackEvent(AnalyticsEvents.ANIME_SEARCH, {
    query_length: query.length,
    results_count: resultsCount,
  });
};

export const trackAnimeSelected = (animeName, animeId) => {
  trackEvent(AnalyticsEvents.ANIME_SELECTED, {
    anime_name: animeName,
    anime_id: animeId,
  });
};

export const trackCommentPosted = (hasParent = false) => {
  trackEvent(AnalyticsEvents.COMMENT_POSTED, {
    is_reply: hasParent,
  });
};

export const trackCommentVoted = (voteType) => {
  trackEvent(AnalyticsEvents.COMMENT_VOTED, {
    vote_type: voteType, // 'up' or 'down'
  });
};

export const trackHistoryItemSelected = (animeName) => {
  trackEvent(AnalyticsEvents.HISTORY_ITEM_SELECTED, {
    anime_name: animeName,
  });
};

export const trackStatsToggled = (visible) => {
  trackEvent(AnalyticsEvents.STATS_TOGGLED, {
    visible: visible,
  });
};

export const trackRoastGenerationFailed = (animeName, errorType) => {
  trackEvent(AnalyticsEvents.ROAST_GENERATION_FAILED, {
    anime_name: animeName,
    error_type: errorType,
  });
};

export const trackSearchFailed = (query, errorType) => {
  trackEvent(AnalyticsEvents.SEARCH_FAILED, {
    query_length: query.length,
    error_type: errorType,
  });
};

export default {
  trackEvent,
  AnalyticsEvents,
  trackRoastGenerated,
  trackRoastCopied,
  trackRoastShared,
  trackAnimeSearch,
  trackAnimeSelected,
  trackCommentPosted,
  trackCommentVoted,
  trackHistoryItemSelected,
  trackStatsToggled,
  trackRoastGenerationFailed,
  trackSearchFailed,
  setAnalyticsConsent,
  getAnalyticsConsent,
};
