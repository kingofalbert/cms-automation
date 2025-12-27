/**
 * Proofreading Position Utilities
 * Spec 014: Proofreading Position Accuracy Improvement
 *
 * This module provides utilities for handling proofreading issue positions
 * in the frontend. It supports both the new plain_text_position field and
 * falls back to text search for backward compatibility.
 */

import { ProofreadingIssue, PlainTextPosition } from '@/types/worklist';

/**
 * Result of position resolution
 */
export interface PositionResult {
  start: number;
  end: number;
  /** Source of the position: 'plain_text_position', 'text_search', or 'not_found' */
  source: 'plain_text_position' | 'text_search' | 'not_found';
  /** Whether the position was validated successfully */
  validated: boolean;
}

/**
 * Options for getIssuePosition
 */
export interface GetIssuePositionOptions {
  /** Starting position for text search (for sequential issues) */
  searchStartFrom?: number;
  /** Enable strict validation (reject positions that don't match expected text) */
  strictValidation?: boolean;
}

/**
 * Strip HTML tags from text for plain text display.
 * This is a frontend version that uses DOMParser.
 */
export function stripHtmlTags(html: string | undefined | null): string {
  if (!html) return '';
  // Step 1: Use DOMParser to strip actual HTML tags and decode entities
  const doc = new DOMParser().parseFromString(html, 'text/html');
  let text = doc.body.textContent || '';
  // Step 2: Remove any remaining HTML-like tags (encoded as entities)
  text = text.replace(/<[^>]*>/g, '');
  // Step 3: Clean up URLs that might leak through
  text = text.replace(/https?:\/\/[^\s<>]*/g, '');
  // Step 4: Normalize whitespace
  text = text.replace(/\s+/g, ' ').trim();
  return text;
}

/**
 * Validate that a position points to the expected text in the content.
 *
 * @param content - The full plain text content
 * @param position - The position to validate
 * @param expectedText - The text expected at this position
 * @param tolerance - Allow whitespace differences (default: 0)
 * @returns true if the position is valid
 */
export function validatePosition(
  content: string,
  position: PlainTextPosition,
  expectedText: string,
  tolerance: number = 0
): boolean {
  if (position.start < 0 || position.end > content.length) {
    return false;
  }
  if (position.start >= position.end) {
    return false;
  }

  const extracted = content.slice(position.start, position.end);

  if (tolerance === 0) {
    return extracted === expectedText;
  }

  // With tolerance, compare normalized versions (collapse whitespace)
  const normalizedExtracted = extracted.replace(/\s+/g, ' ').trim();
  const normalizedExpected = expectedText.replace(/\s+/g, ' ').trim();

  return normalizedExtracted === normalizedExpected;
}

/**
 * Find text position in plain content using text search.
 * This is the fallback mechanism when plain_text_position is not available.
 *
 * @param plainContent - The plain text content to search in
 * @param searchText - The text to find
 * @param startFrom - Position to start searching from (for sequential issues)
 * @returns Position if found, null if not found
 */
export function findTextPosition(
  plainContent: string,
  searchText: string,
  startFrom: number = 0
): PlainTextPosition | null {
  if (!searchText) {
    return null;
  }

  // Try from startFrom position first
  let index = plainContent.indexOf(searchText, startFrom);

  // If not found, try from beginning (for out-of-order issues)
  if (index === -1 && startFrom > 0) {
    index = plainContent.indexOf(searchText);
  }

  if (index === -1) {
    return null;
  }

  return { start: index, end: index + searchText.length };
}

/**
 * Get the position of an issue within the article content.
 *
 * This function implements the Spec 014 position resolution algorithm:
 * 1. First try to use plain_text_position from the issue (if available)
 * 2. Validate the position against the expected text
 * 3. If invalid or not available, fall back to text search
 *
 * @param issue - The proofreading issue
 * @param plainContent - The plain text article content
 * @param options - Optional configuration
 * @returns PositionResult with start/end and metadata about resolution
 */
export function getIssuePosition(
  issue: ProofreadingIssue,
  plainContent: string,
  options: GetIssuePositionOptions = {}
): PositionResult {
  const { searchStartFrom = 0, strictValidation = false } = options;

  // Get the plain text version of the original text
  // Prefer the pre-computed plain text from backend (Spec 014)
  const originalTextPlain = issue.original_text_plain || stripHtmlTags(issue.original_text);

  if (!originalTextPlain) {
    return {
      start: -1,
      end: -1,
      source: 'not_found',
      validated: false,
    };
  }

  // Strategy 1: Use plain_text_position if available (Spec 014)
  if (issue.plain_text_position) {
    const position = issue.plain_text_position;

    // Validate the position
    const isValid = validatePosition(plainContent, position, originalTextPlain, 1);

    if (isValid) {
      return {
        start: position.start,
        end: position.end,
        source: 'plain_text_position',
        validated: true,
      };
    }

    // If strict validation is enabled and position is invalid, fail
    if (strictValidation) {
      return {
        start: -1,
        end: -1,
        source: 'not_found',
        validated: false,
      };
    }

    // Position exists but is invalid - fall through to text search
    console.warn(
      `[Spec014] Position validation failed for issue ${issue.id}. ` +
        `Position: ${position.start}-${position.end}, ` +
        `Expected: "${originalTextPlain.substring(0, 20)}..."`
    );
  }

  // Strategy 2: Fall back to text search
  const foundPosition = findTextPosition(plainContent, originalTextPlain, searchStartFrom);

  if (foundPosition) {
    return {
      start: foundPosition.start,
      end: foundPosition.end,
      source: 'text_search',
      validated: true,
    };
  }

  // Could not find the issue text in the content
  return {
    start: -1,
    end: -1,
    source: 'not_found',
    validated: false,
  };
}

/**
 * Process all issues and resolve their positions in the content.
 * Returns issues with resolved positions, sorted by start position.
 *
 * @param issues - List of proofreading issues
 * @param plainContent - The plain text article content
 * @returns Array of issues with resolved positions (excluding not found)
 */
export function resolveAllIssuePositions(
  issues: ProofreadingIssue[],
  plainContent: string
): Array<{ issue: ProofreadingIssue; position: PositionResult }> {
  const results: Array<{ issue: ProofreadingIssue; position: PositionResult }> = [];
  let searchStartIndex = 0;

  // Process issues in order
  issues.forEach((issue) => {
    const position = getIssuePosition(issue, plainContent, {
      searchStartFrom: searchStartIndex,
    });

    if (position.source !== 'not_found') {
      results.push({ issue, position });
      // Update search start for next issue (sequential processing)
      searchStartIndex = position.end;
    }
  });

  // Sort by start position
  results.sort((a, b) => a.position.start - b.position.start);

  return results;
}

/**
 * Remove overlapping ranges from a list of issue positions.
 * Keeps the first occurrence when ranges overlap.
 *
 * @param positions - Sorted array of issue positions
 * @returns Non-overlapping positions
 */
export function removeOverlappingRanges(
  positions: Array<{ issue: ProofreadingIssue; position: PositionResult }>
): Array<{ issue: ProofreadingIssue; position: PositionResult }> {
  const result: Array<{ issue: ProofreadingIssue; position: PositionResult }> = [];
  let lastEnd = 0;

  positions.forEach((item) => {
    if (item.position.start >= lastEnd) {
      result.push(item);
      lastEnd = item.position.end;
    }
  });

  return result;
}
