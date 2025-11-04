# Tasks: UI Modernization & Design System

**Feature**: 002-ui-modernization
**Version**: 1.0.0
**Created**: 2025-11-04
**Status**: Ready for Implementation
**Related Documents**: [spec.md](./spec.md) | [plan.md](./plan.md) | [research.md](./research.md)

---

## Task Format Legend

```
- [ ] T### [P] [US#] Description with exact file path
```

**Components**:
- `- [ ]` Checkbox for task completion
- `T###` Sequential task ID (T001, T002, etc.)
- `[P]` Parallelizable marker (ONLY if no blocking dependencies)
- `[US#]` User story label ([US1], [US2], etc.) - OMIT for setup/foundational/polish tasks
- Description with exact file path to modified/created file

---

## Summary

**Total Estimated Duration**: 13 days (2.6 weeks)
**Total Tasks**: 86 tasks across 8 phases
**Priority Breakdown**:
- P0 (Critical): 15 tasks - Navigation fix (Days 1-2)
- P1 (High): 38 tasks - Settings enhancement + Design system (Days 3-10)
- P2 (Medium): 20 tasks - Responsive design + Performance (Days 11-13)
- Setup/Polish: 13 tasks

**Success Criteria**:
- Navigation text displays on single line (no wrapping)
- Settings page has loading skeletons, toast notifications, form validation
- 10+ reusable design system components created
- Mobile/tablet responsive layouts functional
- Bundle size <500KB gzipped (30% reduction achieved)

---

## Phase 1: Project Setup (Day 0.5)

**Goal**: Install dependencies, create directory structure, configure build tools

**No [US#] labels in this phase**

- [ ] T001 [P] Install Sonner toast library in frontend/package.json
- [ ] T002 [P] Create design system directory structure at frontend/src/components/ui/
- [ ] T003 [P] Create hooks directory at frontend/src/hooks/
- [ ] T004 [P] Create schemas directory at frontend/src/schemas/
- [ ] T005 [P] Install rollup-plugin-visualizer for bundle analysis in frontend/package.json
- [ ] T006 Update Vite config with bundle analysis plugin at frontend/vite.config.ts
- [ ] T007 Add scrollbar-hide utility to Tailwind config at frontend/tailwind.config.js
- [ ] T008 Create barrel export file at frontend/src/components/ui/index.ts

---

## Phase 2: Foundational Components (Days 0.5-1)

**Goal**: Create utility functions and base hooks needed by multiple user stories

**No [US#] labels in this phase**

- [ ] T009 [P] Create cn utility function for Tailwind class merging at frontend/src/lib/cn.ts
- [ ] T010 [P] Create useMediaQuery hook at frontend/src/hooks/useMediaQuery.ts
- [ ] T011 [P] Create useToast custom hook wrapper at frontend/src/hooks/useToast.ts
- [ ] T012 [P] Create useUnsavedChanges hook at frontend/src/hooks/useUnsavedChanges.ts
- [ ] T013 Add Toaster component to App root at frontend/src/App.tsx

---

## Phase 3: US1 - Navigation Fix (P0) (Days 1-2)

**Goal**: Fix navigation text wrapping and add responsive hamburger menu

**Priority**: P0 - Critical path item
**User Story**: US1 - Navigation Menu Fix
**Estimated Duration**: 2 days

### 3.1 Desktop Navigation Fix

- [ ] T014 [US1] Fix navigation CSS text wrapping issue at frontend/src/components/layout/Navigation.tsx
- [ ] T015 [US1] Add flex-nowrap and whitespace-nowrap classes to navigation menu items at frontend/src/components/layout/Navigation.tsx
- [ ] T016 [US1] Add overflow-x-auto and scrollbar-hide to navigation container at frontend/src/components/layout/Navigation.tsx
- [ ] T017 [US1] Test navigation at 1920px viewport width (verify no wrapping)
- [ ] T018 [US1] Test navigation at 1440px viewport width (verify no wrapping)
- [ ] T019 [US1] Test navigation at 1280px viewport width (verify no wrapping)

### 3.2 Mobile Responsive Menu

- [ ] T020 [US1] Create MobileMenu drawer component at frontend/src/components/layout/MobileMenu.tsx
- [ ] T021 [US1] Implement slide-in animation (300ms, from right) in MobileMenu component at frontend/src/components/layout/MobileMenu.tsx
- [ ] T022 [US1] Add backdrop overlay with click-to-close in MobileMenu at frontend/src/components/layout/MobileMenu.tsx
- [ ] T023 [US1] Implement Escape key handler for mobile menu at frontend/src/components/layout/MobileMenu.tsx
- [ ] T024 [US1] Add focus trap for accessibility in MobileMenu at frontend/src/components/layout/MobileMenu.tsx
- [ ] T025 [US1] Integrate useMediaQuery hook in Navigation component at frontend/src/components/layout/Navigation.tsx
- [ ] T026 [US1] Add hamburger icon button for mobile (<768px) at frontend/src/components/layout/Navigation.tsx
- [ ] T027 [US1] Conditionally render desktop nav (>=768px) vs mobile menu at frontend/src/components/layout/Navigation.tsx

### 3.3 E2E Testing

- [ ] T028 [US1] Create navigation E2E test file at frontend/e2e/navigation.spec.ts
- [ ] T029 [US1] Write test for no text wrapping at 1920px viewport at frontend/e2e/navigation.spec.ts
- [ ] T030 [US1] Write test for no text wrapping at 1440px viewport at frontend/e2e/navigation.spec.ts
- [ ] T031 [US1] Write test for no text wrapping at 1280px viewport at frontend/e2e/navigation.spec.ts
- [ ] T032 [US1] Write test for mobile menu appearance at <768px at frontend/e2e/navigation.spec.ts
- [ ] T033 [US1] Write test for hamburger menu click interaction at frontend/e2e/navigation.spec.ts
- [ ] T034 [US1] Write test for keyboard navigation (Tab, Enter) at frontend/e2e/navigation.spec.ts

---

## Phase 4: US2 - Settings Enhancement (P1) (Days 3-6)

**Goal**: Polish Settings page with loading states, validation, and notifications

**Priority**: P1 - High priority
**User Story**: US2 - Settings Page Enhancement
**Estimated Duration**: 4 days

### 4.1 Skeleton Loading States

- [ ] T035 [P] [US2] Create base Skeleton component at frontend/src/components/ui/Skeleton.tsx
- [ ] T036 [P] [US2] Create SkeletonCard composed component at frontend/src/components/ui/Skeleton.tsx
- [ ] T037 [P] [US2] Create SkeletonSettingsSection composed component at frontend/src/components/ui/Skeleton.tsx
- [ ] T038 [US2] Replace loading spinner with skeleton in SettingsPage at frontend/src/pages/SettingsPageModern.tsx
- [ ] T039 [US2] Add skeleton for accordion headers (4 placeholders) at frontend/src/pages/SettingsPageModern.tsx
- [ ] T040 [US2] Add skeleton for form fields within sections at frontend/src/pages/SettingsPageModern.tsx

### 4.2 Toast Notifications Integration

- [ ] T041 [US2] Replace alert() calls with toast.success() in SettingsPage at frontend/src/pages/SettingsPageModern.tsx
- [ ] T042 [US2] Add toast.error() for save failure with retry action at frontend/src/pages/SettingsPageModern.tsx
- [ ] T043 [US2] Implement toast.promise() for save operation loading state at frontend/src/pages/SettingsPageModern.tsx
- [ ] T044 [US2] Configure toast duration to 5000ms (5 seconds) at frontend/src/App.tsx

### 4.3 Form Validation

- [ ] T045 [P] [US2] Create Zod validation schema for Settings form at frontend/src/schemas/settings-schema.ts
- [ ] T046 [P] [US2] Define providerConfigSchema with API key validation at frontend/src/schemas/settings-schema.ts
- [ ] T047 [P] [US2] Define cmsConfigSchema with URL validation at frontend/src/schemas/settings-schema.ts
- [ ] T048 [P] [US2] Define costLimitsSchema with min/max constraints at frontend/src/schemas/settings-schema.ts
- [ ] T049 [P] [US2] Define screenshotRetentionSchema with range validation at frontend/src/schemas/settings-schema.ts
- [ ] T050 [US2] Integrate React Hook Form with zodResolver in SettingsPage at frontend/src/pages/SettingsPageModern.tsx
- [ ] T051 [US2] Display validation errors below form fields at frontend/src/pages/SettingsPageModern.tsx
- [ ] T052 [US2] Add red border highlight for invalid fields at frontend/src/pages/SettingsPageModern.tsx
- [ ] T053 [US2] Implement real-time validation on blur event at frontend/src/pages/SettingsPageModern.tsx

### 4.4 Save Button Enhancement

- [ ] T054 [US2] Add loading spinner to Save button during submission at frontend/src/pages/SettingsPageModern.tsx
- [ ] T055 [US2] Change button text to "Saving..." during operation at frontend/src/pages/SettingsPageModern.tsx
- [ ] T056 [US2] Disable Save button while submitting at frontend/src/pages/SettingsPageModern.tsx

### 4.5 Unsaved Changes Detection

- [ ] T057 [US2] Integrate useUnsavedChanges hook with form isDirty state at frontend/src/pages/SettingsPageModern.tsx
- [ ] T058 [US2] Display unsaved changes warning banner at frontend/src/pages/SettingsPageModern.tsx
- [ ] T059 [US2] Implement beforeunload browser warning at frontend/src/hooks/useUnsavedChanges.ts

### 4.6 Accordion Animation Polish

- [ ] T060 [US2] Ensure accordion sections animate with 300ms transition at frontend/src/pages/SettingsPageModern.tsx
- [ ] T061 [US2] Add chevron icon rotation (180deg) animation at frontend/src/pages/SettingsPageModern.tsx
- [ ] T062 [US2] Verify smooth height transition (no instant expand/collapse) at frontend/src/pages/SettingsPageModern.tsx

### 4.7 E2E Testing

- [ ] T063 [US2] Create Settings page E2E test file at frontend/e2e/settings.spec.ts
- [ ] T064 [US2] Write test for skeleton loading display at frontend/e2e/settings.spec.ts
- [ ] T065 [US2] Write test for validation error display at frontend/e2e/settings.spec.ts
- [ ] T066 [US2] Write test for successful save with toast notification at frontend/e2e/settings.spec.ts
- [ ] T067 [US2] Write test for failed save with error toast at frontend/e2e/settings.spec.ts
- [ ] T068 [US2] Write test for unsaved changes warning on navigation at frontend/e2e/settings.spec.ts

---

## Phase 5: US3 - Design System (P1) (Days 7-10)

**Goal**: Create reusable component library with design tokens

**Priority**: P1 - High priority
**User Story**: US3 - Global Design System Establishment
**Estimated Duration**: 4 days

### 5.1 Design Tokens Definition

- [ ] T069 [P] [US3] Define color palette in Tailwind config at frontend/tailwind.config.js
- [ ] T070 [P] [US3] Define spacing scale (4px/8px grid) at frontend/tailwind.config.js
- [ ] T071 [P] [US3] Define typography system (font families, sizes, weights) at frontend/tailwind.config.js
- [ ] T072 [P] [US3] Define shadow/elevation system at frontend/tailwind.config.js
- [ ] T073 [P] [US3] Define border radius scale at frontend/tailwind.config.js
- [ ] T074 [P] [US3] Define animation/transition tokens at frontend/tailwind.config.js

### 5.2 Core Components

- [ ] T075 [P] [US3] Create Button component with 5 variants at frontend/src/components/ui/Button.tsx
- [ ] T076 [P] [US3] Create Input component with validation support at frontend/src/components/ui/Input.tsx
- [ ] T077 [P] [US3] Create Toggle switch component at frontend/src/components/ui/Toggle.tsx
- [ ] T078 [P] [US3] Create Accordion component with animation at frontend/src/components/ui/Accordion.tsx
- [ ] T079 [P] [US3] Create Card component with header/body/footer at frontend/src/components/ui/Card.tsx
- [ ] T080 [P] [US3] Create Badge component with color variants at frontend/src/components/ui/Badge.tsx
- [ ] T081 [P] [US3] Create Modal component with focus trap at frontend/src/components/ui/Modal.tsx
- [ ] T082 [P] [US3] Create Drawer component for mobile menu at frontend/src/components/ui/Drawer.tsx
- [ ] T083 [P] [US3] Create Select component with options at frontend/src/components/ui/Select.tsx
- [ ] T084 [P] [US3] Create Textarea component with auto-resize at frontend/src/components/ui/Textarea.tsx
- [ ] T085 [P] [US3] Create Spinner loading component at frontend/src/components/ui/Spinner.tsx

### 5.3 Component Documentation

- [ ] T086 [US3] Add JSDoc comments to Button component at frontend/src/components/ui/Button.tsx
- [ ] T087 [US3] Add JSDoc comments to Input component at frontend/src/components/ui/Input.tsx
- [ ] T088 [US3] Add JSDoc comments to Toggle component at frontend/src/components/ui/Toggle.tsx
- [ ] T089 [US3] Add JSDoc comments to Skeleton component at frontend/src/components/ui/Skeleton.tsx
- [ ] T090 [US3] Update barrel export with all components at frontend/src/components/ui/index.ts

### 5.4 Component Usage Examples

- [ ] T091 [P] [US3] Create example usage file for Button variants at frontend/src/components/ui/Button.examples.tsx
- [ ] T092 [P] [US3] Create example usage file for Input types at frontend/src/components/ui/Input.examples.tsx
- [ ] T093 [P] [US3] Create example usage file for form composition at frontend/src/components/ui/Form.examples.tsx

---

## Phase 6: US4 - Responsive Design (P2) (Days 11-12)

**Goal**: Implement mobile and tablet responsive layouts

**Priority**: P2 - Medium priority
**User Story**: US4 - Responsive Design Improvements
**Estimated Duration**: 2 days

### 6.1 Mobile Layouts (<768px)

- [ ] T094 [US4] Make Settings page single-column layout on mobile at frontend/src/pages/SettingsPageModern.tsx
- [ ] T095 [US4] Ensure touch targets are minimum 44x44px at frontend/src/components/ui/Button.tsx
- [ ] T096 [US4] Adjust accordion header padding for mobile at frontend/src/components/ui/Accordion.tsx
- [ ] T097 [US4] Make buttons full-width on mobile screens at frontend/src/pages/SettingsPageModern.tsx

### 6.2 Tablet Layouts (768px-1024px)

- [ ] T098 [US4] Test Settings page at 768px viewport width at frontend/src/pages/SettingsPageModern.tsx
- [ ] T099 [US4] Test navigation at 768px (hamburger transition point) at frontend/src/components/layout/Navigation.tsx
- [ ] T100 [US4] Ensure proper spacing in two-column layouts on tablet at frontend/src/pages/SettingsPageModern.tsx

### 6.3 Responsive Testing

- [ ] T101 [US4] Create responsive E2E test file at frontend/e2e/responsive.spec.ts
- [ ] T102 [US4] Write test for mobile viewport (375px) at frontend/e2e/responsive.spec.ts
- [ ] T103 [US4] Write test for tablet viewport (768px) at frontend/e2e/responsive.spec.ts
- [ ] T104 [US4] Write test for desktop viewport (1440px) at frontend/e2e/responsive.spec.ts
- [ ] T105 [US4] Write test for orientation change (portrait to landscape) at frontend/e2e/responsive.spec.ts

### 6.4 Content Overflow Prevention

- [ ] T106 [US4] Verify no horizontal scrolling at all breakpoints at frontend/src/components/layout/Layout.tsx
- [ ] T107 [US4] Test long text content wrapping on mobile at frontend/src/pages/SettingsPageModern.tsx
- [ ] T108 [US4] Test form input fields at mobile width at frontend/src/components/ui/Input.tsx

---

## Phase 7: US5 - Performance Optimization (P2) (Day 13)

**Goal**: Reduce bundle size by 30% and improve Core Web Vitals

**Priority**: P2 - Medium priority
**User Story**: US5 - Performance Optimization
**Estimated Duration**: 1 day

### 7.1 Bundle Analysis

- [ ] T109 [US5] Run bundle visualizer and analyze largest chunks at frontend/
- [ ] T110 [US5] Identify heavy dependencies for lazy loading at frontend/vite.config.ts
- [ ] T111 [US5] Document current bundle size baseline at frontend/docs/bundle-analysis.md

### 7.2 Dynamic Imports

- [ ] T112 [P] [US5] Lazy load React Query DevTools at frontend/src/App.tsx
- [ ] T113 [P] [US5] Dynamic import Recharts in stats pages at frontend/src/pages/ProofreadingStatsPage.tsx
- [ ] T114 [P] [US5] Dynamic import TipTap editor in review page at frontend/src/pages/ArticleReviewPage.tsx
- [ ] T115 [US5] Update Vite config to remove editor/charts from shared chunks at frontend/vite.config.ts

### 7.3 Tree-Shaking Verification

- [ ] T116 [US5] Convert Ant Design imports to specific imports at frontend/src/ (multiple files)
- [ ] T117 [US5] Create codemod script for Ant Design import transformation at frontend/scripts/antd-transform.js
- [ ] T118 [US5] Run codemod to transform all Ant Design imports at frontend/src/
- [ ] T119 [US5] Verify tree-shaking with build output analysis at frontend/

### 7.4 Image Optimization

- [ ] T120 [P] [US5] Create OptimizedImage component with lazy loading at frontend/src/components/ui/Image.tsx
- [ ] T121 [P] [US5] Add loading="lazy" attribute to all images at frontend/src/ (multiple files)

### 7.5 Performance Testing

- [ ] T122 [US5] Run Lighthouse audit on production build at frontend/
- [ ] T123 [US5] Measure Core Web Vitals (LCP, FID, CLS) at frontend/
- [ ] T124 [US5] Create performance budget configuration at frontend/lighthouserc.json
- [ ] T125 [US5] Add bundle size check script at frontend/scripts/check-bundle-size.js
- [ ] T126 [US5] Verify bundle size is <500KB gzipped at frontend/

---

## Phase 8: Polish & Deployment (Days 13.5-14)

**Goal**: Accessibility audit, cross-browser testing, production deployment

**No [US#] labels in this phase**

### 8.1 Accessibility Audit

- [ ] T127 [P] Install axe-core for accessibility testing at frontend/package.json
- [ ] T128 Create accessibility E2E test file at frontend/e2e/accessibility.spec.ts
- [ ] T129 Run axe-core audit on all pages at frontend/e2e/accessibility.spec.ts
- [ ] T130 Fix any critical accessibility violations at frontend/src/ (multiple files)
- [ ] T131 Verify keyboard navigation works end-to-end at frontend/e2e/accessibility.spec.ts
- [ ] T132 Test with screen reader (NVDA or JAWS) at frontend/

### 8.2 Cross-Browser Testing

- [ ] T133 [P] Test in Chrome 120+ (verify all features work)
- [ ] T134 [P] Test in Firefox 120+ (verify all features work)
- [ ] T135 [P] Test in Safari 16+ (verify all features work)
- [ ] T136 [P] Test in Edge 120+ (verify all features work)
- [ ] T137 Document browser compatibility results at frontend/docs/browser-testing.md

### 8.3 Production Build

- [ ] T138 Run production build with optimizations at frontend/
- [ ] T139 Verify source maps are generated at frontend/dist/
- [ ] T140 Test production build locally at frontend/
- [ ] T141 Run all E2E tests against production build at frontend/

### 8.4 Deployment

- [ ] T142 Deploy to GCS staging environment at frontend/
- [ ] T143 Smoke test staging deployment
- [ ] T144 Deploy to GCS production environment at frontend/
- [ ] T145 Smoke test production deployment
- [ ] T146 Monitor production for errors (first 24 hours)

---

## Implementation Guidelines

### Task Execution Order

**Sequential Dependencies**:
1. Complete Phase 1 (Setup) before starting any other phase
2. Complete Phase 2 (Foundational) before Phase 3-7
3. Phase 3 (US1) should be completed before Phase 4 (US2)
4. Phase 5 (US3) can run parallel with Phase 4 after foundational work
5. Phase 6 (US4) depends on Phase 5 (design system components)
6. Phase 7 (US5) should be done after all features are complete
7. Phase 8 (Polish) is the final phase

**Parallelization Opportunities** (tasks marked with [P]):
- Within Phase 1: All 8 tasks can run in parallel
- Within Phase 2: Tasks T009-T012 can run in parallel
- Within Phase 5.1: All design token tasks (T069-T074) can run in parallel
- Within Phase 5.2: All component creation tasks (T075-T085) can run in parallel
- Within Phase 7.2: Dynamic import tasks (T112-T114) can run in parallel
- Within Phase 8.1: Browser testing tasks (T133-T136) can run in parallel

### Testing Strategy

**E2E Test Coverage Required**:
- Navigation: 7 tests (T028-T034)
- Settings: 6 tests (T063-T068)
- Responsive: 5 tests (T101-T105)
- Accessibility: Full audit with axe-core (T128-T132)

**Performance Metrics Targets**:
- Lighthouse Performance Score: >=90
- LCP (Largest Contentful Paint): <2.5s
- FID (First Input Delay): <100ms
- CLS (Cumulative Layout Shift): <0.1
- Bundle size: <500KB gzipped (30% reduction from 675KB)

### Quality Gates

**Phase 3 (US1) Exit Criteria**:
- [ ] All E2E tests pass (navigation.spec.ts)
- [ ] Navigation text displays on single line at 1280px+ viewports
- [ ] Mobile hamburger menu works at <768px
- [ ] Keyboard navigation functional

**Phase 4 (US2) Exit Criteria**:
- [ ] All E2E tests pass (settings.spec.ts)
- [ ] Skeleton loading displays during data fetch
- [ ] Toast notifications appear and auto-dismiss
- [ ] Form validation errors display correctly
- [ ] Unsaved changes warning works

**Phase 5 (US3) Exit Criteria**:
- [ ] 10+ components created and documented
- [ ] Design tokens centralized in Tailwind config
- [ ] All components have TypeScript interfaces
- [ ] Components support className extension

**Phase 6 (US4) Exit Criteria**:
- [ ] All E2E tests pass (responsive.spec.ts)
- [ ] Mobile layout works at 375px viewport
- [ ] Tablet layout works at 768px viewport
- [ ] No horizontal scrolling at any breakpoint

**Phase 7 (US5) Exit Criteria**:
- [ ] Bundle size <500KB gzipped
- [ ] Lighthouse Performance Score >=90
- [ ] Core Web Vitals meet "Good" thresholds
- [ ] All dynamic imports working

**Phase 8 (Polish) Exit Criteria**:
- [ ] Zero critical axe-core violations
- [ ] All browsers tested (Chrome, Firefox, Safari, Edge)
- [ ] Production deployment successful
- [ ] No console errors in production

---

## Risk Mitigation

### High-Risk Tasks

**T116-T118 (Ant Design Import Transformation)**:
- **Risk**: Breaking existing functionality
- **Mitigation**: Test thoroughly after transformation, maintain backup branch
- **Rollback**: Git revert + restore original imports

**T112-T114 (Dynamic Imports)**:
- **Risk**: Introducing loading race conditions
- **Mitigation**: Add proper Suspense boundaries, test with slow 3G network
- **Rollback**: Remove lazy() wrapper, restore static imports

**T069-T074 (Design Tokens)**:
- **Risk**: Breaking existing Tailwind classes across codebase
- **Mitigation**: Incremental rollout, extend (don't replace) default theme
- **Rollback**: Restore previous tailwind.config.js

### Monitoring & Alerts

**During Implementation**:
- Run E2E tests after each phase completion
- Monitor bundle size after each build
- Check Lighthouse score weekly
- Review axe-core results before deployment

**Post-Deployment**:
- Monitor production error logs (first 24 hours)
- Track Core Web Vitals with RUM
- Monitor API response times
- Track user feedback on new UI

---

## Success Metrics

### Objective Measurements

- [ ] Navigation text displays on single line (verified in 3 browsers)
- [ ] Settings page loading <2s (p95, measured in Playwright)
- [ ] Bundle size <500KB gzipped (CI check)
- [ ] Lighthouse Performance Score >=90 (CI check)
- [ ] Zero axe-core accessibility violations (automated check)
- [ ] All 18 E2E tests pass (Playwright report)
- [ ] Design system has 11 documented components

### Subjective Measurements (User Feedback)

- [ ] User satisfaction with Settings page UX
- [ ] Developer productivity with design system
- [ ] Visual consistency across application
- [ ] Perceived performance improvement

---

## Task Completion Tracking

**Phase 1 (Setup)**: 0/8 tasks (0%)
**Phase 2 (Foundational)**: 0/5 tasks (0%)
**Phase 3 (US1 - Navigation)**: 0/21 tasks (0%)
**Phase 4 (US2 - Settings)**: 0/34 tasks (0%)
**Phase 5 (US3 - Design System)**: 0/25 tasks (0%)
**Phase 6 (US4 - Responsive)**: 0/15 tasks (0%)
**Phase 7 (US5 - Performance)**: 0/18 tasks (0%)
**Phase 8 (Polish)**: 0/20 tasks (0%)

**Overall Progress**: 0/146 tasks (0%)

---

## Notes

### File Paths Reference

**Modified Files**:
- `frontend/src/components/layout/Navigation.tsx` - Navigation fix
- `frontend/src/pages/SettingsPageModern.tsx` - Settings enhancements
- `frontend/src/App.tsx` - Toaster integration
- `frontend/tailwind.config.js` - Design tokens
- `frontend/vite.config.ts` - Bundle optimization
- `frontend/package.json` - Dependencies

**New Files**:
- `frontend/src/components/ui/*.tsx` - Design system components (11 files)
- `frontend/src/hooks/*.ts` - Custom hooks (3 files)
- `frontend/src/schemas/settings-schema.ts` - Validation schemas
- `frontend/e2e/*.spec.ts` - E2E tests (4 files)
- `frontend/scripts/check-bundle-size.js` - CI script
- `frontend/lighthouserc.json` - Performance budget

### Dependencies to Install

```bash
# Core dependencies
npm install sonner  # Toast notifications (15KB)

# Dev dependencies
npm install --save-dev rollup-plugin-visualizer  # Bundle analysis
```

### Estimated Time per Phase

- Phase 1 (Setup): 0.5 days
- Phase 2 (Foundational): 0.5 days
- Phase 3 (US1): 2 days
- Phase 4 (US2): 4 days
- Phase 5 (US3): 4 days
- Phase 6 (US4): 2 days
- Phase 7 (US5): 1 day
- Phase 8 (Polish): 1 day

**Total**: 15 days (includes buffer time)

---

**Document Owner**: Frontend Engineering Team
**Last Updated**: 2025-11-04
**Status**: Ready for Implementation
**Next Review**: After Phase 3 completion
