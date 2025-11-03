/**
 * LazyImage Component
 *
 * Lazy loads images using Intersection Observer API
 * Provides loading placeholder and error fallback
 */

import React, { useState, useEffect, useRef } from 'react';
import { clsx } from 'clsx';

export interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
  /** Placeholder image URL while loading */
  placeholder?: string;
  /** Error fallback image URL */
  fallback?: string;
  /** Custom loading component */
  loadingComponent?: React.ReactNode;
  /** Custom error component */
  errorComponent?: React.ReactNode;
  /** Intersection observer root margin */
  rootMargin?: string;
  /** Intersection observer threshold */
  threshold?: number;
  /** Callback when image loads successfully */
  onLoad?: () => void;
  /** Callback when image fails to load */
  onError?: () => void;
}

export const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  placeholder,
  fallback = '/images/placeholder.jpg',
  loadingComponent,
  errorComponent,
  rootMargin = '50px',
  threshold = 0.01,
  className,
  onLoad,
  onError,
  ...props
}) => {
  const [imageSrc, setImageSrc] = useState<string | undefined>(placeholder);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    // Return early if browser doesn't support IntersectionObserver
    if (!('IntersectionObserver' in window)) {
      setImageSrc(src);
      return;
    }

    // Create intersection observer
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // Start loading the image
            loadImage();
            // Stop observing once we've started loading
            if (observerRef.current && imgRef.current) {
              observerRef.current.unobserve(imgRef.current);
            }
          }
        });
      },
      {
        rootMargin,
        threshold,
      }
    );

    // Start observing
    if (imgRef.current) {
      observerRef.current.observe(imgRef.current);
    }

    // Cleanup
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [src, rootMargin, threshold]);

  const loadImage = () => {
    const img = new Image();

    img.onload = () => {
      setImageSrc(src);
      setIsLoading(false);
      setHasError(false);
      onLoad?.();
    };

    img.onerror = () => {
      setImageSrc(fallback);
      setIsLoading(false);
      setHasError(true);
      onError?.();
    };

    img.src = src;
  };

  // Show loading state
  if (isLoading && !imageSrc) {
    if (loadingComponent) {
      return <>{loadingComponent}</>;
    }
    return (
      <div
        className={clsx(
          'flex items-center justify-center bg-gray-100',
          className
        )}
        role="status"
        aria-label="Loading image"
      >
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
      </div>
    );
  }

  // Show error state
  if (hasError && errorComponent) {
    return <>{errorComponent}</>;
  }

  return (
    <img
      ref={imgRef}
      src={imageSrc}
      alt={alt}
      className={clsx(
        'transition-opacity duration-300',
        isLoading ? 'opacity-50' : 'opacity-100',
        className
      )}
      loading="lazy"
      {...props}
    />
  );
};

export default React.memo(LazyImage);
