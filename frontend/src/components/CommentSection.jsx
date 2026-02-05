import React, { useState, useEffect, useCallback } from 'react';
import { MessageSquare, ChevronUp, ChevronDown, MoreHorizontal, Edit2, Trash2 } from 'lucide-react';
import { sanitizeContent } from '../utils/sanitize';
import { trackCommentPosted, trackCommentVoted } from '../utils/analytics';

const API_URL = import.meta.env.VITE_API_URL || '';
const USERNAME_STORAGE_KEY = 'animeRoastUsername_v2';
const USERNAME_COOKIE_KEY = 'animeRoastUsername';
const COLLAPSED_THREADS_KEY = 'animeRoastCollapsedThreads';

// Generate a random anime-themed username
const generateRandomUsername = () => {
  const prefixes = [
    'Weeb', 'Otaku', 'Anime', 'Manga', 'Chibi', 'Senpai', 'Kouhai',
    'Tsundere', 'Yandere', 'Ninja', 'Samurai', 'Dragon', 'Demon',
    'Angel', 'Vampire', 'Neko', 'Sakura', 'Shadow', 'Phantom', 'Crystal'
  ];
  
  const suffixes = [
    'Lord', 'King', 'Queen', 'Master', 'Slayer', 'Hunter', 'Fan',
    'Critic', 'Senpai', 'Kouhai', 'Hero', 'Villain', 'Watcher',
    'Sage', 'Knight', 'Mage', 'Rogue', 'Paladin', 'Warlock'
  ];
  
  const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
  const suffix = suffixes[Math.floor(Math.random() * suffixes.length)];
  const number = Math.floor(Math.random() * 9999) + 1;
  
  return `${prefix}${suffix}_${number}`;
};

// Cookie helpers
const setCookie = (name, value, days = 365) => {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Strict`;
};

const getCookie = (name) => {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
};

// Get or create username from localStorage with cookie backup
const getStoredUsername = () => {
  // Try localStorage first
  let stored = localStorage.getItem(USERNAME_STORAGE_KEY);
  
  // If not in localStorage, try cookie
  if (!stored) {
    stored = getCookie(USERNAME_COOKIE_KEY);
    if (stored) {
      // Restore to localStorage
      localStorage.setItem(USERNAME_STORAGE_KEY, stored);
    }
  }
  
  // If still not found, generate new
  if (!stored) {
    stored = generateRandomUsername();
    localStorage.setItem(USERNAME_STORAGE_KEY, stored);
    setCookie(USERNAME_COOKIE_KEY, stored);
  }
  
  return stored;
};

// Get collapsed threads from localStorage
const getCollapsedThreads = () => {
  const stored = localStorage.getItem(COLLAPSED_THREADS_KEY);
  return stored ? JSON.parse(stored) : {};
};

// Save collapsed threads to localStorage
const saveCollapsedThreads = (collapsed) => {
  localStorage.setItem(COLLAPSED_THREADS_KEY, JSON.stringify(collapsed));
};

// Format relative time from UTC
const formatDate = (dateString) => {
  // Parse UTC date and convert to local
  const date = new Date(dateString + 'Z'); // Ensure UTC parsing
  const now = new Date();
  const diffMs = now - date;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffSecs < 10) return 'just now';
  if (diffSecs < 60) return `${diffSecs}s`;
  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 30) return `${diffDays}d`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

// Format exact timestamp for hover
const formatExactDate = (dateString) => {
  const date = new Date(dateString + 'Z');
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });
};

const VoteButtons = ({ comment, onVote, disabled }) => {
  return (
    <div className="vote-buttons">
      <button
        className={`vote-button upvote ${comment.user_vote === 1 ? 'active' : ''}`}
        onClick={() => onVote(comment.id, comment.user_vote === 1 ? 0 : 1)}
        disabled={disabled}
        title="Upvote"
      >
        <ChevronUp className="w-4 h-4" />
      </button>
      <span className={`vote-score ${comment.score > 0 ? 'positive' : comment.score < 0 ? 'negative' : ''}`}>
        {comment.score}
      </span>
      <button
        className={`vote-button downvote ${comment.user_vote === -1 ? 'active' : ''}`}
        onClick={() => onVote(comment.id, comment.user_vote === -1 ? 0 : -1)}
        disabled={disabled}
        title="Downvote"
      >
        <ChevronDown className="w-4 h-4" />
      </button>
    </div>
  );
};

const CommentItem = ({ 
  comment, 
  onVote, 
  onReply, 
  onEdit, 
  onDelete, 
  depth = 0,
  collapsedThreads,
  onToggleCollapse,
  currentUsername
}) => {
  const [isReplying, setIsReplying] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [editContent, setEditContent] = useState(comment.content);
  const [isCollapsed, setIsCollapsed] = useState(collapsedThreads[comment.id] || false);
  const [showActions, setShowActions] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const isOwnComment = comment.author_name === currentUsername && !comment.is_deleted;
  const canEdit = isOwnComment && !comment.is_deleted;
  const timeSinceCreation = new Date() - new Date(comment.created_at + 'Z');
  const canEditTime = timeSinceCreation < 15 * 60 * 1000; // 15 minutes
  
  const handleReply = async () => {
    if (!replyContent.trim()) return;
    setIsSubmitting(true);
    try {
      await onReply(comment.id, replyContent.trim());
      setReplyContent('');
      setIsReplying(false);
    } catch (err) {
      // Error handled in parent
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handleEdit = async () => {
    if (!editContent.trim() || editContent === comment.content) {
      setIsEditing(false);
      return;
    }
    setIsSubmitting(true);
    try {
      await onEdit(comment.id, editContent.trim());
      setIsEditing(false);
    } catch (err) {
      // Error handled in parent
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handleDelete = async () => {
    if (window.confirm('Delete this comment?')) {
      await onDelete(comment.id);
    }
  };
  
  const toggleCollapse = () => {
    const newCollapsed = !isCollapsed;
    setIsCollapsed(newCollapsed);
    onToggleCollapse(comment.id, newCollapsed);
  };
  
  if (isCollapsed) {
    return (
      <div className="comment-item collapsed" style={{ marginLeft: depth * 24 }}>
        <div className="comment-collapsed-header" onClick={toggleCollapse}>
          <span className="comment-author">{comment.author_name}</span>
          <span className="comment-score">{comment.score} points</span>
          <span className="comment-replies">{comment.reply_count} replies</span>
          <button className="comment-expand">[ + ]</button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="comment-item" style={{ marginLeft: depth * 24 }}>
      <div className="comment-main">
        <VoteButtons comment={comment} onVote={onVote} disabled={comment.is_deleted} />
        
        <div className="comment-content-wrapper">
          <div className="comment-header">
            <span className={`comment-author ${isOwnComment ? 'is-you' : ''}`}>
              {comment.author_name}
            </span>
            <span className="comment-separator">•</span>
            <span 
              className="comment-time" 
              title={formatExactDate(comment.created_at)}
            >
              {formatDate(comment.created_at)}
            </span>
            {comment.is_edited === 1 && (
              <>
                <span className="comment-separator">•</span>
                <span className="comment-edited">edited</span>
              </>
            )}
            {depth > 0 && comment.reply_count > 0 && (
              <button className="comment-collapse-btn" onClick={toggleCollapse} title="Collapse thread">
                [ - ]
              </button>
            )}
          </div>
          
          {isEditing ? (
            <div className="comment-edit-form">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                maxLength={1000}
                rows={3}
                className="comment-textarea"
                disabled={isSubmitting}
              />
              <div className="comment-edit-actions">
                <button 
                  className="comment-btn-secondary" 
                  onClick={() => setIsEditing(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button 
                  className="comment-btn-primary" 
                  onClick={handleEdit}
                  disabled={isSubmitting || !editContent.trim()}
                >
                  {isSubmitting ? 'Saving...' : 'Save'}
                </button>
              </div>
            </div>
          ) : (
            <div className="comment-body">{sanitizeContent(comment.content)}</div>
          )}
          
          {!comment.is_deleted && !isEditing && (
            <div className="comment-actions">
              <button 
                className="comment-action-btn" 
                onClick={() => setIsReplying(!isReplying)}
              >
                Reply
              </button>
              
              {canEdit && canEditTime && (
                <div className="comment-action-menu">
                  <button 
                    className="comment-action-btn"
                    onClick={() => setShowActions(!showActions)}
                  >
                    <MoreHorizontal className="w-4 h-4" />
                  </button>
                  
                  {showActions && (
                    <div className="comment-dropdown">
                      <button onClick={() => { setIsEditing(true); setShowActions(false); }}>
                        <Edit2 className="w-4 h-4" />
                        Edit
                      </button>
                      <button onClick={() => { handleDelete(); setShowActions(false); }} className="delete">
                        <Trash2 className="w-4 h-4" />
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          
          {isReplying && (
            <div className="comment-reply-form">
              <textarea
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                placeholder="What are your thoughts?"
                maxLength={1000}
                rows={3}
                className="comment-textarea"
                disabled={isSubmitting}
                autoFocus
              />
              <div className="comment-reply-actions">
                <span className="char-count">{replyContent.length}/1000</span>
                <button 
                  className="comment-btn-secondary" 
                  onClick={() => setIsReplying(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button 
                  className="comment-btn-primary" 
                  onClick={handleReply}
                  disabled={isSubmitting || !replyContent.trim()}
                >
                  {isSubmitting ? 'Posting...' : 'Reply'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Render replies */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="comment-replies-list">
          {comment.replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              onVote={onVote}
              onReply={onReply}
              onEdit={onEdit}
              onDelete={onDelete}
              depth={depth + 1}
              collapsedThreads={collapsedThreads}
              onToggleCollapse={onToggleCollapse}
              currentUsername={currentUsername}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const CommentSection = ({ animeId }) => {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [newComment, setNewComment] = useState('');
  const [username, setUsername] = useState('');
  const [totalComments, setTotalComments] = useState(0);
  const [sortBy, setSortBy] = useState('best');
  const [cursor, setCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [collapsedThreads, setCollapsedThreads] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [votingCommentId, setVotingCommentId] = useState(null);

  // Initialize username and collapsed threads on mount
  useEffect(() => {
    setUsername(getStoredUsername());
    setCollapsedThreads(getCollapsedThreads());
  }, []);

  // Fetch comments when animeId or sortBy changes
  const fetchComments = useCallback(async (reset = false) => {
    if (!animeId) return;
    
    setLoading(true);
    setError('');
    
    try {
      const currentCursor = reset ? '' : cursor;
      const response = await fetch(
        `${API_URL}/api/anime/${animeId}/comments?sort=${sortBy}${currentCursor ? `&cursor=${currentCursor}` : ''}&limit=20`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch comments');
      }
      
      const data = await response.json();
      
      if (reset) {
        setComments(data.comments || []);
      } else {
        setComments(prev => [...prev, ...(data.comments || [])]);
      }
      
      setTotalComments(data.total || 0);
      setHasMore(data.has_more || false);
      
      // Set cursor for next page (use last comment ID)
      if (data.comments && data.comments.length > 0) {
        const lastComment = data.comments[data.comments.length - 1];
        setCursor(lastComment.id);
      }
    } catch (err) {
      console.error('Error fetching comments:', err);
      setError('Failed to load comments');
    } finally {
      setLoading(false);
    }
  }, [animeId, sortBy, cursor]);

  useEffect(() => {
    setCursor(null);
    fetchComments(true);
  }, [animeId, sortBy]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newComment.trim() || !animeId) return;
    
    setIsSubmitting(true);
    setError('');
    
    try {
      const response = await fetch(`${API_URL}/api/anime/${animeId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: newComment.trim(),
          author_name: username,
        }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        if (response.status === 429) {
          throw new Error(data.detail || 'Please wait a moment before posting');
        }
        throw new Error(data.detail || 'Failed to post comment');
      }
      
      const data = await response.json();
      setComments(prev => [data, ...prev]);
      setTotalComments(prev => prev + 1);
      setNewComment('');
      // Track comment posted
      trackCommentPosted(false);
    } catch (err) {
      setError(err.message || 'Failed to post comment');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVote = async (commentId, voteType) => {
    setVotingCommentId(commentId);
    
    try {
      const response = await fetch(`${API_URL}/api/comments/${commentId}/vote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ vote_type: voteType }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to vote');
      }
      
      const data = await response.json();
      
      // Track vote
      const voteTypeStr = voteType === 1 ? 'up' : voteType === -1 ? 'down' : 'remove';
      trackCommentVoted(voteTypeStr);
      
      // Update comment in state
      const updateCommentVotes = (commentsList) => {
        return commentsList.map(comment => {
          if (comment.id === commentId) {
            return {
              ...comment,
              upvotes: data.upvotes,
              downvotes: data.downvotes,
              score: data.score,
              user_vote: data.user_vote
            };
          }
          if (comment.replies) {
            return {
              ...comment,
              replies: updateCommentVotes(comment.replies)
            };
          }
          return comment;
        });
      };
      
      setComments(prev => updateCommentVotes(prev));
    } catch (err) {
      setError(err.message || 'Failed to vote');
    } finally {
      setVotingCommentId(null);
    }
  };

  const handleReply = async (parentId, content) => {
    try {
      const response = await fetch(`${API_URL}/api/comments/${parentId}/reply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          content,
          author_name: username // Send username for replies too
        }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to post reply');
      }
      
      const data = await response.json();
      
      // Add reply to the correct parent
      const addReplyToParent = (commentsList) => {
        return commentsList.map(comment => {
          if (comment.id === parentId) {
            return {
              ...comment,
              replies: [...(comment.replies || []), data],
              reply_count: comment.reply_count + 1
            };
          }
          if (comment.replies) {
            return {
              ...comment,
              replies: addReplyToParent(comment.replies)
            };
          }
          return comment;
        });
      };
      
      setComments(prev => addReplyToParent(prev));
      setTotalComments(prev => prev + 1);
      // Track reply posted
      trackCommentPosted(true);
    } catch (err) {
      setError(err.message || 'Failed to post reply');
      throw err;
    }
  };

  const handleEdit = async (commentId, content) => {
    try {
      const response = await fetch(`${API_URL}/api/comments/${commentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to edit comment');
      }
      
      const data = await response.json();
      
      // Update comment in state
      const updateComment = (commentsList) => {
        return commentsList.map(comment => {
          if (comment.id === commentId) {
            return { ...comment, ...data };
          }
          if (comment.replies) {
            return {
              ...comment,
              replies: updateComment(comment.replies)
            };
          }
          return comment;
        });
      };
      
      setComments(prev => updateComment(prev));
    } catch (err) {
      setError(err.message || 'Failed to edit comment');
      throw err;
    }
  };

  const handleDelete = async (commentId) => {
    try {
      const response = await fetch(`${API_URL}/api/comments/${commentId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to delete comment');
      }
      
      // Mark as deleted in state
      const markDeleted = (commentsList) => {
        return commentsList.map(comment => {
          if (comment.id === commentId) {
            return {
              ...comment,
              content: '[deleted]',
              author_name: '[deleted]',
              is_deleted: 1
            };
          }
          if (comment.replies) {
            return {
              ...comment,
              replies: markDeleted(comment.replies)
            };
          }
          return comment;
        });
      };
      
      setComments(prev => markDeleted(prev));
      setTotalComments(prev => prev - 1);
    } catch (err) {
      setError(err.message || 'Failed to delete comment');
    }
  };

  const handleToggleCollapse = (commentId, isCollapsed) => {
    const newCollapsed = { ...collapsedThreads, [commentId]: isCollapsed };
    if (!isCollapsed) {
      delete newCollapsed[commentId];
    }
    setCollapsedThreads(newCollapsed);
    saveCollapsedThreads(newCollapsed);
  };

  const handleLoadMore = () => {
    fetchComments(false);
  };

  if (!animeId) return null;

  return (
    <div className="comment-section">
      <div className="comment-section-header">
        <div className="comment-title">
          <MessageSquare className="w-5 h-5" />
          <h3>Comments</h3>
          <span className="comment-count">{totalComments}</span>
        </div>
        
        <div className="comment-sort">
          <button 
            className={sortBy === 'best' ? 'active' : ''} 
            onClick={() => setSortBy('best')}
          >
            Best
          </button>
          <button 
            className={sortBy === 'new' ? 'active' : ''} 
            onClick={() => setSortBy('new')}
          >
            New
          </button>
          <button 
            className={sortBy === 'top' ? 'active' : ''} 
            onClick={() => setSortBy('top')}
          >
            Top
          </button>
        </div>
      </div>

      {/* Comment Form */}
      <form onSubmit={handleSubmit} className="comment-form">
        <div className="comment-form-header">
          <span className="comment-username">{username}</span>
        </div>
        
        <textarea
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="What are your thoughts?"
          maxLength={1000}
          rows={4}
          className="comment-textarea"
          disabled={isSubmitting}
        />
        
        <div className="comment-form-footer">
          <span className="char-count">{newComment.length}/1000</span>
          <button
            type="submit"
            disabled={!newComment.trim() || isSubmitting}
            className="comment-submit-btn"
          >
            {isSubmitting ? 'Posting...' : 'Comment'}
          </button>
        </div>
      </form>

      {/* Error Message */}
      {error && (
        <div className="comment-error">
          {error}
        </div>
      )}

      {/* Comments List */}
      <div className="comments-list">
        {loading && comments.length === 0 ? (
          <div className="comments-loading">Loading comments...</div>
        ) : comments.length === 0 ? (
          <div className="no-comments">
            <MessageSquare className="w-12 h-12" />
            <p>No comments yet</p>
            <p className="text-muted">Be the first to share your thoughts</p>
          </div>
        ) : (
          <>
            {comments.map((comment) => (
              <CommentItem
                key={comment.id}
                comment={comment}
                onVote={handleVote}
                onReply={handleReply}
                onEdit={handleEdit}
                onDelete={handleDelete}
                depth={0}
                collapsedThreads={collapsedThreads}
                onToggleCollapse={handleToggleCollapse}
                currentUsername={username}
              />
            ))}
            
            {hasMore && (
              <button 
                className="load-more-btn" 
                onClick={handleLoadMore}
                disabled={loading}
              >
                {loading ? 'Loading...' : 'Load more comments'}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default CommentSection;
