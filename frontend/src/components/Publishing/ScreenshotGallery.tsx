/**
 * Screenshot Gallery component.
 * Displays screenshots from the publishing process.
 */

import { useState } from 'react';
import { Screenshot } from '@/types/publishing';
import { clsx } from 'clsx';
import { format } from 'date-fns';

export interface ScreenshotGalleryProps {
  screenshots: Screenshot[];
  className?: string;
}

export const ScreenshotGallery: React.FC<ScreenshotGalleryProps> = ({
  screenshots,
  className,
}) => {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  if (screenshots.length === 0) {
    return (
      <div className={clsx('text-center py-8', className)}>
        <svg
          className="w-12 h-12 mx-auto text-gray-400 mb-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <p className="text-gray-500 text-sm">暂无截图</p>
      </div>
    );
  }

  const selectedScreenshot =
    selectedIndex !== null ? screenshots[selectedIndex] : null;

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Gallery Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {screenshots.map((screenshot, index) => (
          <button
            key={screenshot.id}
            type="button"
            onClick={() => setSelectedIndex(index)}
            className={clsx(
              'relative aspect-video rounded-lg overflow-hidden border-2 transition-all',
              'hover:scale-105 hover:shadow-lg',
              selectedIndex === index
                ? 'border-primary-500 ring-2 ring-primary-200'
                : 'border-gray-200'
            )}
          >
            <img
              src={screenshot.url}
              alt={screenshot.description || screenshot.step}
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
              <p className="text-white text-xs font-medium truncate">
                {screenshot.step}
              </p>
            </div>
            <div className="absolute top-2 right-2 bg-black/50 text-white text-xs px-1.5 py-0.5 rounded">
              {index + 1}
            </div>
          </button>
        ))}
      </div>

      {/* Lightbox */}
      {selectedScreenshot && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
          onClick={() => setSelectedIndex(null)}
        >
          <div
            className="relative max-w-6xl w-full"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              type="button"
              onClick={() => setSelectedIndex(null)}
              className="absolute -top-12 right-0 text-white hover:text-gray-300"
            >
              <svg
                className="w-8 h-8"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>

            {/* Image */}
            <img
              src={selectedScreenshot.url}
              alt={selectedScreenshot.description || selectedScreenshot.step}
              className="w-full rounded-lg"
            />

            {/* Info */}
            <div className="mt-4 bg-white/10 backdrop-blur rounded-lg p-4 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold mb-1">
                    {selectedScreenshot.step}
                  </h4>
                  {selectedScreenshot.description && (
                    <p className="text-sm text-gray-300">
                      {selectedScreenshot.description}
                    </p>
                  )}
                </div>
                <div className="text-right text-sm">
                  <p className="text-gray-300">
                    {format(
                      new Date(selectedScreenshot.timestamp),
                      'HH:mm:ss'
                    )}
                  </p>
                  <p className="text-gray-400 text-xs">
                    {selectedIndex! + 1} / {screenshots.length}
                  </p>
                </div>
              </div>
            </div>

            {/* Navigation */}
            <div className="absolute top-1/2 -translate-y-1/2 left-0 right-0 flex justify-between px-4">
              <button
                type="button"
                onClick={() =>
                  setSelectedIndex(Math.max(0, selectedIndex! - 1))
                }
                disabled={selectedIndex === 0}
                className="w-12 h-12 bg-white/20 backdrop-blur rounded-full text-white hover:bg-white/30 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <svg
                  className="w-6 h-6 mx-auto"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </button>
              <button
                type="button"
                onClick={() =>
                  setSelectedIndex(
                    Math.min(screenshots.length - 1, selectedIndex! + 1)
                  )
                }
                disabled={selectedIndex === screenshots.length - 1}
                className="w-12 h-12 bg-white/20 backdrop-blur rounded-full text-white hover:bg-white/30 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <svg
                  className="w-6 h-6 mx-auto"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
