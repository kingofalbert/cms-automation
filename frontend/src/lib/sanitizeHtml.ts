/**
 * HTML Sanitization utility
 *
 * Provides safe HTML rendering by sanitizing potentially dangerous HTML content.
 */

import DOMPurify from 'dompurify';

/**
 * Extended options for HTML sanitization.
 */
export interface SanitizeOptions {
  /** Remove style tags and inline styles */
  removeStyles?: boolean;
  /** Remove script tags (always true for security) */
  removeScripts?: boolean;
  /** Remove CSS text from the content */
  removeCssText?: boolean;
  /** Convert HTML to plain text */
  convertToText?: boolean;
}

/**
 * Default DOMPurify configuration for safe HTML rendering.
 */
const defaultConfig: DOMPurify.Config = {
  // Allow safe HTML tags
  ALLOWED_TAGS: [
    'p', 'br', 'b', 'i', 'em', 'strong', 'u', 's', 'strike',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'blockquote', 'pre', 'code',
    'a', 'img', 'figure', 'figcaption',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'span', 'div', 'hr', 'mark',
  ],
  // Allow safe attributes
  ALLOWED_ATTR: [
    'href', 'src', 'alt', 'title', 'class', 'id',
    'target', 'rel',
    'width', 'height',
    'style', 'data-issue-id', 'data-severity',
  ],
  // Add target="_blank" rel="noopener" to all links
  ADD_ATTR: ['target'],
  // Forbid dangerous patterns
  FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'form', 'input'],
  FORBID_ATTR: ['onerror', 'onclick', 'onload', 'onmouseover'],
};

/**
 * Remove CSS/style content from HTML string.
 */
function removeCssContent(html: string): string {
  // Remove <style> tags and their content
  let result = html.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
  // Remove inline style attributes
  result = result.replace(/\s*style="[^"]*"/gi, '');
  result = result.replace(/\s*style='[^']*'/gi, '');
  return result;
}

/**
 * Sanitize HTML content to prevent XSS attacks.
 *
 * @param html - Raw HTML string to sanitize
 * @param options - Optional sanitization options
 * @returns Sanitized HTML string safe for rendering
 */
export function sanitizeHtml(html: string, options?: SanitizeOptions): string {
  if (!html) {
    return '';
  }

  let result = html;

  // Pre-processing: remove styles if requested
  if (options?.removeStyles || options?.removeCssText) {
    result = removeCssContent(result);
  }

  // Build DOMPurify config
  const forbidTags = options?.removeStyles
    ? [...(defaultConfig.FORBID_TAGS || []), 'style']
    : defaultConfig.FORBID_TAGS;

  const allowedAttr = options?.removeStyles
    ? (defaultConfig.ALLOWED_ATTR || []).filter(attr => attr !== 'style')
    : defaultConfig.ALLOWED_ATTR;

  // Sanitize with DOMPurify
  result = DOMPurify.sanitize(result, {
    ALLOWED_TAGS: defaultConfig.ALLOWED_TAGS,
    ALLOWED_ATTR: allowedAttr,
    ADD_ATTR: defaultConfig.ADD_ATTR,
    FORBID_TAGS: forbidTags,
    FORBID_ATTR: defaultConfig.FORBID_ATTR,
  });

  return result;
}

/**
 * Alias for sanitizeHtml for backward compatibility.
 * Used by ProofreadingArticleContent.
 */
export const sanitizeHtmlContent = sanitizeHtml;

/**
 * Create safe HTML props for React dangerouslySetInnerHTML
 *
 * @param html - Raw HTML string
 * @param options - Optional sanitization options
 * @returns Object suitable for dangerouslySetInnerHTML prop
 */
export function createSafeHtml(
  html: string,
  options?: SanitizeOptions
): { __html: string } {
  return {
    __html: sanitizeHtml(html, options),
  };
}

export default sanitizeHtml;
