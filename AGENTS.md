# Repository Guidelines

## Project Structure & Module Organization
The FastAPI backend sits in `backend/src`, with domain logic under `services`, REST routers in `api/routes`, scheduled jobs in `workers`, and Alembic migrations in `backend/migrations`. Targeted backend tests mirror that layout inside `backend/tests`. The React TypeScript client lives in `frontend/src`; feature folders (e.g., `components/ArticleGenerator`) pair UI, hooks, and utilities, while UI tests reside in `frontend/tests`. Deployment assets and specs are at the repo root, including Docker Compose manifests, nginx configs, and the planning docs inside `specs/`.

## Build, Test, and Development Commands
- `docker-compose up -d` boots the full stack; follow with `docker-compose exec backend alembic upgrade head` after schema changes.
- Inside `backend/`, run `poetry install`, then `poetry run uvicorn src.main:app --reload --port 8000` for the API and start Celery with `poetry run celery -A src.workers.celery_app worker` plus the `beat` scheduler in a second shell.
- In `frontend/`, `npm install` sets dependencies, `npm run dev` serves Vite at `:3000`, and `npm run build` prepares production bundles.

## Coding Style & Naming Conventions
Python code uses Black (4-space indents, 100-char lines) and isort (`poetry run black .`, `poetry run isort .`); keep modules snake_case, classes PascalCase, and Celery tasks/action functions verb_noun. Enforce linting with `poetry run ruff check .` and static typing via `poetry run mypy src`. Frontend code relies on ESLint and Prettier (`npm run lint`, `npm run format:check`); name React components PascalCase, hooks `useSomething`, and colocate shared helpers in `frontend/src/utils` using camelCase identifiers.

## Testing Guidelines
Backend tests belong in `backend/tests`, named `test_<feature>.py`, and should exercise both service logic and API handlers; run `poetry run pytest` for quick feedback and review the default coverage report (`--cov=src`) to keep statement coverage ≥90%. Frontend tests live in `frontend/tests` or alongside components as `<Component>.test.tsx`; rely on Testing Library queries by role/text and run `npm run test:coverage` before raising a PR. For async workflows, spin up the Celery worker/beat pair locally to verify task chaining.

## Commit & Pull Request Guidelines
Follow Conventional Commits as used in history (`feat:`, `fix:`, `docs:`); keep subjects imperative, add scope when clarity helps (`feat(scheduler):`), and avoid batching unrelated changes. Each PR should summarize behavioral impact, list automated/manual test results, link specs or issues, and include screenshots or API samples for UI or contract updates. Request reviews from the GitHub teams that own backend/API and frontend/UI surfaces; if CODEOWNERS is not current, flag the change in the shared Slack channel so both domain leads sign off before merge.

## Security & Configuration Tips
Configuration comes from `.env` files copied from `.env.example`; never commit secrets and coordinate rotations with DevOps when updating Anthropic or CMS credentials. For production parity, reuse the compose profiles in `docker-compose.prod.yml` and review nginx hardening rules in `nginx/` before altering ingress. When custom monitoring is added, mirror dashboards under `monitoring/` to keep team observability templates in sync.
