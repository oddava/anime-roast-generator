import DOMPurify from 'dompurify';

/**
 * Sanitize HTML content to prevent XSS attacks.
 * Removes all HTML tags and returns plain text.
 * 
 * @param {string} content - The content to sanitize
 * @returns {string} - Sanitized plain text
 */
export const sanitizeContent = (content) => {
  if (!content) return '';
  
  // Configure DOMPurify to remove all HTML tags
  const config = {
    ALLOWED_TAGS: [], // No HTML tags allowed
    ALLOWED_ATTR: [], // No attributes allowed
    KEEP_CONTENT: true, // Keep the text content
  };
  
  return DOMPurify.sanitize(content, config);
};

/**
 * Sanitize content while preserving basic formatting (newlines, etc.)
 * Use this for display where you want to keep line breaks.
 * 
 * @param {string} content - The content to sanitize
 * @returns {string} - Sanitized content with preserved newlines
 */
export const sanitizeContentWithFormatting = (content) => {
  if (!content) return '';
  
  // Replace newlines with a placeholder before sanitization
  const placeholder = '\n';
  const contentWithPlaceholders = content.replace(/\n/g, placeholder);
  
  // Sanitize
  const sanitized = sanitizeContent(contentWithPlaceholders);
  
  // Restore newlines
  return sanitized.replace(new RegExp(placeholder, 'g'), '\n');
};
