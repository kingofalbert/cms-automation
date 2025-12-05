/**
 * WordPress taxonomy configuration for DJY Health website.
 * This mirrors the backend configuration in wordpress_taxonomy.py
 *
 * Phase 11: Primary + Secondary category system
 */

// Category hierarchy: Primary Category -> Secondary Categories
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
    "茶 & 湯",
    "四季養生",
    "保健品",
    "養肝養胃",
    "改善記憶力",
  ],

  // 中醫寶典 - Traditional Chinese Medicine
  "中醫寶典": [
    "經絡調理",
    "整合醫學",
    "延緩衰老",
    "中醫理療",
    "中醫保健",
    "中醫減肥",
    "中草藥",
  ],

  // 心靈正念 - Mindfulness & Mental Health
  "心靈正念": [
    "正念冥想",
    "正念飲食",
    "感恩筆記",
    "心靈療癒",
    "正念社交",
    "正念消費",
  ],

  // 醫師專欄 - Doctor's Column
  "醫師專欄": [],

  // 健康新聞 - Health News
  "健康新聞": [],

  // 健康生活 - Healthy Living
  "健康生活": [
    "運動養生",
    "居家樂活",
    "抗老減重",
    "人生健康站",
  ],

  // 醫療科技 - Medical Technology
  "醫療科技": [],

  // 精選內容 - Featured Content
  "精選內容": [
    "特別報導",
    "必備指南",
    "原創系列",
  ],

  // 診室外的醫話 - Doctor's Stories Outside the Clinic
  "診室外的醫話": [],

  // 每日呵護 - Daily Care
  "每日呵護": [
    "今晚睡得好",
    "健康小任務",
    "一念舒心",
    "每週一穴",
    "今日一方",
    "節氣與生活",
    "每日一靜心",
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
