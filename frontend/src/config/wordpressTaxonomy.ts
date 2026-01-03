/**
 * WordPress taxonomy configuration for DJY Health website.
 * This mirrors the backend configuration in wordpress_taxonomy.py
 *
 * Phase 11: Primary + Secondary category system
 */

// Category hierarchy: Primary Category -> Secondary Categories
// Updated 2026-01-03: New category structure from DJY Health website menu
export const CATEGORY_HIERARCHY: Record<string, string[]> = {
  // 食療養生 - Food Therapy & Health Preservation
  "食療養生": [
    "血糖調節",
    "安神助眠",
    "補氣補血",
    "美容美顏",
    "清肺潤喉",
    "祛濕排毒",
    "健腎健脾",
    "四季養生",
    "養肝養胃",
  ],

  // 中醫寶典 - Traditional Chinese Medicine
  "中醫寶典": [
    "中醫保健",
    "經絡調理",
    "整合醫學",
    "中醫減肥",
    "中草藥",
  ],

  // 心靈正念 - Mindfulness & Mental Health (no subcategories)
  "心靈正念": [],

  // 健康生活 - Healthy Living
  "健康生活": [
    "居家樂活",
    "運動養生",
    "抗老減重",
    "人生健康站",
    "改善記憶力",
  ],

  // 病症查詢 - Disease Lookup (no subcategories)
  "病症查詢": [],

  // 健康專題 - Health Topics
  "健康專題": [
    "糖尿病教育專區",
  ],

  // 醫師專欄 - Doctor's Column (no subcategories)
  "醫師專欄": [],

  // 更多 - More
  "更多": [
    "健康新聞",
    "健康圖解",
    "醫療科技",
    "療癒故事",
    "直播",
    "精選內容",
  ],
};

// Primary categories (main categories that determine URL structure)
export const PRIMARY_CATEGORIES: string[] = Object.keys(CATEGORY_HIERARCHY);

// Flat list of all categories (for backward compatibility)
export const ALL_CATEGORIES: string[] = Object.entries(CATEGORY_HIERARCHY).flatMap(
  ([primary, secondaries]) => [primary, ...secondaries]
);

/**
 * Get secondary categories for a given primary category.
 */
export function getSecondaryCategories(primary: string): string[] {
  return CATEGORY_HIERARCHY[primary] || [];
}

/**
 * Check if a category is a primary category.
 */
export function isPrimaryCategory(category: string): boolean {
  return PRIMARY_CATEGORIES.includes(category);
}

/**
 * Get the parent primary category for a secondary category.
 */
export function getParentCategory(secondary: string): string | null {
  for (const [primary, secondaries] of Object.entries(CATEGORY_HIERARCHY)) {
    if (secondaries.includes(secondary)) {
      return primary;
    }
  }
  return null;
}
