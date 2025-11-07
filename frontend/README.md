# CMS Automation Frontend

React + TypeScript frontend for the CMS Automation System.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run E2E tests
npx playwright test
```

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Query** - Data fetching and caching
- **React Router** - Routing
- **Tailwind CSS** - Styling
- **Vitest** - Unit testing
- **Playwright** - E2E testing

## Project Structure

```
frontend/
├── src/
│   ├── components/     # React components
│   ├── hooks/          # Custom React hooks
│   ├── pages/          # Page components
│   ├── services/       # API services
│   ├── types/          # TypeScript types
│   └── utils/          # Utility functions
├── e2e/                # Playwright E2E tests
├── docs/               # Documentation
└── public/             # Static assets
```

## Documentation

- **[Testing Best Practices](./docs/TESTING_BEST_PRACTICES.md)** - Essential guide for writing tests
  - Vitest Fake Timers and async operations
  - React Testing Library patterns
  - Playwright E2E testing strategies
  - Common pitfalls and solutions

## Development

### Running Tests

```bash
# Run all unit tests
npm test

# Run tests in watch mode
npm run test:watch

# Run specific test file
npx vitest run src/hooks/__tests__/usePolling.test.ts

# Run E2E tests
npx playwright test

# Run specific E2E test
npx playwright test e2e/worklist-page.spec.ts
```

### Code Quality

```bash
# Type check
npm run type-check

# Lint
npm run lint

# Format code
npm run format
```

## Deployment

The frontend is deployed to Google Cloud Storage and served as a static website.

```bash
# Build for production
npm run build

# Deploy to GCS (requires gcloud CLI)
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-cmsupload-476323/
```

## Testing Guidelines

Before writing tests, please read our [Testing Best Practices](./docs/TESTING_BEST_PRACTICES.md). Key highlights:

- **Fake Timers**: Understand the difference between microtasks and timer ticks
- **Async Operations**: Properly separate `Promise.resolve()` from `vi.advanceTimersByTime()`
- **Common Pitfalls**: Avoid `waitFor()` with fake timers, don't use `runAllTimersAsync()` with intervals

## Contributing

1. Create a new branch for your feature
2. Write tests for your changes
3. Ensure all tests pass: `npm test`
4. Submit a pull request

## Troubleshooting

### Tests failing with "Aborting after running 10000 timers"

See [Testing Best Practices - Fake Timers](./docs/TESTING_BEST_PRACTICES.md#vitest-fake-timers-与异步操作)

### CDN cache issues after deployment

Clear your browser cache or use hard refresh:
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

## License

Proprietary
