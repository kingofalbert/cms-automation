/**
 * Type definitions for application settings.
 */

import { ProviderType } from './publishing';

/**
 * Provider configuration settings.
 */
export interface ProviderConfig {
  playwright: PlaywrightConfig;
  computer_use: ComputerUseConfig;
  hybrid: HybridConfig;
}

/**
 * Playwright provider configuration.
 */
export interface PlaywrightConfig {
  enabled: boolean;
  headless: boolean;
  timeout: number; // milliseconds
  retry_count: number;
  screenshot_on_error: boolean;
  browser: 'chromium' | 'firefox' | 'webkit';
}

/**
 * Computer Use provider configuration.
 */
export interface ComputerUseConfig {
  enabled: boolean;
  model: string;
  max_tokens: number;
  timeout: number; // milliseconds
  retry_count: number;
  screenshot_interval: number; // milliseconds
}

/**
 * Hybrid provider configuration.
 */
export interface HybridConfig {
  enabled: boolean;
  primary_provider: Exclude<ProviderType, 'hybrid'>;
  fallback_enabled: boolean;
  fallback_on_error: boolean;
  auto_switch_threshold: number; // success rate percentage
}

/**
 * CMS connection configuration.
 */
export interface CMSConfig {
  wordpress_url: string;
  username: string;
  password: string; // Encrypted in storage
  verify_ssl: boolean;
  timeout: number; // milliseconds
  max_retries: number;
}

/**
 * Cost limit settings.
 */
export interface CostLimits {
  daily_limit: number; // USD
  monthly_limit: number; // USD
  per_task_limit: number; // USD
  alert_threshold: number; // Percentage (0-100)
  auto_pause_on_limit: boolean;
}

/**
 * Screenshot retention settings.
 */
export interface ScreenshotRetention {
  retention_days: number;
  max_screenshots_per_task: number;
  compress_screenshots: boolean;
  compression_quality: number; // 0-100
  delete_on_success: boolean;
  delete_on_failure: boolean;
}

/**
 * Complete application settings.
 */
export interface AppSettings {
  provider_config: ProviderConfig;
  cms_config: CMSConfig;
  cost_limits: CostLimits;
  screenshot_retention: ScreenshotRetention;
  updated_at: string;
}

/**
 * Settings update request.
 */
export interface SettingsUpdateRequest {
  provider_config?: Partial<ProviderConfig>;
  cms_config?: Partial<CMSConfig>;
  cost_limits?: Partial<CostLimits>;
  screenshot_retention?: Partial<ScreenshotRetention>;
}
