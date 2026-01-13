/**
 * Hooks Index
 *
 * Central export point for all custom hooks.
 */

export { usePolling, useQueryPolling } from './usePolling';
export type { UsePollingOptions, UsePollingReturn } from './usePolling';

export { useWebSocket, useWebSocketSubscription } from './useWebSocket';
export type { UseWebSocketOptions, UseWebSocketReturn } from './useWebSocket';

export { useUnsavedChanges } from './useUnsavedChanges';

export { useAutoSave, useUnsavedChangesWarning } from './useAutoSave';
export type { SaveStatus, AutoSaveConfig, AutoSaveReturn } from './useAutoSave';
