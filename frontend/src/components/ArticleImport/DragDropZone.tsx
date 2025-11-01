/**
 * DragDropZone component for file uploads.
 * Supports drag-and-drop and click to select files.
 */

import { useCallback } from 'react';
import { useDropzone, DropzoneOptions } from 'react-dropzone';
import { clsx } from 'clsx';

export interface DragDropZoneProps {
  onFilesAccepted: (files: File[]) => void;
  acceptedFileTypes?: Record<string, string[]>;
  maxFiles?: number;
  maxSize?: number; // in bytes
  multiple?: boolean;
  className?: string;
  children?: React.ReactNode;
}

export const DragDropZone: React.FC<DragDropZoneProps> = ({
  onFilesAccepted,
  acceptedFileTypes = {
    'text/csv': ['.csv'],
    'application/json': ['.json'],
  },
  maxFiles = 1,
  maxSize = 10 * 1024 * 1024, // 10MB default
  multiple = false,
  className,
  children,
}) => {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      onFilesAccepted(acceptedFiles);
    },
    [onFilesAccepted]
  );

  const dropzoneOptions: DropzoneOptions = {
    onDrop,
    accept: acceptedFileTypes,
    maxFiles,
    maxSize,
    multiple,
  };

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject,
    fileRejections,
  } = useDropzone(dropzoneOptions);

  const getFileTypeLabel = () => {
    const extensions = Object.values(acceptedFileTypes).flat();
    return extensions.join(', ');
  };

  return (
    <div className={clsx('w-full', className)}>
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          isDragActive && !isDragReject && 'border-primary-500 bg-primary-50',
          isDragAccept && 'border-green-500 bg-green-50',
          isDragReject && 'border-red-500 bg-red-50',
          !isDragActive && 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        )}
      >
        <input {...getInputProps()} />

        {children || (
          <div className="flex flex-col items-center gap-3">
            {/* Upload Icon */}
            <svg
              className={clsx(
                'w-12 h-12',
                isDragActive
                  ? isDragReject
                    ? 'text-red-500'
                    : 'text-primary-500'
                  : 'text-gray-400'
              )}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>

            {/* Text */}
            <div>
              {isDragActive ? (
                isDragReject ? (
                  <p className="text-red-600 font-medium">
                    File type not accepted
                  </p>
                ) : (
                  <p className="text-primary-600 font-medium">Drop files here...</p>
                )
              ) : (
                <>
                  <p className="text-gray-700 font-medium">
                    Drag & drop {multiple ? 'files' : 'a file'} here, or click to
                    select
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    Accepted: {getFileTypeLabel()}
                  </p>
                  <p className="text-sm text-gray-500">
                    Max size: {(maxSize / 1024 / 1024).toFixed(0)}MB
                  </p>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Error Messages */}
      {fileRejections.length > 0 && (
        <div className="mt-3 space-y-2">
          {fileRejections.map(({ file, errors }) => (
            <div
              key={file.name}
              className="text-sm text-red-600 bg-red-50 p-2 rounded"
            >
              <p className="font-medium">{file.name}</p>
              <ul className="list-disc list-inside mt-1">
                {errors.map((e) => (
                  <li key={e.code}>{e.message}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
