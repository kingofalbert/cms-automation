/**
 * Articles API Integration Tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { articlesAPI } from '../articles';
import { api, apiClient } from '../api-client';
import {
  mockArticle,
  mockArticles,
  createMockAPIResponse,
  createMockPaginatedResponse,
} from '../../test/mockData';

// Mock the api module
vi.mock('../api-client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('Articles API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('list', () => {
    it('should fetch articles with default params', async () => {
      const mockResponse = createMockAPIResponse(createMockPaginatedResponse(mockArticles));
      (api.get as any).mockResolvedValue(mockResponse);

      const result = await articlesAPI.list();

      expect(api.get).toHaveBeenCalledWith('/api/v1/articles', { params: undefined });
      expect(result).toEqual(mockResponse);
    });

    it('should fetch articles with filters', async () => {
      const mockResponse = createMockAPIResponse(createMockPaginatedResponse([mockArticle]));
      (api.get as any).mockResolvedValue(mockResponse);

      const filters = {
        status: 'published' as const,
        page: 2,
        limit: 10,
      };

      const result = await articlesAPI.list(filters);

      expect(api.get).toHaveBeenCalledWith('/api/v1/articles', { params: filters });
      expect(result).toEqual(mockResponse);
    });

    it('should handle API errors', async () => {
      const error = new Error('Network error');
      (api.get as any).mockRejectedValue(error);

      await expect(articlesAPI.list()).rejects.toThrow('Network error');
    });
  });

  describe('get', () => {
    it('should fetch a single article by ID', async () => {
      const mockResponse = createMockAPIResponse(mockArticle);
      (api.get as any).mockResolvedValue(mockResponse);

      const result = await articlesAPI.get(1);

      expect(api.get).toHaveBeenCalledWith('/api/v1/articles/1');
      expect(result).toEqual(mockResponse);
    });

    it('should handle 404 errors', async () => {
      const error = new Error('Article not found');
      (api.get as any).mockRejectedValue(error);

      await expect(articlesAPI.get(999)).rejects.toThrow('Article not found');
    });
  });

  describe('create', () => {
    it('should create a new article', async () => {
      const mockResponse = createMockAPIResponse(mockArticle);
      (api.post as any).mockResolvedValue(mockResponse);

      const newArticle = {
        title: 'New Article',
        content: 'Content',
        source: 'manual_entry' as const,
      };

      const result = await articlesAPI.create(newArticle);

      expect(api.post).toHaveBeenCalledWith('/api/v1/articles', newArticle);
      expect(result).toEqual(mockResponse);
    });

    it('should handle validation errors', async () => {
      const error = new Error('Validation failed');
      (api.post as any).mockRejectedValue(error);

      await expect(articlesAPI.create({ title: '', content: '' } as any)).rejects.toThrow(
        'Validation failed'
      );
    });
  });

  describe('update', () => {
    it('should update an existing article', async () => {
      const mockResponse = createMockAPIResponse({ ...mockArticle, title: 'Updated Title' });
      (api.put as any).mockResolvedValue(mockResponse);

      const updates = { title: 'Updated Title' };
      const result = await articlesAPI.update(1, updates);

      expect(api.put).toHaveBeenCalledWith('/api/v1/articles/1', updates);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('delete', () => {
    it('should delete an article', async () => {
      const mockResponse = createMockAPIResponse(undefined);
      (api.delete as any).mockResolvedValue(mockResponse);

      const result = await articlesAPI.delete(1);

      expect(api.delete).toHaveBeenCalledWith('/api/v1/articles/1');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('importCSV', () => {
    it('should import articles from CSV file', async () => {
      const mockResponse = createMockAPIResponse({
        success: true,
        total: 10,
        imported: 9,
        failed: 1,
        skipped: 0,
        errors: [],
      });
      (api.post as any).mockResolvedValue(mockResponse);

      const file = new File(['csv content'], 'articles.csv', { type: 'text/csv' });
      const result = await articlesAPI.importCSV(file, false);

      expect(api.post).toHaveBeenCalled();
      const call = (api.post as any).mock.calls[0];
      expect(call[0]).toBe('/api/v1/articles/import/csv');
      expect(call[1]).toBeInstanceOf(FormData);
      expect(result).toEqual(mockResponse);
    });

    it('should validate CSV without importing', async () => {
      const mockResponse = createMockAPIResponse({
        success: true,
        total: 10,
        imported: 0,
        failed: 0,
        skipped: 0,
        errors: [],
      });
      (api.post as any).mockResolvedValue(mockResponse);

      const file = new File(['csv content'], 'articles.csv', { type: 'text/csv' });
      const result = await articlesAPI.importCSV(file, true);

      const call = (api.post as any).mock.calls[0];
      const formData = call[1] as FormData;
      expect(formData.get('validate_only')).toBe('true');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('uploadImage', () => {
    it('should upload a featured image', async () => {
      const mockResponse = createMockAPIResponse({ path: '/images/test.jpg' });
      (api.post as any).mockResolvedValue(mockResponse);

      const file = new File(['image data'], 'test.jpg', { type: 'image/jpeg' });
      const result = await articlesAPI.uploadImage(1, file, 'featured');

      expect(api.post).toHaveBeenCalled();
      const call = (api.post as any).mock.calls[0];
      expect(call[0]).toBe('/api/v1/articles/1/images');
      expect(call[1]).toBeInstanceOf(FormData);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('deleteImage', () => {
    it('should delete an image', async () => {
      const mockResponse = createMockAPIResponse(undefined);
      (api.delete as any).mockResolvedValue(mockResponse);

      const result = await articlesAPI.deleteImage(1, '/images/test.jpg');

      expect(api.delete).toHaveBeenCalledWith('/api/v1/articles/1/images', {
        data: { image_path: '/images/test.jpg' },
      });
      expect(result).toEqual(mockResponse);
    });
  });
});
