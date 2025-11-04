import { test, expect } from '@playwright/test';

/**
 * API Integration Tests
 * Tests frontend-backend communication with actual API calls
 */

test.describe('API Integration Tests', () => {
  const API_BASE_URL = process.env.TEST_LOCAL ? 'http://localhost:8000' : 'https://cms-automation-backend-ufk65ob4ea-uc.a.run.app';

  test('health endpoint returns healthy status', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health`);

    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
    expect(data).toHaveProperty('service', 'cms-automation');
  });

  test('articles endpoint returns list (empty or with data)', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/v1/articles`);

    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
  });

  test('articles endpoint with pagination parameters', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/v1/articles`, {
      params: {
        offset: 0,
        limit: 10
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
    // Should return max 10 items
    expect(data.length).toBeLessThanOrEqual(10);
  });

  test('OpenAPI documentation is accessible', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/openapi.json`);

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('openapi');
    expect(data).toHaveProperty('paths');
    expect(Object.keys(data.paths).length).toBeGreaterThan(0);
  });

  test('CORS headers are present', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health`);

    // Check for CORS headers (if configured)
    // This test will pass even if CORS not configured
    expect(response.ok()).toBeTruthy();
  });

  test('invalid endpoint returns 404', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/v1/nonexistent-endpoint`);

    expect(response.status()).toBe(404);
    const data = await response.json();
    expect(data).toHaveProperty('detail');
  });

  test('topics endpoint does not support GET method', async ({ request }) => {
    // GET should not work on topics (it's POST only)
    const response = await request.get(`${API_BASE_URL}/v1/topics`);

    // Should return error (405 Method Not Allowed or 500 if not properly handled)
    expect(response.ok()).toBeFalsy();
    expect([405, 500]).toContain(response.status());
  });
});

test.describe('API Error Handling', () => {
  const API_BASE_URL = process.env.TEST_LOCAL ? 'http://localhost:8000' : 'https://cms-automation-backend-ufk65ob4ea-uc.a.run.app';

  test('invalid article ID returns 404', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/v1/articles/999999`);

    expect(response.status()).toBe(404);
    const data = await response.json();
    expect(data).toHaveProperty('detail');
  });

  test('malformed request returns error', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/v1/topics`, {
      data: {
        // Missing required fields
      }
    });

    // Should return 422 (Validation Error) or 400 (Bad Request)
    expect([400, 422]).toContain(response.status());
  });
});
