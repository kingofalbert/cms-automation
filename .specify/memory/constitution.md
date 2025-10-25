<!--
Sync Impact Report - Constitution v1.0.0
═══════════════════════════════════════════════════════════════════════

VERSION CHANGE: Template → 1.0.0 (MAJOR - Initial ratification)

MODIFICATIONS:
- Initial constitution ratified with 5 core engineering principles
- Added modularity principle for component separation
- Added observability principle for structured logging and monitoring
- Added security principle for authentication and data protection
- Added testability principle (non-negotiable) for TDD workflows
- Added API-first design principle for contract-driven development

NEW SECTIONS:
- Core Principles: 5 principles defined (Modularity, Observability, Security, Testability, API-First Design)
- Quality Standards: Performance, reliability, and architectural requirements
- Development Workflow: Test-driven development, code review, and deployment gates
- Governance: Amendment procedures and compliance verification

TEMPLATE SYNC STATUS:
✅ plan-template.md - Constitution Check section aligns with principles
✅ spec-template.md - User story and acceptance criteria format supports testability
✅ tasks-template.md - Task organization supports modularity and parallel execution
✅ README.md - Architecture section reflects modularity and API-first design

FOLLOW-UP ACTIONS:
- None - All templates aligned with constitution principles
- Next phase: Review against actual implementation tasks

Generated: 2025-10-25
-->

# AI-Powered CMS Automation Constitution

## Core Principles

### I. Modularity

**Services MUST be independently deployable and replaceable.** Each service (article generator, content analyzer, scheduler, CMS adapter, workflow manager) operates as a self-contained module with:

- Clear boundaries: Services communicate via defined interfaces (API contracts, message queues)
- Single responsibility: Each service owns one domain capability
- Dependency inversion: Services depend on abstractions (base classes, protocols) not concrete implementations
- Independent testing: Each module has comprehensive unit and integration tests that run in isolation

**Rationale**: Modularity enables parallel development, simplifies debugging, supports gradual migration, and allows targeted scaling of individual components.

### II. Observability

**All automation operations MUST produce structured, traceable logs.** Observability is achieved through:

- **Structured logging**: JSON format with correlation IDs linking requests across services
- **Performance metrics**: Track generation time (p50, p95, p99), API latency, queue depth, error rates
- **Audit trails**: Log all state changes (article creation, status transitions, approvals, publications)
- **Health checks**: Expose service health endpoints reporting dependency status (database, Redis, Claude API, CMS)

**Mandatory log fields**: `timestamp`, `level`, `service`, `correlation_id`, `user_id` (when applicable), `event_type`, `metadata`

**Rationale**: Structured observability enables root cause analysis, SLA verification, security auditing, and proactive incident detection.

### III. Security

**Authentication, authorization, and data protection are NON-NEGOTIABLE.** Security requirements:

- **Authentication**: All API endpoints MUST validate bearer tokens or session credentials
- **Authorization**: Role-based access control (RBAC) enforced at service boundaries (content manager, reviewer, admin)
- **Input validation**: Pydantic schemas MUST validate and sanitize all user inputs (XSS, SQL injection prevention)
- **Secret management**: API keys, database credentials, and tokens MUST be stored in environment variables or secret vaults (never committed to source control)
- **Audit logging**: Security events (login attempts, permission denials, data access) MUST be logged with tamper-proof timestamps

**Rationale**: CMS automation handles proprietary content and user credentials; security breaches risk data leaks, unauthorized publications, and compliance violations.

### IV. Testability (NON-NEGOTIABLE)

**Test-Driven Development (TDD) is MANDATORY for all user stories.** The development cycle MUST follow:

1. **Red**: Write tests for acceptance criteria → Tests FAIL (feature not implemented)
2. **Green**: Implement minimal code to pass tests
3. **Refactor**: Improve code quality while maintaining test coverage
4. **Review**: User approves tests and implementation before merge

**Test requirements**:

- **Contract tests**: Verify API endpoints match OpenAPI specifications (request/response schemas, status codes)
- **Integration tests**: Validate end-to-end user journeys (topic submission → article generation → publication)
- **Unit tests**: Test service logic in isolation with mocked dependencies
- **Coverage threshold**: Minimum 80% code coverage for services and API routes

**Test organization**: Tests MUST be grouped by user story to enable independent validation of each feature.

**Rationale**: TDD prevents regression bugs, ensures acceptance criteria are met, enables safe refactoring, and provides living documentation of feature behavior.

### V. API-First Design

**All features MUST be accessible via well-documented REST APIs.** API design principles:

- **OpenAPI specification**: Define contracts BEFORE implementation in `contracts/api-spec.yaml`
- **RESTful conventions**: Use standard HTTP methods (GET, POST, PATCH, DELETE) with appropriate status codes (200, 201, 400, 401, 404, 500)
- **Versioning**: API routes include version prefix (`/v1/`, `/v2/`) to support backward compatibility
- **Pagination**: List endpoints MUST support `limit`, `offset`, and return `total_count` metadata
- **Error format**: Consistent error responses with `error_code`, `message`, `details` fields
- **Documentation**: Interactive API docs auto-generated via FastAPI `/docs` endpoint

**Rationale**: API-first design enables frontend-backend parallel development, supports third-party integrations, facilitates automated testing, and ensures consistent behavior across clients.

## Quality Standards

### Performance Requirements

- **Article generation**: 95th percentile latency < 5 minutes (tracked via Celery task duration)
- **API response time**: < 500ms for non-generation endpoints (measured at p95)
- **Concurrent capacity**: Support 50+ simultaneous article generation requests without degradation
- **Database queries**: Optimize for < 100ms query time via indexes on `articles.status`, `schedules.scheduled_time`, `tags.name`

### Reliability Requirements

- **System uptime**: 99.5% availability during business hours (tracked via health check monitoring)
- **Scheduled publishing accuracy**: 99% of articles publish within ±1 minute of scheduled time
- **Error handling**: All Celery tasks implement retry logic with exponential backoff (max 3 retries, 2x multiplier)
- **Data integrity**: Zero data loss during article processing (transactions for multi-step operations)

### Architectural Constraints

- **Database**: PostgreSQL with pgvector extension for semantic similarity (embeddings deferred to Phase 4)
- **Task queue**: Celery + Redis for asynchronous article generation and scheduled publishing
- **CMS adapter pattern**: Abstract base class `CMSAdapter` with WordPress implementation; extensible to Strapi, Ghost, etc.
- **Docker deployment**: All services containerized with Docker Compose for consistent development/production environments

## Development Workflow

### Test-Driven Development

1. **Before coding**: Write tests for user story acceptance criteria in `tests/integration/test_<story>.py`
2. **Verify failure**: Run tests to confirm they FAIL (red phase)
3. **Implement**: Write minimal code to pass tests (green phase)
4. **Refactor**: Improve code quality, remove duplication, optimize performance
5. **User approval**: Submit tests + implementation for review; user MUST approve before merge

### Code Review Requirements

- **Peer review**: All pull requests require approval from at least one team member
- **Constitution compliance**: Reviewer MUST verify adherence to modularity, security, testability, and API-first principles
- **Test coverage**: Automated CI checks MUST confirm ≥80% coverage before merge
- **Linting**: Code MUST pass ruff, mypy (backend) and eslint, prettier (frontend) checks

### Deployment Gates

- **Pre-deployment checklist**:
  - ✅ All tests pass (unit, integration, contract)
  - ✅ Database migrations tested in staging environment
  - ✅ OpenAPI spec matches implemented endpoints
  - ✅ Structured logs include correlation IDs
  - ✅ Environment variables documented in `.env.example`
- **Rollback procedure**: All deployments MUST support one-click rollback to previous version
- **Zero-downtime**: Use blue-green deployment or rolling updates for production releases

## Governance

### Amendment Procedure

**Constitution updates require formal approval.** To amend principles or standards:

1. **Proposal**: Document change rationale, impact on existing features, migration plan
2. **Review**: Team discusses proposal, identifies affected code/tests, estimates effort
3. **Approval**: Constitution changes require consensus (all core team members agree)
4. **Version bump**: Increment version according to semantic versioning (MAJOR for breaking changes, MINOR for additions, PATCH for clarifications)
5. **Propagation**: Update dependent templates (plan, spec, tasks), document in Sync Impact Report

### Compliance Verification

- **All pull requests MUST confirm constitution compliance** in review checklist
- **Constitution violations require justification**: Document in `plan.md` Complexity Tracking table (e.g., "Why 4th service needed when 3 projects limit exists?")
- **Quarterly audits**: Review codebase for drift from principles, update documentation as needed

### Principle Priority

**When conflicts arise between principles, apply this priority order:**

1. **Security** (NON-NEGOTIABLE) - No exceptions for authentication, authorization, or data protection
2. **Testability** (NON-NEGOTIABLE) - TDD workflow cannot be skipped
3. **API-First Design** - Contracts define behavior, implementation follows
4. **Modularity** - Services remain independently deployable
5. **Observability** - Structured logging and metrics track operations

**Version**: 1.0.0 | **Ratified**: 2025-10-25 | **Last Amended**: 2025-10-25
